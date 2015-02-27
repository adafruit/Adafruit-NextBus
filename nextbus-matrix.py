# NextBus scrolling marquee display for Adafruit RGB LED matrix (64x32).
# Requires rgbmatrix.so library: github.com/adafruit/rpi-rgb-led-matrix

import atexit
import Image
import ImageDraw
import ImageFont
import math
import time
from predict import predict
from rgbmatrix import Adafruit_RGBmatrix

# Configurable stuff ---------------------------------------------------------

# List of bus lines/stops to predict.  Use routefinder.py to look up
# lines/stops for your location, copy & paste results here.  The 4th
# string on each line can then be edited for brevity if desired.
stops = [
  ( 'actransit', '210', '0702640', 'Ohlone College' ),
  ( 'actransit', '232', '0704440', 'Fremont BART'   ),
  ( 'actransit', '210', '0702630', 'Union Landing'  ),
  ( 'actransit', '232', '0704430', 'NewPark Mall'   ) ]

maxPredictions = 3   # NextBus shows up to 5; limit to 3 for simpler display
minTime        = 0   # Drop predictions below this threshold (minutes)
shortTime      = 5   # Times less than this are displayed in red
midTime        = 10  # Times less than this are displayed yellow

width          = 64  # Matrix size (pixels) -- change for different matrix
height         = 32  # types (incl. tiling).  Other code may need tweaks.
matrix         = Adafruit_RGBmatrix(32, 2) # rows, chain length
fps            = 20  # Scrolling speed (ish)

routeColor     = (255, 255, 255) # Color for route labels (usu. numbers)
descColor      = (110, 110, 110) # " for route direction/description
longTimeColor  = (  0, 255,   0) # Ample arrival time = green
midTimeColor   = (255, 255,   0) # Medium arrival time = yellow
shortTimeColor = (255,   0,   0) # Short arrival time = red
minsColor      = (110, 110, 110) # Commans and 'minutes' labels
noTimesColor   = (  0,   0, 255) # No predictions = blue

# TrueType fonts are a bit too much for the Pi to handle -- slow updates and
# it's hard to get them looking good at small sizes.  A small bitmap version
# of Helvetica Regular taken from X11R6 standard distribution works well:
font           = ImageFont.load('helvR08.pil')
fontYoffset    = -2  # Scoot up a couple lines so descenders aren't cropped


# Main application -----------------------------------------------------------

# Drawing takes place in offscreen buffer to prevent flicker
image       = Image.new('RGB', (width, height))
draw        = ImageDraw.Draw(image)
currentTime = 0.0
prevTime    = 0.0

# Clear matrix on exit.  Otherwise it's annoying if you need to break and
# fiddle with some code while LEDs are blinding you.
def clearOnExit():
	matrix.Clear()

atexit.register(clearOnExit)

# Populate a list of predict objects (from predict.py) from stops[].
# While at it, also determine the widest tile width -- the labels
# accompanying each prediction.  The way this is written, they're all the
# same width, whatever the maximum is we figure here.
tileWidth = font.getsize(
  '88' *  maxPredictions    +          # 2 digits for minutes
  ', ' * (maxPredictions-1) +          # comma+space between times
  ' minutes')[0]                       # 1 space + 'minutes' at end
w = font.getsize('No Predictions')[0]  # Label when no times are available
if w > tileWidth:                      # If that's wider than the route
	tileWidth = w                  # description, use as tile width.
predictList = []                       # Clear list
for s in stops:                        # For each item in stops[] list...
	predictList.append(predict(s)) # Create object, add to predictList[]
	w = font.getsize(s[1] + ' ' + s[3])[0] # Route label
	if(w > tileWidth):                     # If widest yet,
		tileWidth = w                  # keep it
tileWidth += 6                         # Allow extra space between tiles


class tile:
	def __init__(self, x, y, p):
		self.x = x
		self.y = y
		self.p = p  # Corresponding predictList[] object

	def draw(self):
		x     = self.x
		label = self.p.data[1] + ' ' # Route number or code
		draw.text((x, self.y + fontYoffset), label, font=font,
		  fill=routeColor)
		x    += font.getsize(label)[0]
		label = self.p.data[3]       # Route direction/desc
		draw.text((x, self.y + fontYoffset), label, font=font,
		  fill=descColor)
		x     = self.x
		if self.p.predictions == []: # No predictions to display
			draw.text((x, self.y + fontYoffset + 8),
			  'No Predictions', font=font, fill=noTimesColor)
		else:
			isFirstShown = True
			count        = 0
			for p in self.p.predictions:
				t = p - (currentTime - self.p.lastQueryTime)
				m = int(t / 60)
				if   m <= minTime:   continue
				elif m <= shortTime: fill=shortTimeColor
				elif m <= midTime:   fill=midTimeColor
				else:                fill=longTimeColor
				if isFirstShown:
					isFirstShown = False
				else:
					label = ', '
					# The comma between times needs to
					# be drawn in a goofball position
					# so it's not cropped off bottom.
					draw.text((x + 1,
					  self.y + fontYoffset + 8 - 2),
					  label, font=font, fill=minsColor)
					x += font.getsize(label)[0]
				label  = str(m)
				draw.text((x, self.y + fontYoffset + 8),
				  label, font=font, fill=fill)
				x     += font.getsize(label)[0]
				count += 1
				if count >= maxPredictions:
					break
			if count > 0:
				draw.text((x, self.y + fontYoffset + 8),
				  ' minutes', font=font, fill=minsColor)


# Allocate list of tile objects, enough to cover screen while scrolling
tileList = []
if tileWidth >= width: tilesAcross = 2
else:                  tilesAcross = int(math.ceil(width / tileWidth)) + 1

nextPrediction = 0  # Index of predictList item to attach to tile
for x in xrange(tilesAcross):
	for y in xrange(0, 2):
		tileList.append(tile(x * tileWidth + y * tileWidth / 2, 
		  y * 17, predictList[nextPrediction]))
		nextPrediction += 1
		if nextPrediction >= len(predictList):
			nextPrediction = 0

# Initialization done; loop forever ------------------------------------------
while True:

	# Clear background
	draw.rectangle((0, 0, width, height), fill=(0, 0, 0))

	for t in tileList:
		if t.x < width:        # Draw tile if onscreen
			t.draw()
		t.x -= 1               # Move left 1 pixel
		if(t.x <= -tileWidth): # Off left edge?
			t.x += tileWidth * tilesAcross     # Move off right &
			t.p  = predictList[nextPrediction] # assign prediction
			nextPrediction += 1                # Cycle predictions
			if nextPrediction >= len(predictList):
				nextPrediction = 0

	# Try to keep timing uniform-ish; rather than sleeping a fixed time,
	# interval since last frame is calculated, the gap time between this
	# and desired frames/sec determines sleep time...occasionally if busy
	# (e.g. polling server) there'll be no sleep at all.
	currentTime = time.time()
	timeDelta   = (1.0 / fps) - (currentTime - prevTime)
	if(timeDelta > 0.0):
		time.sleep(timeDelta)
	prevTime = currentTime

	# Offscreen buffer is copied to screen
	matrix.SetImage(image.im.id, 0, 0)
