import cv2
import numpy as np
import torch
import datetime
import os
import matplotlib.pyplot as plt

def create_pair(input_path, output_dir='output', done_dir='input/done', show=False):
    # Read image
    img = cv2.imread(input_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {input_path}")
    h, w = img.shape[:2]
    TARGET_HEIGHT = 1080
    TARGET_WIDTH = 1920
    MAX_CONFORTABLE_WIDTH = 550 # max picture width that eyes can resolve in goggles
    frame_perc = 60
    resize_h = int(TARGET_HEIGHT / (1 + frame_perc/100))
    resize_w = int(img.shape[1] * (resize_h / img.shape[0]))
    if resize_w > MAX_CONFORTABLE_WIDTH:
        # resize again to fit comfortable width
        print(f'ℹ️ Picture too wide. Further resizing')
        scale_factor = MAX_CONFORTABLE_WIDTH / resize_w
        resize_w = MAX_CONFORTABLE_WIDTH
        resize_h = int(resize_h * scale_factor)
    img = cv2.resize(img, (resize_w, resize_h), interpolation=cv2.INTER_AREA)
    h, w = img.shape[:2]

    # Load MiDaS model
    midas = torch.hub.load('intel-isl/MiDaS', 'DPT_Large')
    midas.eval()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    midas.to(device)
    transform = torch.hub.load('intel-isl/MiDaS', 'transforms').dpt_transform
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    input_batch = transform(img_rgb).to(device)
    with torch.no_grad():
        prediction = midas(input_batch)
        depth_map = prediction.squeeze().cpu().numpy()
    depth_map = cv2.normalize(depth_map, None, 0, 255, cv2.NORM_MINMAX)
    depth_map = depth_map.astype(np.uint8)
    depth_map = cv2.resize(depth_map, (w, h))
    os.makedirs(output_dir, exist_ok=True)
    cv2.imwrite(os.path.join(output_dir, 'depth_map.jpg'), depth_map)
    combined = cv2.addWeighted(img, 0.5, cv2.cvtColor(depth_map, cv2.COLOR_GRAY2BGR), 0.5, 0)
    cv2.imwrite(os.path.join(output_dir, 'combined.jpg'), combined)

    # Create stereoscopic SBS pair using depth map for pixel-wise shift
    max_shift_perc = 1.5
    max_shift = int(w * max_shift_perc / 100)
    left_img = np.zeros_like(img)
    right_img = np.zeros_like(img)
    depth_norm = cv2.normalize(depth_map.astype(np.float32), None, 0, 1, cv2.NORM_MINMAX)
    for y in range(h):
        for x in range(w):
            shift = int(depth_norm[y, x] * max_shift)
            lx = x - shift
            if 0 <= lx < w:
                left_img[y, lx] = img[y, x]
            rx = x + shift
            if 0 <= rx < w:
                right_img[y, rx] = img[y, x]
    # Fill blanks by propagating from left (for left_img) and right (for right_img)
    for y in range(h):
        last_pixel = None
        for x in range(w):
            if np.all(left_img[y, x] == 0):
                if last_pixel is not None:
                    left_img[y, x] = last_pixel
            else:
                last_pixel = left_img[y, x]
    for y in range(h):
        last_pixel = None
        for x in range(w-1, -1, -1):
            if np.all(right_img[y, x] == 0):
                if last_pixel is not None:
                    right_img[y, x] = last_pixel
            else:
                last_pixel = right_img[y, x]
    black_band_perc = 11
    sbs_depth = cv2.hconcat([left_img, np.zeros((h, int(w * black_band_perc/100), 3), dtype=np.uint8), right_img])
    sbs_depth = cv2.copyMakeBorder(sbs_depth, int(h * frame_perc/200), int(h * frame_perc/200), int(w * frame_perc/200), int(w * frame_perc/200), cv2.BORDER_CONSTANT, value=[0, 0, 0])
    final_h = sbs_depth.shape[0]
    if final_h > TARGET_HEIGHT:
        excess = final_h - TARGET_HEIGHT
        sbs_depth = sbs_depth[excess//2:final_h - (excess - excess//2), :, :]
    elif final_h < TARGET_HEIGHT:
        deficit = TARGET_HEIGHT - final_h
        sbs_depth = cv2.copyMakeBorder(sbs_depth, deficit//2, deficit - deficit//2, 0, 0, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    final_w = sbs_depth.shape[1]
    if final_w > TARGET_WIDTH:
        excess = final_w - TARGET_WIDTH
        sbs_depth = sbs_depth[:, excess//2:final_w - (excess - excess//2), :]
    elif final_w < TARGET_WIDTH:
        deficit = TARGET_WIDTH - final_w
        sbs_depth = cv2.copyMakeBorder(sbs_depth, 0, 0, deficit//2, deficit - deficit//2, cv2.BORDER_CONSTANT, value=[0, 0, 0])
    # out_sbs = os.path.join(output_dir, 'stereoscopic_sbs_from_depth_pixelwise.jpg')
    out_sbs=f'gallery/stereo/{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.jpg'
    cv2.imwrite(out_sbs, sbs_depth)
    # Move input to done_dir
    os.makedirs(done_dir, exist_ok=True)
    base = os.path.basename(input_path)
    done_path = os.path.join(done_dir, base)
    os.rename(input_path, done_path)
    if show:
        plt.imshow(cv2.cvtColor(sbs_depth, cv2.COLOR_BGR2RGB))
        plt.axis('off')
        plt.title('Stereoscopic SBS from Depth (Pixel-wise Shift)')
        plt.show()
    return out_sbs, done_path
