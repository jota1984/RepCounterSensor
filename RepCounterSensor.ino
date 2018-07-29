#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include <SoftwareSerial.h>
#include <XBee.h>

// main loop execution interval 
const long interval = 250;
// last loop execution time; 
unsigned long previousMillis = 0; 

// pin definitions 
const int trigPin = 9; 
const int echoPin = 10;

// Initialize XBee 
XBee xbee = XBee(); 
// we are sending 4 ints, payload = 4*2
uint8_t payload[8];
// send to coordinator (DH = 0, DL = 0)
XBeeAddress64 addr64 = XBeeAddress64(0x0000000, 0x00000000);
ZBTxRequest zbTx = ZBTxRequest(addr64, payload, sizeof(payload));
ZBTxStatusResponse txStatus = ZBTxStatusResponse();

// Sense distance flag
int senseDistanceFlag = 1; 

//Sensor data variables
int x, y, z; 
int distance; 

// initialize serial com for Xbee 
SoftwareSerial softSerial(2,3);

/* Assign ID to to accelerometer */
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);

void setup() {
  // Initialize serial 
  Serial.begin(9600);
  softSerial.begin(9600); 
  xbee.setSerial(softSerial);

  // Initialize Ultrasonic Sensor
  pinMode(trigPin, OUTPUT); 
  pinMode(echoPin, INPUT); 

  // Initialize accelerometer 
  if (!accel.begin()) {
    Serial.println("Ooops, no ADXL345 detected ... Check your wiring!");
    while(1);
  }
  accel.setRange(ADXL345_RANGE_2_G);
}

void senseDistance() {
  if (senseDistanceFlag){
    // send trigger pulse
    digitalWrite(trigPin, LOW); 
    delayMicroseconds(2); 
    digitalWrite(trigPin, HIGH); 
    delayMicroseconds(10); 
    digitalWrite(trigPin, LOW); 

    // read echo 
    long pulseDuration = pulseIn(echoPin, HIGH); 
    // speed of sound = 340 m/s = 0.034 cm / us 
    // distance = speed of sound * pulseDuration / 2; 
    distance = pulseDuration * 0.034 / 2;  
  }
}

void senseTilt(){
  sensors_event_t event; 
  accel.getEvent(&event);

  // We are storing values as ints  for easier encoding for
  // transmission
  x = (int)(event.acceleration.x * 100);
  y = (int)(event.acceleration.y * 100);
  z = (int)(event.acceleration.z * 100); 
   
}

void sendData() {
  String x_str, y_str, z_str;
  x_str = String(x/100.0);
  y_str = String(y/100.0);
  z_str = String(z/100.0); 
  String out = String("X->" + x_str + ",Y->" + y_str + ",Z->" + z_str +",D->" + distance); 

  Serial.println(out);
  //Xbee.println(out);  

  payload[0] = x >> 8; 
  payload[1] = x; 
  payload[2] = y >> 8; 
  payload[3] = y; 
  payload[4] = z >> 8; 
  payload[5] = z; 
  payload[6] = distance >> 8; 
  payload[7] = distance; 

  xbee.send(zbTx); 
}

void loop() {

  unsigned long currentMillis = millis(); 
  
  if (currentMillis - previousMillis >= interval) {
    senseTilt(); 
    senseDistance(); 
    sendData();
    previousMillis = currentMillis;  
  }
  
}
