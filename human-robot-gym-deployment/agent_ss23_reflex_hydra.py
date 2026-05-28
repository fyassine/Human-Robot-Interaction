#!/usr/bin/env python
"""This script is used to deploy a hard-coded agent on the real Schunk robot. This can be helpful if you want the agent
to have, in contrary to a reinforcement learning agent, a completely predictable behavior, for example when debugging or
tuning the parameters of the safety shield.

Commandline args:
    config (str): Name of the config file which was used during training

Creator:
    Simon Dobers

Contributor:
    Ansgar Schäfftlein

"""


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
from utils import get_config_path

config_path = get_config_path()


@hydra.main(version_base=None, config_path=config_path, config_name="human_reach_ss23")
def main(config: Config):
    # Ordered list of observations that get passed to the agent
    observation_list = ['RHand_pos']
    extended_logging = False
    agent_name = config["training"]["run_id"]
    runtime = 301

    # Remove /config from config path
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

    # Initialize UDP communication
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

    # Get latest observations as defined in config.yaml and the array index ,where the goal must be inserted
    observation = udpData.get_ordered_data(observation_list)
    logger.info("First observation: {}".format(observation))
    logger.info("Agent successfully loaded.")

    t = time.time()
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

            # Code for the reflex agent
            hand_pos = observation
            # set y-entry to zero to compute distance only in x-y-plane
            hand_pos[-1] = 0
            dist = np.linalg.norm(hand_pos)
            # action switches depending on whether the distance between the right hand and the end effector in  the
            # x-y-plane is bigger or smaller than 1.5 meters
            if dist < 1.5:
                int_action = 0
            else:
                int_action = 1

            # Convert integer actions obtained from the agent to actions in joint space
            if int_action == 0:
                q_goal = np.array([0.0, -0.5, 0.0, 0.0, 0.0, 0.0])  # right of table
            elif int_action == 1:
                q_goal = np.array([0.0, 0.5, 0.0, 0.0, 0.0, 0.0])  # home position
            else:
                raise ValueError('The dimension for the action space is wrong.')
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

            # Print actions for debugging purposes
            print('Int action: {}'.format(int_action))
            print('Real action: {}'.format(np.round(action, decimals=2)))

            # Acquire joint configuration for printing
            q_current = udpData.get_robot_position()
            print('Q_current: {}'.format(np.round(q_current, decimals=2)))

            # Make sure that the action has the correct shape
            assert np.shape(action) == np.shape(np.array([0, 0, 0, 0, 0, 0]))

            # Send action to robot
            agent.send_data(action)

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
