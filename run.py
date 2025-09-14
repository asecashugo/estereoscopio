import os
from stereo_batch import create_pair
from glob import glob
import time

input_dir = 'input'
done_dir = os.path.join(input_dir, 'done')
jpg_files = glob(os.path.join(input_dir, '*.jpg'))
print(f'Found {len(jpg_files)} jpg files in {input_dir}')
for i, jpg_path in enumerate(jpg_files):
    try:
        out_sbs, done_path = create_pair(jpg_path, output_dir='output', done_dir=done_dir, show=False)
        print(f'[{i+1}/{len(jpg_files)}] Processed: {os.path.basename(jpg_path)} → {os.path.basename(out_sbs)}')
    except Exception as e:
        print(f'Error processing {jpg_path}: {e}')
    time.sleep(0.1)  # for progress update