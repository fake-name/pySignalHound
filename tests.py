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

import logSetup
import sys
import time
import numpy as np

from SignalHound import SignalHound

START_TIME = time.time()
DATA_LOG = []

def callbackTestFunc(bufPtr, bufLen):
	global START_TIME  #hacking about for determining callback interval times. I shouldn't be using global, but fukkit.

	now = time.time()

	print "Callback!", bufPtr, bufLen
	print bufPtr[0]

	arr = SignalHound.decodeRawSweep(bufPtr, bufLen)

	print "NP Array = ", arr.shape, arr
	print "Elapsed Time = ", now-START_TIME
	START_TIME = now


def testCallback(sh):
	sh.configureCenterSpan(150e6, 100e6)
	sh.configureLevel(-50, 10)
	sh.configureGain(0)
	sh.configureSweepCoupling(9.863e3, 9.863e3, 10, "native", "no-spur-reject")
	sh.configureWindow("hamming")
	sh.configureProcUnits("power")
	sh.configureTrigger("none", "rising-edge", 0, 5)
	sh.configureIO("dc", "int-ref-out", "out-logic-low")
	sh.configureDemod("fm", 92.9e6, 250e3, 12e3, 20, 50)
	sh.initiate("raw-sweep-loop", 0)
	sh.startRawSweepLoop(callbackTestFunc)

	try:
		time.sleep(50)
	except KeyboardInterrupt:
		pass


	sh.abort()

def testIqStreaming(sh):
	global START_TIME  #hacking about for determining callback interval times. I shouldn't be using global, but fukkit.

	START_TIME = time.time()
	loops = 0

	sh.configureCenterSpan(100e6, 20e6)
	sh.configureLevel(10, "auto")
	sh.configureGain(0)
	sh.configureIO("dc", "int-ref-out", "out-logic-low")
	sh.configureIQ(1, 20e6)  # 2x downdampling, 15 Mhz bandwith


	sh.initiate("streaming", None)
	print sh.queryStreamInfo()
	print sh.rawDataArrSize

	out = open("dat.bin", "wb")

	try:
		while 1:
			try:
				data = sh.fetchRaw()
				DATA_LOG.append(data)
			except IOError:

				print "ioerror"

			if loops % 100 == 0:
				print loops
				now = time.time()
				delta = now-START_TIME
				freq = 1 / (delta / 100)
				print "Elapsed Time = ", delta, "Frequency = ", freq
				START_TIME = now
			if len(DATA_LOG):
				tmp = DATA_LOG.pop()
				out.write(tmp["data"])
				out.write(tmp["triggers"])
			loops += 1

		time.sleep(50)

	except KeyboardInterrupt:
		pass

	out.close()
	sh.abort()


def testRawPipeMode(sh):
	global START_TIME  #hacking about for determining callback interval times. I shouldn't be using global, but fukkit.

	START_TIME = time.time()
	loops = 0

	sh.configureAcquisition("average", "log-scale")
	sh.configureCenterSpan(150e6, 100e6)
	sh.configureLevel(10, "auto")
	sh.configureGain(0)
	sh.configureSweepCoupling(9.863e3, 9.863e3, 10, "native", "no-spur-reject")
	sh.configureWindow("hamming")
	sh.configureProcUnits("power")
	sh.configureTrigger("none", "rising-edge", 0, 5)
	sh.configureIO("dc", "int-ref-out", "out-logic-low")
	sh.configureDemod("fm", 92.9e6, 250e3, 12e3, 20, 50)

	sh.configureRawSweep(100, 1, 16)

	# sh.initiate("raw-sweep-loop", 0)
	sh.initiate("raw-pipe", "20-mhz")
	# print sh.queryTimestamp()
	# sh.startRawSweepLoop(callbackTestFunc)

	# ret = sh.fetchRawCorrections()
	# for key, value in ret.iteritems():
	# 	print key, value

	# for item in ret["data"]:
	# 	st = "%f" % item
	# 	print st.rjust(12),
	# 	if loops % 10 == 0:
	# 		print
	# 	loops += 1

	out = open("dat.bin", "wb")

	try:
		while 1:
			try:
				DATA_LOG.append(sh.fetchRaw_s())
			except IOError:

				print "ioerror"

			if loops % 100 == 0:
				print loops
				now = time.time()
				delta = now-START_TIME
				freq = 1 / (delta / 100)
				print "Elapsed Time = ", delta, "Frequency = ", freq
				START_TIME = now
			if len(DATA_LOG):
				tmp = DATA_LOG.pop()
				out.write(tmp["data"])
				out.write(tmp["triggers"])
			loops += 1

		time.sleep(50)

	except KeyboardInterrupt:
		pass

	out.close()
	sh.abort()


def testSweeps(sh):
	global START_TIME  #hacking about for determining callback interval times. I shouldn't be using global, but fukkit.

	START_TIME = time.time()
	loops = 0

	sh.configureAcquisition("average", "log-scale")
	sh.configureCenterSpan(center = 150e6, span = 100e6)
	sh.configureLevel(ref = 10, atten = "auto")
	sh.configureGain(gain = 0)
	sh.configureSweepCoupling(rbw = 9.863e3, vbw = 9.863e3, sweepTime = 0.10, rbwType = "native", rejection = "no-spur-reject")
	sh.configureWindow(window = "hamming")
	sh.configureProcUnits(units = "power")
	sh.configureTrigger(trigType = "none", edge = "rising-edge", level = 0, timeout = 5)
	# sh.configureIO("dc", "int-ref-out", "out-logic-low")
	# sh.configureDemod("fm", 102.3e6, 250e3, 12e3, 20, 50)

	# sh.configureRawSweep(100, 8, 2)
	sh.initiate(mode = "sweeping", flag = "ignored")
	print sh.queryTraceInfo()
	# sh.initiate("raw-sweep-loop", 0)
	# print sh.queryTimestamp()
	# sh.startRawSweepLoop(callbackTestFunc)

	# ret = sh.fetchRawCorrections()
	# for key, value in ret.iteritems():
	# 	print key, value

	# for item in ret["data"]:
	# 	st = "%f" % item
	# 	print st.rjust(12),
	# 	if loops % 10 == 0:
	# 		print
	# 	loops += 1

	out = open("dat.bin", "wb")

	try:
		while 1:
			try:
				DATA_LOG.append(sh.fetchTrace())
			except IOError:

				print "ioerror"

			if loops % 20 == 0:
				print loops
				now = time.time()
				delta = now-START_TIME
				freq = 1 / (delta / 20)
				print "Elapsed Time = ", delta, "Frequency = ", freq
				START_TIME = now
			if len(DATA_LOG):
				tmp = DATA_LOG.pop()
				print np.array_str(tmp["max"], max_line_width = sys.maxint), len(tmp["max"])

				outStr = ""
				# outStr = "%s, " % time.time()
				outStr += " ".join(['%f,' % num for num in tmp["max"]])
				outStr = outStr.rstrip(", ").lstrip(", ")
				outStr += "\n"



				out.write(outStr)

				# for item in tmp["max"]:
				# 	 print item

			loops += 1

		time.sleep(50)

	except KeyboardInterrupt:
		pass

	out.close()

	sh.abort()

def interruptedSweeping(sh):
	global START_TIME  #hacking about for determining callback interval times. I shouldn't be using global, but fukkit.

	START_TIME = time.time()
	loops = 0

	sh.configureAcquisition("average", "log-scale")
	sh.configureCenterSpan(center = 150e6, span = 100e6)
	sh.configureLevel(ref = 10, atten = "auto")
	sh.configureGain(gain = 0)
	sh.configureSweepCoupling(rbw = 9.863e3, vbw = 9.863e3, sweepTime = 0.10, rbwType = "native", rejection = "no-spur-reject")
	sh.configureWindow(window = "hamming")
	sh.configureProcUnits(units = "power")
	sh.configureTrigger(trigType = "none", edge = "rising-edge", level = 0, timeout = 5)
	# sh.configureIO("dc", "int-ref-out", "out-logic-low")
	# sh.configureDemod("fm", 102.3e6, 250e3, 12e3, 20, 50)

	# sh.configureRawSweep(100, 8, 2)
	# sh.initiate("raw-sweep-loop", 0)
	# print sh.queryTimestamp()
	# sh.startRawSweepLoop(callbackTestFunc)

	# ret = sh.fetchRawCorrections()
	# for key, value in ret.iteritems():
	# 	print key, value

	# for item in ret["data"]:
	# 	st = "%f" % item
	# 	print st.rjust(12),
	# 	if loops % 10 == 0:
	# 		print
	# 	loops += 1

	out = open("dat.bin", "wb")

	try:
		while 1:

			sh.initiate(mode = "sweeping", flag = "ignored")

			print sh.queryTraceInfo()
			try:
				tmp = sh.fetchTrace()
				DATA_LOG.append(tmp)
				print(tmp)
			except IOError:

				print "ioerror"

			if loops % 20 == 0:
				print loops
				now = time.time()
				delta = now-START_TIME
				freq = 1 / (delta / 20)
				print "Elapsed Time = ", delta, "Frequency = ", freq
				START_TIME = now
			if len(DATA_LOG):
				tmp = DATA_LOG.pop()
				print np.array_str(tmp["max"], max_line_width = sys.maxint), len(tmp["max"])

				outStr = ""
				# outStr = "%s, " % time.time()
				outStr += " ".join(['%f,' % num for num in tmp["max"]])
				outStr = outStr.rstrip(", ").lstrip(", ")
				outStr += "\n"



				out.write(outStr)

				# for item in tmp["max"]:
				# 	 print item

			loops += 1

			sh.abort()

		time.sleep(50)

	except KeyboardInterrupt:
		pass

	out.close()


def testGpsSweeps(sh):
	global START_TIME  #hacking about for determining callback interval times. I shouldn't be using global, but fukkit.

	START_TIME = time.time()
	loops = 0

	sh.configureAcquisition("average", "log-scale")
	sh.configureCenterSpan(center = 150e6, span = 100e6)
	sh.configureLevel(ref = 10, atten = "auto")
	sh.configureGain(gain = 0)
	sh.configureSweepCoupling(rbw = 9.863e3, vbw = 9.863e3, sweepTime = 0.10, rbwType = "native", rejection = "no-spur-reject")
	sh.configureWindow(window = "hamming")
	sh.configureProcUnits(units = "power")
	sh.configureTrigger(trigType = "gps-pps", edge = "rising-edge", level = 0, timeout = 5)
	# sh.configureIO("dc", "int-ref-out", "out-logic-low")
	# sh.configureDemod("fm", 102.3e6, 250e3, 12e3, 20, 50)

	# sh.configureRawSweep(100, 8, 2)
	sh.initiate(mode = "sweeping", flag = "ignored")
	print sh.queryTraceInfo()
	# sh.initiate("raw-sweep-loop", 0)
	# print sh.queryTimestamp()
	# sh.startRawSweepLoop(callbackTestFunc)

	# ret = sh.fetchRawCorrections()
	# for key, value in ret.iteritems():
	# 	print key, value

	# for item in ret["data"]:
	# 	st = "%f" % item
	# 	print st.rjust(12),
	# 	if loops % 10 == 0:
	# 		print
	# 	loops += 1

	out = open("dat.bin", "wb")

	try:
		while 1:
			try:
				DATA_LOG.append(sh.fetchTrace())
			except IOError:

				print "ioerror"

			if loops % 20 == 0:
				print loops
				now = time.time()
				delta = now-START_TIME
				freq = 1 / (delta / 20)
				print "Elapsed Time = ", delta, "Frequency = ", freq
				START_TIME = now
			if len(DATA_LOG):
				tmp = DATA_LOG.pop()
				print np.array_str(tmp["max"], max_line_width = sys.maxint), len(tmp["max"])

				outStr = ""
				# outStr = "%s, " % time.time()
				outStr += " ".join(['%f,' % num for num in tmp["max"]])
				outStr = outStr.rstrip(", ").lstrip(", ")
				outStr += "\n"


				out.write(outStr)

				# for item in tmp["max"]:
				# 	 print item

			loops += 1

		time.sleep(50)

	except KeyboardInterrupt:
		pass

	out.close()

	sh.abort()

def testDeviceStatusQueries(sh):
	sh.getFirmwareVersion()
	sh.getAPIVersion()
	print sh.getDeviceDiagnostics()
	sh.getDeviceType()
	sh.getSerialNumber()

def resetDevice(sh):
	sh.preset()




def audioTest(sh, freq = 88.7e6):

	print "Executing audio-test"

	import pyaudio

	c_FORMAT = pyaudio.paFloat32
	c_CHANNELS = 1
	c_RATE = 32000  # bbFetchAudio returns samples at 32 Khz

	sOut = pyaudio.PyAudio()
	stream = sOut.open(format = c_FORMAT, channels = c_CHANNELS, rate = c_RATE, output = True, frames_per_buffer = 4096)

	# sh.preset()
	sh.getDeviceDiagnostics()
	# sh.configureAcquisition("average", "log-scale")
	# sh.configureCenterSpan(100e6, 50e6)
	# sh.configureLevel(-50, 10)
	# sh.configureGain(0)
	# sh.configureSweepCoupling(9.863e3, 9.863e3, 10, "native", "no-spur-reject")
	# sh.configureWindow("hamming")
	# sh.configureProcUnits("power")
	# sh.configureTrigger("none", "rising-edge", 0, 5)
	# sh.configureIO("dc", "int-ref-out", "out-logic-low")
	sh.configureDemod("fm", freq, 160e3, 12e3, 20, 75)
	# sh.getDeviceType()
	# sh.getSerialNumber()
	# sh.getFirmwareVersion()
	# sh.getAPIVersion()
	# sh.initiate("raw-sweep-loop", 0)
	sh.initiate("audio-demod", "demod-fm")
	# print sh.queryTimestamp()
	# sh.startRawSweepLoop(testFunct)

	try:
		while 1:
			audio = sh.fetchAudio()  # fetchAudio is blocking.
			stream.write(audio.astype(np.float32).tostring())

	except KeyboardInterrupt:
		pass
	# sh.configureTimeGate(0,0,0)
	# sh.configureRawSweep(500, 10, 16)

	sh.abort()

def printUsage():

		print "Available tests:"
		print "	'radio' - Do streaming decode of a FM radio signal"
		print "	'status' - Query device and API for some status and model information"
		print "	'raw-pipe' - Try to log data from a raw-pipe connection to disk (warning - uses enormous amounts of disk space)"
		print "	'callback' - Try to capture data via bbStartRawSweepLoop"
		print "	'traces' - Fetch formatted traces, and log to disk"
		print "	'int-traces' - Fetch formatted traces while continually restarting the acquisition, and log to disk"
		print "	'iq' - Fetch IQ samples"
		print "	'reset' - Reset the connected device"



def go():



	if len(sys.argv) <= 1:
		print "You must enter a test mode!"
		printUsage()
		sys.exit()

	funcs = {
		'radio'      : audioTest,
		'status'     : testDeviceStatusQueries,
		'raw-pipe'   : testRawPipeMode,
		'callback'   : testCallback,
		'traces'     : testSweeps,
		'int-traces' : interruptedSweeping,
		'gps'        : testGpsSweeps,
		'reset'      : resetDevice,
		'iq'         : testIqStreaming
	}

	if sys.argv[1] in funcs:

		logSetup.initLogging()

		sh = SignalHound()
		# sh.preset()

		# testDeviceStatusQueries(sh)
		# testRawPipeMode(sh)
		if len(sys.argv) == 2:
			funcs[sys.argv[1]](sh)
		if len(sys.argv) == 3:
			funcs[sys.argv[1]](sh, float(sys.argv[2]))

		# testCallback(sh)

		sh.closeDevice()

	else:
		print "Error! You must enter a valid test-mode!"
		printUsage()


if __name__ == "__main__":
	go()
