
import multithread

from pybmt.callback.base import PyBMTCallback
from collections import deque

from pybmt.fictrac.state import FicTracState

class ThresholdCallback(PyBMTCallback):
    """
    This class implements control logic for triggering a stimulus when tracking velocity reaches a certain
    threshold. It is just an example of how things can work in a closed loop experiment where tracking state triggers
    stimuli response.
    """

    def __init__(self, speed_threshold=0.009, num_frames_mean=25, is_ball_moving=None):
        """
        Setup a closed loop experiment that keeps track of a running average of the ball speed and generates a stimulus
        when the speed crosses a threshold.

        :param speed_threshold: The speed threshold that must be reached to generate a stimulus.
        :param num_frames_mean: The number frames to use in computing the average.
        """

        # Call the base class constructor
        super(ThresholdCallback, self).__init__()

        self.speed_threshold = speed_threshold
        self.num_frames_mean = num_frames_mean
        self.is_fly_moving = is_ball_moving

    def setup_callback(self):
        """
        We don't need to do much here.

        :return:
        """

        # Our buffer of past speeds
        self.speed_history = deque(maxlen=self.num_frames_mean)
        self.is_signal_on = False

    def process_callback(self, track_state: FicTracState):
        """
        This function is called with each update of fictrac's tracking state.
        A closed loop experiment that keeps track of a running average of the ball speed and generates a stimulus
        when the speed crosses a threshold.

        :param track_state:
        :return:
        """

        # Get the current ball speed
        speed = track_state.speed

        # Add the speed to our history
        self.speed_history.append(speed)
        # Get the running average speed
        avg_speed = sum(self.speed_history) / len(self.speed_history)

        if avg_speed > self.speed_threshold and not self.is_signal_on:
            print("Fly is moving!")
            # Start image aquisition of Basler cameras in sync with Basler.py code
            self.is_fly_moving.value = 1
            self.is_signal_on = True
            switch_left_led(True)

        if avg_speed < self.speed_threshold and self.is_signal_on:
            # Stop image aquisition of Basler cameras in sync with Basler.py code
            print("Fly is resting or dead!")
            self.is_fly_moving.value = 0
            self.is_signal_on = False
            switch_left_led(False)

        return True

    def shutdown_callback(self):
        """
        We don't need to do anything special during shutdown.

        :return:
        """
        pass
