import glob
import pickle
import time

import serial
from pypylon import genicam
from pypylon import pylon

FrameRate = 100  # (fps)
ExposureTime = 500  # (us)
FrameCount = 100  # Number of images to be grabbed
maxCamerasToUse = 2  # Limits the amount of cameras used for grabbing
maxTime = 5  # acquisition time [min]
shape = (1920, 1232)
path = '/home/nely/Desktop/Cedric/images/'


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


def set_camera_params(cam_array, shape=(960, 480), FrameCount=1):
    try:
        for i, camera in enumerate(cam_array):
            # camera name
            camera_name = '_'.join([camera.GetDeviceInfo().GetModelName(),
                                    camera.GetDeviceInfo().GetSerialNumber()])

            # pylon.FeaturePersistence.Load('./camera_params/' + cam_name + '.pfs', camera.GetNodeMap())

            # set camera parameters
            camera.Width = shape[0]
            camera.Height = shape[1]
            camera.MaxNumBuffer = 200  # count of buffers allocated for grabbing
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


def grab_frames(cam_array, flystate, path='/home/nely/Desktop/Cedric/images/', FrameCount=1):

    imgs_cam0 = []
    imgs_cam1 = []

    imgs = {}

    # Start the stopwatch / counter
    start = time.clock()

    while cam_array.IsGrabbing():
        if not bool(flystate.value): break
        for i, camera in enumerate(cam_array):
            # Wait for an image and then retrieve it. A timeout of 5000 ms is used.
            grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            print("GrabSucceeded: ", grabResult.GrabSucceeded())
            if i == 0:
                imgs_cam0.append(grabResult.GetArray())
            if i == 1:
                imgs_cam1.append(grabResult.GetArray())
            grabResult.Release()

    imgs['cam' + str(0)] = imgs_cam0
    imgs['cam' + str(1)] = imgs_cam1

    if path is not None:
        if len(imgs['cam0']):
            # Stop the stopwatch / counter
            end = time.clock()

            print("Elapsed time:", end - start)
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
        imgs_to_video(imgs, 1, path + time + 'cam0.mp4')
        imgs = pickle.load(open(f, 'rb'))
        imgs = imgs['cam1']
        time = f.split('_')[-1][:-4]
        imgs_to_video(imgs, 1, path + time + 'cam1.mp4')


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

def all_cameras_stop(cam_array):
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
    cam_array = set_camera_params(cam_array, shape, FrameCount)

    print("Cameras initialized..")

    return cam_array


# =============================================================================
# Main script
# =============================================================================
def main():

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
