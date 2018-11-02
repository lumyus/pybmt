import pytest
from math import isclose

from pybmt.fictrac.state import FicTracState

def assert_vec(field, test_values):
    for i in range(3):
        assert isclose(field[i], test_values[i])

def test_zmq_string_to_fictrac_state():
    test_msg = "1, 0.00061658055072047, 0.00049280924124894, 0.00028854775028054, 4383.0244305051, -0.00049229297796647, 0.00028846777828354, -0.00061703022026165, 0.0053108667004006, -0.0013475230246914, 0.00028682299296761, -1.2046443372631, 1.2104273986131, 1.2054460682211, 0.00028831588044736, 0.00049238194388207, 0.00061703022026165, 1.0407586027826, 0.00057058394234585, 0.00028846777828354, 0.00049229297796647, 20, 1"

    fstate = FicTracState.zmq_string_msg_to_state(test_msg)

    # Check all the values
    assert (fstate.frame_cnt == 1)
    assert_vec(fstate.del_rot_cam_vec, [0.00061658055072047, 0.00049280924124894, 0.00028854775028054])
    assert isclose(fstate.del_rot_error, 4383.0244305051)
    assert_vec(fstate.del_rot_lab_vec, [-0.00049229297796647, 0.00028846777828354, -0.00061703022026165])
    assert_vec(fstate.abs_ori_cam_vec, [0.0053108667004006, -0.0013475230246914, 0.00028682299296761])
    assert_vec(fstate.abs_ori_lab_vec, [-1.2046443372631, 1.2104273986131, 1.2054460682211])
    assert isclose(fstate.posx, 0.00028831588044736)
    assert isclose(fstate.posy, 0.00049238194388207)
    assert isclose(fstate.heading, 0.00061703022026165)
    assert isclose(fstate.direction, 1.0407586027826)
    assert isclose(fstate.speed, 0.00057058394234585)
    assert isclose(fstate.intx, 0.00028846777828354)
    assert isclose(fstate.inty, 0.00049229297796647)
    assert isclose(fstate.timestamp, 20)
    assert (fstate.seq_num == 1)

