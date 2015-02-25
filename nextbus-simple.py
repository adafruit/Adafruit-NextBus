# Super simple NextBus display thing (prints to console).

import time
from predict import predict

# List of bus lines/stops to predict.  Use routefinder.py to look up
# lines/stops for your location, copy & paste results here.  The 4th
# element on each line can then be edited for brevity if desired.
stops = [
  ( 'actransit', '210', '0702640', 'Ohlone College' ),
  ( 'actransit', '210', '0702630', 'Union Landing' ),
  ( 'actransit', '232', '0704440', 'Fremont BART' ),
  ( 'actransit', '232', '0704430', 'NewPark Mall' ),
]

# Populate a list of predict objects from stops[].  Each then handles
# its own periodic NextBus server queries.  Can then read or extrapolate
# arrival times from each object's predictions[] list (see code later).
predictList = []
for s in stops:
	predictList.append(predict(s))

time.sleep(1) # Allow a moment for initial results

while True:
	currentTime = time.time()
	print
	for pl in predictList:
		print pl.data[1] + ' ' + pl.data[3] + ':'
		if pl.predictions: # List of arrival times, in seconds
			for p in pl.predictions:
				# Extrapolate from predicted arrival time,
				# current time and time of last query,
				# display in whole minutes.
				t = p - (currentTime - pl.lastQueryTime)
				print '\t' + str(int(t/60)) + ' minutes'
		else:
			print '\tNo predictions'
	prevTime = currentTime;
	time.sleep(5) # Refresh every ~5 seconds
