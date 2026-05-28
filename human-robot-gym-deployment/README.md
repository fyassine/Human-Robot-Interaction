# human-robot-gym-deployment-ss-23
This repo is the summer semester 2023 version of the addition to the [human-robot-gym](https://gitlab.lrz.de/cps-rl/human-robot-gym) repo and adds the following functionalites:
1. Deploy a trained RL agent on the real Schunk Robot.
2. Transform motions recorded with the Vicon System into .bvh and mujoco format.

# Installation 
1. Install human-robot-gym by following the [instructions](https://gitlab.lrz.de/cps-rl/human-robot-gym#human-robot-gym) (only Linux works).


[Here](https://gitlab.lrz.de/cps-robotics/modular-robot-toolbox/-/wikis/home), you can find the wiki of the old version of this repository.

# Hardware and software setup

The following instructions are based on the PDF provided to us. You can also refer to this document directly.

1. Plug in the robot and ensure the four green lights on its front side are on.
2. Turn on the Speedgoat to the left of the computer using the switch beside the power supply cable. A blue light on its front side should now be turend on.
3. Turn on the Vicon switch underneath the screen. Having done this, the cameras should be running as well, which is indicated by their lights.
4. Connect the PC via ethernet to the Speedgoat and configure the ip address to be `192.168.9.2`. A detailed explanation of this can be found in the [wiki](https://gitlab.lrz.de/cps-robotics/modular-robot-toolbox/-/wikis/Real%20Robot%20Setup/2.%20Hardware%20and%20LAN%20Connection%20Setup). Note that the ethernet adapters feature different IP addresses. Detailed information regarding how to plug in the cables can be found in your supervisor's PDF instructions.
5. Start Matlab 2020a using the symbol on the DELL PC’s desktop. Other Matlab versions will not work.
6. Using Matlab’s file browser, go to `C:\Users\cps_group\Documents\Projects`.
7. Right-click on `modular-robot-toolbox` and choose "Add to path”, then choose “All subfolders".
8. Run `init_rl_setup.m` to initialize the workspace parameters using the green arrow.
9. Click on `rl_setup.slx` to open the Simulink model. Choose “model only”.
10. Connect the TargetPC1 by clicking on “disconnected” (left upper corner). If the ethernet setup is incorrect (see step 4), connecting to the TargetPC1 will not work. If there are unexplainable connection issues, it might help to restart all systems.
11. Compile and run the Simulink model by clicking on the green arrow above “Run on Target”. This will take some time, especially if you are doing it for the first time after starting the Simulink script. Note that after compilation is finished, a second progress bar, which measures the time since the file was started, will appear.
12. The robot should move to its home position if not already there. Note that the safety shield is not turned on when the robot is returning to its home position, so be careful.
13. Start the Vicon tracker program using the green symbol on the desktop. In the navigation bar, you can access a PDF file with detailed instructions on using the program.
14. In the Vicon tracker application, go to “Objects” and make sure that all the needed markers (head, left hand, right hand, left elbow, right elbow, left shoulder, right shoulder, collar, torso) are selected.
15. Using the file explorer, go to the `modular-robot-toolbox` folder. Execute the ViconUDP.exe file you can find here. Alternatively, you can also use the link to the file. Note that this file is crucial for providing data to the UDP interface of the agent and the Speedgoat monitor. If there are problems with deployment, you should make sure that ViconUDP.exe is running properly.
16. Make sure the ethernet connection of the lab PC is activated (right upper corner).

# Deploy the agent
1. Define the agent you want to load using the `run_id` parameter in the `default_training.yaml` file. This parameter equals the Weights & Biases run ID, which you can find at the end of the link leading to your run data. You can find this file in the `human-robot-gym-ss-23/human_robot_gym/training/config/training` folder of the `human-robot-gym-ss-23` repository. If you have not already cloned this repository, please [do so](https://gitlab.lrz.de/cps-rl/human-robot-gym-ss-23/-/tree/ss-23-dev). In the same file, specify the load_episode parameter (episode number or 'final' for the final model).
2. Make sure that the `obs_keys_UDP` parameter in `human-robot-gym-ss-23/human_robot_gym/training/config/human_reach_ss23.yaml` matches the observation keys the agent was trained on. If you have used custom observation keys, make sure these are defined in the method `UDPData.get_ordered_data` of `/home/aj/PycharmProjects/human-robot-gym-deployment/communi_cat/udp_data.py`.
3. Make sure that the emergency stop can be pushed immediately. When we worked with the robot, the emergency stop belonging to the Schunk robot was slightly triangular.
4. You are now ready to deploy the agent. For using a trained agent, run `agent_ss23_hydra2.py`. For deploying the hard-coded agent, run `agent_ss23_reflex_hydra.py`. You can stop deployment by stopping the Python file. You change the duration of deployment by adapting the `runtime` parameter the deployment, which specifies the runtime in seconds.

# Run the transformation pipeline
A detailed explanation on how to install and run the transformation pipeline can be found in the `transformation_pipeline` directory and its subfolders.

# UDP communication (communi_cat)
For a documentation about the UDP communication, please refer to this [wiki entry](https://gitlab.lrz.de/cps-robotics/modular-robot-toolbox/-/wikis/home).
