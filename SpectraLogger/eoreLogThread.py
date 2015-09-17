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
import multiprocessing as mp



import traceback

from EOREsettings import EORE_COM_PORT, EORE_CONFIGS, EORE_SWITCHES, EORE_ATTENUATORS

def startEORELog(dataQueues, cmdQueue, FELock, ctrlNs, printQueue):
	print("Creating GPS thread")
	EORERunner = EORELogThread(dataQueues, printQueue, ctrlNs)
	EORERunner.sweepSource(cmdQueue, FELock, ctrlNs)

class EORELogThread(object):
	log = logging.getLogger("Main.EOREProcess")
	mainIndex = 0
	SWRIndex = 0

	state = EORE_CONFIGS["default"]
	stateBackup = EORE_CONFIGS["default"]
	attenuators = EORE_ATTENUATORS

	switches = EORE_SWITCHES

	def __init__(self, dataQueues, printQueue, ctrlNs):
		self.log.info("Initializing EORE")
		self.dataQueue, self.plotQueue = dataQueues
		self.ctrlNs = ctrlNs
		self.printQueue = printQueue
		logSetup.initLogging(printQ=printQueue)

		serialfailcount = 0
		try:
			self.eoreCTL = eore.EoreController(EORE_COM_PORT)
		except serial.serialutil.SerialException:
				self.eoreCTL = eore.EoreController(EORE_COM_PORT)
				if (serialfailcount > 1):
					self.log.error("No connection to EORE could be established!")
					self.log.error("You sure this thing's plugged in?")
					self.state = EORE_CONFIGS["invalid"]	

		self.state['temp'] = float(self.Watchdog(lambda: self.eoreCTL.getTemperature()[25:34]) or -1)

		self.update("default")



	def sweepSource(self, cmdQueue, FELock, ctrlNs):
		print("EORE Log Thread starting")
		
		self.cmdQueue = cmdQueue
		
		while 1:
			FELock.acquire()
			self.state['temp'] = float(self.Watchdog(lambda: self.eoreCTL.getTemperature()[25:34]) or -1)
			if cmdQueue.empty():
				time.sleep(0.005)
			else:
				cmd = cmdQueue.get()
				if "update" in cmd:
					self.update(cmd["update"])
				else:
					for key in cmd:
						self.state[key] = cmd[key]
						if key in self.switches:
							self.parseMessage(self.Watchdog(lambda: self.eoreCTL.writeSwitch(key, cmd[key])))
						elif key in self.attenuators:
							self.parseMessage(self.Watchdog(lambda: self.eoreCTL.writeAtten(key, cmd[key])))
						elif key == 'noiseDiode':
							self.parseMessage(self.Watchdog(lambda: self.eoreCTL.noiseDiodePowerCtl(cmd[key])))
						elif key == 'oscillator':
							self.parseMessage(self.Watchdog(lambda: self.eoreCTL.writeOscillator(0, cmd[key])))
						elif key == 'VCO' :
							if cmd['VCO'] > 0:
								self.parseMessage(self.Watchdog(lambda: self.eoreCTL.chirpVco(cmd[key])))
							else: self.Watchdog(lambda: self.eoreCTL.powerDownVco())
						elif key == 'targetTemp' :
							self.parseMessage(self.Watchdog(lambda: self.eoreCTL.setTemperature(cmd[key])))
				self.log.info("EORE state updated!")
				self.sendState()			

			FELock.release()	
			if ctrlNs.run == False:
				self.log.info("Stopping EORE-thread!")

				break
		self.exit()

	def exit(self): 
		self.log.info("EORE-thread closing dataQueue!")
		self.dataQueue.close()
		self.dataQueue.join_thread()

		self.plotQueue.close()
		self.plotQueue.cancel_join_thread()

		self.ctrlNs.EORERunning = False
		self.log.warning("EORE-thread exiting!")
		self.printQueue.close()
		self.printQueue.join_thread()
		sys.exit()


	def parseMessage(self, ret):
		if (ret[0:3] == "OK:"):
			return True
		if (ret[0:5] == "ERROR:"):
			self.log.error("ERROR when attempting to modify EORE state!")
			self.log.error(ret)
			return False
		else:
			self.log.error("Error parsing EORE status info!")
			self.log.error(ret)
			return False

	def Watchdog(self, f):
		failcount = 0
		serialfailcount = 0
		while (1):
			try:
				if serialfailcount > 0:
					self.eoreCTL = eore.EoreController(EORE_COM_PORT)
					self.log.warning("EORE successfully reconnected!")
					self.state = self.stateBackup
					self.update()
				return f()
			except (eore.TimeoutError, eore.CommandError, eore.UnknownResponseError) as e:
				self.log.warning("Could not access EORE, Retrying...")
				failcount += 1
				if (failcount > 5):
					self.log.error("ERROR when attempting to modify EORE state!")
					self.log.error(e)
					self.state = EORE_CONFIGS["invalid"]
					return None
			except serial.serialutil.SerialException:
				self.log.warning("EORE disconnected!")
				serialfailcount += 1
				if (serialfailcount > 1):
					self.log.error("No connection to EORE could be established!")
					self.log.error("You sure this thing's plugged in?")
					self.state = EORE_CONFIGS["invalid"]
					return None


	def update(self, mode = None):
		#TODO: Make the actual settings completely hidden so that if more attenuators or switches are added only an update of the settings is needed.
		if mode == "now":
			if len(self.state['MAIN_SWITCH_ROTATION']) > 1:
				self.mainIndex = (self.mainIndex + 1) % len(self.state['MAIN_SWITCH_ROTATION'])
				self.state['MAIN_SWITCH'] = self.state['MAIN_SWITCH_ROTATION'][self.mainIndex]
				self.parseMessage(self.Watchdog(lambda: self.eoreCTL.writeSwitch(eore.MAIN_SWITCH, self.state['MAIN_SWITCH'])))
			if len(self.state['SWR_SWITCH_ROTATION']) > 1:
				self.SWRIndex = (self.SWRIndex + 1) % len(self.state['SWR_SWITCH_ROTATION'])
				self.state['SWR_SWITCH'] = self.state['SWR_SWITCH_ROTATION'][self.SWRIndex]
				self.parseMessage(self.Watchdog(lambda: self.eoreCTL.writeSwitch(eore.SWR_SWITCH, self.state['SWR_SWITCH_'])))
			return
		else:
			if mode != None:
				self.state = EORE_CONFIGS[mode]
				self.stateBackup = EORE_CONFIGS[mode]
			self.parseMessage(self.Watchdog(lambda: self.eoreCTL.writeAtten(eore.MAIN_TONE_ATTEN,       self.state['MAIN_TONE_ATTEN'])))
			self.parseMessage(self.Watchdog(lambda: self.eoreCTL.writeAtten(eore.AUX_TONE_ATTEN,        self.state['AUX_TONE_ATTEN'])))
			self.parseMessage(self.Watchdog(lambda: self.eoreCTL.writeAtten(eore.NOISE_DIODE_ATTEN,     self.state['NOISE_DIODE_ATTEN'])))
			self.parseMessage(self.Watchdog(lambda: self.eoreCTL.writeAtten(eore.SWITCH_SWR_TONE_ATTEN, self.state['SWITCH_SWR_TONE_ATTEN'])))
			self.parseMessage(self.Watchdog(lambda: self.eoreCTL.writeAtten(eore.SWITCH_TONE_ATTEN,     self.state['SWITCH_TONE_ATTEN'])))
			self.parseMessage(self.Watchdog(lambda: self.eoreCTL.writeAtten(eore.MID_AMP_ATTEN,         self.state['MID_AMP_ATTEN'])))
			self.parseMessage(self.Watchdog(lambda: self.eoreCTL.noiseDiodePowerCtl(self.state['noiseDiode'])))
			self.parseMessage(self.Watchdog(lambda: self.eoreCTL.writeOscillator(0, self.state['oscillator'])))
			self.parseMessage(self.Watchdog(lambda: self.eoreCTL.powerDownVco()))
			self.parseMessage(self.Watchdog(lambda: self.eoreCTL.setTemperature(self.state['targetTemp'])))
			self.parseMessage(self.Watchdog(lambda: self.eoreCTL.writeSwitch(eore.MAIN_SWITCH, self.state['MAIN_SWITCH'])))
			self.parseMessage(self.Watchdog(lambda: self.eoreCTL.writeSwitch(eore.SWR_SWITCH, self.state['SWR_SWITCH'])))

	def sendState(self):
		
		# We have everything we want
		#	if all(self.state.values()):
		self.log.debug("Complete self.state = %s. emitting to logger!", self.state)
		self.dataQueue.put({"eore-info" : self.state.copy()})
		self.clearData()


	def clearData(self):

			self.state['temp'] = None



def dotest():
	print("Starting test")
	import Queue
	logSetup.initLogging()
	startGpsLog((Queue.Queue(), Queue.Queue()), None, Queue.Queue())

if __name__ == "__main__":
	dotest()


