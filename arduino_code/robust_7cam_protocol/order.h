#ifndef ORDER_H
#define ORDER_H

// Define the orders that can be sent and received
enum Order {
  HELLO = 0,
  ALREADY_CONNECTED = 3,
  ERROR = 4,
  RECEIVED = 5,
  START_CAM = 7,
  TURN_LEFT_LIGHT_ON = 8,
  TURN_RIGHT_LIGHT_OFF = 9,
  TURN_RIGHT_LIGHT_ON = 10,
  TURN_LEFT_LIGHT_OFF = 11
};

typedef enum Order Order;

#endif
