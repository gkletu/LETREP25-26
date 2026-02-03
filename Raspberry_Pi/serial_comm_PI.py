# Once on the PI, deleate "_PI" from file name
import serial
import json
import time

class SerialCom:
    def __init__(self, port='/dev/serial0', baudrate=115200):
        """Initialize serial connection"""
        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=2
        )
        time.sleep(2) #wait for connection to stablize
        print(f"Pi serial initialized on {port}")

    def send_command(self,command, data=None):
        """Send command to laptop"""
        message = {
            'command': command,
            'data': data
        }
        json_msg = json.dumps(message) = '\n'
        self.ser.write(json_msg.encode('utf-8'))
        print(f"Sent: {command}")

    def read_response(self, timeout=5):
        """Read response from laptop"""
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if self.ser.in_waiting > 0:
                try:
                    line = self.ser.readline().decode('utf-8').strip()
                    response = json.loads(line)
                    print(f"Received: {response}")
                    return response
                except Exception as e:
                    print(f"Error reading response: {e}")
                    return None
            time.sleep(0.01)
        print("Response timeout")
        return None
    
    def close(self):
        """Close serial connection"""
        self.ser.close()
        print("Serial closed")