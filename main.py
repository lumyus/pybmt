import multiprocessing
import pickle
import time

import yaml

from motion_tracking.utils.ball_movements import BallMovements
from arduino_serial.arduino_serial import ArduinoSerial
from motion_tracking.callback.movement_callback import MovementCallback
from motion_tracking.fictrac_handler.driver import FicTracDriver
from basler import Basler, write_videos


def read_yaml(file_path):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def performance_test(status):
    while True:
        print('Running performance test!')
        time.sleep(5)
        status.value = BallMovements.BALL_MOVING.value
        starttime = time.perf_counter()
        time.sleep(30)
        print(f'Time for experiment: {time.perf_counter() - starttime}')
        status.value = BallMovements.BALL_STOPPED.value


def run_fictrac_process(status):

    config = read_yaml("config.yml")["FICTRAC_PARAMS"]

    fictrac_config = config["FICTRAC_CONFIGURATION_FILE"]
    fictrac_console_out = config["FICTRAC_CONSOLE_OUT_FILE"]
    fic_trac_bin_path = config["FICTRAC_BIN_PATH"]

    TESTING = read_yaml("config.yml")["TESTING"]

    if TESTING:
        performance_test(status)
    else:
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


def run_acquisition_process(status):

    config = read_yaml("config.yml")["BASLER_PARAMS"]

    #TODO serial number is randomly selecting a fictrac_handler cam at the moment
    serial_numbers = config["SERIAL_NUMBERS"]
    frame_size = config["FRAME_SIZE"]
    output_path = config["OUTPUT_PATH"]
    buffer = config["BUFFER"]

    basler_cameras = Basler(shape=frame_size, serial_numbers=serial_numbers, buffer=buffer)

    captured_frames = []
    recording_time = 0

    while True:

        ball_status = BallMovements(status.value)

        if ball_status == BallMovements.BALL_MOVING:
            # grab the available frames for each camera
            captured_frames, recording_time = basler_cameras.grab_frames(status)

        elif ball_status == BallMovements.BALL_STOPPED:
            # Fictrac is not registering movement anymore. Save the captured frames.
            if len(captured_frames):

                if len(set(map(len, captured_frames))) == 0:
                    print("ATTENTION. The cameras did not record the same amount of frames!")
                    print("Stopping the program now!")
                    break

                frames_per_camera = len(captured_frames[0])
                average_fps_obtained = frames_per_camera / recording_time

                time_stamp = time.strftime("%Y%m%d-%H%M%S")
                print(f'Saving the data..')
                saving_time = time.perf_counter()
                pickle.dump(captured_frames, open(output_path + 'results_' + time_stamp + '.pkl', 'wb'))
                print(
                    f"Saving completed within {time.perf_counter()-saving_time} seconds. Exported frames: {frames_per_camera}. Averaged FPS during recording: {average_fps_obtained}")
                captured_frames.clear()


def run_experimentation_process(status):

    config = read_yaml("config.yml")["ARDUINO_PARAMS"]
    baud_rate = config["BAUD_RATE"]
    fps = config["FPS"]
    exposure_time = config["EXPOSURE_TIME"]

    arduino_protocol = ArduinoSerial(baud_rate, fps, exposure_time)

    if not arduino_protocol.connect_arduino():
        print("Connection with Arduino failed!")
        raise Exception

    while True:

        ball_status = BallMovements(status.value)
        if ball_status == BallMovements.BALL_MOVING:
            arduino_protocol.switch_left_led(True)
        if ball_status == BallMovements.BALL_STOPPED:
            arduino_protocol.switch_left_led(False)

        ''' 
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
            arduino_protocol.switch_right_led(False) '''


if __name__ == "__main__":
    # https://stackoverflow.com/questions/56549971/sharing-boolean-between-processes
    # https://stackoverflow.com/questions/27868395/python-multiprocessing-object-passed-by-value

    # Easiest way to connect a specific camera to fictrac_handler:
    # Pass a list of cameras that we want to connect to. The one not on the list will be connected to Fictrac
    # We need to start the Fictrac process after the cameras have been initialized

    EXPORT_VIDEOS = False

    if EXPORT_VIDEOS:
        config = read_yaml("config.yml")["BASLER_PARAMS"]
        write_videos(config["OUTPUT_PATH"])
        exit(0)

    shared_status = multiprocessing.Manager().Value('i', BallMovements.BALL_STOPPED)

    process1 = multiprocessing.Process(target=run_acquisition_process, args=(shared_status,))
    process2 = multiprocessing.Process(target=run_fictrac_process, args=(shared_status,))
    process3 = multiprocessing.Process(target=run_experimentation_process, args=(shared_status,))

    process1.start()
    process2.start()
    process3.start()

    process1.join()
    process2.join()
    process3.join()
