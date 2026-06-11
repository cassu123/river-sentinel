#!/usr/bin/env python3
# River Sentinel - Autonomous Quadruped Security System

import rclpy
from rclpy.node import Node

from core.config import Config
from core.constants import CONTROL_LOOP_PERIOD_S, DEFAULT_NODE_NAME, VERSION
from core.orchestrator import RiverCore


class RiverSentinelCore(Node):
    def __init__(self):
        super().__init__(DEFAULT_NODE_NAME)
        self.config = Config()
        self.get_logger().info(f"Initializing River Sentinel Core v{VERSION}")
        self.get_logger().info(
            f"Unit ID: {self.config.unit_id} ({self.config.platform_type.value})"
        )

        self.core = RiverCore(self.config)
        self.create_timer(CONTROL_LOOP_PERIOD_S, self.main_loop)

    def main_loop(self):
        self.core.tick()
        if self.core.estop.is_triggered():
            self.get_logger().warning(
                f"E-Stop active: {self.core.estop.get_trigger_reason()}"
            )

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
