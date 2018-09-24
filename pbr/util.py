import os
import re
import bpy
import random as rand
from math import pi

from config import scene_config as scene_cfg

from scene import environment as env

DEG_TO_RAD = pi / 180.

# Import assets from path as defined by asset_list
# Where asset list ('assets') is a list of two-tuples, each containing
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
    subdirs = sorted([x for x in files if os.path.isdir(os.path.join(path, x))])

    # For each subdirectory, recursively populate assets
    for subdir in subdirs:
        assets += populate_assets(os.path.join(path, subdir), asset_list)

    return assets

# Load ball and HDR map data from respective paths,
#   traversing recursively through subdirectories
def load_assets():
    # Populate list of hdr scenes
    print("[INFO] Importing environments from '{0}'".format(scene_cfg.scene_hdr['path']))
    hdrs = populate_assets(
        scene_cfg.scene_hdr['path'], [
            ('raw_path', scene_cfg.HDRI_RAW_REGEX),
            ('mask_path', scene_cfg.HDRI_MASK_REGEX),
            ('info_path', scene_cfg.HDRI_INFO_REGEX),
        ]
    )
    print("[INFO] \tNumber of environments imported: {0}".format(len(hdrs)))

    # Create container for ball entries
    print("[INFO] Importing balls from '{0}'".format(scene_cfg.ball['ball_dir']))
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

# Renders image frame for either raw or mask image (defined by <isRawImage>)
# def render_image(imageType, toggles, ball, world, env, hdr_path, output_path):
def render_image(isMaskImage, toggle, ball, world, env, hdr_path, output_path):
    # Turn off all render layers
    for l in bpy.context.scene.render.layers:
        l.use = isMaskImage

    # Enable raw image rendering if required
    bpy.context.scene.render.layers['RenderLayer'].use = not isMaskImage

    # Switch
    toggle[0].check = isMaskImage

    # Alpha Over
    toggle[1].inputs[0].default_value = 0. if isMaskImage else 1.

    if not isMaskImage:
        # Depth Viewer
        toggle[2].format.file_format = 'OPEN_EXR'
        toggle[2].base_path = os.path.join(os.path.dirname(output_path), '..', 'depth')
        toggle[2].file_slots[0].path = os.path.basename(output_path)

        # Mist Viewer
        toggle[3].format.file_format = 'PNG'
        toggle[3].base_path = os.path.join(os.path.dirname(output_path), '..', 'mist')
        toggle[3].file_slots[0].path = os.path.basename(output_path)

    # Hide ball shadow catcher plane when rendering the mask image
    ball.sc_plane.hide_render = isMaskImage

    # Update HDRI map
    env.update_hdri_env(world, hdr_path)

    # Update render output filepath
    bpy.data.scenes['Scene'].render.filepath = output_path
    bpy.ops.render.render(write_still=True)

    # if depth_path:
    #     img = bpy.data.images['Viewer Node']
    #     min_val = None
    #     max_val = None
    #     with open('{}.pfm'.format(depth_path), 'wb') as f:
    #         f.write('Pf\n'.encode('utf-8'))
    #         f.write('{:d} {:d}\n'.format(img.size[0], img.size[1]).encode('utf-8'))
    #         f.write('{:f}\n'.format(-1.0).encode('utf-8'))
    #         for p in img.pixels:
    #             if not min_val or p < min_val:
    #                 min_val = p
    #             if not max_val or p > max_val:
    #                 max_val = p
    #             f.write('{:f}'.format(p).encode('utf-8'))

    #     with open('{}.pgm'.format(depth_path), 'wb') as f:
    #         f.write('P5\n'.encode('utf-8'))
    #         f.write('{:d} {:d}\n'.format(img.size[0], img.size[1]).encode('utf-8'))
    #         f.write('255\n'.encode('utf-8'))
    #         for p in img.pixels:
    #             f.write('{:d}'.format(int(((p - min_val) / (max_val - min_val)) * 255)).encode('utf-8'))

# Updates position and rotation for ball, camera and camera anchor objects
def update_scene(ball, cam, anch, env_info):
    # TODO: Update object limits based on if field/goals are rendered
    # Calculate synthetic limits

    synth_cam_limits = {
        'position': {
            'x': [0., 0.],
            'y': [0., 0.],
            'z': scene_cfg.camera['limits']['position']['z']
        },
        'rotation': scene_cfg.camera['limits']['rotation']
    }

    # Update ball
    ball_limits = scene_cfg.ball['limits']
    # if env_info['to_draw']['field']:
    #     ball_limits = {
    #         'position': {
    #             'x'
    #         }
    #     }
    update_obj(ball, ball_limits)

    # Update camera
    cam_limits = scene_cfg.camera['limits'] if env_info['to_draw']['field'] else synth_cam_limits
    update_obj(cam, cam_limits)

    # Update anchor
    update_obj(anch, ball_limits)

# Updates position and rotation by uniform random generation within limits for each component
def update_obj(obj, limits):
    if 'position' in limits:
        obj.move((
            rand.uniform(limits['position']['x'][0], limits['position']['x'][1]),
            rand.uniform(limits['position']['y'][0], limits['position']['y'][1]),
            rand.uniform(limits['position']['z'][0], limits['position']['z'][1]),
        ))
    if 'rotation' in limits:
        obj.rotate((
            rand.uniform(limits['rotation']['pitch'][0], limits['rotation']['pitch'][1]) * DEG_TO_RAD,
            rand.uniform(limits['rotation']['yaw'][0], limits['rotation']['yaw'][1]) * DEG_TO_RAD,
            rand.uniform(limits['rotation']['roll'][0], limits['rotation']['roll'][1]) * DEG_TO_RAD,
        ))
