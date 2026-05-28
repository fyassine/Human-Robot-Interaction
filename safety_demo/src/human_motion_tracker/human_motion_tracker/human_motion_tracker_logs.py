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

# Threaded UDP data receiving
def data_receiver(client, stop_event):
    while not stop_event.is_set():
        client.receive_data()
    client.stop()

class HumanMotionTracker(Node):
    def __init__(self):
        super().__init__('human_motion_tracker')
        self.publisher_ = self.create_publisher(Float32MultiArray, 'human_measurements', 10)
        
        # Setup log files for all body parts
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Joint names in order (matching the joint mapping)
        self.joint_names = ["LShoulder", "LElbow", "LHand", "RShoulder", "RElbow", "RHand", "Collar", "Torso", "Head"]
        
        # Create separate log files for each joint
        self.log_file_paths = {}
        for joint_name in self.joint_names:
            file_path = os.path.join(log_dir, f'{joint_name}_position_{timestamp}.txt')
            self.log_file_paths[joint_name] = file_path
            
            # Write header to each log file
            with open(file_path, 'w') as f:
                f.write("timestamp,x,y,z\n")
        
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
        
        # Extract right hand coordinates (index 5 in the joint mapping)
        right_hand_xyz = joint_positions[5]  # [x, y, z]
        x, y, z = right_hand_xyz
        
        # Log all body parts positions to their respective files
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]  # Include milliseconds
        for i, joint_name in enumerate(self.joint_names):
            joint_pos = joint_positions[i]
            with open(self.log_file_paths[joint_name], 'a') as f:
                f.write(f"{current_time},{joint_pos[0]:.6f},{joint_pos[1]:.6f},{joint_pos[2]:.6f}\n")
        
        # Flatten the data for publishing
        msg = Float32MultiArray()
        msg.data = joint_positions.flatten().tolist()
        
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published {len(msg.data)} joint values. Right hand: ({x:.3f}, {y:.3f}, {z:.3f})')
       #self.get_logger().info(f'Measurements: {msg.data}')

    def destroy_node(self):
        self.get_logger().info("Shutting down UDP client thread.")
        self.stop_event.set()
        self.receiver_thread.join()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = HumanMotionTracker()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
