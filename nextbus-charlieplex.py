# NextBus scrolling marquee display for Adafruit CharliePlex matrices.
# Requires IS31FL3731 library: github.com/adafruit/Adafruit_Python_IS31FL3731
# Also PIL or Pillow library for graphics.

import atexit
import math
import os
import time
from predict import predict
from Adafruit_IS31FL3731 import *
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


# Configurable stuff ---------------------------------------------------------

i2c_address = 0x74  # IS31FL3731 display address

# Use this declaration for an IS31FL3731 16x9 breakout board:
#disp = CharlieBreakout(i2c_address)

# Or this for a 16x8 Pi bonnet:
disp = CharlieBonnet(i2c_address)

# Or this one for a 15x7 FeatherWing:
#disp = CharlieWing(i2c_address)

# List of bus lines/stops to predict.  Use routefinder.py to look up
# lines/stops for your location, copy & paste results here.  The 4th
# string on each line can then be edited for brevity if desired.
# Probably want to keep this short due to tiny display.
stops = [
  ( 'actransit', '210', '0702640', 'Ohlone College' ),
  ( 'actransit', '210', '0702630', 'Union Landing'  ) ]

# Small bitmap version of Helvetica Regular from X11R6 distribution:
font = ImageFont.load(os.path.dirname(os.path.realpath(__file__)) +
       '/helvR08.pil')  # realpath stuff allows run from rc.local
y    = -2  # Vertical position; moved up so descenders aren't cropped

maxPredictions = 3 # NextBus shows up to 5; limit to 3 for simpler display
minTime        = 5 # Drop predictions below this threshold (minutes)
routeColor   = 128 # Brightness for route numbers/letters
descColor    =  16 # " for route direction/description
timeColor    = 128 # " for prediction times
minsColor    =  16 # Commas and 'minutes' labels
noTimesColor =  16 # "No predictions" color

image = Image.new('L', (disp.width, disp.height))
draw  = ImageDraw.Draw(image)
fps   = disp.width  # Scroll width of screen in 1 second

# Draws text at position (x,y), returns x following cursor advance
def advanceX(x, y, label, color):
	draw.text((x, y), label, font=font, fill=color)
	return x + font.getsize(label)[0]

# Clear matrix on exit.  Otherwise it's annoying if you need to break and
# fiddle with some code while LEDs are blinding you.
def clearOnExit():
	disp.selectFrame(0)
	disp.clear()
	disp.update()
	disp.showFrame(0)


# Main application -----------------------------------------------------------

currentTime = 0.0
prevTime    = 0.0
backBuffer  = 1
xx          = 0  # Cursor X position for horizontal scroll


atexit.register(clearOnExit)

# Populate a list of predict objects (from predict.py) from stops[]
predictList = []                       # Clear list
for s in stops:                        # For each item in stops[] list...
	predictList.append(predict(s)) # Create object, add to predictList[]

while True:  # Init done; loop forever...

	# Clear background
	draw.rectangle((0, 0, disp.width, disp.height), fill=0)

	x = xx                 # Start at cursor X
	while x < disp.width:  # Repeat until X off right edge
		for p in predictList:  # For each bus line...
			x = advanceX(x, y, p.data[1] + ' ', routeColor)
			x = advanceX(x, y, p.data[3] + ' ', descColor)
			if p.predictions == []:
				x = advanceX(x, y,
				  'No Predictions', noTimesColor)
			else:
				isFirstShown = True
				count        = 0
				for p2 in p.predictions:
					t = p2 - (currentTime -
					  p.lastQueryTime)
					m = int(t / 60)
					if m <= minTime: continue
					if isFirstShown:
						isFirstShown = False
					else:
						x = advanceX(x, y - 2,
						  ', ', minsColor)
					x = advanceX(x, y, str(m), timeColor)
					count += 1
					if count >= maxPredictions: break
				if count > 0:
					x = advanceX(x, y, ' min', minsColor)
			x = advanceX(x, 0, '  ', 0)  # 2 spaces b/t buses
		# If x is off left edge after all lines have been
		# printed, reset cursor x to that position (outer loop
		# repeats so bus lines are still printed)
		if x < 0: xx = x

	# Select back buffer and push PIL image there:
	disp.selectFrame(backBuffer)
	disp.image(image)
	disp.update()

	# Try to keep timing uniform-ish; rather than sleeping a fixed time,
	# interval since last frame is calculated, the gap time between this
	# and desired frames/sec determines sleep time...occasionally if busy
	# (e.g. polling server) there'll be no sleep at all.
	currentTime = time.time()
	timeDelta   = (1.0 / fps) - (currentTime - prevTime)
	if(timeDelta > 0.0):
		time.sleep(timeDelta)
	prevTime = currentTime

	# Display the newly-pushed image, then invert the front/back index:
	disp.showFrame(backBuffer)
	backBuffer = 1 - backBuffer

	xx -= 1  # Move cursor start left by 1 pixel
