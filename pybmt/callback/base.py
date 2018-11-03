

class PyBMTCallback:
    """
    FlyVRCallback is a base class that derived classes should use to implement control logic for closed loop experiments.
    It provides developers with method entry points for injecting custom logic for processing tracking signals and
    triggering stimuli. This class should never be instantiated directly, it provides only an abstract interface.
    """

    def setup_callback(self):
        """
        This method is called once and only once before any event processing is triggered. Place any one time setup
        functionality within this function.

        :return: None
        """
        pass

    def shutdown_callback(self):
        """
        This method is called once and only once before exiting the programe. Place any one time shutdown
        functionality within this function.

        :return: None
        """
        pass

    def process_callback(self, track_state):
        """
        This method is called each time an update is detected in the online tracking state. Code placed within this
        method should execute as quickly and deterministically as possible.

        :param tracking_update: A ctypes structure of type fictrac.SHMEMFicTracState
        :return: bool True to keep running, False to stop running.
        """
        pass
