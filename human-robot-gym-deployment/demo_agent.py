#!/usr/bin/env python
"""This script is used to test UDP execution on the real Schunk robot.

Creator:
    Jakob Thumm
"""
from communi_cat.agent_cat import AgentCat
from communi_cat.client_cat import ClientCat
from communi_cat.udp_data import UDPData
from communi_cat.config_cat import ConfigCat
from communi_cat.logging_helper import LoggingHelper
import logging
import numpy as np
import time
import json


if __name__ == "__main__":
    # get configuration
    config = ConfigCat().config["agent"]

    # describes how long the sending of new goals should be
    file_path = config["file_path"]
    # ordered list of observations, that get passed to the agent
    observation_list = config["input"]
    extended_logging = config["extended_logging"]
    agent_name = config["name"]
    runtime = config["runtime"]
    with open(config["failsafe_config"], "r") as file:
        failsafe_config_path = json.load(file)

    # init logging
    LoggingHelper.init_logging(extended_logging)
    logger = logging.getLogger(agent_name)
    LoggingHelper.init_logger(logger, extended_logging)

    # initialize sending and receiving data
    logger.info("Initalizing UDP communication and loading agent...")

    # initialize UDP comunication
    agent = AgentCat()
    client = ClientCat()

    agent.start()
    client.start()

    start = time.time()
    time_last_step = start % 0.2
    current = 0.0

    # Receive data from robot
    client.receive_data()
    # client.data[-1] is the last saved position of the robot
    udpData = UDPData(client.data[-1])
    # get latest observations as defined in config.yaml and the array index,
    # where the goal must be inserted
    observation, goal_position_idx = udpData.get_ordered_data(observation_list)
    logger.info("First observation: {}".format(observation))

    t = time.time()
    logger.info("Executing fixed trajectory.")

    # some "nice looking" positions
    goals = np.array([
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [1.0, 1.4, 0.0, 0.0, 0.0, 0.0],
        [0.0, 1.4, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.5, -0.9, 0.0, 0.0, 0.0],
        [0.0, 1.4, 0.0, 0.0, 0.0, 0.0],
        [-1.4, 1.4, 0.0, 0.0, 0.0, 0.0],
        [-2.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    ])

    goal_counter = 0
    send_time = 3
    execution_time = 0.2
    send_steps = int(send_time/execution_time)
    step_counter = 0
    goal_id = 0
    while True:
        # receive data over UDP
        client.receive_data()

        current = time.time()
        diff = current - start
        mod_curr = current % execution_time
        # If the current time is smaller mod execution_time,
        # than the last timestep then it means that at least
        # execution_time have passed since then
        if mod_curr < time_last_step:

            # client.data[-1] is the last saved position of the robot
            udpData = UDPData(client.data[-1])
            if step_counter >= send_steps:
                goal_id = goal_counter % goals.shape[0]
                print("Moving to goal {} = {}".format(goal_id, goals[goal_id]))
                goal_counter += 1
                step_counter = 0
            goal = goals[goal_id]
            # send to robot
            agent.send_data(goal)
            step_counter += 1
        time_last_step = mod_curr
        # Exiting when time is up
        if diff > runtime:
            break

    # Closing sockets
    agent.stop()
    client.stop()
