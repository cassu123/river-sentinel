#!/usr/bin/env python3
# River Sentinel - Autonomous Quadruped Security System

# System Constants
VERSION = "0.1.0"
DEFAULT_NODE_NAME = "river_sentinel_core"

# ROS Topics
TOPIC_IMU = "/sensor/imu"
TOPIC_GPS = "/sensor/gps"
TOPIC_BATTERY = "/sensor/battery"
TOPIC_GAIT_CMD = "/cmd/gait"
TOPIC_ESTOP = "/safety/estop"
TOPIC_ALERTS = "/telemetry/alerts"

# Safety Thresholds
BATTERY_CRITICAL = 15.0
GEOFENCE_LIMIT_M = 500.0

# Locomotion Modes
MODE_IDLE = 0
MODE_WALK = 1
MODE_TROT = 2
MODE_SIT = 3
MODE_STAND = 4

# Connectivity
HEARTBEAT_INTERVAL_S = 1.0
API_RETRY_COUNT = 3
