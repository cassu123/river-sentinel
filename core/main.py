#!/usr/bin/env python3
# River Sentinel - Autonomous Quadruped Security System

import rclpy
from rclpy.node import Node
from core.config import config
from core.constants import DEFAULT_NODE_NAME, VERSION

class RiverSentinelCore(Node):
    def __init__(self):
        super().__init__(DEFAULT_NODE_NAME)
        self.get_logger().info(f"Initializing River Sentinel Core v{VERSION}")
        self.get_logger().info(f"Unit ID: {config.unit_id}")
        
        # Initialize components (Placeholders for actual module integration)
        self.setup_subscribers()
        self.setup_publishers()
        self.create_timer(1.0, self.main_loop)

    def setup_subscribers(self):
        # Example subscriber
        # self.create_subscription(BatteryState, TOPIC_BATTERY, self.battery_callback, 10)
        pass

    def setup_publishers(self):
        # Example publisher
        # self.alert_pub = self.create_publisher(String, TOPIC_ALERTS, 10)
        pass

    def main_loop(self):
        self.get_logger().debug("Heartbeat - System Normal")

def main(args=None):
    rclpy.init(args=args)
    node = RiverSentinelCore()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("System shutting down...")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
