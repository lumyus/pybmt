from __future__ import print_function, division, absolute_import

import time

from robust_serial import write_order, Order, read_order, write_i8
from robust_serial.utils import open_serial_port


class ArduinoSerial:

    serial_file = 0

    def connect_arduino(self):
        try:
            self.serial_file = open_serial_port(baudrate=115200, timeout=None)
        except Exception as e:
            raise e
        time.sleep(3)  # TODO: This is a hack
        is_connected = False
        # Initialize communication with Arduino
        while not is_connected:
            print("Waiting for Arduino...")
            write_order(self.serial_file, Order.HELLO)
            bytes_array = bytearray(self.serial_file.read(1))
            if not bytes_array:
                time.sleep(3)
                continue
            byte = bytes_array[0]
            if byte in [Order.HELLO.value, Order.ALREADY_CONNECTED.value]:
                is_connected = True

        print("Connecting to Arduino...")
        read_order(self.serial_file)
        read_order(self.serial_file)

        if read_order(self.serial_file) == Order.RECEIVED:
            print("Connected to Arduino!")
        else:
            print("Error with connection to Arduino!!")

        write_order(self.serial_file, Order.START_CAM)
        if read_order(self.serial_file) == Order.RECEIVED:
            print("Camera hardware triggering started!")

    def switch_left_led(self, turn_on_left):

        if turn_on_left:
            write_order(self.serial_file, Order.TURN_LEFT_LIGHT_ON)
        else:
            write_order(self.serial_file, Order.TURN_LEFT_LIGHT_OFF)

        if read_order(self.serial_file) != Order.RECEIVED:
            print('An error occurred while trying to send a order [TURN_LEFT_LIGHT_ON/OFF] to the Arduino!')

    def switch_right_led(self, turn_on_right):

        if turn_on_right:
            write_order(self.serial_file, Order.TURN_RIGHT_LIGHT_ON)
        else:
            write_order(self.serial_file, Order.TURN_RIGHT_LIGHT_OFF)

        if read_order(self.serial_file) != Order.RECEIVED:
            print('An error occurred while trying to send a order [TURN_RIGHT_LIGHT_ON/OFF] to the Arduino!')
