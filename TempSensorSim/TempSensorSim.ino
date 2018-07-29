#include <Wire.h>
#include <SoftwareSerial.h>
#include <XBee.h>

// main loop execution interval 
const long interval = 250;
// last loop execution time; 
unsigned long previousMillis = 0; 

// initialize serial com with Xbee 
SoftwareSerial softSerial(2,3);

// initialize xbee
XBee xbee = XBee();

// vector for storing of the data.
 uint8_t payload[13];

 // SH + SL Address of receiving XBee
 XBeeAddress64 addr64 = XBeeAddress64(0x0000000, 0x00000000);
 ZBTxRequest zbTx = ZBTxRequest(addr64, payload, sizeof(payload));
 ZBTxStatusResponse txStatus = ZBTxStatusResponse();

// HR and Temp data 
int base_hr = 60; 
int base_temp = 90;

void setup() {
  // Initialize serial 
  Serial.begin(9600);
  softSerial.begin(9600); 

	xbee.setSerial(softSerial);
}

void sendData() {
	
  payload[0] = (uint8_t) 0xAB;
  payload[1] = (uint8_t) 54;
  payload[2] = (uint8_t) 48;
  payload[3] = (uint8_t) 46; 
  payload[4] = (uint8_t) 48;
  payload[5] = (uint8_t) 48;
  payload[6] = (uint8_t) 0xCD;
  payload[7] = (uint8_t) 57;
  payload[8] = (uint8_t) 48;
  payload[9] = (uint8_t) 46;
  payload[10] = (uint8_t) 48;
  payload[11] = (uint8_t) 48;
  payload[12] = (uint8_t) 0xEF;
	xbee.send(zbTx); 
}

void loop() {

  unsigned long currentMillis = millis(); 
  
  if (currentMillis - previousMillis >= interval) {
    sendData();
    previousMillis = currentMillis;  
  }
}
