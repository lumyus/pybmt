#ifndef ORDER_H
#define ORDER_H

// Define the orders that can be sent and received
enum Order {
  HELLO = 0,
  ALREADY_CONNECTED = 3,
  ERROR = 4,
  RECEIVED = 5,
  START_CAM = 7,
};

typedef enum Order Order;

#endif
