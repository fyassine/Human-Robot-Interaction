#!/usr/bin/env python3
"""
CSV Motion Data Replay Node
Replays motion capture data from CSV files for testing and debugging
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
import csv
import time
import ast
import os


class MotionDataReplayNode(Node):
    def __init__(self):
        super().__init__('motion_data_replay')
        self.publisher_ = self.create_publisher(Float32MultiArray, 'human_measurements', 10)
        
        # Declare parameters
        self.declare_parameter('scenario', '')
        self.declare_parameter('speed', 1.0)

        # Get parameters
        scenario_name = self.get_parameter('scenario').get_parameter_value().string_value
        self.replay_speed = self.get_parameter('speed').get_parameter_value().double_value

        # Determine CSV file path
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        if scenario_name:
            self.csv_file_path = os.path.join(log_dir, f"{scenario_name}.csv")
            self.get_logger().info(f'Replaying scenario: {scenario_name}')
        else:
            self.get_logger().info('No scenario specified. Finding the latest CSV file...')
            csv_files = [f for f in os.listdir(log_dir) if f.endswith('.csv')]
            if not csv_files:
                self.get_logger().error('No CSV files found in the logs directory.')
                return
            latest_file = max(csv_files, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
            self.csv_file_path = os.path.join(log_dir, latest_file)
            self.get_logger().info(f'Using latest file: {self.csv_file_path}')
        self.motion_data = []
        
        # Load CSV data
        self.load_csv_data()
        
        # Setup timer for replay
        if self.motion_data:
            timer_period = 0.02 / self.replay_speed  # Adjust speed
            self.timer = self.create_timer(timer_period, self.replay_next_frame)
            self.current_frame = 0
            self.start_time = time.time()
            self.get_logger().info(f'Loaded {len(self.motion_data)} frames from {self.csv_file_path}')
            self.get_logger().info(f'Replay speed: {self.replay_speed}x')
        else:
            self.get_logger().error('No motion data loaded!')
    
    def load_csv_data(self):
        """Load motion data from CSV file"""
        try:
            with open(self.csv_file_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Parse the joint data from string representation
                    joint_data_str = row.get('all_joint_data', '')
                    if joint_data_str:
                        try:
                            joint_data = ast.literal_eval(joint_data_str)
                            frame_data = {
                                'timestamp': row['timestamp'],
                                'frame_count': int(row['frame_count']),
                                'joint_data': joint_data,
                                'left_hand': [float(row['left_hand_x']), float(row['left_hand_y']), float(row['left_hand_z'])],
                                'right_hand': [float(row['right_hand_x']), float(row['right_hand_y']), float(row['right_hand_z'])],
                                'left_elbow': [float(row['left_elbow_x']), float(row['left_elbow_y']), float(row['left_elbow_z'])],
                                'right_elbow': [float(row['right_elbow_x']), float(row['right_elbow_y']), float(row['right_elbow_z'])]
                            }
                            self.motion_data.append(frame_data)
                        except (ValueError, SyntaxError) as e:
                            self.get_logger().warn(f'Could not parse joint data for frame {row.get("frame_count", "unknown")}: {e}')
        except Exception as e:
            self.get_logger().error(f'Failed to load CSV file {self.csv_file_path}: {e}')
    
    def replay_next_frame(self):
        """Replay the next frame of motion data"""
        if self.current_frame >= len(self.motion_data):
            self.get_logger().info('Replay completed!')
            self.timer.cancel()
            return
        
        frame_data = self.motion_data[self.current_frame]
        
        # Create and publish the message
        msg = Float32MultiArray()
        msg.data = frame_data['joint_data']
        self.publisher_.publish(msg)
        
        # Log replay info
        left_hand = frame_data['left_hand']
        right_hand = frame_data['right_hand']
        elapsed_time = time.time() - self.start_time
        
        self.get_logger().info(f'Replay frame {self.current_frame+1}/{len(self.motion_data)} '
                              f'(elapsed: {elapsed_time:.1f}s)')
        self.get_logger().info(f'Left hand: ({left_hand[0]:.3f}, {left_hand[1]:.3f}, {left_hand[2]:.3f})')
        self.get_logger().info(f'Right hand: ({right_hand[0]:.3f}, {right_hand[1]:.3f}, {right_hand[2]:.3f})')
        
        self.current_frame += 1

def main(args=None):
    rclpy.init(args=args)
    node = MotionDataReplayNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
