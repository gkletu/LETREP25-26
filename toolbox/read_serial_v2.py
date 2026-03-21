import serial
import time

### Sampling Method: This is the important thing!! ###
def read_serial():
    line_raw = ser.readline().decode('utf-8').strip()
    if line_raw:
        value = float(line_raw)
    return value

### Initialization Code ###---

# --- Settings ---
SERIAL_PORT = '/dev/ttyUSB0'    # Verify using lsusb
BAUD_RATE =  9600   # Must match Baud rate of ESP32

# --- Serial Setup --- We would want this in the initialization
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout = 0.01)
time.sleep(2)

### Conditions for Test ###
read = True
force_reading = []

### Sample Sampling Loop ###

while read:
    force_reading.append(read_serial())
    print(f"Force is {force_reading}")

