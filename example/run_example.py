import multiprocessing

from pypylon import pylon

from pybmt.arduino_serial import ArduinoSerial
from pybmt.callback.threshold_callback import ThresholdCallback
from pybmt.fictrac.driver import FicTracDriver
import basler

def run_fictrac(is_fly_moving):

    fictrac_config = "config.txt"
    fictrac_console_out = "output.txt"

    print('Starting Fictrac..')

    # Instantiate the callback object thats methods are invoked when new tracking state is detected.
    callback = ThresholdCallback(is_fly_moving=is_fly_moving)

    # Instantiate a FicTracDriver object to handle running of FicTrac in the background and communication
    # of program state.
    tracDrv = FicTracDriver(config_file=fictrac_config, console_ouput_file=fictrac_console_out,
                            track_change_callback=callback, plot_on=False, fic_trac_bin_path='/home/nely/Desktop/Cedric/fictrac/bin/fictrac')

    # This will start FicTrac and block until complete
    tracDrv.run()


def run_basler_aquisition(is_fly_moving):

    arduino_protocol = ArduinoSerial()
    arduino_protocol.connect_arduino()

    basler_cameras = basler.Basler()

    cameras = basler_cameras.init_cameras(serial_numbers=['40018631'], shape=(1920,1200)) # TODO: Import these rather than specifying them in code

    # make this cancelable
    while True:
        while bool(is_fly_moving.value):
            basler_cameras.grab_frames(cameras, is_fly_moving)

if __name__ == "__main__":

    # https://stackoverflow.com/questions/56549971/sharing-boolean-between-processes
    # https://stackoverflow.com/questions/27868395/python-multiprocessing-object-passed-by-value

    shared_fly_status = multiprocessing.Manager().Value('i', 0)

    process1 = multiprocessing.Process(target=run_fictrac, args=(shared_fly_status,))
    process2 = multiprocessing.Process(target=run_basler_aquisition, args=(shared_fly_status,))

    process1.start()
    process2.start()

    process1.join()
    process2.join()
