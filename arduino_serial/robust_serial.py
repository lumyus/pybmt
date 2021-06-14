from __future__ import print_function, division, unicode_literals, absolute_import

import struct

from enum import Enum


class Order(Enum):
    """
    Pre-defined orders
    """

    HELLO = 0
    ALREADY_CONNECTED = 3
    ERROR = 4
    RECEIVED = 5
    START_CAM = 7
    TURN_LEFT_LIGHT_ON = 8
    TURN_RIGHT_LIGHT_OFF = 9
    TURN_RIGHT_LIGHT_ON = 10
    TURN_LEFT_LIGHT_OFF = 11
    CONFIGURE_CAM_FPS = 12
    CONFIGURE_CAM_EXPOSURE_TIME = 13

def read_order(f):
    """
    :param f: file handler or serial file
    :return: (Order Enum Object)
    """
    return Order(read_i8(f))

def read_i8(f):
    """
    :param f: file handler or serial file
    :return: (int8_t)
    """
    return struct.unpack('<b', bytearray(f.read(1)))[0]


def read_i16(f):
    """
    :param f: file handler or serial file
    :return: (int16_t)
    """
    return struct.unpack('<h', bytearray(f.read(2)))[0]


def read_i32(f):
    """
    :param f: file handler or serial file
    :return: (int32_t)
    """
    return struct.unpack('<l', bytearray(f.read(4)))[0]


def write_i8(f, value):
    """
    :param f: file handler or serial file
    :param value: (int8_t)
    """
    if -128 <= value <= 127:
        f.write(struct.pack('<b', value))
    else:
        print("Value error:{}".format(value))


def write_order(f, order):
    """
    :param f: file handler or serial file
    :param order: (Order Enum Object)
    """
    write_i8(f, order.value)


def write_i16(f, value):
    """
    :param f: file handler or serial file
    :param value: (int16_t)
    """
    f.write(struct.pack('<h', value))


def write_i32(f, value):
    """
    :param f: file handler or serial file
    :param value: (int32_t)
    """
    f.write(struct.pack('<l', value))