import eore

#the com port that eore is connecteded to. eg. "COM1"
EORE_COM_PORT = "COM7"

EORE_CONFIGS = {}

EORE_CONFIGS["invalid"] = {
		'MAIN_TONE_ATTEN' : -1,
		'AUX_TONE_ATTEN' : -1,
		'NOISE_DIODE_ATTEN' : -1,
		'SWITCH_SWR_TONE_ATTEN' : -1,
		'SWITCH_TONE_ATTEN' : -1,
		'MID_AMP_ATTEN' : -1,
		'noiseDiode' : -1, 
		'oscillator' : -1,
		'VCO' : -1,
		'temp' : -1, 
		'targetTemp' : -1,
		'MAIN_SWITCH' : -1,
		'SWR_SWITCH' : -1,
		'MAIN_SWITCH_ROTATION' : [eore.TERMINATION],
		'SWR_SWITCH_ROTATION' : [eore.SWITCHED_SWEEPER_INPUT]
	} 

EORE_CONFIGS["default"] = {
		'MAIN_TONE_ATTEN' : 0,
		'AUX_TONE_ATTEN' : 0,
		'NOISE_DIODE_ATTEN' : 0,
		'SWITCH_SWR_TONE_ATTEN' : 0,
		'SWITCH_TONE_ATTEN' : 0,
		'MID_AMP_ATTEN' : 0,
		'noiseDiode' : 0, 
		'oscillator' : 0,
		'VCO' : 0,
		'temp' : None, 
		'targetTemp' : 15,
		'MAIN_SWITCH' : eore.TERMINATION,
		'SWR_SWITCH' : eore.SWITCHED_SWEEPER_INPUT,
		'MAIN_SWITCH_ROTATION' : [eore.TERMINATION, eore.NOISE_SOURCE],
		'SWR_SWITCH_ROTATION' : [eore.SWITCHED_SWEEPER_INPUT]
	}   

EORE_CONFIGS["chop test"] = {
		'MAIN_TONE_ATTEN' : 0,
		'AUX_TONE_ATTEN' : 0,
		'NOISE_DIODE_ATTEN' : 0,
		'SWITCH_SWR_TONE_ATTEN' : 0,
		'SWITCH_TONE_ATTEN' : 0,
		'MID_AMP_ATTEN' : 0,
		'noiseDiode' : 1, 
		'oscillator' : 0,
		'VCO' : 0,
		'temp' : None, 
		'targetTemp' : 15,
		'MAIN_SWITCH' : eore.TERMINATION,
		'SWR_SWITCH' : eore.SWITCHED_SWEEPER_INPUT,
		'MAIN_SWITCH_ROTATION' : [eore.TERMINATION, eore.NOISE_SOURCE],
		'SWR_SWITCH_ROTATION' : [eore.SWITCHED_SWEEPER_INPUT]
	}  

EORE_ATTENUATORS = [
		eore.MAIN_TONE_ATTEN, 
		eore.MAIN_TONE_ATTEN, 
		eore.NOISE_DIODE_ATTEN, 
		eore.SWITCH_SWR_TONE_ATTEN,
		eore.SWITCH_TONE_ATTEN, 
		eore.MID_AMP_ATTEN
	]


EORE_SWITCHES = [
		eore.MAIN_SWITCH, 
		eore.SWR_SWITCH, 
	]