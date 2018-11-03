import numpy as np
import ctypes

# The number of FicTrac fields in the output file
NUM_FICTRAC_FIELDS = 23

class FicTracState(ctypes.Structure):
    """
    This class represents the FicTrac tracking state. These are the exact same values written to the output log file
    when FicTrac is run. Please consult the FicTrac user documentation for their meaning. I have made it a ctypes
    structure because it will be easier to fill it later if we switch to binary messages or go back to shared memory.
    """
    _fields_ = [
        ('frame_cnt', ctypes.c_int),
        ('del_rot_cam_vec', ctypes.c_double * 3),
        ('del_rot_error', ctypes.c_double),
        ('del_rot_lab_vec', ctypes.c_double * 3),
        ('abs_ori_cam_vec', ctypes.c_double * 3),
        ('abs_ori_lab_vec', ctypes.c_double * 3),
        ('posx', ctypes.c_double),
        ('posy', ctypes.c_double),
        ('heading', ctypes.c_double),
        ('direction', ctypes.c_double),
        ('speed', ctypes.c_double),
        ('intx', ctypes.c_double),
        ('inty', ctypes.c_double),
        ('timestamp', ctypes.c_double),
        ('seq_num', ctypes.c_int),
    ]

    @classmethod
    def zmq_string_msg_to_state(cls, data):
        """
        A simpe functiont that parses a zero MQ string message and converts it to our
        fic trac state data structure.

        :param data: The raw string message received from the zero MQ socket.
        :return: The FicTracState structure with values corresponding to data.
        """

        # Create a FicTrac state object\structure
        fstate = cls()

        # Parse the string
        values = [x.strip() for x in data.split(',')]

        if len(values) != NUM_FICTRAC_FIELDS:
            raise ValueError("Message from FicTrac did not have appropriate number of fields.")

        # Convert strings to appropriate types and assign fields
        i = 0
        for field_name, field_type in fstate._fields_:
            field = getattr(fstate, field_name)
            if (isinstance(field, float) ):
                setattr(fstate, field_name, float(values[i]))
                i = i + 1
            elif (isinstance(field, int)):
                setattr(fstate, field_name, int(values[i]))
                i = i + 1
            elif len(field) == 3:
                field[0] = float(values[i])
                field[1] = float(values[i+1])
                field[2] = float(values[i+2])
                i = i + 3

        return fstate

    def to_np_array(self):
        """
        Create a vector from the structure of FicTrac state fields.

        :return: The fic trace state as a simply 1D numpy.array
        """
        return np.array([self.frame_cnt,
                         self.del_rot_cam_vec[0],
                         self.del_rot_cam_vec[1],
                         self.del_rot_cam_vec[2],
                         self.del_rot_error,
                         self.del_rot_lab_vec[0],
                         self.del_rot_lab_vec[1],
                         self.del_rot_lab_vec[2],
                         self.abs_ori_cam_vec[0],
                         self.abs_ori_cam_vec[1],
                         self.abs_ori_cam_vec[2],
                         self.abs_ori_lab_vec[0],
                         self.abs_ori_lab_vec[1],
                         self.abs_ori_lab_vec[2],
                         self.posx,
                         self.posy,
                         self.heading,
                         self.direction,
                         self.speed,
                         self.intx,
                         self.inty,
                         self.timestamp,
                         self.seq_num
                         ])

    def __repr__(self):
        return "FicTracState({})".format(self.__str__())

    def __str__(self):
        """
        Convert the fictrac state to a string.

        :return: The string representing the state.
        """
        state_string = ""
        for field_name, field_type in self._fields_:
            field = getattr(self, field_name)
            if(isinstance(field, float) | isinstance(field, int)):
                state_string = state_string + str(field) + "\t"
            else:
                state_string = state_string + str(field[0]) + "\t" + str(field[1]) + "\t" + str(field[2]) + "\t"

        return(state_string)