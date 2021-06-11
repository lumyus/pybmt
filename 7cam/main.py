import multiprocessing
import pickle
import time
import timeit
from enum import Enum

import yaml
from pypylon import pylon

from ball_movements import BallMovements
from pybmt.arduino_serial import ArduinoSerial
from pybmt.callback.movement_callback import MovementCallback
from pybmt.fictrac.driver import FicTracDriver
from basler import Basler, write_videos


def read_yaml(file_path):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def run_fictrac_process(status):

    config = read_yaml("config.yml")["FICTRAC_PARAMS"]

    fictrac_config = config["FICTRAC_CONFIGURATION_FILE"]
    fictrac_console_out = config["FICTRAC_CONSOLE_OUT_FILE"]
    fic_trac_bin_path = config["FICTRAC_BIN_PATH"]

    while True:
        print('Running performance test!')
        time.sleep(2)
        status.value = BallMovements.BALL_MOVING
        time.sleep(5)
        status.value = BallMovements.BALL_STOPPED

    print('Starting Fictrac..')

    # Instantiate the callback object thats methods are invoked when new tracking state is detected.
    callback = MovementCallback(shared_status=status)

    # Instantiate a FicTracDriver object to handle running of FicTrac in the background and communication
    # of program state.
    tracDrv = FicTracDriver(config_file=fictrac_config, console_ouput_file=fictrac_console_out,
                            track_change_callback=callback, plot_on=False,
                            fic_trac_bin_path=fic_trac_bin_path)

    # This will start FicTrac and block until complete
    tracDrv.run()


def run_aquisation_process(status):

    config = read_yaml("config.yml")["BASLER_PARAMS"]

    #TODO serial number is randomly selecting a fictrac cam at the moment
    serial_numbers = config["SERIAL_NUMBERS"]
    frame_size = config["FRAME_SIZE"]
    output_path = config["OUTPUT_PATH"]
    baud_rate = config["BAUD_RATE"]
    buffer = config["BUFFER"]

   # arduino_protocol = ArduinoSerial(baud_rate)

    #TODO Remove this part and add it to the ArduiinoSerial class
    #if not arduino_protocol.connect_arduino():
    #    print("Connection with Arduino failed!")
    #    raise Exception


    basler_cameras = Basler(shape=frame_size, serial_numbers=serial_numbers, buffer=buffer)
    basler_cameras.run()

    captured_frames = []
    recording_start_time = 0

    while True:

        ball_status = BallMovements(status.value)

        if ball_status == BallMovements.BALL_MOVING:
            # grab the available frames for each camera

            if recording_start_time == 0:
                recording_start_time = time.perf_counter()
                captured_frames.append(basler_cameras.grab_frames(status.value))

        elif ball_status == BallMovements.BALL_STOPPED:
            # Fictrac is not registering movement anymore. Save the captured frames.
            if len(captured_frames):

                if len(set(map(len, captured_frames))) == 0:
                    print("ATTENTION. The cameras did not record the same amount of frames!")
                    print("Stopping the program now!")
                    break

                elapsed_time = time.perf_counter() - recording_start_time
                average_fps_obtained = int((len(captured_frames)-buffer) / elapsed_time)
                recording_start_time = 0

                time_stamp = time.strftime("%Y%m%d-%H%M%S")
                pickle.dump(captured_frames, open(output_path + 'results_' + time_stamp + '.pkl', 'wb'))
                print(
                    f"Saving completed. Exported frames: {len(captured_frames)}. Averaged FPS during recording: {average_fps_obtained}")
                captured_frames.clear()

        #handle_experiment(ball_status, arduino_protocol)


def handle_experiment(ball_status, arduino_protocol):

    if ball_status == BallMovements.BALL_ROTATING_LEFT:
        # turn the left LED ON
        arduino_protocol.switch_left_led(True)
        arduino_protocol.switch_right_led(False)

    elif ball_status == BallMovements.BALL_ROTATING_RIGHT:
        # turn the right LED ON
        arduino_protocol.switch_right_led(True)
        arduino_protocol.switch_left_led(False)

    elif ball_status == BallMovements.BALL_STOPPED:
        # turn both LEDs OFF
        arduino_protocol.switch_left_led(False)
        arduino_protocol.switch_right_led(False)


if __name__ == "__main__":
    # https://stackoverflow.com/questions/56549971/sharing-boolean-between-processes
    # https://stackoverflow.com/questions/27868395/python-multiprocessing-object-passed-by-value

    # Easiest way to connect a specific camera to fictrac:
    # Pass a list of cameras that we want to connect to. The one not on the list will be connected to Fictrac
    # We need to start the Fictrac process after the cameras have been initialized

    EXPORT_VIDEOS = False

    if EXPORT_VIDEOS:
        config = read_yaml("config.yml")["BASLER_PARAMS"]
        write_videos(config["OUTPUT_PATH"])
        exit(0)

    shared_status = multiprocessing.Manager().Value('i', BallMovements.BALL_STOPPED)

    process1 = multiprocessing.Process(target=run_aquisation_process, args=(shared_status,))
    process2 = multiprocessing.Process(target=run_fictrac_process, args=(shared_status,))

    process1.start()
    process2.start()

    process1.join()
    process2.join()
