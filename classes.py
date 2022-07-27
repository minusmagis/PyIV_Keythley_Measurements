import time
import serial


class Keithley():
    def __init__(self, port):
        self.port=port
        self.status="close"
        self.door=self.assign_port()

    def assign_port(self):
        try:
            door=serial.Serial(self.port, 9600, timeout=5)
            door.close()
            return door
        except serial.serialutil.SerialException:
            print('Port not Found')
            return None

    def on_off_door(self):
        if self.door!=None:
            if self.status=="close":
                self.open_door()
            elif self.status=="open":
                self.close_door()

    def close_door(self):
        self.door.close()
        self.status="close"

    def open_door(self):
        self.door.open()
        self.status="open"

    def init_keithley(self, channel_nb, current_lim, oversamplerate):
        if self.status=="close":
            self.on_off_door()
        channel_name = 'CH' + str(channel_nb)
        self.door.write(bytes(channel_name +':ENA\r\n', encoding='utf8'))
        time.sleep(0.05)
        if current_lim != None:
            self.door.write(bytes(channel_name +':CUR '+ str(current_lim) + '\r\n', encoding='utf8'))
            time.sleep(0.05)
        if oversamplerate != None:
            self.door.write(bytes(channel_name +':OSR '+ str(oversamplerate) + '\r\n', encoding='utf8'))
            time.sleep(0.05)

    def send_voltage_to_keithley(self, channel_nb, voltage):
        channel_name = 'CH' + str(channel_nb)
        self.door.write(str(channel_name +":MEA:VOL {}\r\n".format(voltage)).encode('utf-8'))
        self.door.flushInput()

    def receive_result(self):
        keithley_output = self.door.readline().decode('utf-8') # Read response from keithley. Output is in the format "0.123,4.56E-7" for 0.123V and 4.56E-7A
        keithley_output.replace('\x00', '') # Remove null characters
        keithley_output.replace('\x0a', '') # Remove newline character
        return keithley_output

class Measurement():
    def __init__(self, channel_nb, current_lim, oversamplerate, voltagemin, voltagemax, step):
        self.channel_nb = channel_nb
        self.current_lim = current_lim
        self.oversamplerate = oversamplerate
        self.voltagemin = voltagemin
        self.voltagemax = voltagemax
        self.step = step
        self.result = []

    def measure(self, okeithley):
        okeithley.init_keithley(self.channel_nb, self.current_lim, self.oversamplerate)
        self.get_complete_iv(okeithley)
        okeithley.close_door()

    def get_complete_iv(self, okeithley):
        num_steps=(abs(self.voltagemin) + abs(self.voltagemax)) / (self.step / 1000)
        for voltage_step in range(0, int(num_steps) + 2):
            self.get_data_one_iv(okeithley, voltage_step)

    def get_one_iv(self, okeithley, voltage_step):
        set_voltage = self.voltagemin + (voltage_step * (self.step / 1000))
        keithley_output=''
        while keithley_output=='':
            okeithley.send_voltage_to_keithley(self.channel_nb, set_voltage)
            keithley_output = okeithley.receive_result()
        self.build_result(keithley_output)

    def build_result(self, keithley_output):
        keithley_list=keithley_output.split(",")
        self.result.append({'Voltage(V)':float(keithley_list[0]), 'Current(A)':float(keithley_list[1])})