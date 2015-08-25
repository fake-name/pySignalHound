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

IF_WIDTH = 27e6


import logSetup
import logging
import time
import traceback
from multiprocessing import Lock

import numpy as np

# Pull in the settings crap
from settings import ACQ_FREQ, ACQ_SPAN, ACQ_REF_LEVEL_DB, ACQ_ATTENUATION_DB, ACQ_GAIN_SETTING, ACQ_RBW, ACQ_VBW, ACQ_OVERLAP, ACQ_BIN_SAMPLES
from settings import ACQ_SWEEP_TIME_SECONDS, ACQ_WINDOW_TYPE, ACQ_UNITS, ACQ_TYPE, ACQ_MODE, ACQ_Y_SCALE, PRINT_LOOP_CNT, CAL_CHK_LOOP_CNT
from settings import NUM_AVERAGE

def sweepSource(dataQueues,  cmdQueue, FELock, ctrlNs, printQueue):
	acqRunner = InternalSweepAcqThread(printQueue)
	acqRunner.sweepSource(dataQueues, cmdQueue, FELock, ctrlNs)

class InternalSweepAcqThread(object):
	log = logging.getLogger("Main.AcqProcess")

	def __init__(self, printQueue):
		self.printQueue = printQueue
		logSetup.initLogging(printQ=printQueue)

		self.calcScanBands()

		if ACQ_TYPE != "real-time-sweeping":
			raise ValueError("internalSweep module only supports 'real-time-sweeping' mode! Configured mode = {mode}".format(mode=ACQ_TYPE))

	def calcScanBands(self):
		if ACQ_SPAN < IF_WIDTH:
			raise ValueError("Scan width is smaller then the IF bandwidth!")
		if ACQ_SPAN == IF_WIDTH:
			raise ValueError("Scan width is exactly the IF bandwith. Maybe use the real-time mode instead?")

		sweepWidth = IF_WIDTH * (1-ACQ_OVERLAP)
		bins = ACQ_SPAN/sweepWidth
		sweepSteps = int(bins+0.5)

		effectiveScanWidth = sweepWidth*sweepSteps

		self.binFreqs = []
		baseFreq = ACQ_FREQ - (effectiveScanWidth/2 + sweepWidth/2)

		for x in xrange(1, sweepSteps+1):
			self.binFreqs.append(baseFreq+x*sweepWidth)

		self.binFreqIndice = 0

	def retune(self):
		self.sh.configureCenterSpan(center = self.binFreqs[self.binFreqIndice], span = IF_WIDTH)
		self.binFreqIndice = (self.binFreqIndice + 1) % len(self.binFreqs)


	def startAcquisition(self, dataQueue, plotQueue):


		self.sh.configureAcquisition(ACQ_MODE, ACQ_Y_SCALE)

		self.retune()

		self.sh.configureLevel(ref = ACQ_REF_LEVEL_DB, atten = ACQ_ATTENUATION_DB)
		self.sh.configureGain(gain = ACQ_GAIN_SETTING)
		self.sh.configureSweepCoupling(rbw = ACQ_RBW, vbw = ACQ_VBW, sweepTime = ACQ_SWEEP_TIME_SECONDS, rbwType = "native", rejection = "no-spur-reject")
		self.sh.configureWindow(window = ACQ_WINDOW_TYPE)
		self.sh.configureProcUnits(units = ACQ_UNITS)
		self.sh.configureTrigger(trigType = "none", edge = "rising-edge", level = 0, timeout = 5)

		self.sh.initiate(mode = "real-time", flag = "ignored")



		dataQueue.put({"settings" : self.sh.getCurrentAcquisitionSettings()})
		plotQueue.put({"settings" : self.sh.getCurrentAcquisitionSettings()})

	def sweepSource(self, dataQueues, cmdQueue, FELock, ctrlNs):

		dataQueue, plotQueue = dataQueues


		from SignalHound import SignalHound


		loop_timer = time.time()
		print "Starting sweep-logger!"

		loop_timer = time.time()
		loops = 0

		self.sh = SignalHound()
		self.startAcquisition(dataQueue, plotQueue)

		# Send the trace size to the acq thread so I can properly set up the data-log file
		numPoints = self.sh.queryTraceInfo()["arr-size"]
		dataQueue.put({"arrSize" : numPoints})

		temperature = self.sh.getDeviceDiagnostics()["temperature"]


		runningSum = np.array(())
		runningSumItems = 0
		startFreq = 0
		lockcheck = False

		while 1:
			# only aquire lock the first time
			if not lockcheck:
				try:
					FELock.acquire()
					lockcheck = True
				except LockTimeout:
					self.log.error("Spectral Acquisition Thread is Deadlocked!")
			try:


				trace = self.sh.fetchTrace()
				traceInfo = self.sh.queryTraceInfo()
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
					self.log.info("Running average array size changed! Either the system just started, or something is seriously wrong!")

				changed = False
				if startFreq != acqInfo["ret-start-freq"]:
					changed = True

				else:
					runningSum += dataDict["data"]["max"]
					runningSumItems += 1



				# if we've reached the number of average items per output array, or the frequency has changed, requiring an early dump of the specra data.
				# since data is no loger being aquired, the lock can be released
				if runningSumItems == NUM_AVERAGE or changed:
					self.log.info("Running sum shape = %s, items = %s", runningSum.shape, runningSumItems)
					# Divide down to the average
					arr = runningSum / runningSumItems

					# Build array to write out.
					saveTime = time.time()
					# self.log.info("Saving data record with timestamp %f", saveTime)

					# Only write out to the file if we actually have data
					if runningSumItems != 0:


						dataQueue.put({"row" : (saveTime, startFreq, binSize, runningSumItems, arr)})
						if plotQueue:
							plotQueue.put({"row" : (saveTime, startFreq, binSize, runningSumItems, arr)})





						runningSum = np.zeros_like(runningSum)
						self.log.info("Estimated items in processing queue %s", dataQueue.qsize())
						self.log.info("Running sum shape = %s, items = %s", runningSum.shape, runningSumItems)
						runningSumItems = 0

					# now = time.time()
					# delta = now-loop_timer
					# freq = 1 / (delta)
					# self.log.info("Elapsed Time = %0.5f, Frequency = %s", delta, freq)
					# loop_timer = now


					# If we wrote the output because the current spectra has changed, we need to update the running acq info variables with the new frequencies.
					if changed:
						self.log.info("Retuned! Old freq = %s, new freq = %s", startFreq, acqInfo["ret-start-freq"])

						runningSum += dataDict["data"]["max"]
						startFreq = acqInfo["ret-start-freq"]
						binSize = acqInfo["arr-bin-size"]
						runningSumItems = 1


					del(trace)




			except Exception: 
				# release lock if there is an exception
				FELock.release()
				lockcheck = False
				self.log.error("IOError in Acquisition Thread!")
				self.log.error(traceback.format_exc())

				dataQueue.put({"status" : "Error: Device interface craself.shed. Reinitializing"})
				self.log.error("Resetting hardware!")
				# self.sh.preset()
				self.sh.forceClose()
				try:
					while 1:
						self.log.warning("Trying to free python device handle")
						del(self.sh)
				except UnboundLocalError:
					self.log.info("Handle freed?")
				except AttributeError:
					self.log.info("Handle freed?")

				self.log.error("Hardware shut down, completely re-initializing device interface!")
				# sys.exit()

				self.log.info("Preparing to reset device.")
				self.sh = SignalHound()
				self.log.info("Performing hardware reset")
				self.sh.preset()

				self.log.info("Reset triggered. Waiting 5 seconds for device to restart.")
				time.sleep(5)


				self.log.info("Hardware reset. Reopening device.")
				self.sh = SignalHound()



				self.startAcquisition(dataQueue, dataQueue)


			loops += 1

			if loops % ACQ_BIN_SAMPLES == 0:
				print("Should retune frontend!")
				FELock.release()
				self.sh.abort()
				FELock.acquire()
				self.startAcquisition(dataQueue, dataQueue)

				# print("Current acq mode = ", self.sh.queryTraceInfo())

			if loops % PRINT_LOOP_CNT == 0:
				now = time.time()
				delta = now-loop_timer
				freq = 1 / (delta / PRINT_LOOP_CNT)
				# self.log.info("Elapsed Time = %0.5f, Frequency = %s", delta, freq)
				loop_timer = now

			if loops % CAL_CHK_LOOP_CNT == 0:
				diags = self.sh.getDeviceDiagnostics()
				dataQueue.put({"status" : diags})

				temptmp = diags["temperature"]
				if abs(temperature - temptmp) > 2.0:    # Temperature deviations of > 2° cause IF self.shifts. Therefore, we do a re-cal if they're detected
					dataQueue.put({"status" : "Recalibrating IF"})
					self.sh.selfCal()
					self.startAcquisition(dataQueue, dataQueue)
					self.log.warning("Temperature changed > 2.0 C. Delta is %f. Recalibrated!", abs(temperature - temptmp))
					temperature = temptmp
				else:
					self.log.info("Temperature deviation = %f. Not doing recal, since drift < 2C", abs(temperature - temptmp))


			if ctrlNs.run == False:

				self.log.info("Stopping Acq-thread!")
				break

		FELock.release()
		lockcheck = False
		self.sh.abort()
		self.sh.closeDevice()

		del(self.sh)



		self.log.info("Acq-thread closing dataQueue!")
		dataQueue.close()
		dataQueue.join_thread()

		plotQueue.close()
		plotQueue.cancel_join_thread()

		ctrlNs.acqRunning = False

		self.log.info("Acq-thread exiting!")
		self.printQueue.close()
		self.printQueue.join_thread()
