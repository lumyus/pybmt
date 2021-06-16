import multiprocessing
import pickle
import time

from image_acquisition.image_acquisition import ImageAcquisition
from arduino_serial.arduino_serial import ArduinoSerial
from motion_tracking.callback.movement_callback import MovementCallback
from motion_tracking.fictrac_handler.driver import FicTracDriver
from utils import read_yaml, BallMovements, write_videos


def performance_test(status):

    while True:
        print('Running performance test...')
        time.sleep(5)
        status.value = BallMovements.BALL_MOVING.value
        starttime = time.perf_counter()
        time.sleep(30)
        print(f'Time for experiment: {time.perf_counter() - starttime}')
        status.value = BallMovements.BALL_STOPPED.value


def run_motion_tracking_process(status):

    motion_tracking_config = read_yaml("config.yaml")["FICTRAC_PARAMS"]

    fictrac_config = motion_tracking_config["FICTRAC_CONFIGURATION_FILE"]
    fictrac_console_out = motion_tracking_config["FICTRAC_CONSOLE_OUT_FILE"]
    fic_trac_bin_path = motion_tracking_config["FICTRAC_BIN_PATH"]

    TESTING = read_yaml("config.yaml")["TESTING"]

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


def run_image_acquisition_process(status):

    image_acquisition_config = read_yaml("config.yaml")["IMAGE_ACQUISITION_PARAMS"]

    serial_numbers = image_acquisition_config["CAMERA_SERIAL_NUMBERS"]
    frame_size = image_acquisition_config["FRAME_SIZE"]
    output_path = image_acquisition_config["OUTPUT_PATH"]
    buffer = image_acquisition_config["BUFFERED_FRAMES"]

    cameras = ImageAcquisition(shape=frame_size, serial_numbers=serial_numbers, buffer=buffer)
    cameras.run()

    recording_time = 0
    captured_frames = []

    while True:

        ball_status = BallMovements(status.value)

        if ball_status == BallMovements.BALL_MOVING:

            captured_frames, recording_time = cameras.grab_frames(status)

        elif ball_status == BallMovements.BALL_STOPPED:

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


def run_experiment_execution_process(status):

    arduino = ArduinoSerial()
    arduino.connect()

    while True:

        ball_status = BallMovements(status.value)
        if ball_status == BallMovements.BALL_MOVING:
            arduino.switch_left_led(True)
        if ball_status == BallMovements.BALL_STOPPED:
            arduino.switch_left_led(False)


if __name__ == "__main__":
    # https://stackoverflow.com/questions/56549971/sharing-boolean-between-processes
    # https://stackoverflow.com/questions/27868395/python-multiprocessing-object-passed-by-value

    # Easiest way to connect a specific camera to fictrac_handler:
    # Pass a list of cameras that we want to connect to. The one not on the list will be connected to Fictrac
    # We need to start the Fictrac process after the cameras have been initialized

    EXPORT_VIDEOS = True

    if EXPORT_VIDEOS:
        config = read_yaml("config.yaml")["IMAGE_ACQUISITION_PARAMS"]
        write_videos(config["OUTPUT_PATH"])
        exit(0)

    shared_ball_status = multiprocessing.Manager().Value('i', BallMovements.BALL_STOPPED)

    image_acquisition_process = multiprocessing.Process(name='image_acquisition_process', target=run_image_acquisition_process, args=(shared_ball_status,))
    motion_tracking_process = multiprocessing.Process(name='motion_tracking_process', target=run_motion_tracking_process, args=(shared_ball_status,))
    experiment_execution_process = multiprocessing.Process(name='experiment_execution_process', target=run_experiment_execution_process, args=(shared_ball_status,))

    image_acquisition_process.start()
    motion_tracking_process.start()
    experiment_execution_process.start()

    image_acquisition_process.join()
    motion_tracking_process.join()
    experiment_execution_process.join()
