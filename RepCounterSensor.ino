#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>
#include <SoftwareSerial.h>

// main loop execution interval 
const long interval = 250;
// last loop execution time; 
unsigned long previousMillis = 0; 

// pin definitions 
const int trigPin = 9; 
const int echoPin = 10;

// Sense distance flag
int senseDistanceFlag = 1; 

//Sensor data variables
String x, y, z; 
int distance; 

// initialize serial com with Xbee 
SoftwareSerial Xbee(2,3);

/* Assign ID to to accelerometer */
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);

void setup() {
  // Initialize serial 
  Serial.begin(9600);
  Xbee.begin(9600); 

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

  x = String(event.acceleration.x);
  y = String(event.acceleration.y);
  z = String(event.acceleration.z); 
   
}

void sendData() {
  String out = String("X->" + x + ",Y->" + y + ",Z->" + z +",D->" + distance); 
  Serial.println(out);
  Xbee.println(out);  
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
