#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import numpy as np
import math


class HumanMotionTracker(Node):
    def __init__(self):
        super().__init__('human_motion_tracker')
        
        # Publisher for human measurements (3D points)
        self.publisher_ = self.create_publisher(Float32MultiArray, '/human_measurements', 10)
        
        # Timer to publish at 100Hz (faster than UDP version's 50Hz for better synchronization)
        self.timer = self.create_timer(0.01, self.publish_human_measurements)
        
        # Counter for generating varying dummy data
        self.counter = 0
        
        # Number of joints expected by safety shield (from config: 9 joints)
        self.n_joints = 9
        
        self.get_logger().info('Human Motion Tracker node started')
        self.get_logger().info(f'Publishing {self.n_joints} human 3D points at 100Hz')

    def publish_human_measurements(self):
        """Publish dummy human 3D point measurements"""
        msg = Float32MultiArray()
        
        # Generate dummy 3D points (x, y, z) for human body parts
        points = []
        for i in range(self.n_joints):
            # Create varying motion for each human body part
            # Simulate human body parts moving in 3D space
            x = 0.5 + 0.3 * math.sin(self.counter * 0.1 + i * 0.5)  # x: 0.2 to 0.8
            y = 0.0 + 0.4 * math.cos(self.counter * 0.1 + i * 0.3)  # y: -0.4 to 0.4
            z = 1.0 + 0.2 * math.sin(self.counter * 0.15 + i * 0.7)  # z: 0.8 to 1.2
            
            points.extend([x, y, z])
        
        msg.data = points
        
        # Publish the message
        self.publisher_.publish(msg)
        
        # Log every 100 messages (every 1 second at 100Hz)
        if self.counter % 100 == 0:
            # Format points for logging
            formatted_points = []
            for i in range(0, len(points), 3):
                formatted_points.append(f"({points[i]:.2f}, {points[i+1]:.2f}, {points[i+2]:.2f})")
            self.get_logger().info(f'Published {self.n_joints} human 3D points: {formatted_points}')
        
        self.counter += 1


def main(args=None):
    rclpy.init(args=args)
    
    human_motion_tracker = HumanMotionTracker()
    
    try:
        rclpy.spin(human_motion_tracker)
    except KeyboardInterrupt:
        pass
    
    human_motion_tracker.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
