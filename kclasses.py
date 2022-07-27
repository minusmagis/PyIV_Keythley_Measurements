import pyvisa
import pandas as pd
import math

# Small function that outputs text only when debugging is enabled
def debug(text):
    DEBUG = False
    if DEBUG: print(text)
    return


class Keythley():
    def __init__(self,gpib_num):
        self.gpib_num = gpib_num
        self.keythley_object = None

    def start(self,debugging=True):
        rm = pyvisa.ResourceManager()
        if debugging: debug(rm.list_resources())
        self.keythley_object = rm.open_resource('GPIB0::'+str(self.gpib_num)+'::INSTR')
        if debugging: debug(self.keythley_object.query('*IDN?'))

    def voltage_sweep(self,start,stop,step,max_current,delay):

        point_num = math.ceil(abs(start-stop)/step)+1

        self.keythley_object.timeout = point_num*300
        self.keythley_object.write(':CONFigure:VOLTage:DC')

        self.keythley_object.write(':CONFigure:CURRent:DC')

        self.keythley_object.write(':OUTP OFF')

        # my_instrument.write('*RST')
        # my_instrument.write(':BEEPer:STATe OFF')
        self.keythley_object.write(':SENS:FUNC:CONC OFF')
        self.keythley_object.write(':SOUR:FUNC VOLT')
        self.keythley_object.write(':SOUR:VOLT:START '+str(start))
        self.keythley_object.write(':SOUR:VOLT:STOP '+str(stop))
        self.keythley_object.write(':SOUR:VOLT:STEP '+str(step))
        # my_instrument.write(':CURR:RANG:AUTO ON')
        self.keythley_object.write(':SENS:FUNC "CURR"')
        self.keythley_object.write(':SENS:CURR:PROT '+str(max_current))

        self.keythley_object.write(':SOUR:VOLT:MODE SWE')
        self.keythley_object.write(':SOUR:SWE:RANG AUTO')
        self.keythley_object.write(':SOUR:SWE:SPAC LIN')
        self.keythley_object.write(':TRIG:COUN '+str(point_num))
        self.keythley_object.write(':SOUR:DEL '+str(delay))  # delay, maybe for each measurement, have to check
        self.keythley_object.write(':OUTP ON')
        values = self.keythley_object.query(':READ?')

        self.keythley_object.write(':OUTP OFF')

        return self._treat_values(values)

    def voltage_sweep_auto(self, point_num, delay):

        voc = self.detect_voc()
        isc = self.detect_isc()

        start = -voc*0.15 if voc >= 0 else voc*0.15
        stop = voc + voc*0.1 if voc >= 0 else voc - voc*0.1
        max_current = isc + isc*0.2

        step = (stop-start)/(point_num-1)

        self.keythley_object.timeout = point_num * 300
        self.keythley_object.write(':CONFigure:VOLTage:DC')

        self.keythley_object.write(':CONFigure:CURRent:DC')

        self.keythley_object.write(':OUTP OFF')

        # my_instrument.write('*RST')
        # my_instrument.write(':BEEPer:STATe OFF')
        self.keythley_object.write(':SENS:FUNC:CONC OFF')
        self.keythley_object.write(':SOUR:FUNC VOLT')
        self.keythley_object.write(':SOUR:VOLT:START ' + str(start))
        self.keythley_object.write(':SOUR:VOLT:STOP ' + str(stop))
        self.keythley_object.write(':SOUR:VOLT:STEP ' + str(step))
        # my_instrument.write(':CURR:RANG:AUTO ON')
        self.keythley_object.write(':SENS:FUNC "CURR"')
        self.keythley_object.write(':SENS:CURR:PROT ' + str(max_current))

        self.keythley_object.write(':SOUR:VOLT:MODE SWE')
        self.keythley_object.write(':SOUR:SWE:RANG AUTO')
        self.keythley_object.write(':SOUR:SWE:SPAC LIN')
        self.keythley_object.write(':TRIG:COUN ' + str(point_num))
        self.keythley_object.write(':SOUR:DEL ' + str(delay))  # delay, maybe for each measurement, have to check
        self.keythley_object.write(':OUTP ON')
        values = self.keythley_object.query(':READ?')

        self.keythley_object.write(':OUTP OFF')

        return self._treat_values(values)

    def detect_voc(self,averages=10,max_volt=21):
        self.keythley_object.timeout = 100000
        self.keythley_object.write(':TRIG:COUN ' + str(averages))
        self.keythley_object.write(':SOUR:FUNC CURR')
        self.keythley_object.write(':SENS:FUNC "VOLT"')
        self.keythley_object.write(':SENS:VOLT:PROT '+str(max_volt))
        self.keythley_object.write(':OUTP ON')
        values = self.keythley_object.query(':READ?')

        self.keythley_object.write(':OUTP OFF')

        values = self._treat_values(values)

        return float(sum(d['Voltage(V)'] for d in values))/len(values)

    def detect_isc(self, averages=10, max_cur=1):
        self.keythley_object.timeout = 100000
        self.keythley_object.write(':TRIG:COUN ' + str(averages))
        self.keythley_object.write(':SOUR:FUNC VOLT')
        self.keythley_object.write(':SENS:FUNC "CURR"')
        self.keythley_object.write(':SENS:CURR:PROT ' + str(max_cur))
        self.keythley_object.write(':OUTP ON')
        values = self.keythley_object.query(':READ?')

        self.keythley_object.write(':OUTP OFF')

        values = self._treat_values(values)

        return float(sum(d['Current(A)'] for d in values)) / len(values)

        #····· ESTIC intentant que em llegeixi el voc i la jsc per fer el rang automaticament, també falta mirar lo del delay de la mesura


    def close(self):
        self.keythley_object.close()

    def _treat_values(self,values,debugging = True):
        values = values.split(",")

        counter = 0
        buffer_list = list()
        final_list = list()
        for value in values:
            if counter < 5:
                buffer_list.append(value)
                counter += 1

            else:
                final_list.append(buffer_list)
                counter = 1
                buffer_list = [value]
                # if counter < 3:
                #     buffer_list.append(value)

        IV_curve = list()
        for row in final_list:
            IV_curve.append({'Voltage(V)': float(row[0]), 'Current(A)': float(row[1])})

        if debugging: debug(IV_curve)

        return IV_curve


class SolarCell:
    def __init__(self, df_iv, light_power, area):
        self.df_iv = df_iv.copy()
        self.df_iv = self._get_df_iv_with_power(df_iv.copy())
        self.light_power = light_power
        self.area = area
        self.isc = None
        self.voc = None
        self.ff = None
        self.pce = None

    def _get_df_iv_with_power(self, df_iv):
        df_iv['Power(W)'] = self.df_iv['Voltage(V)']*self.df_iv['Current(A)']
        return df_iv

    def _calculate_isc(self):
        if 0 in self.df_iv['Voltage(V)'].unique():
            self.isc=self.df_iv['Current(A)'][self.df_iv['Voltage(V)'].sub(0).abs().idxmin()]
        else:
            i=abs(self.df_iv['Voltage(V)']-0).idxmin()
            if self.df_iv.index[-1]<=i:
                i=self.df_iv.index[-1]-1
            c=(self.df_iv['Current(A)'][i+1]-self.df_iv['Current(A)'][i])/(self.df_iv['Voltage(V)'][i+1]-self.df_iv['Voltage(V)'][i])
            self.isc=self.df_iv['Current(A)'][i+1]-c*self.df_iv['Voltage(V)'][i+1]

    def _calculate_jsc(self):
        self._calculate_isc()
        self.jsc = self.isc/self.area

    def _calculate_voc(self):
        if 0 in self.df_iv['Current(A)'].unique():
            self.voc=self.df_iv['Voltage(V)'][self.df_iv['Current(A)'].sub(0).abs().idxmin()]
        else:
            i=abs(self.df_iv['Current(A)']-0).idxmin()
            a=(self.df_iv['Voltage(V)'][i+1]-self.df_iv['Voltage(V)'][i])/(self.df_iv['Current(A)'][i+1]-self.df_iv['Current(A)'][i])
            self.voc=self.df_iv['Voltage(V)'][i+1]-a*self.df_iv['Current(A)'][i+1]

    def _calculate_ff(self):
        max_power_index=self.df_iv['Power(W)'].idxmin()
        if self.isc*self.voc!=0:
            self.ff=self.df_iv['Power(W)'][max_power_index]/(self.isc*self.voc)
        else:
            self.ff=0

    def _calculate_pce(self):
        self.pce=100*(abs(self.jsc)*self.voc*self.ff)/self.light_power

    def calculate_cell_parameters(self):
        self._calculate_voc(),
        self._calculate_jsc(),
        self._calculate_ff(),
        self._calculate_pce()
        self.cell_parameters = {'Voc(V)' : round(self.voc,2),
                                'Jsc(A/m^2)' : round(self.jsc,2),
                                'FF' : round(self.ff,2),
                                'PCE' : round(self.pce,2)}


class CalibrationCell:
    def __init__(self, area, sun1current, mea_current):
        self.area = area
        self.sun1current = sun1current
        self.mea_current = mea_current
        self.irradiance = abs(1000*mea_current/sun1current)












