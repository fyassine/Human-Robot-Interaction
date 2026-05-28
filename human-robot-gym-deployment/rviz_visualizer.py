#!/usr/bin/env python3
"""This script creates a ROS2 node to visualize human motion data from a UDP stream in RViz.

It receives data using the ClientCat utility, processes the joint data, and publishes
visualization_msgs/MarkerArray messages to the /human_markers topic.
"""

import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
import numpy as np
import threading
import time

# Assuming communi_cat is in the same project directory
from communi_cat.client_cat import ClientCat

# Define the connections between joints to draw the skeleton
# Based on common human skeleton structures
BONE_CONNECTIONS = [
    ('rShoulder', 'rElbow'), ('rElbow', 'rHand'),
    ('lShoulder', 'lElbow'), ('lElbow', 'lHand'),
    ('Collar', 'rShoulder'), ('Collar', 'lShoulder'),
    ('Collar', 'Torso'), ('Collar', 'Head')
]

HUMAN_JOINT_NAMES = [
    "lShoulder", "lElbow", "lHand", "rShoulder", "rElbow", "rHand", "Collar", "Torso", "Head"
]

# Create a mapping from joint name to index
JOINT_MAP = {name: i for i, name in enumerate(HUMAN_JOINT_NAMES)}


def data_receiver(client):
    """Threaded function to continuously receive UDP data."""
    while rclpy.ok():
        client.receive_data()
        time.sleep(0.001) # Small sleep to prevent busy-waiting
    client.stop()

class RvizVisualizerNode(Node):
    def __init__(self, client):
        super().__init__('rviz_visualizer_node')
        self.client = client
        self.publisher_ = self.create_publisher(MarkerArray, 'human_markers', 10)
        self.timer = self.create_timer(0.02, self.publish_markers) # 50Hz
        self.get_logger().info('RViz visualizer node started. Publishing to /human_markers.')

    def publish_markers(self):
        if not self.client.data:
            return

        data = self.client.data[-1]

        if len(data) < 2 + 36:
            self.get_logger().warn(f"Skipping frame — expected at least 38 values, got {len(data)}")
            return

        joint_data = data[2:2+36]  # Skip first 2 values
        try:
            points = np.array(joint_data).reshape(9, 4)[:, :3] # Use only x, y, z
        except ValueError as e:
            self.get_logger().error(f"Could not reshape joint data: {e}")
            return

        marker_array = MarkerArray()
        now = self.get_clock().now().to_msg()

        # Create sphere markers for joints
        for i, point in enumerate(points):
            marker = Marker()
            marker.header.frame_id = "world" # Adjust this frame_id if needed
            marker.header.stamp = now
            marker.ns = "joints"
            marker.id = i
            marker.type = Marker.SPHERE
            marker.action = Marker.ADD
            marker.pose.position.x = point[0]
            marker.pose.position.y = point[1]
            marker.pose.position.z = point[2]
            marker.pose.orientation.w = 1.0
            marker.scale.x = 0.05
            marker.scale.y = 0.05
            marker.scale.z = 0.05
            marker.color.a = 1.0
            marker.color.r = 0.0
            marker.color.g = 1.0
            marker.color.b = 0.0
            marker_array.markers.append(marker)

        # Create line strip markers for bones
        bone_id_counter = 0
        for joint1_name, joint2_name in BONE_CONNECTIONS:
            marker = Marker()
            marker.header.frame_id = "world"
            marker.header.stamp = now
            marker.ns = "bones"
            marker.id = bone_id_counter
            bone_id_counter += 1
            marker.type = Marker.LINE_STRIP
            marker.action = Marker.ADD
            marker.pose.orientation.w = 1.0
            marker.scale.x = 0.02 # Line width
            marker.color.a = 1.0
            marker.color.r = 1.0
            marker.color.g = 0.0
            marker.color.b = 0.0

            p1_idx = JOINT_MAP[joint1_name]
            p2_idx = JOINT_MAP[joint2_name]

            p1 = Point()
            p1.x, p1.y, p1.z = points[p1_idx]
            p2 = Point()
            p2.x, p2.y, p2.z = points[p2_idx]

            marker.points.append(p1)
            marker.points.append(p2)

            marker_array.markers.append(marker)

        self.publisher_.publish(marker_array)

def main(args=None):
    rclpy.init(args=args)

    # Start the UDP client
    client = ClientCat()
    client.start()
    receiver_thread = threading.Thread(target=data_receiver, args=(client,))
    receiver_thread.daemon = True
    receiver_thread.start()

    node = RvizVisualizerNode(client)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
