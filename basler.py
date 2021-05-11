import glob
import pickle
import time

import serial
from pypylon import genicam
from pypylon import pylon

FrameRate = 100  # (fps)
ExposureTime = 500  # (us)
MaxNumBuffer = 100
FrameCount = 100  # Number of images to be grabbed
maxCamerasToUse = 2  # Limits the amount of cameras used for grabbing
maxTime = 5  # acquisition time [min]
shape = (1920, 1232)
arduinoPort = '/dev/ttyACM0'
serial_numbers = ['40022761']
path = '/home/nely/Desktop/Cedric/'
is_fly_moving = False

def connect_arduino(arduinoPort):
    try:
        arduino = serial.Serial(arduinoPort, 9600, timeout=1)
        print('Arduino connected.')
        time.sleep(1)
        return arduino

    except:
        print("Arduino not found. Check serial port number.")
        return 0


def trigger_arduino(arduino, ExposureTime, FrameRate=1, FrameCount=1):
    arduino.write(('trig_' + str(1 / FrameRate * 1000000) + '_' + str(FrameCount) + '_' + str(ExposureTime)).encode())
    time.sleep(0.1)
    response = arduino.readline()
    response = response.decode().rstrip().lstrip().split('_')
    assert (float(response[0]) == 1 / FrameRate * 1000000) & (float(response[1]) == FrameCount) & (
            float(response[2]) == ExposureTime), 'data not sent to Arduino.'

    print("Arduino triggered at " + str(FrameRate) + " fps!")

def start_arduino(arduino):
    arduino.write(('trig_' + str(1 / FrameRate * 1000000) + '_' + str(1) + '_' + str(ExposureTime)).encode())
    time.sleep(0.1)
    response = arduino.readline()
    response = response.decode().rstrip().lstrip().split('_')
    assert (float(response[0]) == 1 / FrameRate * 1000000) & (float(response[1]) == 1) & (
            float(response[2]) == ExposureTime), 'data not sent to Arduino.'

    print("Arduino started at " + str(FrameRate) + " fps!")

def stop_arduino(arduino):
    arduino.write(('trig_' + str(1 / FrameRate * 1000000) + '_' + str(0) + '_' + str(ExposureTime)).encode())
    time.sleep(0.1)
    response = arduino.readline()
    response = response.decode().rstrip().lstrip().split('_')
    assert (float(response[0]) == 1 / FrameRate * 1000000) & (float(response[1]) == 0) & (
            float(response[2]) == ExposureTime), 'data not sent to Arduino.'

    print("Arduino stopped")


def find_cameras(serial_numbers):

    if len(serial_numbers) == 0: print('No serial numbers found. Enter them before starting.')

    try:
        tlFactory = pylon.TlFactory.GetInstance()

        # get all attached devices
        devices = tlFactory.EnumerateDevices()

        # look for unique devices that match the serial numbers
        camera_devices = []
        for device in devices:
            sn = device.GetSerialNumber()

            for _sn in serial_numbers:
                if sn == _sn:
                    camera_devices.append(device)
                    serial_numbers.remove(sn)
                    break

        camera_devices = tuple(camera_devices)

        # exit if no camera found
        if len(camera_devices) == 0:
            raise pylon.RuntimeException("No camera present.")

    except genicam.GenericException as e:
        print("An exception occurred.")
        print(e.GetDescription())

    return tlFactory, camera_devices


def attach_camera_to_worker(tlFactory, device):
    camera = pylon.InstantCamera(tlFactory.CreateDevice(device))

    return camera


def attach_cameras(tlFactory, camera_devices, parallel=False):
    try:
        # Create an array of instant cameras for the found devices 
        # and avoid exceeding a maximum number of devices.
        cam_array = pylon.InstantCameraArray(min(len(camera_devices), maxCamerasToUse))

        for i, camera in enumerate(cam_array):
            # Create an instant camera object
            camera.Attach(tlFactory.CreateDevice(camera_devices[i]))

        print(str(len(camera_devices)) + ' cameras attached.')

    except genicam.GenericException as e:
        print("An exception occurred.")
        print(e.GetDescription())

    return cam_array


def open_cameras(cam_array):
    try:
        for _, camera in enumerate(cam_array):
            camera.Open()

    except genicam.GenericException as e:
        print("An exception occurred.")
        print(e.GetDescription())

    print("Cameras opened for acquisition.")

    return cam_array


def close_cameras(cam_array):
    try:
        for _, camera in enumerate(cam_array):
            camera.Close()

    except genicam.GenericException as e:
        print("An exception occurred.")
        print(e.GetDescription())

    print("Cameras opened for acquisition.")

    return cam_array


def set_camera_params(cam_array, shape=(960, 480), MaxNumBuffer=100, FrameCount=1):
    try:
        for i, camera in enumerate(cam_array):
            # camera name
            camera_name = '_'.join([camera.GetDeviceInfo().GetModelName(),
                                    camera.GetDeviceInfo().GetSerialNumber()])

            # pylon.FeaturePersistence.Load('./camera_params/' + cam_name + '.pfs', camera.GetNodeMap())

            # set camera parameters
            camera.Width = shape[0]
            camera.Height = shape[1]
            camera.MaxNumBuffer = MaxNumBuffer  # count of buffers allocated for grabbing
            camera.AcquisitionMode.SetValue('Continuous')
            camera.TriggerSelector.SetValue('FrameStart')
            camera.TriggerMode.SetValue('On')  # hardware trigger
            camera.TriggerSource.SetValue('Line1')
            camera.TriggerActivation.SetValue('RisingEdge')
            camera.ExposureAuto.SetValue('Off')
            camera.ExposureMode.SetValue("TriggerWidth")


            # Print the model name of the camera.
            print("Setup of camera ", camera_name, " complete.")

    except genicam.GenericException as e:
        print("An exception occurred.")
        print(e.GetDescription())

    return cam_array


def read_cam(camera, timeout=5000, FrameCount=1):
    imgs_cam = []
    try:
        grabResult = camera.RetrieveResult(timeout, pylon.TimeoutHandling_ThrowException)
        if grabResult.GrabSucceeded():
            print('Grabbing frames...')
            # Timestamps timestamp = grabResult.TimeStamp
            imgs_cam.append(grabResult.GetArray())
            grabResult.Release()

    except genicam.GenericException as e:
        print("Some frames have been dropped.")
        print(e.GetDescription())

    return imgs_cam


def grab_frames(cam_array, path=None, FrameCount=1):
    imgs = {}
    for i, camera in enumerate(cam_array):
        imgs['cam' + str(i)] = read_cam(camera, FrameCount=FrameCount)

        # number of frames to grab
        # camera.StartGrabbingMax(100)
        # camera.StartGrabbing(pylon.GrabStrategy_OneByOne)

    # jobs = []
    # for i, camera in enumerate(cam_array):
    #     process = multiprocessing.Process(target=read_cam, 
    #                                       args=(camera,))
    #     jobs.append(process)

    # # Start the processes     
    # for j in jobs:
    #     j.start()

    # # Ensure all of the processes have finished
    # for j in jobs:
    #     j.join()

    # with multiprocessing.Pool(2) as p:  # One for each image
    #     p.map(read_cam, enumerate(cam_array))

    if path is not None:
        save_frames(imgs, path)


def save_frames(imgs, fname=''):
    print("Saving")

    timestr = time.strftime("%Y%m%d-%H%M%S")
    pickle.dump(imgs, open(fname + 'results_' + timestr + '.pkl', 'wb'))


def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(timer, end="\r")
        time.sleep(1)
        t -= 1


def write_videos(path):
    print('Writing videos...')
    files = glob.glob(path + '*.pkl')

    for f in files:
        imgs = pickle.load(open(f, 'rb'))
        imgs = imgs['cam0']
        time = f.split('_')[-1][:-4]
        imgs_to_video(imgs, 25, path + time + '.mp4')


def imgs_to_video(imgs, fps, out_path):
    '''Write video from a list of images'''
    import cv2

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, fps, imgs[0].shape[:2][::-1], 0)
    for i, img in enumerate(imgs):
        out.write(img)
    out.release()


# =============================================================================
# Capture script
# =============================================================================
def all_cameras_record(cam_array):
    for i, camera in enumerate(cam_array):
        camera.StartGrabbing()
    grab_frames(cam_array, path, FrameCount=FrameCount)

def all_cameras_stop(arduino, cam_array):
    stop_arduino(arduino)
    print("Arduino stopped")
    for i, camera in enumerate(cam_array):
        camera.StopGrabbing()
    print("Cameras stopped")

# =============================================================================
# Init script
# =============================================================================
def init_cameras(serial_numbers):
    tlFactory, camera_devices = find_cameras(serial_numbers)
    cam_array = attach_cameras(tlFactory, camera_devices)

    cam_array = open_cameras(cam_array)
    cam_array = set_camera_params(cam_array, shape, MaxNumBuffer, FrameCount)

    print("Cameras initialized..")

    return cam_array


# =============================================================================
# Main script
# =============================================================================
def main():
    arduino = connect_arduino(arduinoPort)
    tlFactory, camera_devices = find_cameras(serial_numbers)
    cam_array = attach_cameras(tlFactory, camera_devices)

    usr_input = None
    while usr_input != 'exit':

        usr_input = input('Choose trigger mode (single/burst/motion/videos/exit)! ')

        if usr_input == 'burst':
            cam_array = open_cameras(cam_array)
            cam_array = set_camera_params(cam_array, shape, MaxNumBuffer, FrameCount)
            trigger_arduino(arduino, ExposureTime, FrameRate, FrameCount)
            now = time.time()
            grab_frames(cam_array, path, FrameCount=FrameCount)
            then = time.time()
            execution_time = then - now

            print("Execution time {} ms".format(execution_time * 1000))

        elif usr_input == 'videos':
            write_videos(path)


if __name__ == "__main__":
    main()

    # Select the acquisition start trigger 
    # camera.TriggerSelector.SetValue(TriggerSelector_AcquisitionStart)]

    # Check the acquisition start trigger acquisition status
    # Set the acquisition status selector
    # camera.AcquisitionStatusSelector.SetValue(AcquisitionStatusSelector_AcquisitionT riggerWait)

    # Read the acquisition status
    # IsWaitingForAcquisitionTrigger = Camera.AcquisitionStatus.GetValue()

    # Check the frame start trigger acquisition status
    # Set the acquisition status selector
    # camera.AcquisitionStatusSelector.SetValue(AcquisitionStatusSelector_FrameTrigger Wait)

    # Read the acquisition status
    # IsWaitingForFrameTrigger = Camera.AcquisitionStatus.GetValue()

    # readout time 
    # ReadoutTime = camera.ReadoutTimeAbs.GetValue()    

    # Set the acquisition frame count 
    # camera.AcquisitionFrameCount.SetValue(5)
