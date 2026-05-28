#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray

class MinimalPublisher(Node):
    def __init__(self):
        super().__init__('minimal_publisher')
        self.publisher_ = self.create_publisher(Float32MultiArray, 'human_measurements', 10)
        timer_period = 1.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0.0

    def timer_callback(self):
        msg = Float32MultiArray()
        msg.data = [self.i, self.i + 1.0, self.i + 2.0]
        self.publisher_.publish(msg)
        self.get_logger().info('Publishing: "%s"' % str(list(msg.data)))
        self.i += 1.0

def main(args=None):
    rclpy.init(args=args)

    minimal_publisher = MinimalPublisher()

    try:
        rclpy.spin(minimal_publisher)
    except KeyboardInterrupt:
        pass
    finally:
        minimal_publisher.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
