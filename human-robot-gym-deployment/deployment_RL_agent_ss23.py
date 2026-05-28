#!/usr/bin/env python
"""This script is used to deploy an agent trained in simulation to the real Schunk robot.

Commandline args:
    config (str): Name of the config file which was used during training

Creator:
    Simon Dobers
    
Contributors:
    Yangtao Chen
    Ansgar Schäfftlein

Changes as of June 30th 2023:
    Made the deployment of reinforcement learning agents possible directly through the
    human robot gym repository (Yangtao C., Ansgar S.). Discrete actions are postprocessed
    through the SkillWrapper (see line 170-177).
"""


from ast import While
from communi_cat.agent_cat import AgentCat
from communi_cat.client_cat import ClientCat
from communi_cat.udp_data import UDPData
from communi_cat.logging_helper import LoggingHelper

import logging
import numpy as np
import time
import json
import hydra
import os

import human_robot_gym.robots  # noqa: F401
import human_robot_gym.environments.manipulation.ss23_env  # noqa: F401
from human_robot_gym.utils.config_utils import Config
from human_robot_gym.utils.training_utils import create_environment, load_model
from human_robot_gym.wrappers.skill_wrapper import SkillWrapper

# The following lines are written to obtain the config path of the training repository.

# Get path to the folder in which this file is
dir_path = os.path.dirname(os.path.realpath(__file__))
print('dir_path: {}'.format(dir_path))

# Get project folder path with the deployment and robot-gym repos in it
dir_path = os.path.dirname(dir_path)
print('dir_path: {}'.format(dir_path))
config_path = dir_path + "/human-robot-gym-ss-23/human_robot_gym/training/config"

# Assert that the human-robot-gym-ss-23 repository from the config file has already been cloned
error_message = "You need to clone our training repository human-robot-gym-ss-23 as well."
assert os.path.exists(dir_path + "/human-robot-gym-ss-23"), error_message


@hydra.main(version_base=None, config_path=config_path, config_name="human_reach_ss23")
def main(config: Config):

    # Ordered list of observations, that get passed to the agent
    observation_list = config["training"]["obs_keys_UDP"]

    extended_logging = False
    agent_name = config["training"]["run_id"]
    runtime = 301

    # remove /config from config path
    path = os.path.dirname(config_path)

    # remove /training from config path
    path = os.path.dirname(path)
    path += "/"

    # Load Failsafe config
    with open(path + config["robot"]["controller_config_path"], "r") as file:
        failsafe_config_path = json.load(file)

    # Init logging
    LoggingHelper.init_logging(extended_logging)
    logger = logging.getLogger(agent_name)
    LoggingHelper.init_logger(logger, extended_logging)

    logger.info("Initalizing UDP communication and loading agent...")

    # create environment - must be similar to training environment 
    env = create_environment(config=config, evaluation_mode=True)

    # << Environment Wrappers >>
    # if not hasattr(env, "spec"):
    #     env.spec = struct
    #
    # if env.spec is None:
    #     env.spec = struct
    # env = TimeLimit(env, max_episode_steps=training_config["algorithm"]["max_ep_len"])
    # env = CollisionPreventionWrapper(
    #     env=env,
    #     collision_check_fn=env._check_collision_action,
    #     replace_type=training_config["environment"]["replace_type"],
    # )

    # initialize UDP comunication
    agent = AgentCat()
    client = ClientCat()

    agent.start()
    client.start()

    start = time.time()
    time_last_step = start % 0.2

    # Receive data from robot
    client.receive_data()

    # client.data[-1] is the last saved position of the robot
    print('client.data')
    print(client.data)

    udpData = UDPData(client.data[-1])

    # get latest observations as defined in config.yaml and the array index ,where the goal must be inserted    
    observation = udpData.get_ordered_data(observation_list)
    logger.info("First observation: {}".format(observation))

    obs = env.reset()
    print('Obs reset')
    print(obs)

    # Load model
    model = load_model(
        config=config,
        env=env,
        run_id=config.training.run_id,
        load_episode=config.training.load_episode
        )
    logger.info("Agent successfully loaded.")

    t = time.time()

    # Return to home position
    logger.info("Returning to home position")
    while True:
        
        agent.send_data(np.array([0, 0, 0, 0, 0, 0]))
        if time.time() - t > 5:
            break

    while True:
        # Receive data over UDP
        client.receive_data()

        current = time.time()
        diff = current - start
        mod_curr = current % 0.2
        # If the current time is smaller module 0.2 than the last timestep then it means
        # that at least 200 ms have passed since then
        if mod_curr < time_last_step:

            # client.data[-1] is the last saved position of the robot
            udpData = UDPData(client.data[-1])

            # observation, goal_position_idx = udpData.get_ordered_data(observation_list)
            observation = udpData.get_ordered_data(observation_list)

            # Step the agent
            int_action, _states = model.predict(observation, deterministic=True)

            # Acquire robot pos for SkillWrapper postprocessing
            q_current = udpData.get_robot_position()
            print(q_current)

            # Transformation of integer actions to desired positions as in the skill wrapper
            if int_action == 0:
                # q_goal = np.array([0, 1.5, 0, 0, 0, 0])  # right of table
                q_goal = np.array([0, -1.5, 0, 0, 0, 0])  # left of table
            elif int_action == 1:
                    q_goal = np.array([0, 0, 0, 0, 0, 0])  # home position
            else:
                raise ValueError
           
            action = q_goal 

            # Transform agents output ([-1,1]) into range [-0.2,0.2] as defined in the failsafe
            # controller config 
            action_scale = abs(
                failsafe_config_path["output_max"] - failsafe_config_path["output_min"]
            ) / abs(
                failsafe_config_path["input_max"] - failsafe_config_path["input_min"]
            )
            action_output_transform = (
                failsafe_config_path["output_max"] + failsafe_config_path["output_min"]
            ) / 2.0
            action_input_transform = (
                failsafe_config_path["input_max"] + failsafe_config_path["input_min"]
            ) / 2.0
            action = np.clip(
                action,
                failsafe_config_path["input_min"],
                failsafe_config_path["input_max"],
            )
            transformed_action = (
                action - action_input_transform
            ) * action_scale + action_output_transform

            # Send action to robot
            print('Int action: {}'.format(int_action))
            print('Real action: {}'.format(np.round(action, decimals=2)))
            print('Q_current: {}'.format(np.round(q_current, decimals=2)))
            assert np.shape(action) == np.shape(np.array([0, 1, 0, 0, 0, 0]))

            agent.send_data(action)

            if extended_logging:
                logger.debug(f"Observation passed to agent: {obs}")
                logger.debug(
                    f"Agent's predicted action: {action}\n-----------------------------------------------------"
                )
        time_last_step = mod_curr

        # Exiting when time is up
        if diff > runtime:
            break

    # Closing sockets
    print('Closing sockets...')
    agent.stop()
    client.stop()

if __name__ == "__main__":
    main()
