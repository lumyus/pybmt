import glob
import pickle
import time

import serial
from pypylon import genicam
from pypylon import pylon


class Basler:

    def find_cameras(self, serial_numbers):

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

    def attach_camera_to_worker(self, tlFactory, device):
        camera = pylon.InstantCamera(tlFactory.CreateDevice(device))

        return camera

    def attach_cameras(self, tlFactory, camera_devices, parallel=False):
        try:
            # Create an array of instant cameras for the found devices
            # and avoid exceeding a maximum number of devices.
            cam_array = pylon.InstantCameraArray(min(len(camera_devices), 5))

            for i, camera in enumerate(cam_array):
                # Create an instant camera object
                camera.Attach(tlFactory.CreateDevice(camera_devices[i]))

            print(str(len(camera_devices)) + ' cameras attached.')

        except genicam.GenericException as e:
            print("An exception occurred.")
            print(e.GetDescription())

        return cam_array

    def open_cameras(self, cam_array):
        try:
            for _, camera in enumerate(cam_array):
                camera.Open()

        except genicam.GenericException as e:
            print("An exception occurred.")
            print(e.GetDescription())

        print("Cameras opened for acquisition.")

        return cam_array

    def close_cameras(self, cam_array):
        try:
            for _, camera in enumerate(cam_array):
                camera.Close()

        except genicam.GenericException as e:
            print("An exception occurred.")
            print(e.GetDescription())

        print("Cameras opened for acquisition.")

        return cam_array

    def set_camera_params(self, cam_array, shape=(960, 480)):
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

    def grab_frames(self, cam_array, flystate, path='/home/nely/Desktop/Cedric/images/', FrameCount=1):

        imgs = []

        while cam_array.IsGrabbing():
            if not bool(flystate.value): break
            for i, camera in enumerate(cam_array):
                # Wait for an image and then retrieve it. A timeout of 5000 ms is used.
                grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                imgs[i].append(grabResult.GetArray())

                grabResult.Release()

        if path is not None and len(imgs[0]):
            time_stamp = time.strftime("%Y%m%d-%H%M%S")
            pickle.dump(imgs, open(path + 'results_' + time_stamp + '.pkl', 'wb'))
            print(f"Saving completed. Exported frames: {len(imgs[0])}")

    def imgs_to_video(self, imgs, fps, out_path):
        '''Write video from a list of images'''
        import cv2

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(out_path, fourcc, fps, imgs[0].shape[:2][::-1], 0)
        for i, img in enumerate(imgs):
            out.write(img)
        out.release()

    def write_videos(self, path):

        print('Writing videos...')
        files = glob.glob(path + '*.pkl')

        for f in files:
            imgs = pickle.load(open(f, 'rb'))
            for i, camera_images in enumerate(imgs):
                time = f.split('_')[-1][:-4]
                self.imgs_to_video(camera_images, 1, path + time + 'cam' + str(i) + '.mp4')

    def init_cameras(self, serial_numbers, shape):

        tlFactory, camera_devices = self.find_cameras(serial_numbers)
        cam_array = self.attach_cameras(tlFactory, camera_devices)

        cam_array = self.open_cameras(cam_array)
        cam_array = self.set_camera_params(cam_array, shape)

        cam_array.StartGrabbing(pylon.GrabStrategy_OneByOne)

        print("Cameras initialized..")

        return cam_array
