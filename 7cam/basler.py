import glob
import pickle
import time

import numpy as np
import serial
from pypylon import genicam
from pypylon import pylon

from ball_movements import BallMovements


def imgs_to_video(imgs, fps, out_path):
    '''Write video from a list of images'''
    import cv2

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, fps, imgs[0].shape[:2][::-1], 0)
    for i, img in enumerate(imgs):
        out.write(img)
    out.release()


def write_videos(path):

    print('Writing videos...')
    files = glob.glob(path + '*.pkl')

    for f in files:
        imgs = pickle.load(open(f, 'rb'))
        for i, camera_images in enumerate(imgs):
            time = f.split('_')[-1][:-4]
            imgs_to_video(camera_images, 1, path + time + 'cam' + str(i) + '.mp4')


def attach_cameras(tl_factory, camera_devices):
    try:
        # Create an array of instant cameras for the found devices
        # and avoid exceeding a maximum number of devices.
        cam_array = pylon.InstantCameraArray(min(len(camera_devices), len(camera_devices)))

        for i, camera in enumerate(cam_array):
            # Create an instant camera object
            camera.Attach(tl_factory.CreateDevice(camera_devices[i]))

        print(str(len(camera_devices)) + ' cameras attached.')

        return cam_array

    except genicam.GenericException as e:
        print("An exception occurred.")
        print(e.GetDescription())
        return 0


class Basler:

    def __init__(self, shape, serial_numbers, buffer):

        self.buffer = buffer
        self.shape = shape
        self.serial_numbers = serial_numbers

        tl_factory, camera_devices = self.find_cameras()
        self.cam_array = attach_cameras(tl_factory, camera_devices)

        self.open_cameras()
        self.set_camera_params()

        print("Cameras initialized..")

    def run(self):
        self.cam_array.StartGrabbing(pylon.GrabStrategy_OneByOne)

    def find_cameras(self):

        if len(self.serial_numbers) == 0:
            print('No serial numbers for the cameras found. Enter them before starting.')

        try:
            tl_factory = pylon.TlFactory.GetInstance()

            # get all attached devices
            devices = tl_factory.EnumerateDevices()

            # look for unique devices that match the serial numbers
            camera_devices = []
            for device in devices:
                sn = device.GetSerialNumber()

                for _sn in self.serial_numbers:
                    if sn == _sn:
                        camera_devices.append(device)
                        self.serial_numbers.remove(sn)
                        break

            camera_devices = tuple(camera_devices)

            # exit if no camera found
            if len(camera_devices) == 0:
                raise pylon.RuntimeException("No camera present.")

            return tl_factory, camera_devices

        except genicam.GenericException as e:
            print("An exception occurred.")
            print(e.GetDescription())
            return 0, 0

    def open_cameras(self):
        try:
            for _, camera in enumerate(self.cam_array):
                camera.Open()

        except genicam.GenericException as e:
            print("An exception occurred.")
            print(e.GetDescription())

        print("Cameras opened for acquisition.")

    def close_cameras(self):
        try:
            for _, camera in enumerate(self.cam_array):
                camera.Close()

        except genicam.GenericException as e:
            print("An exception occurred.")
            print(e.GetDescription())

        print("Cameras opened for acquisition.")

    def set_camera_params(self):
        try:
            for i, camera in enumerate(self.cam_array):
                # camera name
                camera_name = '_'.join([camera.GetDeviceInfo().GetModelName(),
                                        camera.GetDeviceInfo().GetSerialNumber()])

                # pylon.FeaturePersistence.Load('./camera_params/' + cam_name + '.pfs', camera.GetNodeMap())

                # set camera parameters
                camera.Width = int(self.shape[0])
                camera.Height = int(self.shape[1])
                camera.MaxNumBuffer = self.buffer  # count of buffers allocated for grabbing
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

    def grab_frames(self, status):

        imgs = [[]] * self.cam_array.GetSize()

        while self.cam_array.IsGrabbing():
            if status.value == BallMovements.BALL_STOPPED: break

            for i, camera in enumerate(self.cam_array):
                # Wait for an image and then retrieve it. A timeout of 5000 ms is used.
                grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                imgs[i].append(grabResult.GetArray())
                grabResult.Release()

        return imgs
