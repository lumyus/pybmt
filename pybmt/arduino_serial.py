from __future__ import print_function, division, absolute_import

import time

from robust_serial import write_order, Order, write_i8, write_i16, read_i8, read_order
from robust_serial.utils import open_serial_port


def connect_arduino():
    try:
        serial_file = open_serial_port(baudrate=115200, timeout=None)
    except Exception as e:
        raise e
    time.sleep(3) # TODO: This is a hack
    is_connected = False
    # Initialize communication with Arduino
    while not is_connected:
        print("Waiting for Arduino...")
        write_order(serial_file, Order.HELLO)
        bytes_array = bytearray(serial_file.read(1))
        if not bytes_array:
            time.sleep(3)
            continue
        byte = bytes_array[0]
        if byte in [Order.HELLO.value, Order.ALREADY_CONNECTED.value]:
            is_connected = True

    print("Connecting to Arduino...")
    read_order(serial_file)
    read_order(serial_file)

    if read_order(serial_file) == Order.RECEIVED:
        print("Connected to Arduino!")
    else: print("Error with connection to Arduino!!")

    # Equivalent to write_i8(serial_file, Order.MOTOR.value)
    write_order(serial_file, Order.START_CAM)
    read_order(serial_file)

    if read_order(serial_file) == Order.RECEIVED:
        print("Triggering started!")

