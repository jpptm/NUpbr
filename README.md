# NUpbr
This repository holds code to generate a Physically-Based Rendered (PBR) and configurable football field.

# Example
![Field Example](./docs/outputs/scene_example.gif)

# Requirements
+ [Blender](https://www.blender.org/download/) (2.79+)
+ [Python](https://www.python.org/downloads/) (3.6.5+)
+ [Pillow](https://pillow.readthedocs.io/en/5.1.x/installation.html) (5.1.0+)

# Usage
## Generating field UV map
A UV map for the field can be generated by running [`generate_uv.py`](./field_uv_generation/generate_uv.py). This will use the configuration listed in [`scene_config.py`](./field_uv_generation/scene_config.py).

## Building the scene
To generate the scene with default field UV map, the `pbr_scene` script should be run through the Blender Python API. That is, `blender --python pbr_scene.py` while in the pbr_scene directory.

The ball UV map and HRDI environment image are randomly selected from the respective configured directory.

To build only the goal, ball or field, run `blender --python <script>` where `<script>` is either `goal`, `ball` or `field` from the `pbr_scene` directory.

## Custom UV Maps and HRDI Environment
The resources used for texturing the ball and field by default are found in [`resources/ball_uv`](./resources/ball_uv) and [`resources/field_uv`](./resources/field_uv) respectively. There is no default HDRI environment directory within the repository, but will attempt to be read from  `resources/scene_hdr`. The directory to look for these resources can be modified in [`scene_config.py`](./field_uv_generation/scene_config.py) under `field_uv['uv_path']`, `ball['uv_path']` and `scene_hdr['path']`.

### Field
A new field UV map and construction can be configured in [`scene_config.py`](./field_uv_generation/scene_config.py).

### Ball
Custom UV maps to be considered for selection when generating the scene can be placed in the ball UV directory (by default [`resources/ball_uv`](./resources/ball_uv)). 

### Environment
Similarly to the ball UV maps, a random HRDI environment image is selected from the pool of images within the scene HDR directory.
