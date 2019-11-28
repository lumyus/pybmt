
from pybmt.callback.base import PyBMTCallback
from pybmt.fictrac.driver import FicTracDriver, FicTracState

class ShutdownCallback(PyBMTCallback):
    def __init__(self, frame_cnt_limt: int = 200):
        # Call the base class constructor
        super(ShutdownCallback, self).__init__()

        self.frame_cnt_limit = frame_cnt_limt

    def process_callback(self, track_state: FicTracState):
        if track_state.frame_cnt < self.frame_cnt_limit:
            return True
        else:
            return False


def run_pybmt_example():

    fictrac_config = "config.txt"
    fictrac_console_out = "output.txt"

    # Instantiate the callback object thats methods are invoked when new tracking state is detected.
    callback = ShutdownCallback(frame_cnt_limt=300)

    # Instantiate a FicTracDriver object to handle running of FicTrac in the background and communication
    # of program state.
    tracDrv = FicTracDriver(config_file=fictrac_config, console_ouput_file=fictrac_console_out,
                            track_change_callback=callback, plot_on=False)

    # This will start FicTrac and block until complete
    tracDrv.run()

if __name__ == "__main__":
    run_pybmt_example()