
from pybmt.callback.threshold_callback import ThresholdCallback
from pybmt.fictrac.driver import FicTracDriver
import basler


serial_numbers=['40022761'] # Enter all serial numbers except the one camera used for Fictrac (40018632, 40022761)

def run_pybmt_example():

    fictrac_config = "config.txt"
    fictrac_console_out = "output.txt"

    arduino = basler.connect_arduino(arduinoPort='/dev/ttyACM0')
    cameras = basler.init_cameras(serial_numbers=serial_numbers)

    print('Starting Fictrac..')

    # Instantiate the callback object thats methods are invoked when new tracking state is detected.
    callback = ThresholdCallback(arduino=arduino, cameras=cameras)

    # Instantiate a FicTracDriver object to handle running of FicTrac in the background and communication
    # of program state.
    tracDrv = FicTracDriver(config_file=fictrac_config, console_ouput_file=fictrac_console_out,
                            track_change_callback=callback, plot_on=False, fic_trac_bin_path='/home/nely/Desktop/Cedric/fictrac/bin/fictrac')

    # This will start FicTrac and block until complete
    tracDrv.run()

if __name__ == "__main__":
    run_pybmt_example()