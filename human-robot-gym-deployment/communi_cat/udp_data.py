"""This class handles reading the datastream sent over UDP.

Author:
    Simon Dobers
    Jakob Thumm
"""
from typing import Tuple
import numpy as np


class UDPData:
    """Handle formatting of the data received over UDP according to the messages defined in the UDPMessage catalog.

    https://gitlab.lrz.de/cps-robotics/modular-robot-toolbox/-/wikis/Real%20Robot%20Setup/2.%20Hardware%20and%20LAN%20Connection%20Setup#2-speedgoat-pc-running-the-rl-agent
    """

    def __init__(self, data: Tuple) -> None:
        """Initialize the UDPData class.

        Args:
            data (Tuple): The data array received over Udp, 159 floating point numbers
        """
        self.data = np.array(data)
        self.joint_dic = {
            "LShoulder": 0,
            "LElbow": 1,
            "LHand": 2,
            "RShoulder": 3,
            "RElbow": 4,
            "RHand": 5,
            "Collar": 6,
            "Torso": 7,
            "Head": 8,
        }

    def get_joint_position(self, joint_name: str) -> np.array:
        """Return global joint position (x,y,z) of specified joint.

        Joint indexes:
        {"LShoulder": 0,
         "LElbow":    1,
         "LHand":     2,
         "RShoulder": 3,
         "RElbow":    4,
         "RHand":     5,
         "Collar":    6,
         "Torso":     7,
         "Head" :     8}

        Args:
            joint_name (str): Name of the joint for which to return the position

        Returns:
            np.array: Global joint position: [x,y,z]
        """
        if joint_name not in self.joint_dic:
            raise KeyError(
                f"Specified joint does not exist in the data, must be one of {self.joint_dic}"
            )

        idx = self.joint_dic[joint_name] * 3
        pos = self.data[idx:(idx + 3)]
        return pos

    def get_joint_velocity(self, joint_name: str) -> np.array:
        """Return global joint velocity (v_x,v_y,v_z) of specified joint.

        Joint indexes:
        {"LShoulder": 0,
        "LElbow":     1,
        "LHand":      2,
        "RShoulder":  3,
        "RElbow":     4,
        "RHand":      5,
        "Collar":     6,
        "Torso":      7,
        "Head" :      8}

        Args:
            joint_name (str): Name of the joint for which to return the velocity

        Returns:
            np.array: Global joint velocity: [vx,vy,vz]
        """
        if joint_name not in self.joint_dic:
            raise KeyError(
                f"Specified joint does not exist in the data, must be one of {self.joint_dic}"
            )

        idx = self.joint_dic[joint_name] * 3 + 27
        vel = self.data[idx:(idx + 3)]
        return vel

    def get_joint_rotation(self, joint_name: str) -> np.array:
        """Return global joint rotation in matrix format.

        Joint indexes:
        {"LShoulder": 0,
        "LElbow":     1,
        "LHand":      2,
        "RShoulder":  3,
        "RElbow":     4,
        "RHand":      5,
        "Collar":     6,
        "Torso":      7,
        Head":        8}

        Args:
            joint_name (str): Name of the joint for which to return the rotation

        Returns:
            np.array: Global joint [RotMatrix(0,0), RotMatrix(0,1), RotMatrix(0,2), RotMatrix(1,0),...]
        """
        if joint_name not in self.joint_dic:
            raise KeyError(
                f"Specified joint does not exist in the data, must be one of {self.joint_dic}"
            )

        idx = self.joint_dic[joint_name] * 9 + 54
        rot = self.data[idx:(idx + 9)]
        return rot

    def get_occlusion_information(self) -> np.array:
        """Return an array which indicates which joints are currently observed by the Vicon system.

        Returns:
            np.array: Array of 0/1 : 1 at position 3 means joint 3 is occluded, 0 means visible
        """
        occluded_joints = self.data[135:144]
        return occluded_joints

    def get_robot_position(self) -> np.array:
        """Return current robot positon.

        Returns:
            np.array: Current robot joint angles
        """
        rob_pos = self.data[144:150]
        return rob_pos

    def get_eef_position(self) -> np.array:
        """Return current end effector position in global coordinate frame.

        Returns:
            np.array: Current global eef position
        """
        rob_pos = self.data[150:153]
        return rob_pos

    def get_robot_velocity(self) -> np.array:
        """Return current robot joint velocities.

        Returns:
            np.array: Current robot joint velocities
        """
        rob_vel = self.data[153:159]
        return rob_vel

    def compute_distance_2_joints(self, joints: str) -> np.array:
        """Compute the distance between the joints specified in joints parameter.

        Args:
            joints (string): The joints between which to compute the distance. Format: {jointA_2_jointB}. Example:
                             Head_2_eef computes distances between Head and endeffector
        Returns:
            np.array: Distance between the two specified joints
        """
        joint1, joint2 = joints.split("_2_")

        if joint1 == "eef":
            joint1_pos = self.get_eef_position()
            joint2_pos = self.get_joint_position(joint2)
        elif joint2 == "eef":
            joint2_pos = self.get_eef_position()
            joint1_pos = self.get_joint_position(joint1)
        else:
            joint2_pos = self.get_joint_position(joint2)
            joint1_pos = self.get_joint_position(joint1)

        dist = np.abs(joint1_pos - joint2_pos)

        return dist

    def get_all_data(self) -> dict:
        """Return data all data as dictionary.

        Returns:
            dict: Dictionary with udp data
        """
        data = {}
        joints = {
            "LShoulder": 0,
            "LElbow": 1,
            "LHand": 2,
            "RShoulder": 3,
            "RElbow": 4,
            "RHand": 5,
            "Collar": 6,
            "Torso": 7,
            "Head": 8,
        }

        for joint in joints:
            data[joint + "_pos"] = self.get_joint_position(joint)
            data[joint + "_vel"] = self.get_joint_velocity(joint)
            data[joint + "_rot"] = self.get_joint_rotation(joint)

        data["occluded_joints"] = self.get_occlusion_information()
        data["robot_pos"] = self.get_robot_position()
        data["robot_vel"] = self.get_robot_velocity()
        data["eef_pos"] = self.get_eef_position()

        return data

    def get_ordered_data(self, data_list: list) -> Tuple[np.array, int]:
        """Return data in the order specified in data_list.

        Args:
            data_list (list): List what data should be returned in what order (defined in config.yaml),
            e.g. ['robot_pos' , 'RHand_vel',...]

        Returns:
            Tuple[data,desired_goal_idx]: data: Horizontally stacked array with data order as defined in data_list
                                          desired_goal_idx : array index at which the desired goal part of the data
                                            array is located
        """
        all_data = self.get_all_data()
        data = []
        for key in data_list:
            # if key is "desired_goal", fill with 6 zeros, as this will be overwritten the agent.py
            if key == "desired_goal":
                # goal_idx = len(np.hstack(data))
                data.append(np.zeros(6))
            elif key == "eef_to_human_lh_norm":
                left_hand = all_data['LHand_pos']
                eef = all_data['eef_pos']
                data.append(np.linalg.norm(left_hand-eef))
            elif key == "eef_to_human_rh_norm":
                right_hand = all_data['RHand_pos']
                eef = all_data['eef_pos']
                data.append(np.linalg.norm(right_hand - eef))
            elif key == 'closest_norm':
                left_hand = all_data['LHand_pos']
                right_hand = all_data['RHand_pos']
                head = all_data['Head_pos']
                d_lh = np.linalg.norm(left_hand)
                d_rh = np.linalg.norm(right_hand)
                d_head = np.linalg.norm(head)
                data.append(np.min([d_lh, d_rh, d_head]))
            elif "_2_" in key:
                data.append(self.compute_distance_2_joints(key))
            else:
                data.append(all_data[key])

        return (np.hstack(data))
