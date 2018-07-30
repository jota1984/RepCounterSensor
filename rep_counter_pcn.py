import serial 
import re 
import datetime
import socket 
import requests 
import struct 

from digi.xbee.devices import XBeeDevice
from digi.xbee.util import utils
from digi.xbee.models.address import XBee64BitAddress
from digi.xbee.models.status import PowerLevel
from digi.xbee.exception import InvalidPacketException

SERIAL_PORT = '/dev/ttyUSB0' 
SERIAL_BPS = 9600 

THIGH_SOURCE = XBee64BitAddress(bytearray(b'\x00\x13\xA2\x00\x41\x80\xAA\xA5')) 
ECG_SOURCE = XBee64BitAddress(bytearray(b'\x00\x13\xA2\x00\x41\x80\xAA\xA6')) 

REST_PORT = 3000
REST_ADDR = "18.222.128.16"

POSITION_STANDING = 0
POSITION_SQUAT = 1 
POSITION_PLANK_HIGH = 2
POSITION_PLANK_LOW = 3 
POSITION_UNKNOWN = 4  

POSITION_LABELS = ("STANDING","SQUATTING", "PLANK_HIGH", "PLANK_LOW", "UNKOWN")  

def test_threshold(position, thresh_lo, thresh_hi):
    """Check if position is between thresh_lo and thresh_hi""" 
    x = position[0]
    y = position[1]
    z = position[2]
    d = position[3]
    x_hi = thresh_hi[0]
    y_hi = thresh_hi[1]
    z_hi = thresh_hi[2]
    d_hi = thresh_hi[3]
    x_lo = thresh_lo[0]
    y_lo = thresh_lo[1]
    z_lo = thresh_lo[2]
    d_lo = thresh_lo[3]

    if (x >= x_lo and x <= x_hi 
            and y >= y_lo and y <= y_hi 
            and z >= z_lo and z <= z_hi
            and d >= d_lo and d <= d_hi):
        return True
    else: 
        return False 

class RepCounter():
    """Process data from sensor node to determine pushup
    and squat events and forward them to the cloud""" 

    THRESHOLDS_LOW = (
            (-3.6, 8.0, -3.6, 0.0),
            (-6.0, -3.6, 7.0, 0.0),
            (-3.6, -1.0, -12.0, 20.0),
            (-3.6, -1.0, -12.0, 0.0) 
            )

    THRESHOLDS_HIGH = ( 
            (3.6, 12.0, 3.6, 3000.0),
            (6.0, 3.6, 12.0, 3000.0),
            (3.6, 6.3, -6.2, 3000.0),
            (3.6, 6.3, -6.2, 16.0)
            )


    def __init__(self, addr, port):
        self.addr = addr 
        self.port = port 
        self.current_pos = POSITION_STANDING
        self.last_pos = POSITION_STANDING

    def determine_position(self, position): 
        """categorize a position vector into POSITION_SQUAT, POSITION_STANDING,
        POSITION_PLANK_HIGH, POSITION_PLANK_LOW or POSITION_UNKNOWN"""
        for i in range(0,4):
            if (test_threshold(position, RepCounter.THRESHOLDS_LOW[i], RepCounter.THRESHOLDS_HIGH[i])): 
                return i 
        #return POSITION_UNKOWN if no thresholds match
        return 4 

    def record_squat(self):
        """Report a squat event to the cloud""" 
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("SQUAT!! at " + now)
        requests.post('http://' + REST_ADDR + ':' + str(REST_PORT) + '/squat') 

    def record_pushup(self):
        """Report a pushup event to the cloud""" 
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("PUSHUP!! at " + now)
        requests.post('http://' + REST_ADDR + ':' + str(REST_PORT) + '/pushup') 

    def update_position(self,pos_vector): 
        """update current position and check for transitions"""
        print(pos_vector)
        self.current_pos = self.determine_position(pos_vector)
        print(POSITION_LABELS[self.current_pos])
        if (self.current_pos != POSITION_UNKNOWN):
            if (self.current_pos == POSITION_STANDING and 
                    self.last_pos == POSITION_SQUAT):
                self.record_squat() 
            if (self.current_pos == POSITION_PLANK_HIGH and 
                    self.last_pos == POSITION_PLANK_LOW ):
                self.record_pushup() 
            self.last_pos = self.current_pos

class BioReporter(): 
    """Process data from bio node and report events to the cloud""" 

    def __init__(self, addr, port):
        self.addr = addr 
        self.port = port 

    def report_bio(self, temp, hr ):
        """Report bio entry to the cloud""" 
        print("HR %s TEMP %s" % (hr,temp))
        requests.post('http://' + REST_ADDR + ':' + str(REST_PORT) + 
                '/bio?hr=' + hr + '&temp=' + temp ) 


def main(): 
    rep_counter = RepCounter(REST_ADDR, REST_PORT)
    bio_reporter = BioReporter(REST_ADDR, REST_PORT) 
    device = XBeeDevice(SERIAL_PORT, SERIAL_BPS)
    try:
        device.open()
        device.flush_queues()
        while True:
            try:
                xbee_message = device.read_data()
                if xbee_message is not None:
                    data = xbee_message.data
                    #msg = data.decode()
                    source = xbee_message.remote_device.get_64bit_addr() 
                    print("Msg from %s" % (source))
                    if (source == THIGH_SOURCE):
                        x = struct.unpack(">h",data[0:2])
                        y = struct.unpack(">h",data[2:4])
                        z = struct.unpack(">h",data[4:6])
                        d = struct.unpack(">h",data[6:8])
                        pos_vector = [x[0]/100.0, y[0]/100.0, z[0]/100.0, d[0]] 
                        rep_counter.update_position(pos_vector)
                    elif (source == ECG_SOURCE): 
                        #convert bytearrays to String 
                        hr = "".join(map(chr,data[1:6]))
                        temp = "".join(map(chr,data[7:11]))
                        bio_reporter.report_bio(temp, hr) 
                        
            except InvalidPacketException: 
                print("Invalid Packet") 

    finally:
        if device is not None and device.is_open():
            device.close()

if __name__ == '__main__':
    main()                

