import logging
import os
import numpy as np
from pypylon import pylon
import asyncio

MAX_CAMERAS = 2
COLLECT_PATH = '/data'

formatter = logging.Formatter(
    '%(asctime)s:%(levelname)s:%(process)d:%(thread)d:%(module)s:%(funcName)s:%(lineno)s:%(message)s')
logger = logging.getLogger(__name__)


async def callback(img, camera_model_name, img_id, img_timestamp):
    '''
        callback gets called from imaging event trigger.
        after image grab is finished this callback is called with image array.
        store the image as file.
    '''
    cam_folder = config.camera["nir" if "nir" in camera_model_name.lower()[-3:] else "rgb"]
    img_name = f'{img_id}_{img_timestamp}'
    img_filepath = os.path.join(COLLECT_PATH, cam_folder, img_name)
    with open(img_filepath, 'wb') as f:
        np.save(f, img)


class ConfigurationEventListener(pylon.ConfigurationEventHandler):
    """
        Contains a Configuration Event Handler that prints a message for each event method call.
    """

    def OnAttach(self, camera):
        logger.info(f"OnAttach event")

    def OnAttached(self, camera):
        logger.info(f"OnAttached event for device {camera.GetDeviceInfo().GetModelName()}")

    def OnOpen(self, camera):
        logger.info(f"OnOpen event for device {camera.GetDeviceInfo().GetModelName()}")

    def OnOpened(self, camera):
        logger.info(f"OnOpened event for device {camera.GetDeviceInfo().GetModelName()}")

    def OnGrabStart(self, camera):
        logger.info(f"OnGrabStart event for device {camera.GetDeviceInfo().GetModelName()}")

    def OnGrabStarted(self, camera):
        logger.info(f"OnGrabStarted event for device {camera.GetDeviceInfo().GetModelName()}")

    def OnGrabStop(self, camera):
        logger.info(f"OnGrabStop event for device {camera.GetDeviceInfo().GetModelName()}")

    def OnGrabStopped(self, camera):
        logger.info(f"OnGrabStopped event for device {camera.GetDeviceInfo().GetModelName()}")

    def OnClose(self, camera):
        logger.info(f"OnClose event for device {camera.GetDeviceInfo().GetModelName()}")

    def OnClosed(self, camera):
        logger.info(f"OnClosed event for device {camera.GetDeviceInfo().GetModelName()}")

    def OnDestroy(self, camera):
        logger.info(f"OnDestroy event for device {camera.GetDeviceInfo().GetModelName()}")

    def OnDestroyed(self, camera):
        logger.info(f"OnDestroyed event")

    def OnDetach(self, camera):
        logger.info(f"OnDetach event for device {camera.GetDeviceInfo().GetModelName()}")

    def OnDetached(self, camera):
        logger.info(f"OnDetached event for device {camera.GetDevice().GetModelName()}")

    def OnGrabError(self, camera, errorMessage):
        logger.info(f"OnGrabError event for device {camera.GetDeviceInfo().GetModelName()}")
        logger.info(f"Error Message: {errorMessage}")

    def OnCameraDeviceRemoved(self, camera):
        logger.info(
            f"OnCameraDeviceRemoved event for device {camera.GetDeviceInfo().GetModelName()}")


class ImageEventListener(pylon.ImageEventHandler):
    """
        Contains an Image Event Handler that prints a message for each event method call. also supports callback to pass in captured image.
    """

    def __init__(self, callback):
        super(ImageEventListener, self).__init__()
        self.callback = callback

    def OnImagesSkipped(self, camera, countOfSkippedImages):
        logger.info("OnImagesSkipped event for device {}".format(
            camera.GetDeviceInfo().GetModelName()))
        logger.info("{} images have been skipped.".format(countOfSkippedImages))

    def OnImageGrabbed(self, camera, grabResult):
        logger.info("OnImageGrabbed event for device {}".format(
            camera.GetDeviceInfo().GetModelName()))

        if grabResult.GrabSucceeded():
            logger.info("SizeX: {}".format(grabResult.GetWidth()))
            logger.info("SizeY: {}".format(grabResult.GetHeight()))
            img = grabResult.GetArray()
            print(grabResult.GetID(), grabResult.GetTimeStamp(), grabResult.GetTimeStamp())
            try:
                if self.callback is not None:
                    # check if we are still allowed to fetch images
                    # call fictrac code to run
                    return run_coroutine(self.callback, img=img,
                                         camera_model_name=camera.GetDeviceInfo().GetModelName(),
                                         img_id=grabResult.GetID(), img_timestamp=grabResult.GetTimeStamp())
            except Exception as e:
                logger.error(e)
        else:
            logger.info("Error: {}".format(grabResult.GetErrorCode(),
                                           grabResult.GetErrorDescription()))


class Camera:

    def __init__(self, register_event_listener=False):
        tlFactory = pylon.TlFactory.GetInstance()
        # Get all attached devices and raise an error if no devices found
        devices = tlFactory.EnumerateDevices()
        if not devices:
            raise pylon.RUNTIME_EXCEPTION("No camera present.")

        # Create an array of instant cameras for the found devices and avoid
        # exceeding a maximum number of devices.
        self.cameras = pylon.InstantCameraArray(min(len(devices), MAX_CAMERAS))

        # Create and attach all Pylon Devices.
        for i, cam in enumerate(self.cameras):
            cam.Attach(tlFactory.CreateDevice(devices[i]))
            cam.RegisterConfiguration(ConfigurationEventListener(), pylon.RegistrationMode_Append,
                                      pylon.Cleanup_Delete)
            # Print the model name of the camera.
            logger.info("Initalizing device : {}".format(cam.GetDeviceInfo().GetModelName()))
            if "NIR" in cam.GetDeviceInfo().GetModelName().upper()[-3:]:
                self.nir = self.cameras[i]
            else:
                self.rgb = self.cameras[i]


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG', format=formatter._fmt)
    cams = Camera()

    for camera in cams.cameras:
        event_listener = ImageEventListener(callback=callback)
        camera.RegisterImageEventHandler(
            event_listener, pylon.RegistrationMode_Append, pylon.Cleanup_Delete)
        camera.StartGrabbing(pylon.GrabStrategy_OneByOne, pylon.GrabLoop_ProvidedByInstantCamera)
