# Robot RL

This repository allows to capture human motion data with the Vicon System and transforms it first to a BVH file and aftwards file that can be used for mujoco simulations

## Clone this repo
```
git@gitlab.lrz.de:cps-robotics/rl-in-robotics-lab-course/rl-in-robotics-ws21-22.git
```

## Installation
We work on Ubuntu 20.04. If you want to participate, you need to run this version

1. Install anaconda 
2. create and environment 
    ```
    conda create -n human-motion python==3.8
    ```
3. activate the environment
    ```
    conda activate human-motion 
    ```
4. install the requirements
    ```
    pip install -r requirements.txt 
    ```
4. run the pipeline to convert the collected csv data to a mujoco usable format
    ```
    python transformationPipeline.py --directory motion_capture/dataset/motions/{name of the folder} 
    ```
    use the following arguments:

    --postprocess (apply postprocessing)

    --toBVH (convert CSV to BVH)

    --toMujco (convert BVH to mujoco usable format)

The pipeline creates an extra folder called **mujoco** for the mujoco usable files (.pkl)



