import glob
import pickle


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