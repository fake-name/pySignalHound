# I'm worried about possible IF frequencies creeping into the data, so I'm adding a 2.5 Mhz shift to
# prevent the signal of interest (h-flip band) from being exactly centered in the acquired data.
# I suspect the IF runs at the center frequency, and is sensitive to +-10 Mhz around the center.
# Therefore, I can see some of the IF center-frequency creeping into the actual data.
#
# Note: H_FLIP_FREQ is a convenience variable. It's only defined to make how the ACQ_FREQ is determined
# more clear. The only variable the actual acquisition system cares about is ACQ_FREQ
# H_FLIP_FREQ            = 1.420405751786e9

# Center frequency of the acquisition scan.
# ACQ_FREQ               = H_FLIP_FREQ + 2.5e6
ACQ_FREQ               = 200e6 + 2.5e6

# The ACQ_SPAN is the width of the acquisiton window. For "real-time" mode, the MAXIMUM width is 20 Mhz. For "sweeping" mode, it can be any integer.
ACQ_SPAN               = 30e6
# ACQ_SPAN               = 300e6

# Reference level of the acquisition
ACQ_REF_LEVEL_DB       = -60

# Attenuation and gain for the acquisition. Ranges: 0-3, -1 for "auto", where the hardware tries to determine the ideal gain/attenuation from the specified reference level.
ACQ_ATTENUATION_DB     = 10
ACQ_GAIN_SETTING       = 0

# Realtime Bandwith (e.g. bin-size) of the FFT.
#Possible values:
# 631.2e3, Num Bins: 256    Largest Real-Time RBW
# 315.6e3, Num Bins: 512
# 157.1e3, Num Bins: 1024
# 78.90e3, Num Bins: 2048
# 39.45e3, Num Bins: 4096
# 19.72e3, Num Bins: 8192
# 9.863e3, Num Bins: 16384
# 4.931e3, Num Bins: 32768
# 2.465e3, Num Bins: 65536  Smallest Real-Time RBW
# Bandwidths below 9.863e3 seem to only return 16 kpts. Not sure why.
ACQ_RBW                = 2.465e3

# Acquisition Video-bandwidth. Normally just the same as the RBW
ACQ_VBW                = ACQ_RBW

# Sweep-time. In seconds. Valid ranges - 0.1 - 0.0001
ACQ_SWEEP_TIME_SECONDS = 0.0001

# FFT Windowing function.
# Supported windows:
# "nutall"
# "blackman"
# "hamming"
# "flat-top"
ACQ_WINDOW_TYPE        = "hamming"

# ACQ_UNITS determines what type of video processing is applied to the data.
# "log"      = dBm
# "voltage"  = mV
# "power"    = mW
# "bypass"   = No video processing
ACQ_UNITS              = "power"

# Acquisition mode. The only modes really likely relevant here are "sweeping" or "real-time"
# "sweeping"       : Sweep the acquisition window across a large span, in 20 Mhz chunks. This is the mode the device must be in for any ACQ_SPAN > 20 Mhz.
# "real-time"      : Acquire on the same 20 Mhz window continuously. Should have no dead-time in the acquisition, leading to 100% integration efficency.
# -
# Other, specialized modes.
# "zero-span"
# "time-gate"
# "raw-sweep"
# "raw-sweep-loop"
# "audio-demod"
# "raw-pipe"
#ACQ_TYPE               = "real-time"
#ACQ_TYPE               = "sweeping"

# The real-time-sweeping mode is a synthetic mode provided by this software, rather then an actual hardware mode.
ACQ_TYPE               = "real-time-sweeping"
# overlap of acquisitions in the real-time-sweeping mode. In percentage. 1=100%, 0.5 = 50%, 0.01 = 1%, 0 = 0%
# Don't actually use 1 (100%). Shit would break.
ACQ_OVERLAP            = 0.5
# Number of scans to take at each frequency
ACQ_BIN_SAMPLES        = 1000


# The acquired data modes. Valid options are "average" and "min-max"
# "average" returns the average power integrated over the "sweep-time" interval.
# "min-max" is the minimum and maximum value tracked over the "sweep-time" interval. This mode is not currently supported by the data-logging system.
# Contact Connor if you need it.
ACQ_MODE               = "average"

# Scquisition Y scaling settings.
# Valid options:
# "log-scale"
# "log-full-scale"
# "lin-scale"
# "lin-full-scale"

# The ACQ_Y_SCALE parameter will change the units of returned sweeps. If "log-scale" is provided
# sweeps will be returned in amplitude unit dBm. If "lin-scale" is specified, the returned units will be in
# millivolts. If the full scale units are specified, no corrections are applied to the data and amplitudes are
# taken directly from the full scale input.
ACQ_Y_SCALE            = "log-scale"

# The
PRINT_LOOP_CNT         = 100

# The system temperature and diagnostics are read out every CAL_CHK_LOOP_CNT sweeps. If the system temperature has devicated more then 2C,
# the acquisition loop will automatically recalibrate the IF frontend, and embed the proper information reflecting the fact that the
# system was recalibrated in the cal-log table in the data-log.
CAL_CHK_LOOP_CNT       = 5000

# Number of acquisition sweeps averaged over for each data-array written to the log files.
NUM_AVERAGE            = 600 * 6

# Number of acquisition sweeps averaged over for each data-array fet to the plotting system
# ~60 divided by NUM_AVERAGE yields Hz
NUM_PLOT_AVERAGE       = 30

# File rotation interval in seconds:
FILE_ROTATION_INTERVAL = 60 * 60 # 1 hour

# If you set GPS_COM_PORT to None, GPS logging is disabled
# If GPS_COM_PORT is not none, the system will try to open the port GPS_COM_PORT, and
# expect to receive a NMEA gps data stream.

GPS_COM_PORT = None
# GPS_COM_PORT = 'COM3'
# GPS_COM_PORT = 'COM14'
# GPS_COM_PORT = '/dev/tty.PL2303-00001014'