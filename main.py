from classes import Keithley, Measurement
import pandas as pd


# set keitley port (can be changed)
keithley_port = 'COM1'

# set keitley channel number for the measure
channel_nb = 1

#set current limit for the measure in mA
current_lim = None

#set over sample rate for the measure
oversamplerate = None

#set minimum voltage of the measure in V
voltagemin = -0.2

#set maximum voltage of the measure in V
voltagemax = 1

#set the voltage step between each measure in mV
step = 20

#do measurement
okeithley = Keithley(keithley_port)
omeasurement = Measurement(channel_nb, current_lim, oversamplerate, voltagemin, voltagemax, step)
omeasurement.measure(okeithley)


#save data in txt:
df=pd.DataFrame(omeasurement.result)
df.to_csv('measure.txt', index=None, sep='\t')