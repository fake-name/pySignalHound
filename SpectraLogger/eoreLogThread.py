# -*- coding: UTF-8 -*-

# Wrapper for Test-Equipment-Plus's "SignalHound" series of USB spectrum analysers.
#
# Originaly written By Connor Wolf <wolf@imaginaryindustries.com>
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
import serial
import eore



import traceback

from settings import EORE_COM_PORT

def startEORELog(dataQueues, cmdQueue, ctrlNs, printQueue):
	print("Creating GPS thread")
	self.eoreCTL = EORELogThread(printQueue)
	self.eoreCTL.sweepSource(dataQueues, cmdQueue, ctrlNs)

class EORELogThread(object):
	log = logging.getLogger("Main.EOREProcess")

	message = {
		eore.MAIN_TONE_ATTEN : 0,
		eore.AUX_TONE_ATTEN : 0,
		eore.NOISE_DIODE_ATTEN : 0,
		eore.SWITCH_SWR_TONE_ATTEN : 0,
		eore.SWITCH_TONE_ATTEN : 0,
		eore.MID_AMP_ATTEN : 0,
		'noiseDiode' : False, 
		'oscillator' : 0,
		'VCO' : 0,
		'Temp' : None, 
		'TargetTemp' : 15,
		eore.MAIN_SWITCH : eore.TERMINATION,
		eore.SWR_SWITCH : eore.SWITCHED_SWEEPER_INPUT
	}

	attenuators = [
		eore.MAIN_TONE_ATTEN, 
		eore.MAIN_TONE_ATTEN, 
		eore.NOISE_DIODE_ATTEN, 
		eore.SWITCH_SWR_TONE_ATTEN,
		eore.SWITCH_TONE_ATTEN, 
		eore.MID_AMP_ATTEN
	]

	switches = [
		eore.MAIN_SWITCH, 
		eore.SWR_SWITCH, 
	]

	def __init__(self, printQueue):
		self.log.info("Initializing EORE")
		self.eoreCTL = EoreController("EORE_COM_PORT")
		self.printQueue = printQueue
		logSetup.initLogging(printQ=printQueue)

		
		parseMessage(self.eoreCTL.writeAtten(eore.MAIN_TONE_ATTEN,       0))
		parseMessage(self.eoreCTL.writeAtten(eore.AUX_TONE_ATTEN,        0))
		parseMessage(self.eoreCTL.writeAtten(eore.NOISE_DIODE_ATTEN,     0))
		parseMessage(self.eoreCTL.writeAtten(eore.SWITCH_SWR_TONE_ATTEN, 0))
		parseMessage(self.eoreCTL.writeAtten(eore.SWITCH_TONE_ATTEN,     0))
		parseMessage(self.eoreCTL.writeAtten(eore.MID_AMP_ATTEN,         0))
		parseMessage(self.eoreCTL.noiseDiodePowerCtl(False))
		parseMessage(self.eoreCTL.disableOscillator())
		parseMessage(self.eoreCTL.powerDownVco())
		parseMessage(self.eoreCTL.getTemperature())
		parseMessage(self.eoreCTL.writeSwitch(eore.MAIN_SWITCH, eore.TERMINATION))



	def sweepSource(self, dataQueues, cmdQueue, ctrlNs):
		print("EORE Log Thread starting")
		self.dataQueue, self.plotQueue = dataQueues
		self.cmdQueue = cmdQueue
		# remember to add locks
		while 1:
			if cmdQueue.empty():
				time.sleep(0.005)
			else:
				cmd = cmdQueue.get()
				self.message['Temp'] = self.eoreCTL.getTemperature(),
				for key in cmd:
					self.message[key] = cmd[key]
					if key in self.switches:
						parseMessage(self.eoreCTL.writeSwitch(key, cmd[key]))
					elif key in self.attenuators:
						parseMessage(self.eoreCTL.writeAtten(key, cmd[key]))
					elif key == 'noiseDiode':
						parseMessage(self.eoreCTL.noiseDiodePowerCtl(cmd[key]))
					elif key == 'oscillator':
						parseMessage(self.eoreCTL.writeOscillator(0, cmd[key]))
					elif key == 'VCO' :
						if cmd['VCO'] > 0:
							parseMessage(self.eoreCTL.chirpVco(cmd[key]))
						else self.eoreCTL.powerDownVco()
					elif key == 'TargetTemp' :
						parseMessage(self.eoreCTL.setTemperature(cmd[key]))
				sendState()			



			if ctrlNs.run == False:
				self.log.info("Stopping EORE-thread!")
				break


		self.log.info("EORE-thread closing dataQueue!")
		self.dataQueue.close()
		self.dataQueue.join_thread()

		self.plotQueue.close()
		self.plotQueue.cancel_join_thread()


		self.log.info("EORE-thread exiting!")
		self.printQueue.close()
		self.printQueue.join_thread()


	def parseMessage(self, ret):
		if (ret[0:2] == "OK:"):
			return True
		if (ret[0:5] == "ERROR:"):
			self.log.error("ERROR when attempting to modify EORE state!")
			self.log.error(ret)
			return False
		else:
			self.log.error("Error parsing EORE status info!")
			self.log.error(ret)
			return False


	def sendState(self):
		
		# We have everything we want
		if all(self.message.values()):
			self.log.info("Complete self.message = %s. emitting to logger!", self.message)
			self.dataQueue.put({"gps-info" : self.message.copy()})
			self.clearData()


	def clearData(self):

			self.message['temp'] = None



def dotest():
	print("Starting test")
	import Queue
	logSetup.initLogging()
	startGpsLog((Queue.Queue(), Queue.Queue()), None, Queue.Queue())

if __name__ == "__main__":
	dotest()


