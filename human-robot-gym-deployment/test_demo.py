#!/usr/bin/env python
"""This script is used to deploy an agent trained in simulation to the real Schunk robot.

Commandline args:
    config (str): Name of the config file which was used during training

Creator:
    Simon Dobers

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


def main():
    runtime = 301
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
    # observation = udpData.get_ordered_data(observation_list)
    
    
    t = time.time()
   

    # return to predefined position first, as agent was trained to always start from that position
    while True:
        # TODO: Shouldn't this be done differently to return to the home position?
        # agent.send_data(np.zeros(6))
        # start position for right-left agent
        # agent.send_data(np.array([1.4, 1.5, 0, 0, 0, 0]))
        agent.send_data(np.array([0, 0, 0, 0, 0, 0]))
        if time.time() - t > 5:
            break
    print('Finished moving to home position')
    while True:
        # receive data over UDP
        client.receive_data()

        current = time.time()
        diff = current - start
        mod_curr = current % 0.2
        # If the current time is smaller module 0.2 than the last timestep then it means
        # that at least 200 ms have passed since then
        if mod_curr < time_last_step:

            print('sending action...')
            t = time.time()
            while True:

                agent.send_data(np.array([0,0,0,0,0,0]))
                # agent.send_data(action)

                if  time.time() - t > 5:
                    break
            
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
