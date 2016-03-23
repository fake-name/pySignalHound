# -*- coding: UTF-8 -*-

# Wrapper for Test-Equipment-Plus's "SignalHound" series of USB spectrum analysers.
#
# Written By Connor Wolf <wolf@imaginaryindustries.com>
# Modified by Caio Motta <Caio@deepspace.ucsb.edu>

#  * ----------------------------------------------------------------------------
#  * "THE BEER-WARE LICENSE":
#  * Connor Wolf <wolf@imaginaryindustries.com> wrote this file. As long as you retain
#  * this notice you can do whatever you want with this stuff. If we meet some day,
#  * and you think this stuff is worth it, you can buy me a beer in return.
#  * (Only I don't drink, so a soda will do). Connor
#  * Also, support the Signal-Hound devs. Their hardware is pretty damn awesome.
#  * ----------------------------------------------------------------------------
#

# Drag in path to the library (MESSY)
import os, sys
lib_path = os.path.abspath('../')
print "Lib Path = ", lib_path
sys.path.append(lib_path)


import logSetup
import logging
import time
import numpy as np
import h5py
import eore
import EOREsettings
import os
import os.path
import cPickle

from settings import NUM_AVERAGE, FILE_ROTATION_INTERVAL


def logSweeps(dataQueue, ctrlNs, printQueue, test=False):
	log = logging.getLogger("Main.LogProcess")
	logSetup.initLogging(printQ = printQueue)

	log.info("Logging thread starting")

	# the size of the acquisiton array can vary. Therefore, we wait for the acq thread to send a message containing
	# the array size before allocating the HDF5 array.
	if not test:
		while 1:

			if dataQueue.empty():
				time.sleep(0.005)
			else:
				tmp = dataQueue.get()

				if "arrSize" in tmp:
					log.info("Have array size for acquisition. Creating HDF5 file and starting logging.")
					arrWidth = tmp["arrSize"]
					break
			if ctrlNs.acqRunning == False:
				log.info("Stopping Log-thread!")
				ctrlNs.logRunning = False
				break
	else:
		arrWidth = 20


	while ctrlNs.acqRunning:
		log.debug(ctrlNs.acqRunning)
		logIter(dataQueue, ctrlNs, printQueue, arrWidth, test)

	log.info("Log-thread closing queues!")
	dataQueue.close()
	dataQueue.join_thread()
	log.warning("Log-thread exiting!")
	printQueue.close()
	printQueue.join_thread()

def logIter(dataQueue, ctrlNs, printQueue, arrWidth, test=False):


	log = logging.getLogger("Main.LogProcess.Func")
	loop_timer = time.time()

	logName = time.strftime("Datalog - %Y %m %d, %a, %H-%M-%S.h5", time.localtime())
	logPath = time.strftime("../Data/%Y/%m/%d/", time.localtime())

	if not os.path.exists(logPath):
		os.makedirs(logPath)

	logFQPath = os.path.join(logPath, logName)

	log.info("Logging data to %s", logFQPath)
	out = h5py.File(logFQPath, "w")
	startFreq = 0


	# dTypeStructure = [("TimeStamp", "f8"), ("StartFreq", "f4"), ("BinSize", "f4"), ("NumScans", "f4"), ("data", "f4", arrWidth)]
	# dType = np.dtype(dTypeStructure)
	arrWidth = arrWidth + 17 # Width of the data array, plus - TimeStamp, StartFreq, BinSize, NumScans and eore data
	# Main dataset - compressed, chunked, checksummed.
	dset = out.create_dataset('Spectrum_Data', (0, arrWidth), maxshape=(None, arrWidth), dtype = np.float64, chunks=True, compression="gzip", fletcher32=True, shuffle=True)

	# Cal and system status log dataset.
	calset = out.create_dataset('Acq_info', (0, ), maxshape=(None, ), dtype=h5py.new_vlen(str))




	runningSum = np.array(())
	runningSumItems = 0
	row = False
	while 1:
		if dataQueue.empty():
			#log.info("Data queue empty")
			time.sleep(0.005)
		else:
			tmp = dataQueue.get()
			# print "data" in tmp
			# print "info" in tmp
			# print "data" in tmp and "max" in tmp["data"]
			log.warning("current keys: %s", tmp.keys())

			if "row" in tmp:
				row = True
				saveTime, startFreq, binSize, runningSumItems, arr = tmp["row"]

			elif "eore-info" in tmp:
				row = False
				eoreState = tmp["eore-info"]
				
				# append it to the HDF5 file
				curSize = dset.shape[0]
				# print("Current shape = ", dset.shape)
				dset.resize(curSize+1, axis=0)
				log.debug("About to write row to file!")

				flatten = lambda *args: args
				dset[curSize] = flatten(saveTime, startFreq, binSize, runningSumItems, eoreState['MAIN_TONE_ATTEN'],\
				  eoreState['AUX_TONE_ATTEN'], eoreState['NOISE_DIODE_ATTEN'], eoreState['SWITCH_SWR_TONE_ATTEN'],\
				  eoreState['SWITCH_TONE_ATTEN'], eoreState['MID_AMP_ATTEN'], eoreState['noiseDiode'],\
				  eoreState['oscillator'], eoreState['VCO'], eoreState['temp'], eoreState['targetTemp'],\
				  eoreState['MAIN_SWITCH'], eoreState['SWR_SWITCH'], *arr)

				out.flush()  # FLush early, flush often
				# Probably a bad idea without a SSD


				runningSum = np.zeros_like(runningSum)
				log.info("Writing row to file!")
				log.info("Estimated items in processing queue %s", dataQueue.qsize())

				runningSumItems = 0

				if time.time() - loop_timer > FILE_ROTATION_INTERVAL:
					log.info("Rotating log files")
					break
			

			elif "settings" in tmp or "status" in tmp or "gps-info" in tmp:

				if "settings" in tmp:
					tmp["settings"]["averaging-interval"] = NUM_AVERAGE

				data = [time.time(), tmp]

				dataPik = cPickle.dumps(data)

				calSz = calset.shape[0]
				calset.resize([calSz+1,])
				calset[calSz,...] = dataPik

				# log.info("Status message - %s.", tmp)
				# log.info("StatusTable size = %s", calset.shape)
			else:
				log.error("WAT? Unknown packet!")
				log.info("current keys: %s", tmp.keys())
				log.error(tmp)


		if ctrlNs.acqRunning == False:
			log.info("Stopping Log-thread!")
			ctrlNs.logRunning = False
			break


	out.close()


def dotest():
	print("Starting test")
	import Queue
	logSetup.initLogging()
	logSweeps(Queue.Queue(), None, Queue.Queue(), test=True)

if __name__ == "__main__":
	dotest()
