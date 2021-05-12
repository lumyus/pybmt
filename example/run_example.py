import multiprocessing

from pypylon import pylon

from pybmt.callback.threshold_callback import ThresholdCallback
from pybmt.fictrac.driver import FicTracDriver
import basler


serial_numbers=['40018632'] # Enter all serial numbers except the one camera used for Fictrac (40018632, 40022761)
FrameRate = 100  # (fps)
ExposureTime = 500  # (us)
fly_status = multiprocessing.Value('i', 0)

def run_fictrac(is_fly_moving):

    fictrac_config = "config.txt"
    fictrac_console_out = "output.txt"


    print('Starting Fictrac..')

    # Instantiate the callback object thats methods are invoked when new tracking state is detected.
    callback = ThresholdCallback(is_fly_moving)

    # Instantiate a FicTracDriver object to handle running of FicTrac in the background and communication
    # of program state.
    tracDrv = FicTracDriver(config_file=fictrac_config, console_ouput_file=fictrac_console_out,
                            track_change_callback=callback, plot_on=False, fic_trac_bin_path='/home/nely/Desktop/Cedric/fictrac/bin/fictrac')

    # This will start FicTrac and block until complete
    tracDrv.run()


def run_basler_aquisition(is_fly_moving):
    arduino = basler.connect_arduino(arduinoPort='/dev/ttyACM0')
    basler.start_arduino(arduino=arduino)
    cameras = basler.init_cameras(serial_numbers=serial_numbers)
    for i, camera in enumerate(cameras):
        camera.StartGrabbing(pylon.GrabStrategy_OneByOne)
    while bool(is_fly_moving.val):
        basler.grab_frames(cameras)

def testrunner():
    while True:
        print('Running.')

if __name__ == "__main__":

    process1 = multiprocessing.Process(target=run_fictrac, args=(fly_status,))
    process2 = multiprocessing.Process(target=run_basler_aquisition, args=(fly_status,))

    process1.start()
    process2.start()

    process1.join()
    process2.join()

