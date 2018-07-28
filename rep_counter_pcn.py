import serial 
import re 
import datetime
import socket 
import requests 

UDP_SVR_ADDR = "192.168.1.3" 
UDP_SVR_PORT = 9999

REST_PORT = 3000
REST_ADDR = "18.222.128.16"

POSITION_STANDING = 0
POSITION_SQUAT = 1 
POSITION_PLANK_HIGH = 2
POSITION_PLANK_LOW = 3 
POSITION_UNKNOWN = 4  

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

POSITION_LABELS = ("STANDING","SQUATTING", "PLANK_HIGH", "PLANK_LOW", "UNKOWN")  

ser = serial.Serial(port='/dev/ttyUSB0')
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 

def test_threshold(position, thresh_lo, thresh_hi):
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

def determine_position(position): 
    for i in range(0,4):
        if (test_threshold(position, THRESHOLDS_LOW[i], THRESHOLDS_HIGH[i])): 
            return i 
    return 4 

def record_squat():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print "SQUAT!! at " + now 
    sock.sendto("SQT", (UDP_SVR_ADDR, UDP_SVR_PORT)) 
    requests.post('http://' + REST_ADDR + ':' + str(REST_PORT) + '/squat') 

def record_pushup():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print "PUSHUP!! at " + now 
    sock.sendto("PSH", (UDP_SVR_ADDR, UDP_SVR_PORT)) 
    requests.post('http://' + REST_ADDR + ':' + str(REST_PORT) + '/pushup') 

last_pos = POSITION_STANDING 
pos = POSITION_STANDING
plank_h = 2000

while True:
    msg = ser.readline() 
    #align with start of message 
    if (re.match("X->(-)?\d+\.\d+,Y->(-)?\d+\.\d+,Z->(-)?\d+\.\d+,D->\d+",msg)): 
        pos_vector = re.split("X->|,Y->|,Z->|,D->",msg.rstrip())[1:] 
        pos_vector = map(float, pos_vector) 
        print pos_vector
        pos = determine_position(pos_vector)
        print POSITION_LABELS[pos] 
        if (pos != POSITION_UNKNOWN):
            if (pos == POSITION_STANDING and 
                    last_pos == POSITION_SQUAT):
                record_squat() 
            if (pos == POSITION_PLANK_HIGH and 
                    last_pos == POSITION_PLANK_LOW ):
                record_pushup() 
            last_pos = pos
    else:
        print "GARBLED -> " + msg
                
