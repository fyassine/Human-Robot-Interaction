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

# Threaded UDP data receiving
def data_receiver(client, stop_event):
    while not stop_event.is_set():
        client.receive_data()
    client.stop()

class HumanMotionTracker(Node):
    def __init__(self):
        super().__init__('human_motion_tracker')
        self.publisher_ = self.create_publisher(Float32MultiArray, 'human_measurements', 10)
        
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
        timer_period = 0.01  # 100 Hz
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
        
        # Apply offset to bring all joints to table level (z=0)
        joint_positions[:, 2]+= 0.185
        
        # Flatten the data for publishing
        msg = Float32MultiArray()
        msg.data = joint_positions.flatten().tolist()
        
        self.publisher_.publish(msg)
        #self.get_logger().info(f'Published {len(msg.data)} joint values.')
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
