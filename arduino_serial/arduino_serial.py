from __future__ import print_function, division, absolute_import

import time
from multiprocessing import current_process

from arduino_serial import write_order, Order, read_order, write_i8, write_i16
from arduino_serial.utils import open_serial_port
from utils import read_yaml


class ArduinoSerial:

    def __init__(self):

        arduino_config = read_yaml("config.yaml")["ARDUINO_PARAMS"]

        self.baudrate = arduino_config["BAUD_RATE"]
        self.fps = arduino_config["FPS"]
        self.exposure_time = arduino_config["EXPOSURE_TIME"]

        self.serial_file = 0

        if not self.connect():
            print("Connection with Arduino failed!")
            raise Exception

    def connect(self):
        try:
            self.serial_file = open_serial_port(baudrate=self.baudrate, timeout=None)
        except Exception as e:
            raise e
        time.sleep(3)  # TODO: This is a hack
        is_connected = False
        # Initialize communication with Arduino
        while not is_connected:
            print(f"[{current_process().name}] is waiting for Arduino...")
            write_order(self.serial_file, Order.HELLO)
            bytes_array = bytearray(self.serial_file.read(1))
            if not bytes_array:
                time.sleep(3)
                continue
            byte = bytes_array[0]
            if byte in [Order.HELLO.value, Order.ALREADY_CONNECTED.value]:
                is_connected = True

        print(f"[{current_process().name}] is connecting to Arduino...")
        read_order(self.serial_file)
        read_order(self.serial_file)

        if read_order(self.serial_file) == Order.RECEIVED:
            print("Connected to Arduino!")
        else:
            return 0

    def configure_hardware_trigger(self):
        # Write all required parameters for the  hardware trigger of the camera before starting it
        write_order(self.serial_file, Order.CONFIGURE_CAM_FPS)
        fps_to_us = int((1/self.fps)*1000000)
        write_i16(self.serial_file, fps_to_us)
        if read_order(self.serial_file) == Order.RECEIVED:
            print("Hardware trigger configured [FPS] successfully!")
        else:
            raise Exception

        write_order(self.serial_file, Order.CONFIGURE_CAM_EXPOSURE_TIME)
        write_i16(self.serial_file, self.exposure_time)
        if read_order(self.serial_file) == Order.RECEIVED:
            print("Hardware trigger configured [EXPOSURE_TIME] successfully!")
        else:
            raise Exception

        write_order(self.serial_file, Order.START_CAM)
        if read_order(self.serial_file) == Order.RECEIVED:
            print("Camera hardware triggering started!")
        else:
            raise Exception

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
