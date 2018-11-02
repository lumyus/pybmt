
from pybmt.callback.threshold_callback import ThresholdCallback
from pybmt.fictrac.driver import FicTracDriver

def run_pybmt_example():

    fictrac_config = "config.txt"
    fictrac_console_out = "output.txt"

    # Instantiate the callback object thats methods are invoked when new tracking state is detected.
    callback = ThresholdCallback()

    # Instantiate a FicTracDriver object to handle running of FicTrac in the background and communication
    # of program state.
    tracDrv = FicTracDriver(config_file=fictrac_config, console_ouput_file=fictrac_console_out,
                            #remote_endpoint_url="localhost:5556",
                            track_change_callback=callback, plot_on=False)

    # This will start FicTrac and the
    tracDrv.run()

if __name__ == "__main__":
    run_pybmt_example()