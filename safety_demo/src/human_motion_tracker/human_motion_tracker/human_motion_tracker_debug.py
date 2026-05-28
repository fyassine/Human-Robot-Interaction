#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from communi_cat.client_cat import ClientCat
import numpy as np
import threading
import time
import datetime
import csv

# Threaded UDP data receiving
def data_receiver(client, stop_event):
    while not stop_event.is_set():
        client.receive_data()
    client.stop()

class HumanMotionTrackerDebug(Node):
    def __init__(self):
        super().__init__('human_motion_tracker_debug')
        self.publisher_ = self.create_publisher(Float32MultiArray, 'human_measurements', 10)
        
        # Declare the scenario parameter
        self.declare_parameter('scenario', '')
        scenario_name = self.get_parameter('scenario').get_parameter_value().string_value

        # Setup log files
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Create comprehensive CSV file for debugging and replay
        if scenario_name:
            csv_filename = f'{scenario_name}.csv'
            self.get_logger().info(f'Recording motion data to scenario: {scenario_name}')
        else:
            csv_filename = f'comprehensive_motion_data_{timestamp}.csv'
            self.get_logger().info(f'Recording motion data to default file: {csv_filename}')
        self.debug_csv_path = os.path.join(log_dir, csv_filename)

        # Joint names in order (matching the joint mapping)
        self.joint_names = ["LShoulder", "LElbow", "LHand", "RShoulder", "RElbow", "RHand", "Collar", "Torso", "Head"]

        # Create separate log files for each joint (existing functionality)
        self.log_file_paths = {}
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        for joint_name in self.joint_names:
            file_path = os.path.join(log_dir, f'{joint_name}_position_{timestamp}.txt')
            self.log_file_paths[joint_name] = file_path
            
            # Write header to each log file
            with open(file_path, 'w') as f:
                f.write("timestamp,x,y,z\n")

        with open(self.debug_csv_path, 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'frame_count']
            # Add all joint positions (x,y,z for each joint)
            for joint_name in self.joint_names:
                fieldnames.extend([f'{joint_name}_x', f'{joint_name}_y', f'{joint_name}_z'])
            # Add specific hand positions for easy reference
            fieldnames.extend(['left_hand_x', 'left_hand_y', 'left_hand_z'])
            fieldnames.extend(['right_hand_x', 'right_hand_y', 'right_hand_z'])
            fieldnames.extend(['left_elbow_x', 'left_elbow_y', 'left_elbow_z'])
            fieldnames.extend(['right_elbow_x', 'right_elbow_y', 'right_elbow_z'])
            # Add table reference points for debugging
            fieldnames.extend(['table_left_edge', 'table_right_edge', 'table_center_y'])
            # Add raw data for debugging
            fieldnames.extend(['raw_data_length', 'all_joint_data'])
            
            self.csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            self.csv_writer.writeheader()
            self.csv_file = csvfile
        
        # Frame counter for debugging
        self.frame_count = 0
        
        # Table dimensions for reference (from config)
        self.table_left_edge = -0.91   # -width/2 = -182cm/2 = -0.91m
        self.table_right_edge = 0.91   # +width/2 = +182cm/2 = +0.91m  
        self.table_center_y = 0.0      # Center of table
        
        # Setup UDP client in a separate thread
        self.stop_event = threading.Event()
        self.client = ClientCat()
        
        try:
            self.client.start()
        except OSError as e:
            self.get_logger().error(f'Failed to start UDP client: {e}')
            self.get_logger().error('This usually means the port is already in use. Try killing any existing processes or wait a moment.')
            raise
            
        self.receiver_thread = threading.Thread(target=data_receiver, args=(self.client, self.stop_event))
        self.receiver_thread.start()

        # Timer to check for new data and publish
        timer_period = 0.02  # 50 Hz
        self.timer = self.create_timer(timer_period, self.publish_udp_data)
        self.last_data_timestamp = 0

        # Open CSV file for writing
        self.csv_file = open(self.debug_csv_path, 'a', newline='')
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=fieldnames)

    def publish_udp_data(self):
        if not self.client.data:
            return

        # Avoid reprocessing the same data packet
        if self.client.last_receive_time <= self.last_data_timestamp:
            return
            
        self.last_data_timestamp = self.client.last_receive_time
        data = self.client.data[-1]

        if len(data) < 2 + 36:
            self.get_logger().warn(f"Skipping frame — expected at least 38 values, got {len(data)}")
            return

        # Extract and process joint data (9 joints, xyz)
        joint_positions = np.array(data[2:2+36]).reshape((9, 4))[:, :3]
        
        # Extract specific hand and elbow coordinates for easy reference
        left_hand_xyz = joint_positions[2]    # LHand (index 2)
        right_hand_xyz = joint_positions[5]   # RHand (index 5) 
        left_elbow_xyz = joint_positions[1]   # LElbow (index 1)
        right_elbow_xyz = joint_positions[4]  # RElbow (index 4)
        
        # Log all body parts positions to their respective files (existing functionality)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]  # Include milliseconds
        for i, joint_name in enumerate(self.joint_names):
            joint_pos = joint_positions[i]
            with open(self.log_file_paths[joint_name], 'a') as f:
                f.write(f"{current_time},{joint_pos[0]:.6f},{joint_pos[1]:.6f},{joint_pos[2]:.6f}\n")
        
        # NEW: Write comprehensive data to CSV for debugging
        self.frame_count += 1
        row_data = {
            'timestamp': current_time,
            'frame_count': self.frame_count,
            # All joint positions
            'LShoulder_x': joint_positions[0][0], 'LShoulder_y': joint_positions[0][1], 'LShoulder_z': joint_positions[0][2],
            'LElbow_x': joint_positions[1][0], 'LElbow_y': joint_positions[1][1], 'LElbow_z': joint_positions[1][2],
            'LHand_x': joint_positions[2][0], 'LHand_y': joint_positions[2][1], 'LHand_z': joint_positions[2][2],
            'RShoulder_x': joint_positions[3][0], 'RShoulder_y': joint_positions[3][1], 'RShoulder_z': joint_positions[3][2],
            'RElbow_x': joint_positions[4][0], 'RElbow_y': joint_positions[4][1], 'RElbow_z': joint_positions[4][2],
            'RHand_x': joint_positions[5][0], 'RHand_y': joint_positions[5][1], 'RHand_z': joint_positions[5][2],
            'Collar_x': joint_positions[6][0], 'Collar_y': joint_positions[6][1], 'Collar_z': joint_positions[6][2],
            'Torso_x': joint_positions[7][0], 'Torso_y': joint_positions[7][1], 'Torso_z': joint_positions[7][2],
            'Head_x': joint_positions[8][0], 'Head_y': joint_positions[8][1], 'Head_z': joint_positions[8][2],
            # Easy reference for hands and elbows
            'left_hand_x': left_hand_xyz[0], 'left_hand_y': left_hand_xyz[1], 'left_hand_z': left_hand_xyz[2],
            'right_hand_x': right_hand_xyz[0], 'right_hand_y': right_hand_xyz[1], 'right_hand_z': right_hand_xyz[2],
            'left_elbow_x': left_elbow_xyz[0], 'left_elbow_y': left_elbow_xyz[1], 'left_elbow_z': left_elbow_xyz[2],
            'right_elbow_x': right_elbow_xyz[0], 'right_elbow_y': right_elbow_xyz[1], 'right_elbow_z': right_elbow_xyz[2],
            # Table reference points
            'table_left_edge': self.table_left_edge,
            'table_right_edge': self.table_right_edge,
            'table_center_y': self.table_center_y,
            # Raw data for debugging
            'raw_data_length': len(data),
            'all_joint_data': str(joint_positions.flatten().tolist())
        }
        
        self.csv_writer.writerow(row_data)
        self.csv_file.flush()  # Ensure data is written immediately
        
        # Flatten the data for publishing (existing functionality)
        msg = Float32MultiArray()
        msg.data = joint_positions.flatten().tolist()
        
        self.publisher_.publish(msg)
        
        # Enhanced logging with debugging info
        self.get_logger().info(f'Frame {self.frame_count}: Published {len(msg.data)} joint values')
        self.get_logger().info(f'Left hand: ({left_hand_xyz[0]:.3f}, {left_hand_xyz[1]:.3f}, {left_hand_xyz[2]:.3f})')
        self.get_logger().info(f'Right hand: ({right_hand_xyz[0]:.3f}, {right_hand_xyz[1]:.3f}, {right_hand_xyz[2]:.3f})')
        self.get_logger().info(f'Table Y range: [{self.table_left_edge:.3f}, {self.table_right_edge:.3f}]')
        
        # Check if hands are at table edges for debugging
        if abs(left_hand_xyz[1] - self.table_left_edge) < 0.05:
            self.get_logger().warn(f'LEFT HAND NEAR LEFT EDGE: Y={left_hand_xyz[1]:.3f} (target: {self.table_left_edge:.3f})')
        if abs(right_hand_xyz[1] - self.table_right_edge) < 0.05:
            self.get_logger().warn(f'RIGHT HAND NEAR RIGHT EDGE: Y={right_hand_xyz[1]:.3f} (target: {self.table_right_edge:.3f})')

    def destroy_node(self):
        self.get_logger().info("Shutting down UDP client thread.")
        self.stop_event.set()
        self.receiver_thread.join()
        if hasattr(self, 'csv_file'):
            self.csv_file.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    human_motion_tracker_debug = HumanMotionTrackerDebug()
    try:
        rclpy.spin(human_motion_tracker_debug)
    except KeyboardInterrupt:
        pass
    finally:
        human_motion_tracker_debug.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
