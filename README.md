Adafruit-NextBus
================

Python front-end for the NextBus schedule service, for Raspberry Pi, etc.

routefinder.py: for selecting bus routes/stops for use with the other scripts. Crude textual interface is best used w/terminal with scroll-back ability. Only need to use this for setup, hence the very basic implementation.

predict.py: class that handles periodic queries to the NextBus server. Imported by other scripts; doesn't do anything on its own.

nextbus-simple.py: Minimal front-end to demonstrate use of predict.py. Prints to cosole every 5 seconds.

nextbus-matrix.py: Scrolling marquee using 32x32 RGB LED matrix. Requires rpi-rgb-led-matrix library: https://github.com/adafruit/rpi-rgb-led-matrix
