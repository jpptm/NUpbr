import os
import re

from config import scene_config as scene_cfg
from config import output_config as out_cfg

from scene import environment as env


# Import assets from path as defined by asset_list
# Where asset list is a list of two-tuples, each containing
#   - the dictionary key and
#   - regex string for each field
def populate_assets(path, asset_list):
    # Populate list of assets at path
    files = os.listdir(path)

    # Create container for asset entries
    assets = []

    # Initialise field paths as None
    fields = {}
    for item in asset_list:
        fields.update({item[0]: None})

    # Search through each file in folder to try to find raw and mask image paths
    for file in files:
        for item in asset_list:
            result = re.search(item[1], file, re.I)
            if result is not None:
                fields.update({item[0]: os.path.join(path, file)})

    # If we have a mandatory field (first field listed in asset_list)
    if fields[asset_list[0][0]] is not None:
        assets.append(fields)

    # Populate list of subdirectories at path
    subdirs = sorted(
        [x for x in files if os.path.isdir(os.path.join(path, x))])

    # For each subdirectory, recursively populate assets
    for subdir in subdirs:
        assets += populate_assets(os.path.join(path, subdir), asset_list)

    return assets


def load_assets():
    # Populate list of hdr scenes
    print("[INFO] Importing environments from '{0}'".format(
        scene_cfg.scene_hdr['path']))
    hdrs = populate_assets(scene_cfg.scene_hdr['path'], [
        ('raw_path', scene_cfg.HDRI_RAW_REGEX),
        ('mask_path', scene_cfg.HDRI_MASK_REGEX),
        ('info_path', scene_cfg.HDRI_INFO_REGEX),
    ])
    print("[INFO] \tNumber of environments imported: {0}".format(len(hdrs)))

    # Create container for ball entries
    print("[INFO] Importing balls from '{0}'".format(
        scene_cfg.ball['ball_dir']))
    balls = populate_assets(
        scene_cfg.ball['ball_dir'],
        [
            ('colour_path', scene_cfg.BALL_COL_REGEX),
            ('norm_path', scene_cfg.BALL_NORM_REGEX),
            ('mesh_path', scene_cfg.BALL_MESH_REGEX),
        ],
    )
    print("[INFO] \tNumber of balls imported: {0}".format(len(balls)))

    return hdrs, balls


def setup_environment(hdr):
    # Clear default environment
    env.clear_env()
    # Setup render settings
    env.setup_render()
    # Setup HRDI environment
    world = env.setup_hdri_env(hdr['raw_path'])

    # Setup render layers (visual, segmentation and field lines)
    return env.setup_segmentation_render_layers(len(scene_cfg.classes)), world