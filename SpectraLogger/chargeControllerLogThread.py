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

import datetime
import logging
import logSetup
import time
import traceback
from pyepsolartracer.client import EPsolarTracerClient
from pyepsolartracer.registers import registers,coils
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

from SolarSettings import CONTROLLER_COM_PORT

def startGpsLog(dataQueues, ctrlNs, printQueue):
	print("Creating GPS thread")
	solarRunner = GpsLogThread(printQueue)
	solarRunner.sweepSource(dataQueues, ctrlNs)

class GpsLogThread(object):
	log = logging.getLogger("Main.ChargeControllerProcess")
  
	message = {
		'Battery SOC' : None,
		'Discharging equipment output voltage' : None,
		'Discharging equipment output current' : None,
		'Remote battery temperature' : None,
		'Temperature inside equipment' : None,
		'Battery Current' : None,
		'Battery status' : None,
		'Charging equipment input voltage' : None,
		'Charging equipment input current' : None,
		'Charging equipment output voltage' : None,
		'Charging equipment output current' : None,
	}


	def __init__(self, printQueue):
		self.printQueue = printQueue
		logSetup.initLogging(printQ=printQueue)




	def sweepSource(self, dataQueues, ctrlNs):
		print("Charge Controller Log Thread starting")
		self.dataQueue, self.plotQueue = dataQueues

		serialclient = ModbusClient(method='rtu',port=7,stopbits=1,bytesize=8,baudrate=115200)
		client = EPsolarTracerClient(serialclient = serialclient)
		client.connect()

		while 1:
			time.sleep(30)
			for reg in self.message:
				self.message[reg] = self.parseMessage(reg)

			if ctrlNs.run == False:
				self.log.info("Stopping Charge Controller thread!")
				break
			
		client.close()

		self.log.info("GPS-thread closing dataQueue!")
		self.dataQueue.close()
		self.dataQueue.join_thread()

		self.plotQueue.close()
		self.plotQueue.cancel_join_thread()


		self.log.info("GPS-thread exiting!")
		self.printQueue.close()
		self.printQueue.join_thread()


	def parseMessage(self, register):
		try:
			message = float(client.read_input(register))
			self.processMessage(message, register)
		except UnicodeDecodeError:
			self.log.error("Parse error!")
			self.log.error(traceback.format_exc())
			for key in self.message.keys():
				self.message[key] = None
		except ValueError:
			self.log.error("Parse error!")
			self.log.error(traceback.format_exc())
			for key in self.message.keys():
				self.message[key] = None

	def processMessage(self, msg, reg):
		
		self.message[reg] = msg
		# We have everything we want
		if all(self.message.values()):
			self.log.debug("Complete self.message = %s. emitting to logger!", self.message)
			self.log.info("Complete Charge Controller message. emitting to logger!")
			self.dataQueue.put({"Charge-Controller" : self.message.copy()})
			self.clearData()


	def clearData(self):

		for key in self.message.keys():
			self.message[key] = None



def dotest():
	print("Starting test")
	import Queue
	logSetup.initLogging()
	startGpsLog((Queue.Queue(), Queue.Queue()), None, Queue.Queue())

if __name__ == "__main__":
	dotest()


