#!/usr/bin/env python
"""This script is used to deploy an PPO agent to the real Schunk robot.

Commandline args:
    config (str): Name of the config file which was used during training

Author:
    Jakob Thumm
Date:
    31.01.2023
"""
import numpy as np
import json
import gym
from datetime import datetime
from functools import partial
import logging
import time
import os

# SB3
import torch as th  # noqa: F401
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv

# CommuniCat
from communi_cat.agent_cat import AgentCat
from communi_cat.client_cat import ClientCat
from communi_cat.udp_data import UDPData
from communi_cat.config_cat import ConfigCat
from communi_cat.logging_helper import LoggingHelper

# Environment
import robosuite  # noqa: F401
from robosuite.controllers import load_controller_config
from human_robot_gym.utils.mjcf_utils import file_path_completion, merge_configs
from human_robot_gym.wrappers.visualization_wrapper import VisualizationWrapper
from human_robot_gym.utils.env_util import make_vec_env
import human_robot_gym.robots  # noqa: F401
from human_robot_gym.environments import ReachHumanCost  # noqa: F401
from human_robot_gym.wrappers.collision_prevention_wrapper import (
    CollisionPreventionWrapper,
)
from human_robot_gym.wrappers.cost_reward_penalty_wrapper import CostRewardPenaltyWrapper
from human_robot_gym.wrappers.no_gripper_action_wrapper import NoGripperActionWrapper


def wrap_environment(
    env: gym.Env,
    use_collision_wrapper: bool = False,
    replace_type: int = 0,
    n_resamples: int = 20,
    has_renderer: bool = False,
    action_scaling: float = 1.0,
    cost_reward_penalty: float = 0.0,
    use_action_projection: bool = False,
    additional_radius: float = 0.25,
) -> gym.Env:
    """Wrap the environment with the desired wrappers."""
    if use_collision_wrapper:
        env = CollisionPreventionWrapper(
            env=env,
            collision_check_fn=env.check_collision_action,
            replace_type=replace_type,
            n_resamples=n_resamples
        )
    if cost_reward_penalty > 0.0:
        env = CostRewardPenaltyWrapper(
            env=env,
            cost_penalty=cost_reward_penalty
        )
    if has_renderer:
        env = VisualizationWrapper(env)
    if use_action_projection:
        raise NotImplementedError("Action projection is not implemented yet.")
        # env = ActionProjectionWrapper(
        #     env=env,
        #     additional_radius=additional_radius
        # )
    env = NoGripperActionWrapper(env)
    return env


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
    training_config_file = "schunk_ppo_parallel_failsafe_cost.json"

    # Training config
    base_path = os.path.dirname(os.path.abspath(__file__))
    training_config_path = "{}/configs/{}".format(
        base_path, training_config_file
    )
    try:
        with open(training_config_path) as f:
            training_config = json.load(f)
    except FileNotFoundError:
        print(
            "Error opening controller filepath at: {}. "
            "Please check filepath and try again.".format(training_config_path)
        )
    assert "load_episode" in training_config["training"], "Please provide a load_episode in the config."
    assert "run_id" in training_config["training"], "Please provide a run_id in the config."

    # Load robot and controller config files
    controller_config = dict()
    controller_conig_path = file_path_completion(
        training_config["robot"]["controller_config"]
    )
    robot_conig_path = file_path_completion(training_config["robot"]["robot_config"])
    controller_config = load_controller_config(custom_fpath=controller_conig_path)
    robot_config = load_controller_config(custom_fpath=robot_conig_path)
    controller_config = merge_configs(controller_config, robot_config)
    training_config["environment"]["controller_configs"] = [controller_config]

    env_kwargs = {
        "robots": training_config["robot"]["name"],
        "robot_base_offset": training_config["environment"]["robot_base_offset"],
        "env_configuration": training_config["environment"]["env_configuration"],
        "controller_configs": training_config["environment"]["controller_configs"],
        "gripper_types": training_config["environment"]["gripper_types"],
        "initialization_noise": training_config["environment"]["initialization_noise"],
        "table_full_size": training_config["environment"]["table_full_size"],
        "table_friction": training_config["environment"]["table_friction"],
        "use_camera_obs": training_config["environment"]["use_camera_obs"],
        "use_object_obs": training_config["environment"]["use_object_obs"],
        "reward_scale": training_config["environment"]["reward_scale"],
        "reward_shaping": training_config["environment"]["reward_shaping"],
        "goal_dist": training_config["environment"]["goal_dist"],
        "collision_reward": training_config["environment"]["collision_reward"],
        "goal_reward": training_config["environment"]["goal_reward"],
        "has_renderer": training_config["environment"]["has_renderer"],
        "has_offscreen_renderer": training_config["environment"]["has_offscreen_renderer"],
        "render_camera": training_config["environment"]["render_camera"],
        "render_collision_mesh": training_config["environment"]["render_collision_mesh"],
        "render_visual_mesh": training_config["environment"]["render_visual_mesh"],
        "render_gpu_device_id": training_config["environment"]["render_gpu_device_id"],
        "control_freq": training_config["environment"]["control_freq"],
        "horizon": training_config["environment"]["horizon"],
        "ignore_done": training_config["environment"]["ignore_done"],
        "hard_reset": training_config["environment"]["hard_reset"],
        "camera_names": training_config["environment"]["camera_names"],
        "camera_heights": training_config["environment"]["camera_heights"],
        "camera_widths": training_config["environment"]["camera_widths"],
        "camera_depths": training_config["environment"]["camera_depths"],
        "camera_segmentations": training_config["environment"]["camera_segmentations"],
        "renderer": training_config["environment"]["renderer"],
        "renderer_config": training_config["environment"]["renderer_config"],
        "use_failsafe_controller": training_config["environment"]["use_failsafe_controller"],
        "visualize_failsafe_controller": training_config["environment"]["visualize_failsafe_controller"],
        "visualize_pinocchio": training_config["environment"]["visualize_pinocchio"],
        "control_sample_time": training_config["environment"]["control_sample_time"],
        "human_animation_names": training_config["environment"]["human_animation_names"],
        "base_human_pos_offset": training_config["environment"]["base_human_pos_offset"],
        "human_animation_freq": training_config["environment"]["human_animation_freq"],
        "safe_vel": training_config["environment"]["safe_vel"],
        "self_collision_safety": training_config["environment"]["self_collision_safety"],
        "done_at_collision": training_config["environment"]["done_at_collision"],
        "done_at_success": training_config["environment"]["done_at_success"],
        "init_joint_pos": training_config["environment"]["init_joint_pos"],
        "goal_pos": training_config["environment"]["goal_pos"],
        "seed": training_config["training"]["seed"],
    }
    wrapper_cls = partial(wrap_environment,
                          use_collision_wrapper=True,
                          replace_type=training_config["environment"]["replace_type"],
                          has_renderer=training_config["environment"]["has_renderer"],
                          action_scaling=training_config["environment"]["action_scaling"],
                          cost_reward_penalty=training_config["environment"]["cost_reward_penalty"],
                          use_action_projection=training_config["environment"]["use_action_projection"],
                          additional_radius=training_config["environment"]["additional_radius"],)
    n_envs = training_config["training"]["n_envs"]
    assert n_envs >= 1, "n_envs must be >= 1"
    env = make_vec_env(
        env_id="ReachHumanCost",
        type="env",
        obs_keys=training_config["environment"]["obs_keys"],
        n_envs=n_envs,
        env_kwargs=env_kwargs,
        vec_env_cls=DummyVecEnv if n_envs == 1 else SubprocVecEnv,
        wrapper_class=wrapper_cls,
    )
    now = datetime.now()
    # Load trained agent
    load_episode = training_config["training"]["load_episode"]
    run_id = training_config["training"]["run_id"]
    # << Load the model >>
    model = PPO.load(
        "{}/model_{}".format(f"models/{run_id}", str(load_episode)), env=env
    )
    # load it into the loaded_model
    start_episode = model._episode_num
    model.set_env(env)
    model.env.reset()
    logger.info("Agent successfully loaded.")

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
    # get latest observations as defined in config.yaml and the array index ,where the goal must be inserted
    observation, goal_position_idx = udpData.get_ordered_data(observation_list)
    logger.info("First observation: {}".format(observation))

    obs = env.reset()

    t = time.time()
    logger.info("Returning to home position")
    init_joint_pos = np.array(training_config["environment"]["init_joint_pos"])
    # return to predefined position first, as agent was trained to always start from that position
    last_time = t
    while True:
        client.receive_data()
        if last_time + 0.1 < time.time():
            agent.send_data(init_joint_pos)
            # client.data[-1] is the last saved position of the robot
            udpData = UDPData(client.data[-1])
            # build goal difference observation
            robot_pos = udpData.get_robot_position()
            diff_pos = init_joint_pos - robot_pos
            if np.linalg.norm(diff_pos) < 0.1:
                break
            else:
                logger.info("Starting position not reached yet. Current position: {}, goal position: {}".format(
                    robot_pos, init_joint_pos))
            last_time = time.time()

    action_execution_time = 1/training_config["environment"]["control_freq"]
    time.sleep(10)

    while True:
        # receive data over UDP
        client.receive_data()

        current = time.time()
        diff = current - start
        mod_curr = current % action_execution_time
        # If the current time is smaller module 0.2 than the last timestep then it means
        # that at least 200 ms have passed since then
        if mod_curr < time_last_step:

            # client.data[-1] is the last saved position of the robot
            udpData = UDPData(client.data[-1])

            # build goal difference observation
            goal_pos = env.get_attr("desired_goal")[0]
            robot_pos = udpData.get_robot_position()
            diff_pos = goal_pos - robot_pos
            # build human distance observation
            head_2_eef_distance = np.linalg.norm(udpData.compute_distance_2_joints("Head_2_eef"))
            lHand_2_eef_distance = np.linalg.norm(udpData.compute_distance_2_joints("LHand_2_eef"))
            rhand_2_eef_distance = np.linalg.norm(udpData.compute_distance_2_joints("RHand_2_eef"))
            obs = np.concatenate((diff_pos, [head_2_eef_distance, lHand_2_eef_distance, rhand_2_eef_distance]))

            # step the agent
            action, _states = model.predict(obs, deterministic=True)
            if extended_logging:
                logger.debug(f"Observation passed to agent: \n{obs}")
                logger.debug(
                    f"Agent's predicted action: {action}"
                )
            # transform agents output ([-1,1]) into range [-0.2,0.2] as defined in the failsafe
            # controller config
            # TODO Debug and adjust the action scaling
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

            # compute new intermediate goal, ignore gripper action for now
            intermediate_goal = udpData.get_robot_position() + transformed_action
            if extended_logging:
                logger.debug(f"Sent intermediate goal: {intermediate_goal}\n---------------------------------")
            # send to robot
            agent.send_data(intermediate_goal)

        time_last_step = mod_curr

        # Exiting when time is up
        if diff > runtime:
            break

    # Closing sockets
    agent.stop()
    client.stop()
