import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib
import time
import matplotlib.pyplot as plt
import numpy as np
import PowerMeter_MA24126 as MA24126
import serial
import os


class PowerSensor:
    def __init__(self, port = "/dev/ttyACM*", baudrate = 19200, timeout = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        
        self._init_serial()
        
    def _init_serial(self):
        try:
            self.ser = serial.Serial(port = self.port, baudrate = self.baudrate, bytesize = 7, parity = serial.PARITY_NONE, stopbits = 1, timeout = self.timeout)
            print(f"Connected to {self.port}")
        except serial.SerialException as e:
            print(f"Error: Unable to connect to serial port: {e}")
            raise
        
    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"Disconnected from {self.port}")
        return True
    
    def write(self, command):
        if not self.ser or not self.ser.is_open:
            print("Error: Serial port is not open")
            return False
        
        try:
            self.ser.write(command.encode())
            return True
        except serial.SerialException as e:
            print(f"Error: Unable to send command: {e}")
            return False
        
    def read(self, size = 1024):
        if not self.ser or not self.ser.is_open:
            print("Error: Serial port is not open")
            return ""
        try:
            response = self.ser.read(size).decode().strip()
            return response
        except serial.SerialException as e:
            print(f"Error: Unable to read data: {e}")
            return ""
        
    def query(self, command, size = 1024):
        self.write(command)
        time.sleep(0.05)
        return self.read(size)
    
    def get_id(self):
        return self.query("IDN?\n")
    
    def start(self):
        return self.write("START\n")
    
    def stop(self):
        return self.write("STOP\n")
    
    def zero_calibration(self, show_progress = True):
        if show_progress:
            print("\nZero calibration start...")
            
        self.write("ZERO\n")
        
        if show_progress:
            for i in range(21):
                progress = min(i*5, 100)
                print(f"\rProgress: {progress}%", end = "")
                time.sleep(1.0)
            print("\rProgress: 100%")
            print("Zero calibration finished.\n")
        else:
            time.sleep(20)
            
        return True
    
    def get_power(self):
        response = self.query("PWR?\n")
        try:
            parts = response.split()
            if len(parts) > 1 and parts[-1].replace('.', '', 1).replace('-', '', 1).isdigit():
                return float(parts[-1])
            elif len(parts) == 1:
                return float(parts[0])
            else:
                raise ValueError("unable to find figure")
                
        except ValueError:
            return None
        
    def measure_power(self, display = True):
        power = self.get_power()
        if power is not None and display:
            print(f"Power: {power:.2f} dBm")
        return power
    
    def get_frequency(self):
        response = self.query("FREQ?\n")
        try:
            return float(response)
        except ValueError:
            print(f"Error: Unable to get frequency (Response: {response})")
            return None
        
    def set_frequency(self, freq_ghz):
        command = f"FREQ {freq_ghz:.3f}\n"
        response = self.query(command)
        if response == "OK":
            print(f"Frequency set to {freq_ghz:.3f} GHz")
            return True
        else:
            print(f"Error: Unable to set frequency (Response: {response})")
            return False
        
    def get_aperture_time(self):
        response = self.query("CHAPERT?\n")
        try:
            return float(response)
        except ValueError:
            print(f"Error: Unable to get aperture time (Response: {response})")
            return None
        
    def set_aperture_time(self, time_ms):
        if time_ms < 0.01 or time_ms > 300:
            print(f"Error: Please set aperture time within 0.01 ms ~ 300 ms")
            return False
        command = f"CHAPERT {time_ms:.2f}\n"
        response = self.query(command)
        
        if response == "OK":
            print(f"Aperture time set to {time_ms:.2f} ms")
            return True
        else:
            print(f"Error: Unable to set aperture time (Response: {response})")
            return False
        
    def get_average_mode(self):
        response = self.query("AVGTYP?\n")
        
        if response == "0":
            return "Moving"
        elif response == "1":
            return "Repeat"
        else:
            print(f"Error: Unable to get average mode (Response: {response})")
            return None
        
    def set_average_mode(self, mode):
        if mode == "Moving" or mode == 0:
            command = "AVGTYP 0\n"
            mode_str = "Moving"
        elif mode == "Repeat" or mode == 1:
            command = "AVGTYP 1\n"
            mode_str = "Repeat"
        else:
            print("Error: Please set 'Moving' or 'Repeat' as average mode")
            return False
        
        response = self.query(command)
        if response == "OK":
            print(f"Average mode set to {mode_str}")
            return True
        else:
            print(f"Error: Unable to set average mode (Response: {response})")
            return False
        
    def get_average_count(self):
        response = self.query("AVGCNT?\n")
        try:
            return int(response)
        except ValueError:
            print(f"Error: Unable to get average count (Response: {response})")
            return None
        
    def set_average_count(self, count):
        if count < 1 or count > 1024:
            print("Error: Please set average count within 1 ~ 1024")
            return False
        
        command = f"AVGCNT {count}\n"
        response = self.query(command)
        
        if response == "OK":
            print(f"Average count set to {count}")
            return True
        else:
            print(f"Error: Unable to set average count (Response: {response})")
            return False
        
    def initialize(self, freq_ghz = None, aperture_ms = None, avg_mode = None, avg_count = None):
        print("\nInitializing sensor...")
        
        device_id = self.get_id()
        print(f"Device ID: {device_id}")
        
        if freq_ghz is not None:
            self.set_frequency(freq_ghz)
            
        if aperture_ms is not None:
            self.set_aperture_time(aperture_ms)
            
        if avg_mode is not None:
            self.set_average_mode(avg_mode)
            
        if avg_count is not None:
            self.set_average_count(avg_count)
            
        print("Initialization complete.\n")
        return True
    
    def show_settings(self):
        print("\n === Current Settings ===")
        
        freq = self.get_frequency()
        if freq is not None:
            print(f"Frequency: {freq:.3f} GHz")
            
        aperture = self.get_aperture_time()
        if aperture is not None:
            print(f"Aperture Time: {aperture:.2f} ms")
            
        avg_mode = self.get_average_mode()
        if avg_mode is not None:
            print(f"Average Mode: {avg_mode}")
            
        avg_count = self.get_average_count()
        if avg_count is not None:
            print(f"Average Count: {avg_count}")
            
        print("==========\n")

# define GPIO pins
direction = 20 # DIrection (DIR) GPIO Pin
step = 23 # Step GPIO Pin
EN_pin = 24 # enable Pin (LOW to enable)
steps_per_rev = 200 # number of full steps per one rotation
# one step is 0.02 mm

# decrare a instance of RpiMotorLib (class pass GPIO pins numbers and the motor type)
motor = RpiMotorLib.A4988Nema(direction, step, (21, 21, 21), "DRV8825")
GPIO.setup(EN_pin, GPIO.OUT) # set enable pin as output
GPIO.output(EN_pin, GPIO.LOW) # activate motor driver

# setting of power sensor
COM_PORT1 = "/dev/ttyACM0" # find by hitting "ls /dev/tty*"
COM_PORT2 = "/dev/ttyACM1"
BAUDRATE = 19200

# decrare a instance of power sensor
try:
    sensor1 = PowerSensor(port = COM_PORT1, baudrate = BAUDRATE)
    print("Sensor1 is Connected.")
    sensor2 = PowerSensor(port = COM_PORT2, baudrate = BAUDRATE)
    print("Sensor2 is Connected.")
except serial.SerialException as e:
    print("Error: Unable to connect to power sensor. Please check comport.: {e}")
    exit()

# setting of measurement parameters

# setting of sweep
sweep_total_steps = 6000 # total number of steps ini:6000
step_increment = 150 # number of steps in a measurement interval ini:150 (b3), 75 (b6)
step_delay = 0.0005 # step delay of motor (stepped of motor)
measurement_delay = 2 # initial delay ini:2 (b3), 4 (b6)

# set the initial position of the motor as zero
current_motor_position = 0
result = {'steps': [], 'power1': [], 'power2': []}

# measurement loop execution
print("\n=== measurement start ===")
print(f"Sweep {sweep_total_steps} steps at {step_increment} step intervals.")

# initialize sensor(freq_ghz = frequency, avg_count = number of averaging)
for i in[sensor1, sensor2]:
    i.initialize(freq_ghz = 13, avg_count = int(2**6))
    i.start()
# sensor.initialize(freq_ghz = 13, avg_count = int(2**6)) # avg_count = 50
# sensor.start()

# a loop that repeatedly moves the motor and measures
for i in range(0, sweep_total_steps, step_increment):
    steps_to_move = step_increment
    motor.motor_go(False, # True = Clockwise, False = Counter-Clockwise
                   "Full", # step type (Full, Half, 1/4, 1/8, 1/16, 1/32)
                   steps_to_move,
                   step_delay,
                   False, # True = print verbose output
                   0.005) # initial delay
    
    # update position
    current_motor_position += steps_to_move
    # initial delay
    time.sleep(measurement_delay)
    # measure power
    power_value1 = sensor1.get_power()
    power_value2 = sensor2.get_power()

    if power_value1 is not None and power_value2 is not None:
            result['steps'].append(current_motor_position)
            result['power1'].append(power_value1)
            result['power2'].append(power_value2)
            print(f"position: {(current_motor_position):4d} steps | power1: {power_value1:.3f} dBm | power2: {power_value2:.3f} dBm")
    else:
        print(f"position: {(current_motor_position):4d} steps | unable to measure power")

print("\n=== measurement end ===")
sensor1.stop()
sensor2.stop()
sensor1.close()
sensor2.close()
GPIO.output(EN_pin, GPIO.HIGH) # disable motor driver
GPIO.cleanup()

# save the graph and data as an image file and CSV file to desktop

# first way
if result['steps']:
    timestamp = time.strftime('%Y%m%d_%H%M%S') # include the current date and time
    save_path = '/home/raspi/Desktop' # set the desktop path
    
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    
    plt.figure(figsize = (10, 6))
    plt.plot(result['steps'], result['power1'], label = 'Sensor1 (ACM0)')
    plt.plot(result['steps'], result['power2'], label = 'Sensor2 (ACM1)')
    plt.title('relation between position and power intensity')
    plt.xlabel(f'position ({steps_per_rev} steps per one rotation) [mm]')
    plt.ylabel('power intensity [dBm]')
    plt.legend()
    plt.grid(True)

    filename_img = os.path.join(save_path, f"power_sweep_graph_{timestamp}.png")
    filename_csv = os.path.join(save_path, f"power_sweep_data_{timestamp}.csv")
    data_to_save = np.stack([result['steps'], result['power1'], result['power2']], axis = 1) # prepare the data array
    plt.savefig(filename_img)
    header_line = 'Position_Power (dBm)'
    plt.show()
    
    try:
        np.savetxt(filename_csv, data_to_save, delimiter = ',', header = header_line, comments = '', fmt = '%.4f')
        print(f"save the graph and data as an image file and CSV file to desktop: {filename_img}, {filename_csv}")
    
    except Exception as e:
        print(f"\nError: {e}")
    
    plt.close('all') # close all graph windows

# second way
if result['steps']:
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    save_path = '/home/raspi/Desktop'
    if not os.path.exists(save_path): os.makedirs(save_path)
    
    filename_csv = os.path.join(save_path, f"power_sweep_data_{timestamp}.csv")
    data_to_save = np.stack([result['steps'], result['power1'], result['power2']], axis = 1)
    np.savetxt(filename_csv, data_to_save, delimiter = ',', header = 'Position, Power1 (dBm), Power2 (dBm)', comments = '', fmt = '%.4f')

    plt.figure(figsize = (10, 6))
    plt.plot(result['steps'], result['power1'], label = 'Sensor1 (ACM0)')
    plt.plot(result['steps'], result['power2'], label = 'Sensor2 (ACM1)')
    plt.title('Dual Sensor Power Intensity')
    plt.xlabel(f'Position ({steps_per_rev} steps per rev) [mm]')
    plt.ylabel('Power Intensity [dBm]')
    plt.legend()
    plt.grid(True)
    
    filename_img = os.path.join(save_path, f"dual_power_graph_{timestamp}.png")
    plt.savefig(filename_img)
    print(f"Saved: {filename_csv} and {filename_img}")
    plt.show()

    plt.close('all') # close all graph windows