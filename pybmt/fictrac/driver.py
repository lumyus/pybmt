import subprocess
import time
import os
from collections import deque

import zmq

from pybmt.fictrac.state import FicTracState
from pybmt.tools import which


class FicTracDriver:
    """
    This class drives the tracking of the fly via a separate software called FicTrac. It invokes this process and
    calls a control function once for each time the tracking state is updated.
    """
    def __init__(self, config_file=None, remote_endpoint_url=None, console_ouput_file="output.txt",
                 track_change_callback=None, pgr_enable=False, plot_on=True, fic_trac_bin_path=None):
        """
        Create the FicTrac driver object. This function will perform a check to see if the FicTrac program is present
        on the path. If it is not, it will throw an exception.

        :param str config_file: The path to the configuration file that should be passed to the FicTrac command.
        :param str remote_endpoint_url: If FicTrac is already running on another machine, this is the url.
        :param str console_output_file: The path to the file where console output should be stored.
        :param track_change_callback: A FlyVRCallback class which is called once everytime tracking status changes. See
        control.FlyVRCallback for example.
        :param bool pgr_enable: Is Point Grey camera support needed. This just decides which executable to call, either
        'FicTrac' or 'FicTrac-PGR'.
        :param str fic_trac_bin_path: The path the the fictrac binary to use. Default is None. If None, we will try to
        find fictrac on the path.
        :param str remote_enpoint_url
        """

        self.track_change_callback = track_change_callback
        self.plot_on = plot_on

        # The message loop has to stay above this average number of frames per second. If it falls below we are
        # not grabbing messages fast enough and will fall behind FicTrac in state. I don't like this solution that
        # much, with shared memory this was easier to detect.
        self.average_fps_threshold = 400

        # This is the number of times to try an reconnect the the fictrac client over the socket before failing out.
        # Each time will cause a sleep of 1 second.
        self.max_num_connect_retries = 10

        # If fictrac is already running, for example, on another machine, then we don't need to worry about running it.
        if remote_endpoint_url is not None:
            self.remote_endpoint_url = "tcp://" + remote_endpoint_url
            self.start_fictrac = False
        else:
            self.start_fictrac = True
            self.remote_endpoint_url = "tcp://localhost:5556"

            self.config_file = config_file

            # Get the directory that the config file is in, this will be the current working directory
            # of FicTrac.
            self.config_dir = os.path.dirname(self.config_file)
            if self.config_dir == "":
                self.config_dir = None

            # Get base config file name
            self.config_file_base = os.path.basename(self.config_file)

            self.console_output_file = console_ouput_file
            self.track_change_callback = track_change_callback
            self.pgr_enable = pgr_enable
            self.plot_on = plot_on

            # If the user didn't specify the path to fictrac, look for it on the path.
            if fic_trac_bin_path is None:
                self.fictrac_bin = 'fictrac'
                if self.pgr_enable:
                    self.fictrac_bin = 'fictrac-pgr'

                # If this is Windows, we need to add the .exe extension.
                if os.name == 'nt':
                    self.fictrac_bin = self.fictrac_bin + ".exe"

                # Lets make sure FicTrac exists on the path
                self.fictrac_bin_fullpath = which(self.fictrac_bin)

                if self.fictrac_bin_fullpath is None:
                    raise RuntimeError("Could not find " + self.fictrac_bin + " on the PATH!")

            else:
                self.fictrac_bin_fullpath = fic_trac_bin_path

                # TODO: Make sure we are using the correct version of fictrac.

        self.fictrac_process = None

    def run(self):
        """
        Start the the FicTrac process and block till it closes. This function will poll a shared memory region for
        changes in tracking data and invoke a control function when they occur. FicTrac is assumed to exist on the
        system path.

        :return:
        """

        # Setup anything the callback needs.
        self.track_change_callback.setup_callback()

        try:
            # Start FicTrac if we need to
            if self.start_fictrac:
                with open(self.console_output_file, "wb") as out:
                    self.fictrac_process = subprocess.Popen([self.fictrac_bin_fullpath,
                                                         self.config_file_base],
                                                         stdout=out, stderr=subprocess.STDOUT,
                                                         cwd=self.config_dir)

                    # Lets sleep for a couple seconds, give fictrac a chance to start up.
                    # FIXME: Eww, this is hacky.
                    time.sleep(2)

                    self._process_messages()
            else:
                self._process_messages()

            # Call poll one last time to get the return value
            self.fictrac_process.poll()

            # Get the fic trac process return code
            if self.fictrac_process is not None and self.fictrac_process.returncode is not None and self.fictrac_process.returncode != 0:
                raise RuntimeError("FicTrac failed because of an application error. " +
                                   "Consult the FicTrac console output file ({}). ".format(self.console_output_file))
            if self.frame_cnt == 0:
                raise RuntimeError("Zero frames processed. FicTrac failed because of an application error. " +
                             "Consult the FicTrac console output file ({}). ".format(self.console_output_file))


        except Exception as ex:
            if self.fictrac_process is not None:
                self.fictrac_process.terminate()

            raise Exception("PyBMT Error!") from ex
        finally:
            self.track_change_callback.shutdown_callback()
            self._cleanup()

    def _process_messages(self):

        #  Setup ZeroMQ context and socket to talk to server
        context = zmq.Context()
        socket = context.socket(zmq.SUB)

        # Set a timeout on this socket so we don't block forever
        socket.RCVTIMEO = 1000  # in milliseconds

        # This is the receiver high water mark, zero mq will start to drop incoming messages after it
        # has queued this many. This will let us detect if we are not picking up messages quick enough because of a
        # slow callback process. This isn't perfect though since OS buffers messages as well.
        socket.setsockopt(zmq.RCVHWM, 1)

        # Bind and subscribe
        socket.connect(self.remote_endpoint_url)
        socket.setsockopt(zmq.SUBSCRIBE, b"")

        #           if self.plot_on:
        #               self.plot_task = ConcurrentTask(task=plot_task_fictrac, comms="pipe",
        #                                      taskinitargs=[state])
        #               self.plot_task.start()

        # Lets track average frame rate we are receiving the messages
        # Our buffer of past speeds
        time_history = deque(maxlen=10)
        avg_fps = 0
        self.frame_cnt = 0

        # Lets keep track of the last fictrac state we received
        last_fstate: FicTracState = None
        fstate: FicTracState = None
        isOK = True
        while isOK:

            # If we are running FicTrac, make sure it is running still
            #if frame_cnt > 0 and self.fictrac_process is not None and self.fictrac_process.poll() is None:
            #    print("FicTrac process gone!")
            #    break

            # Receive state update from FicTrac process
            num_connect_trys = 0
            while True:
                try:
                    data = socket.recv_string()

                    # If we got data successfully, We can break out.
                    break
                except zmq.error.Again:

                    # If we get socket error, probably means fictrac is gone.  If we started it, just break.
                    # If we didn't start it, signal the connection error.
                    if self.start_fictrac:

                        if self.frame_cnt == 0:
                            time.sleep(1)
                            num_connect_trys = num_connect_trys + 1

                            if num_connect_trys > self.max_num_connect_retries:
                                isOK = False
                                break
                            else:
                                pass
                        else:
                            isOK = False
                            break
                    else:
                        raise Exception("Socket timed out. Couldn't reach fictrac!")

            if not isOK:
                break

            # Message received start the timer, want to keep track of how long it takes to process the message.
            t0 = time.perf_counter()

            # If FicTrac sent and END signal, its time to clean up
            if data == "END":
                break

            # Lets keep track of the last fictrac state we received
            last_fstate = fstate

            # Parse the data packet into our state structure. Get our new state.
            fstate = FicTracState.zmq_string_msg_to_state(data)

            if last_fstate is not None and fstate.frame_cnt - last_fstate.frame_cnt != 1:
                self.fictrac_process.terminate()
                raise Exception(("FicTrac frame counter jumped by more than 1! oldFrame = " +
                                 str(last_fstate.frame_cnt) + ", newFrame = " + str(fstate.frame_cnt)))

            # Call the main callback function with the current state
            isOK = self.track_change_callback.process_callback(fstate)

            # Stop the clock
            t1 = time.perf_counter()

            # Add the speed to our history
            time_history.append(t1 - t0)

            # Get the running average fps
            avg_fps = 1 / (sum(time_history) / len(time_history))

            if self.average_fps_threshold != 0 and avg_fps < self.average_fps_threshold and self.frame_cnt > 300:
                self.fictrac_process.terminate()
                raise Exception("Average FPS fell below avg_fps_threshold({}). Processing callback is " +
                                "probably operating too slow.")

            self.frame_cnt = self.frame_cnt + 1

        self.fictrac_process.terminate()

    def _cleanup(self):
        """
        This is method is called whenever PyBMT run is shutting down things.

        :return:
        """
        pass
