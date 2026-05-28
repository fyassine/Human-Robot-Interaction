#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import json
import time
import os
import numpy as np

class MinimalPublisherJSON(Node):
    def __init__(self, json_file_path):
        super().__init__('minimal_publisher_json')
        self.publisher_ = self.create_publisher(Float32MultiArray, 'human_measurements', 10)
        
        if not os.path.exists(json_file_path):
            self.get_logger().error(f"JSON file not found at: {json_file_path}")
            return

        with open(json_file_path, 'r') as f:
            self.data = json.load(f)

        self.frame_idx = 0
        # Publish at 50 Hz, similar to the UDP publisher
        self.timer = self.create_timer(0.02, self.publish_frame)

    def publish_frame(self):
        if not self.data or self.frame_idx >= len(self.data):
            self.get_logger().info('End of JSON data. Looping.')
            self.frame_idx = 0
            if not self.data:
                return

        frame_dict = self.data[self.frame_idx]
        raw_data = frame_dict.get('data', [])

        if len(raw_data) < 38:
            self.get_logger().warn(
                f"Skipping frame {self.frame_idx + 1} — expected at least 38 values in 'data', got {len(raw_data)}"
            )
            self.frame_idx += 1
            return

        # Extract and process joint data (12 joints, xyz)
        joint_data = raw_data[2:2+36]
        try:
            measured_points = np.array(joint_data, dtype=float).reshape(12, 3)
        except (ValueError, TypeError) as e:
            self.get_logger().error(
                f"Could not process or reshape frame {self.frame_idx + 1}: {e}."
            )
            self.frame_idx += 1
            return

        msg = Float32MultiArray()
        msg.data = measured_points.flatten().tolist()
        
        self.publisher_.publish(msg)
        self.get_logger().info(f'Published frame {self.frame_idx + 1}/{len(self.data)} with {len(msg.data)} values.')
        self.frame_idx += 1

def main(args=None):
    rclpy.init(args=args)
    
    # Path to the JSON file relative to the script's location
    # This assumes the script is run from the project root
    json_file = 'captured_data/20250626_141831_armband1_vicon_data_unpacked.json'
    
    minimal_publisher_json = MinimalPublisherJSON(json_file)
    
    if minimal_publisher_json.data:
        try:
            rclpy.spin(minimal_publisher_json)
        except KeyboardInterrupt:
            pass
        finally:
            minimal_publisher_json.destroy_node()
            rclpy.shutdown()

if __name__ == '__main__':
    main()
