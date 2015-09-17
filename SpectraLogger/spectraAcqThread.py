# -*- coding: UTF-8 -*-

# Wrapper for Test-Equipment-Plus's "SignalHound" series of USB spectrum analysers.
#
# Written By Connor Wolf <wolf@imaginaryindustries.com>

#  * ----------------------------------------------------------------------------
#  * "THE BEER-WARE LICENSE":
#  * Connor Wolf <wolf@imaginaryindustries.com> wrote this file. As long as you retain
#  * this notice you can do whatever you want with this stuff. If we meet some day,
#  * and you think this stuff is worth it, you can buy me a beer in return.
#  * (Only I don't drink, so a soda will do). Connor
#  * Also, support the Signal-Hound devs. Their hardware is pretty damn awesome.
#  * ----------------------------------------------------------------------------
#


import logSetup
import logging
import time
import traceback
import numpy as np

# Pull in the settings crap
from settings import ACQ_FREQ, ACQ_SPAN, ACQ_REF_LEVEL_DB, ACQ_ATTENUATION_DB, ACQ_GAIN_SETTING, ACQ_RBW, ACQ_VBW
from settings import ACQ_SWEEP_TIME_SECONDS, ACQ_WINDOW_TYPE, ACQ_UNITS, ACQ_TYPE, ACQ_MODE, ACQ_Y_SCALE, PRINT_LOOP_CNT, CAL_CHK_LOOP_CNT

from settings import NUM_AVERAGE

def startAcquisition(sh, dataQueue, plotQueue):

	sh.configureAcquisition(ACQ_MODE, ACQ_Y_SCALE)
	sh.configureCenterSpan(center = ACQ_FREQ, span = ACQ_SPAN)
	sh.configureLevel(ref = ACQ_REF_LEVEL_DB, atten = ACQ_ATTENUATION_DB)
	sh.configureGain(gain = ACQ_GAIN_SETTING)
	sh.configureSweepCoupling(rbw = ACQ_RBW, vbw = ACQ_VBW, sweepTime = ACQ_SWEEP_TIME_SECONDS, rbwType = "native", rejection = "no-spur-reject")
	sh.configureWindow(window = ACQ_WINDOW_TYPE)
	sh.configureProcUnits(units = ACQ_UNITS)
	sh.configureTrigger(trigType = "none", edge = "rising-edge", level = 0, timeout = 5)
	# sh.configureIO("dc", "int-ref-out", "out-logic-low")
	# sh.configureDemod("fm", 102.3e6, 250e3, 12e3, 20, 50)

	# sh.configureRawSweep(100, 8, 2)
	try:
		self.startAcquisition(dataQueue, plotQueue)
	except KeyError:
		self.log.error("SignalHound cannot be accessed. Already In use?") 
		self.exit(dataQueues, cmdQueue, FELock, ctrlNs)

	dataQueue.put({"settings" : sh.getCurrentAcquisitionSettings()})
	if plotQueue:
		plotQueue.put({"settings" : sh.getCurrentAcquisitionSettings()})

def sweepSource(dataQueues, cmdQueue, ctrlNs, printQueue):
	dataQueue, plotQueue = dataQueues


	from SignalHound import SignalHound

	logSetup.initLogging(printQ = printQueue)
	loop_timer = time.time()
	print "Starting sweep-logger!"
	log = logging.getLogger("Main.AcqProcess")

	loop_timer = time.time()
	loops = 0

	sh = SignalHound()
	startAcquisition(sh, dataQueue, plotQueue)

	# Send the trace size to the acq thread so I can properly set up the data-log file
	numPoints = sh.queryTraceInfo()["arr-size"]
	dataQueue.put({"arrSize" : numPoints})

	temperature = sh.getDeviceDiagnostics()["temperature"]


	runningSum = np.array(())
	runningSumItems = 0
	startFreq = 0


	while 1:
		# only aquire lock the first time
		if not lockcheck:
			FELock.acquire()
			lockcheck = True
		try:
			trace = sh.fetchTrace()
			traceInfo = sh.queryTraceInfo()
			dataDict = {
							"info": traceInfo,
							"data": trace
						}

			acqInfo = dataDict["info"]
			if runningSum.shape != dataDict["data"]["max"].shape:
				runningSum = np.zeros_like(dataDict["data"]["max"])
				runningSumItems = 0
				startFreq = acqInfo["ret-start-freq"]
				binSize = acqInfo["arr-bin-size"]
				log.info("Running average array size changed! Either the system just started, or something is seriously wrong!")

			changed = False
			if startFreq != acqInfo["ret-start-freq"]:
				changed = True

			else:
				runningSum += dataDict["data"]["max"]
				runningSumItems += 1



			# if we've reached the number of average items per output array, or the frequency has changed, requiring an early dump of the specra data.
			if runningSumItems == NUM_AVERAGE or changed:



				# Divide down to the average
				arr = runningSum / runningSumItems

				# Build array to write out.
				saveTime = time.time()
				# log.info("Saving data record with timestamp %f", saveTime)

				# Only write out to the file if we actually have data
				if runningSumItems != 0:
					if cmdQueue != None:
							cmdQueue.put({"update": "now"})

					dataQueue.put({"row" : (saveTime, startFreq, binSize, runningSumItems, arr)})
					if plotQueue:
						plotQueue.put({"row" : (saveTime, startFreq, binSize, runningSumItems, arr)})


					del(trace)


					runningSum = np.zeros_like(runningSum)
					log.info("Estimated items in processing queue %s", dataQueue.qsize())
					log.info("Running sum shape = %s, items = %s", runningSum.shape, runningSumItems)
					runningSumItems = 0
				if  lockcheck:
					FELock.release()
					lockcheck = False

				# now = time.time()
				# delta = now-loop_timer
				# freq = 1 / (delta)
				# log.info("Elapsed Time = %0.5f, Frequency = %s", delta, freq)
				# loop_timer = now


				# If we wrote the output because the current spectra has changed, we need to update the running acq info variables with the new frequencies.
				if changed:
					log.info("Retuned! Old freq = %s, new freq = %s", startFreq, acqInfo["ret-start-freq"])

					runningSum += dataDict["data"]["max"]
					startFreq = acqInfo["ret-start-freq"]
					binSize = acqInfo["arr-bin-size"]
					runningSumItems = 1




		except Exception:
			if  lockcheck:
				FELock.release()
				lockcheck = False
			log.error("IOError in Acquisition Thread!")
			log.error(traceback.format_exc())

			dataQueue.put({"status" : "Error: Device interface crashed. Reinitializing"})
			log.error("Resetting hardware!")
			# sh.preset()
			sh.forceClose()
			try:
				while 1:
					log.warning("Freeing python device handle")
					del(sh)
			except UnboundLocalError:
				pass

			log.error("Hardware shut down, completely re-initializing device interface!")
			# sys.exit()
			sh = SignalHound()
			startAcquisition(sh, dataQueue, plotQueue)

		if loops % PRINT_LOOP_CNT == 0:
			now = time.time()
			delta = now-loop_timer
			freq = 1 / (delta / PRINT_LOOP_CNT)
			# log.info("Elapsed Time = %0.5f, Frequency = %s", delta, freq)
			loop_timer = now

		if loops % CAL_CHK_LOOP_CNT == 0:
			diags = sh.getDeviceDiagnostics()
			dataQueue.put({"status" : diags})

			temptmp = diags["temperature"]
			if abs(temperature - temptmp) > 2.0:    # Temperature deviations of > 2° cause IF shifts. Therefore, we do a re-cal if they're detected
				dataQueue.put({"status" : "Recalibrating IF"})
				sh.selfCal()
				startAcquisition(sh, dataQueue, plotQueue)
				log.warning("Temperature changed > 2.0 C. Delta is %f. Recalibrated!", abs(temperature - temptmp))
				temperature = temptmp
			else:
				log.info("Temperature deviation = %f. Not doing recal, since drift < 2C", abs(temperature - temptmp))

		loops += 1

		if ctrlNs.run == False:
			if  lockcheck:
				FELock.release()
				lockcheck = False
			log.info("Stopping Acq-thread!")
			break

	if  lockcheck:
		FELock.release()
		lockcheck = False
	sh.abort()
	self.exit(dataQueues, cmdQueue, FELock, ctrlNs)

	def exit(self, dataQueues, cmdQueue, FELock, ctrlNs):
		dataQueue, plotQueue = dataQueues
		
		self.sh.closeDevice()

		del(self.sh)



		self.log.info("Acq-thread closing dataQueue!")
		dataQueue.close()
		dataQueue.join_thread()

		plotQueue.close()
		plotQueue.cancel_join_thread()

		ctrlNs.acqRunning = False

		self.log.warning("Acq-thread exiting!")
		self.printQueue.close()
		self.printQueue.join_thread()
		sys.exit()
 