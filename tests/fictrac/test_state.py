import pytest
import numpy as np
from math import isclose

from pybmt.fictrac.state import FicTracState

# A test message that is exactly formatted like fictrac's state messages
test_msg = "1, 0.00061658055072047, 0.00049280924124894, 0.00028854775028054, 4383.0244305051, -0.00049229297796647, 0.00028846777828354, -0.00061703022026165, 0.0053108667004006, -0.0013475230246914, 0.00028682299296761, -1.2046443372631, 1.2104273986131, 1.2054460682211, 0.00028831588044736, 0.00049238194388207, 0.00061703022026165, 1.0407586027826, 0.00057058394234585, 0.00028846777828354, 0.00049229297796647, 20, 1"

# The values of the message.
test_values = np.array([1, 0.00061658055072047, 0.00049280924124894, 0.00028854775028054,
                        4383.0244305051, -0.00049229297796647, 0.00028846777828354,
                        -0.00061703022026165, 0.0053108667004006, -0.0013475230246914,
                        0.00028682299296761, -1.2046443372631, 1.2104273986131, 1.2054460682211,
                        0.00028831588044736, 0.00049238194388207, 0.00061703022026165,
                        1.0407586027826, 0.00057058394234585, 0.00028846777828354, 0.00049229297796647,
                        20, 1])

# Create a state from the above message
fstate = FicTracState.zmq_string_msg_to_state(test_msg)

def assert_vec(field, vals):
    for i in range(3):
        assert isclose(field[i], vals[i])

def test_zmq_string_to_fictrac_state():

    # Check all the values
    assert (fstate.frame_cnt == test_values[0])
    assert_vec(fstate.del_rot_cam_vec, test_values[1:4])
    assert isclose(fstate.del_rot_error, test_values[4])
    assert_vec(fstate.del_rot_lab_vec, test_values[5:8])
    assert_vec(fstate.abs_ori_cam_vec, test_values[8:11])
    assert_vec(fstate.abs_ori_lab_vec, test_values[11:14])
    assert isclose(fstate.posx, test_values[14])
    assert isclose(fstate.posy, test_values[15])
    assert isclose(fstate.heading, test_values[16])
    assert isclose(fstate.direction, test_values[17])
    assert isclose(fstate.speed, test_values[18])
    assert isclose(fstate.intx, test_values[19])
    assert isclose(fstate.inty, test_values[20])
    assert isclose(fstate.timestamp, test_values[21])
    assert (fstate.seq_num == test_values[22])

def test_print():
    print(fstate)
    fstate

def test_to_np_array():
    np.allclose(fstate.to_np_array(), test_values)
    assert (test_values[0] == fstate.to_np_array()[0])
    assert (test_values[22] == fstate.to_np_array()[22])


