import multiprocessing
import pickle
import time
from enum import Enum

from pypylon import pylon

from ball_movements import BallMovements
from pybmt.arduino_serial import ArduinoSerial
from pybmt.callback.threshold_callback import ThresholdCallback
from pybmt.fictrac.driver import FicTracDriver
from basler import Basler


def run_fictrac(status):
    fictrac_config = "config.txt"
    fictrac_console_out = "output.txt"

    print('Starting Fictrac..')

    # Instantiate the callback object thats methods are invoked when new tracking state is detected.
    callback = ThresholdCallback(shared_status=status)

    # Instantiate a FicTracDriver object to handle running of FicTrac in the background and communication
    # of program state.
    tracDrv = FicTracDriver(config_file=fictrac_config, console_ouput_file=fictrac_console_out,
                            track_change_callback=callback, plot_on=False,
                            fic_trac_bin_path='/home/nely/Desktop/Cedric/fictrac/bin/fictrac')

    # This will start FicTrac and block until complete
    tracDrv.run()


def run_basler_aquisition(status):
    serial_numbers = ['40018619']
    frame_size = (1920, 1200)
    output_path = '/home/nely/Desktop/Cedric/images/'

    arduino_protocol = ArduinoSerial()
    arduino_protocol.connect_arduino()

    basler_cameras = Basler(shape=frame_size, serial_numbers=serial_numbers,buffer=200)
    basler_cameras.run()

    # make this cancelable

    captured_frames = []

    while True:

        ball_status = int(BallMovements(status.value))

        if ball_status == BallMovements.BALL_MOVING:
            # grab the available frames for each camera
            captured_frames.append(basler_cameras.grab_frames())

        elif status.value == BallMovements.BALL_STOPPED:
            # Fictrac is not registering movement anymore. Save the captured frames.
            if len(captured_frames):
                time_stamp = time.strftime("%Y%m%d-%H%M%S")
                pickle.dump(captured_frames, open(output_path + 'results_' + time_stamp + '.pkl', 'wb'))
                print(f"Saving completed. Exported frames: {len(captured_frames[0])}")
                captured_frames.clear()

        elif status.value == BallMovements.BALL_ROTATING_LEFT:
            arduino_protocol.switch_left_led(True)
            arduino_protocol.switch_right_led(False)
        elif status.value == BallMovements.BALL_ROTATING_RIGHT:
            arduino_protocol.switch_right_led(True)
            arduino_protocol.switch_left_led(False)


if __name__ == "__main__":
    # https://stackoverflow.com/questions/56549971/sharing-boolean-between-processes
    # https://stackoverflow.com/questions/27868395/python-multiprocessing-object-passed-by-value

    # Easiest way to connect a specific camera to fictrac:
    # Pass a list of cameras that we want to connect to. The one not on the list will be connected to Fictrac
    # We need to start the Fictrac process after the cameras have been initialized

    shared_status = multiprocessing.Manager().Value('i', BallMovements.BALL_STOPPED)

    process1 = multiprocessing.Process(target=run_fictrac, args=(shared_status,))
    process2 = multiprocessing.Process(target=run_basler_aquisition, args=(shared_status,))

    process1.start()
    process2.start()

    process1.join()
    process2.join()
