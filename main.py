import sys, os
import numpy as np
try: # Pillow
  from PIL import Image, ImageDraw
except:
  print 'Error: Pillow has not been installed.'
  sys.exit(0)
try: # PyOpenGL
  from OpenGL.GLUT import *
  from OpenGL.GL import *
  from OpenGL.GLU import *
except:
  print 'Error: PyOpenGL has not been installed.'
  sys.exit(0)
import Tkinter, tkFileDialog

# window dimensions

windowWidth  = 600
windowHeight =  800

# Linear Scaling (y = mx + b)

contrast = 1 # slope (m) of linear function.
brightness = 0 # intercept (b) of linear function.

# Image directory and path to image file

imgDir      = 'images'
imgFilename = 'mandrill.png'
imgPath = os.path.join(imgDir, imgFilename)

# Name of the filter and attributes

filterName = 'shift2right'

# Dimensions and scale of the filter

newFilter = [] # Filter weights to be applied
xdimFilter = 0
ydimFilter = 0
scale = 0

# Radius around the mouse the filter will be applied to

radius = 50
button = None

# Pre- and Post- operation images.

currentImage = None
newImage = None

# File dialog

root = Tkinter.Tk()
root.withdraw()

def imageToArray (image):
    """Converts an image into a three-dimensional numpy array."""

    array = np.array(image, dtype = 'uint8')

    return array
def arrayToImage (array):
    """Converts a three-dimensional numpy array into an YCbCr image."""

    image = Image.fromarray(array, 'YCbCr')

    return image

def histogramEqualization ():
    """Applies histogram equalization to the current image."""
    
    global currentImage, newImage
    
    ycbcr = currentImage.convert('YCbCr')

    array = imageToArray(ycbcr)

    bins = 256 # Number of bins in the histogram. Corresponds to the intensity range for each pixel.
    pixels = float(currentImage.width * currentImage.height)

    frequencies = np.bincount(array[:,:,0].flatten(), minlength=bins) # Returns the frequency of each intensity value occurring.
    equalizedFrequencies = np.zeros(bins)
    
    mapping = dict()
    
    for r in range(bins):
        
        # Creates a mapping of every intensity r in the current image to an intensity s in the new image.
        
        s = int(np.clip(round((bins/pixels) * np.sum(frequencies[0:r]) - 1), 0, 255))


        equalizedFrequencies[s] += frequencies[r]
        mapping[r] = s

    vfunc = np.vectorize(mapping.get)

    array[:,:,0] = vfunc(array[:,:,0])

    ycbcr = arrayToImage(array)
    newImage = ycbcr.convert('RGB')

    currentImage = newImage

    #draw = ImageDraw.Draw(currentImage)
    #draw.text((0, 0),"Sample Text",(255,255,255))

# Question 5
def loadFilter() :
    """Loads the specified filter (in global variables) from its file."""
    
    f = open(os.path.join( 'filters', filterName ), 'r')
    
    # Read the first 2 numbers as xdimFilter and ydimFilter
    global xdimFilter, ydimFilter, scale
    xdimFilter, ydimFilter = [int(x) for x in next(f).split()]
    
    # Read in the next number as the scale
    scale = float(next(f))
    
    # Read the filter weights into the 1D array newFilter
    for line in f:
      for word in line.split():
        newFilter.append(int(word))

# Question 6
def convolveFull():
    """Performs convolving on the full image."""
  
    # Check if the filter has been loaded yet
    if (xdimFilter == 0 or ydimFilter == 0):
      print 'No filter has been loaded.'
      return
  
    global newImage
    newImage = currentImage
    
    # Convert the image to a YCbCr array
    newImage = newImage.convert('YCbCr')
    newImage = imageToArray(newImage)

    width = newImage.shape[1]
    height = newImage.shape[0]
    xStart = 0
    yStart = 0

    #Define the size (x and y) of the filtered image (boundary of the filter)
    rx = xdimFilter + (width-1)
    ry = ydimFilter + (height-1)
    #Create a 1D array to store the new values (after filtering)
    filteredImage = np.empty(shape=(rx*ry), dtype='uint8')
    k = -1
  
    #Create new values via convolving
    for y in range(yStart, ry + yStart):
      for x in range(xStart, rx + xStart):
        k += 1 # k corresponds to the pixel being valued
        newValue = 0
        for i in range(0, xdimFilter):
          for j in range(0, ydimFilter):
            newValue = newValue + lookupFilter(i, j) * lookupImage(x-i, y-j, width+xStart, height+yStart)
            filteredImage[k] = newValue

    # Transfer the new pixel values into the image 
    createImage(xStart, yStart, filteredImage, height + yStart, width + xStart, [])

    # Convert it back into RGBso it can be displayed
    newImage = arrayToImage(newImage)
    newImage = newImage.convert('RGB')
    global currentImage
    currentImage = newImage

# Question 7
def convolveRadius(xClick, yClick):
    """Performs convolving within the radius of the mouse."""
  
    # Check if the filter has been loaded yet
    if (xdimFilter == 0 or ydimFilter == 0):
      print 'No filter has been loaded.'
      return
  
    global newImage
    newImage = currentImage
    
    # Convert the image to a YCbCr array
    newImage = newImage.convert('YCbCr')
    newImage = imageToArray(newImage)

    topX, topY = findTopLeft() # Givcs the top left corner of the image
    
    # If the click is farther away from the image than the radius
    if (xClick < topX - radius or xClick > topX + newImage.shape[1] + radius
        or yClick < topY - radius or yClick > topY + newImage.shape[0] + radius):
      return
    width = radius * 2
    height = radius * 2
    xStart = xClick - topX - radius 
    yStart = yClick - topY - radius 

    #Define the size (x and y) of the filtered image (boundary of the filter)
    rx = xdimFilter + (width-1)
    ry = ydimFilter + (height-1)

    #Create a 1D array to store the new values (after filtering)
    filteredImage = np.empty(shape=(rx*ry), dtype='uint8')
    k = -1

    # Will store the pixels that are not in the circular radius but within the
    # square radius (used for modifying the image after)
    noValue = []
  
    #Create new values via convolving
    for y in range(yStart, ry + yStart):
      for x in range(xStart, rx + xStart):
        k += 1 # k corresponds to the pixel being valued
        newValue = 0
        
        # Check if the pixel is inside the radius (if on click) or
        # if either x or y are less than 0 
        if ((xClick != -1 and not checkInRadius(x, y, xStart + radius, yStart + radius))
          or x < 0 or y < 0 or x >= newImage.shape[1] or y >= newImage.shape[0]):
            noValue.append([x-int(xdimFilter/2),y-int(ydimFilter/2)])
            continue # Don't calculate the new pixel value
          
        for i in range(0, xdimFilter):
          for j in range(0, ydimFilter):
            newValue = newValue + lookupFilter(i, j) * lookupImage(x-i, y-j, width+xStart, height+yStart)
            filteredImage[k] = newValue

    # Transfer the new pixel values into the image 
    createImage(xStart, yStart, filteredImage, height + yStart, width + xStart, noValue)

    # Convert it back into RGBso it can be displayed
    newImage = arrayToImage(newImage)
    newImage = newImage.convert('RGB')
    global currentImage
    currentImage = newImage
    
def lookupImage(x, y, xdim, ydim):
    """Used to lookup a pixel value within the image (2D array)."""
  
    if (x < 0 or x >= xdim or y < 0 or y >= ydim or x > newImage.shape[1] or y > newImage.shape[0]):
      return 0
    return newImage[y,x,0]

def lookupFilter(x, y):
    """Used to lookup a pixel value within the filter (1D array)."""
  
    if (x < 0 or x >= xdimFilter or y < 0 or y >= ydimFilter):
      return 0
    return newFilter[x+(y*xdimFilter)] * scale

def findTopLeft():
    """Finds the top left corner of the picture, used to detect where the
      click is in relation to the image."""
    width = newImage.shape[1]
    height = newImage.shape[0]
    topX = (windowWidth-width)/2
    topY = (windowHeight-height)/2
    return topX, topY

def checkInRadius(x, y, xClick, yClick):
    """Check if the given pixel is within the radius around the orgin
      (xClick, yClick)."""
    xComponent = x - xClick
    yComponent = y - yClick
    return np.sqrt((xComponent * xComponent) + (yComponent * yComponent)) <= radius


def createImage(xStart, yStart, filteredImage, height, width, noValue):
    """Combines the 1D filteredImage array with the newImage array in order to
        create a new image."""
    for y in range(yStart, height):
      for x in range(xStart, width):
        # If the pixel is outside the image/radius, don't need to change it
        if (x > newImage.shape[1] - 1 or y > newImage.shape[0] - 1 or ([x,y] in noValue)):
          continue

        # Used to correct screen wrapping in the radius filtering
        if (x < 0):
          x = x + int(xdimFilter/2)
        if (y < 0):
          y = y + int(ydimFilter/2)
        
        # Calculates the idex within the 1D new image array
        index = (x-xStart+int(xdimFilter/2))+((y-yStart+int(ydimFilter/2))*(width-xStart+xdimFilter-1))
        value = filteredImage[index]

        # Modify the value in tfhe new image
        newImage[y,x,0] = value

def buildImage ():
    """Propogates changes in brightness and contrast to the new image."""
    
    global currentImage, newImage

    if currentImage == None:
        currentImage = Image.open(imgPath)
        
    ycbcr = currentImage.convert('YCbCr')
    array = imageToArray(ycbcr)

    array[:,:,0] = np.clip((array[:,:,0] * contrast + brightness), 0, 255)
    
    ycbcr = arrayToImage(array)
    newImage = ycbcr.convert('RGB')

# Set up the display and draw the current image

def display():
    
    # Clear window

    glClearColor (1, 1, 1, 0)
    glClear(GL_COLOR_BUFFER_BIT)

    # rebuild the image

    buildImage()

    width  = currentImage.width
    height = currentImage.height

    # Find where to position lower-left corner of image

    baseX = (windowWidth-width)/2
    baseY = (windowHeight-height)/2

    glWindowPos2i(baseX, baseY)

    # Get pixels and draw

    array = np.flip(imageToArray(currentImage),0)

    glDrawPixels(width, height, GL_RGB, GL_UNSIGNED_BYTE, array)

    glutSwapBuffers()
  
# Handle keyboard input

def keyboard(key, x, y):

    if key == '\033': # ESC = exit
        sys.exit(0)
    elif key == 'l':
        inputPath = tkFileDialog.askopenfilename(initialdir = imgDir)
        if inputPath:
            loadImage(inputPath)
    elif key == 's':
        outputPath = tkFileDialog.asksaveasfilename(initialdir = '.')
        if outputPath:
            saveImage(outputPath)
    elif key == 'h':
        histogramEqualization()
    elif key == 'f':
        loadFilter()
    elif key == 'a':
        convolveFull()
    elif key == '=' or key == '+':
      global radius
      radius = radius + 1
      print 'Radius is now {0}'.format(radius)
    elif key == '-' or key == '_':
      global radius
      radius = radius - 1
      print 'Radius is now {0}'.format(radius)

    else:
        print 'key =', key

    glutPostRedisplay()

# Load and save images.

def loadImage(path):
    
    global imgPath, currentImage
    imgPath = path
    currentImage = None
    
def saveImage(path):

  currentImage.save(path)

# Handle window reshape

def reshape(newWidth, newHeight):

  global windowWidth, windowHeight

  windowWidth  = newWidth
  windowHeight = newHeight

  glutPostRedisplay()

# Mouse state on initial click

button = None
initX = 0
initY = 0
initContrast = 0
initBrightness = 0

# Handle mouse click/unclick

def mouse(btn, state, x, y):

    global currentImage, initX, initY, initContrast, contrast, initBrightness, brightness, button

    if state == GLUT_DOWN:
        
        if(btn == GLUT_LEFT_BUTTON):
            button = btn
            initX = x
            initY = y
            initContrast = contrast
            initBrightness = brightness
        elif(btn == GLUT_RIGHT_BUTTON):
            button = btn
            convolveRadius(x, y)
    elif state == GLUT_UP:

        currentImage = newImage
        contrast = 1
        brightness = 0

        button = None
        
# Handle mouse motion

def motion( x, y ):

    diffX = x - initX
    diffY = y - initY

    global contrast, brightness

    contrast = initContrast + diffY / float(windowHeight)
    brightness = initBrightness + diffX / float(windowWidth)

    if contrast < 0:
        contrast = 0
    if brightness < 0:
        brightness = 0

    if(button == GLUT_RIGHT_BUTTON):
      convolveRadius(x, y)

    glutPostRedisplay()
    
# Run OpenGL

glutInit()
glutInitDisplayMode( GLUT_DOUBLE | GLUT_RGB )
glutInitWindowSize( windowWidth, windowHeight )
glutInitWindowPosition( 50, 50 )

glutCreateWindow( 'imaging' )

glutDisplayFunc( display )
glutKeyboardFunc( keyboard )
glutReshapeFunc( reshape )
glutMouseFunc( mouse )
glutMotionFunc( motion )

glutMainLoop()
