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
# Drag in path to the library (MESSY)
import os, sys
lib_path = os.path.abspath('../')
print "Lib Path = ", lib_path
sys.path.append(lib_path)

import datetime
import logging
import logSetup
import time
import serial
import pynmea2
import traceback

from settings import GPS_COM_PORT

def startGpsLog(dataQueues, ctrlNs, printQueue):
	print("Creating GPS thread")
	gpsRunner = GpsLogThread(printQueue)
	gpsRunner.sweepSource(dataQueues, ctrlNs)

class GpsLogThread(object):
	log = logging.getLogger("Main.GpsProcess")

	message = {
		'latitude' : None,
		'longitude' : None,
		'numsatview' : None,
		'fix_type' : None,
		'datetime' : None,
		'altitude' : None,
		'altitude_units' : None,
		'hdop' : None,
	}

	date = None
	time = None
	def __init__(self, printQueue):
		self.printQueue = printQueue
		logSetup.initLogging(printQ=printQueue)



	def sweepSource(self, dataQueues, ctrlNs):
		print("GPS Log Thread starting")
		self.dataQueue, self.plotQueue = dataQueues


		ser   = serial.Serial(GPS_COM_PORT, 9600, timeout=1)
		parse = pynmea2.NMEAStreamReader()


		inBuf = ""

		while 1:

			inBuf += ser.read(16)
			inBuf = inBuf.replace("\r\n", "\n")
			inBuf = inBuf.replace("\r", "\n")
			inBuf = inBuf.replace("$", "\n")
			parsed = []
			while "\n" in inBuf:

				message, inBuf = inBuf.split("\n", 1)
				message = message.strip()
				if message:
					self.parseMessage(message)



			if ctrlNs.run == False:
				self.log.info("Stopping GPS-thread!")
				break


		self.log.info("GPS-thread closing dataQueue!")
		self.dataQueue.close()
		self.dataQueue.join_thread()

		self.plotQueue.close()
		self.plotQueue.cancel_join_thread()


		self.log.info("GPS-thread exiting!")
		self.printQueue.close()
		self.printQueue.join_thread()


	def parseMessage(self, message):
		try:
			message = pynmea2.parse(message)
			self.processMessage(message)
		except UnicodeDecodeError:
			self.log.error("Parse error!")
			self.log.error(traceback.format_exc())
			for key in self.message.keys():
				self.message[key] = None
		except pynmea2.nmea.ParseError:
			self.log.error("Parse error!")
			self.log.error(traceback.format_exc())
			for key in self.message.keys():
				self.message[key] = None
		except pynmea2.nmea.ChecksumError:
			self.log.error("Parse error!")
			self.log.error(traceback.format_exc())
			for key in self.message.keys():
				self.message[key] = None
		except ValueError:
			self.log.error("Parse error!")
			self.log.error(traceback.format_exc())
			for key in self.message.keys():
				self.message[key] = None

	def processMessage(self, msg):
		if hasattr(msg, "latitude"):
			self.message['latitude'] = msg.latitude
		if hasattr(msg, "longitude"):
			self.message['longitude'] = msg.longitude
		if hasattr(msg, "altitude"):
			self.message['altitude'] = msg.altitude
		if hasattr(msg, "altitude_units"):
			self.message['altitude_units'] = msg.altitude_units
		if hasattr(msg, "num_sats"):
			self.message['numsatview'] = int(msg.num_sats)
		if hasattr(msg, "mode_fix_type"):
			self.message['fix_type'] = int(msg.mode_fix_type)
		if hasattr(msg, "hdop"):
			self.message['hdop'] = float(msg.hdop)
		if hasattr(msg, "timestamp") and not isinstance(msg.timestamp, basestring):
			self.time = msg.timestamp
		if hasattr(msg, "datestamp"):
			self.date = msg.datestamp

		if self.date and self.time:
			self.message['datetime'] = datetime.datetime.combine(self.date, self.time)
		# We have everything we want
		if all(self.message.values()) and self.date and self.time:
			self.log.info("Complete self.message = %s. emitting to logger!", self.message)
			self.dataQueue.put({"gps-info" : self.message.copy()})
			self.clearData()


	def clearData(self):
		self.date = None
		self.time = None

		for key in self.message.keys():
			self.message[key] = None



def dotest():
	print("Starting test")
	import Queue
	logSetup.initLogging()
	startGpsLog((Queue.Queue(), Queue.Queue()), None, Queue.Queue())

if __name__ == "__main__":
	dotest()


