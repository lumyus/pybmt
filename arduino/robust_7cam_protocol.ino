#include <Arduino.h>
#include <Servo.h>

#include "order.h"
#include "slave.h"
#include "parameters.h"

bool is_connected = false; ///< True if the connection with the master is available
bool camera_activated = false;



unsigned long previousMicros = 0;


int camState = 0;

unsigned long fps = 0;
unsigned long exposure_time = 0;

bool turn_on_left_led = false;
bool turn_on_right_led = false;

void setup()
{
  // Init Serial
  Serial.begin(SERIAL_BAUD);

  // Init Motor
  pinMode(LED_PIN, OUTPUT);
  pinMode(CAM_PIN, OUTPUT);
  pinMode(LEFT_LIGHT_PIN, OUTPUT);
  pinMode(RIGHT_LIGHT_PIN, OUTPUT);

  // Wait until the arduino is connected to master
  while(!is_connected)
  {
    write_order(HELLO);
    wait_for_bytes(1, 1000);
    get_messages_from_serial();
  } 
 
}

void loop()
{
  
  get_messages_from_serial();
 
  if (camera_activated == true){
    digitalWrite(LED_PIN, HIGH);
    handle_cameras();
  }else{
    digitalWrite(LED_PIN, LOW);
  }

  if(turn_on_left_led == true){
    digitalWrite(LEFT_LIGHT_PIN, HIGH);
  }else{
    digitalWrite(LEFT_LIGHT_PIN, LOW);
  }

  if(turn_on_right_led == true){
    digitalWrite(RIGHT_LIGHT_PIN, HIGH);
  }else{
    digitalWrite(RIGHT_LIGHT_PIN, LOW);
  }


}

void handle_cameras(){

      if(previousMicros == 0){
        previousMicros =  micros();
        digitalWrite(CAM_PIN, HIGH);
        camState = 1;
      }
     
        unsigned long currentMicros = micros();
        unsigned long elapsed_time = currentMicros - previousMicros;
       
        if(elapsed_time > exposure_time && camState==1){
         digitalWrite(CAM_PIN, LOW);
         camState = 0;
        }
        
        if(elapsed_time > fps && camState==0){
          digitalWrite(CAM_PIN, HIGH);
          camState = 1;
          previousMicros =  currentMicros;
        }
}


void get_messages_from_serial()
{
  if(Serial.available() > 0)
  {
    // The first byte received is the instruction
    Order order_received = read_order();

    if(order_received == HELLO)
    {
      
      // If the cards haven't say hello, check the connection
      if(!is_connected)
      {
        is_connected = true;
        write_order(HELLO);
      }
      else
      {
        // If we are already connected do not send "hello" to avoid infinite loop
        write_order(ALREADY_CONNECTED);
      }
    }
    else if(order_received == ALREADY_CONNECTED)
    {
      is_connected = true;
    }
    else
    {
      switch(order_received)
      {
        // update the camera state
        case START_CAM:
        {
          if(fps && exposure_time){
           camera_activated = true;
          }
          //write_order(START_CAM);
          break;
        }

         case CONFIGURE_CAM_FPS:
        {
          fps = read_i16();
          //write_order(START_CAM);
          break;
        }

         case CONFIGURE_CAM_EXPOSURE_TIME:
        {
          exposure_time = read_i16();
          //write_order(START_CAM);
          break;
        }

        case TURN_LEFT_LIGHT_ON:
        {
          turn_on_left_led = true;
          break;
        }

        case TURN_LEFT_LIGHT_OFF:
        {
          turn_on_left_led = false;
          break;
        }

        case TURN_RIGHT_LIGHT_ON:
        {
          turn_on_right_led = true;
          break;
        }

        case TURN_RIGHT_LIGHT_OFF:
        {
          turn_on_right_led = false;
          break;
        }
        
        // Unknown order
        default:
        
          write_order(ERROR);
          write_i16(404);
          return;
      }
    }
    write_order(RECEIVED); // Confirm the reception
  }
}


Order read_order()
{
  return (Order) Serial.read();
}

void wait_for_bytes(int num_bytes, unsigned long timeout)
{
  unsigned long startTime = millis();
  //Wait for incoming bytes or exit if timeout
  while ((Serial.available() < num_bytes) && (millis() - startTime < timeout)){}
}

// NOTE : Serial.readBytes is SLOW
// this one is much faster, but has no timeout
void read_signed_bytes(int8_t* buffer, size_t n)
{
  size_t i = 0;
  int c;
  while (i < n)
  {
    c = Serial.read();
    if (c < 0) break;
    *buffer++ = (int8_t) c; // buffer[i] = (int8_t)c;
    i++;
  }
}

int8_t read_i8()
{
  wait_for_bytes(1, 100); // Wait for 1 byte with a timeout of 100 ms
  return (int8_t) Serial.read();
}

int16_t read_i16()
{
  int8_t buffer[2];
  wait_for_bytes(2, 100); // Wait for 2 bytes with a timeout of 100 ms
  read_signed_bytes(buffer, 2);
  return (((int16_t) buffer[0]) & 0xff) | (((int16_t) buffer[1]) << 8 & 0xff00);
}

int32_t read_i32()
{
  int8_t buffer[4];
  wait_for_bytes(4, 200); // Wait for 4 bytes with a timeout of 200 ms
  read_signed_bytes(buffer, 4);
  return (((int32_t) buffer[0]) & 0xff) | (((int32_t) buffer[1]) << 8 & 0xff00) | (((int32_t) buffer[2]) << 16 & 0xff0000) | (((int32_t) buffer[3]) << 24 & 0xff000000);
}

void write_order(enum Order myOrder)
{
  uint8_t* Order = (uint8_t*) &myOrder;
  Serial.write(Order, sizeof(uint8_t));
}

void write_i8(int8_t num)
{
  Serial.write(num);
}

void write_i16(int16_t num)
{
  int8_t buffer[2] = {(int8_t) (num & 0xff), (int8_t) (num >> 8)};
  Serial.write((uint8_t*)&buffer, 2*sizeof(int8_t));
}

void write_i32(int32_t num)
{
  int8_t buffer[4] = {(int8_t) (num & 0xff), (int8_t) (num >> 8 & 0xff), (int8_t) (num >> 16 & 0xff), (int8_t) (num >> 24 & 0xff)};
  Serial.write((uint8_t*)&buffer, 4*sizeof(int8_t));
}
