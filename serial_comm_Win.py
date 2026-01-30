# Once the PI version is on the Pi, remove "_Win" from this file name
import serial
import json
import time

class SerialComm:
    def __init__(self, port='COM3', baudrate=115200):  # Change COM port as needed
        """Initialize serial connection"""
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=2
        )
        time.sleep(2)
        print(f"Windows serial initialized on {port}")
    
    def read_command(self, timeout=None):
        """Read command from Pi"""
        if timeout:
            start = time.time()
        
        while True:
            if timeout and (time.time() - start) > timeout:
                return None
                
            if self.ser.in_waiting > 0:
                try:
                    line = self.ser.readline().decode('utf-8').strip()
                    command = json.loads(line)
                    print(f"Received command: {command}")
                    return command
                except Exception as e:
                    print(f"Error reading command: {e}")
                    return None
            time.sleep(0.01)
    
    def send_response(self, status, data=None):
        """Send response back to Pi"""
        response = {
            'status': status,
            'data': data
        }
        json_msg = json.dumps(response) + '\n'
        self.ser.write(json_msg.encode('utf-8'))
        print(f"Sent response: {status}")
    
    def close(self):
        """Close serial connection"""
        self.ser.close()
        print("Serial closed")