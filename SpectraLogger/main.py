# -*- coding: UTF-8 -*-

# Wrapper for Test-Equipment-Plus's "SignalHound" series of USB spectrum analysers.
#
# Written By Connor Wolf <wolf@imaginaryindustries.com>
#

#  * ----------------------------------------------------------------------------
#  * "THE BEER-WARE LICENSE":
#  * Connor Wolf <wolf@imaginaryindustries.com> wrote this file. As long as you retain
#  * this notice you can do whatever you want with this stuff. If we meet some day,
#  * and you think this stuff is worth it, you can buy me a beer in return.
#  * (Only I don't drink, so a soda will do). Connor
#  * Also, support the Signal-Hound devs. Their hardware is pretty damn awesome.
#  * ----------------------------------------------------------------------------
#

# pylint: disable=R0913, R0912, W0603

import multiprocessing as mp
import sys
import logSetup
import logging
import spectraAcqThread
import internalSweepSpectraAcqThread
import spectraLogThread
import eoreSpectraLogThread

import spectraPlotApiThread
import printThread
import EOREsettings
import settings


def go(logGps=False, gpsTest=False, logEORE = False):

	plotQueue = mp.Queue()
	dataQueue = mp.Queue()
	printQueue = mp.Queue()
	cmdQueue = mp.Queue()
	ctrlManager = mp.Manager()
	FELock = mp.Lock()

	logSetup.initLogging(printQ = printQueue)
	log = logging.getLogger("Main.Main")

	ctrlNs = ctrlManager.Namespace()
	ctrlNs.run = True
	ctrlNs.acqRunning = True
	ctrlNs.apiRunning = True
	ctrlNs.logRunning = True
	ctrlNs.stopped = False

	if not settings.GPS_COM_PORT:
		print("WARNING: No GPS port specified. GPS mode can not work.")
	

	if not gpsTest :
		if settings.ACQ_TYPE == "real-time-sweeping":
			print("Importing real-time-sweeping module!")
			acqProc = mp.Process(target=internalSweepSpectraAcqThread.sweepSource, name="AcqThread", args=((dataQueue, plotQueue), cmdQueue, FELock, ctrlNs, printQueue))
		else:
			print("Importing real-time module!")
			acqProc = mp.Process(target=spectraAcqThread.sweepSource, name="AcqThread", args=((dataQueue, plotQueue), cmdQueue, FELock, ctrlNs, printQueue))

		acqProc.start()

	if logEORE:
		import EOREsettings
		import eoreLogThread
		if not EOREsettings.EORE_COM_PORT:
			print("WARNING: No EORE port specified. EORE mode can not work.")

		EOREProc = mp.Process(target=eoreLogThread.startEORELog, name="EOREThread", args=((dataQueue, plotQueue), cmdQueue, FELock, ctrlNs, printQueue))
		EOREProc.start()
		logProc = mp.Process(target=eoreSpectraLogThread.logSweeps, name="LogThread", args=(dataQueue, ctrlNs, printQueue, gpsTest))
		logProc.start()


	if logGps and settings.GPS_COM_PORT:
		import gpsLogThread
		gpsProc = mp.Process(target=gpsLogThread.startGpsLog, name="GpsThread", args=((dataQueue, plotQueue), ctrlNs, printQueue))
		gpsProc.start()


	if not logEORE:
		logProc = mp.Process(target=spectraLogThread.logSweeps, name="LogThread", args=(dataQueue, ctrlNs, printQueue, gpsTest))
		logProc.start()

	if not gpsTest:
		plotProc = mp.Process(target=spectraPlotApiThread.startApiServer, name="PlotApiThread", args=(plotQueue, ctrlNs, printQueue))
		plotProc.start()


	# A separate process for printing, which allows nice easy non-blocking printing.
	printProc = mp.Process(target=printThread.printer, name="PrintArbiter", args=(printQueue, ctrlNs))
	printProc.daemon = True
	printProc.start()


	try:
		while 1:
			inStr = raw_input()
			print inStr
			if inStr == "q":
				break


	except KeyboardInterrupt:
		pass



	log.info("Stopping Processes!")


	ctrlNs.run = False

	# You have to empty the queue for everything to exit properly
	log.info("Emptying Queue")

	# Sometimes the last few queue items take a little while to trickle in.
	# therefore, we both poll the queue for items, and try to join() the thread. That way
	# as soon as the queue is *actually* empty, we exit immediately
	# - - -
	# this was a fucking nightmare to track down.


	if not gpsTest:
		log.info("Joining on AcqProc")
		while acqProc.is_alive():
			acqProc.join(0.1)

	if logGps and settings.GPS_COM_PORT:
		log.info("Joining on GpsProc")
		while gpsProc.is_alive():
			gpsProc.join(0.1)

		if gpsTest:
			print("Faking halt signals")
			ctrlNs.acqRunning = False

	if logEORE:
		log.info("Joining on EOREProc")
		while EOREProc.is_alive():
			EOREProc.join(0.1)


		# print("acqProc.is_alive()", acqProc.is_alive(), "logProc.is_alive()", logProc.is_alive(), "plotProc.is_alive()", plotProc.is_alive())
	log.info("Joining on LogProc")
	while logProc.is_alive():
		logProc.join(0.1)
		# print("acqProc.is_alive()", acqProc.is_alive(), "logProc.is_alive()", logProc.is_alive(), "plotProc.is_alive()", plotProc.is_alive())


	if not gpsTest:
		log.info("Joining on PlotProc")
		while plotProc.is_alive():
			plotProc.join(0.1)
			# print("acqProc.is_alive()", acqProc.is_alive(), "logProc.is_alive()", logProc.is_alive(), "plotProc.is_alive()", plotProc.is_alive())

	if gpsTest:
		print("Faking halt signals")
		ctrlNs.apiRunning = False

	print("Joining on PrintProc")
	while printProc.is_alive():
		printProc.join(0.05)
		print("wating on printProc")



	print("Threads stopped.")
	print("Stopping Shared Memory Manager.")
	ctrlManager.shutdown()

	print("Shutdown complete. Exiting.")

	sys.exit()

def parseArgs():
	if len(sys.argv) == 1:
		print("Python Signal-Hound spectra logging tool.")
		print("")
		print("	Error: No arguments specified.")
		print("")
		print("	Arguments")
		print("		--go         Begin acquisition (if not specified, this message is printed)")
		print("		--gps        Take GPS data. Requires a USB GPS if specified.")
		print("		--gps-only   Take GPS data and *not* spectra. Intended for verifying GPS functionality.")
		print("		--eore       Log EORE state with data.")


		return

	availableArgs = ["--go", "--gps", "--gps-only", "--eore"]

	args = sys.argv[1:]

	badArgs = [arg for arg in args if arg not in availableArgs]

	if badArgs:
		print("ERROR")
		print("Invalid command line argument")
		for arg in badArgs:
			print ("Did not understand '%s'" % arg)
		return

	logGps = False
	if "--gps" in args:
		logGps = True
		print("Taking GPS position data. Please ensure you have a GPS device connected")

	gpsTest = False
	if "--gps-only" in args:
		logGps = True
		gpsTest = True
		print("GPS Testing mode. Will not take actual spectra!")

	logEORE = False
	if "--eore" in args:
		logEORE= True
		print("Logging EORE data. Please ensure you have a EORE connected")

	if '--go' in args:
		go(logGps=logGps, gpsTest=gpsTest, logEORE=logEORE)
	else:
		print("'--go' was not passed. Not doing actual acquisition.")

if __name__ == "__main__":

	parseArgs()