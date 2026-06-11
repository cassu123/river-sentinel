#!/usr/bin/env python3
# River Song Robotics Foundation - Shared Constants
#
# Values referenced across the safety, locomotion, navigation, and
# connectivity layers. Constants here apply to every River Song unit
# type unless a unit profile overrides them.

VERSION = "0.2.0"
DEFAULT_NODE_NAME = "river_sentinel_core"

# Control loop
CONTROL_LOOP_PERIOD_S = 0.02  # 50 Hz

# ROS Topics
TOPIC_IMU = "/sensor/imu"
TOPIC_GPS = "/sensor/gps"
TOPIC_BATTERY = "/sensor/battery"
TOPIC_GAIT_CMD = "/cmd/gait"
TOPIC_ESTOP = "/safety/estop"
TOPIC_ALERTS = "/telemetry/alerts"

# Safety thresholds
BATTERY_CRITICAL = 15.0
BATTERY_LOW = 25.0
GEOFENCE_LIMIT_M = 500.0
MIN_BOUNDARY_MARGIN_M = 5.0

# Locomotion
JOINT_MIN_DEG = -90.0
JOINT_MAX_DEG = 90.0
MAX_BALANCE_CORRECTION_DEG = 15.0
IMU_STALENESS_THRESHOLD_S = 0.5
IMU_RECOVERY_TIMEOUT_S = 10.0
DEGRADED_SPEED_FACTOR = 0.5

# Navigation
WAYPOINT_ARRIVAL_RADIUS_M = 1.5
BASE_ARRIVAL_RADIUS_M = 1.0
OBSTACLE_SAFE_DISTANCE_M = 2.0
GPS_REACQUIRE_TIMEOUT_S = 30.0

# Vision
PERSON_DETECTION_THRESHOLD = 0.6
PERSON_DWELL_TIMEOUT_S = 30.0

# Connectivity
HEARTBEAT_INTERVAL_S = 1.0
API_RETRY_COUNT = 3
VPN_MAX_RETRY_ATTEMPTS = 5
PICO_RECONNECT_ATTEMPTS = 3

# Telemetry
TELEMETRY_MAX_INTERVAL_S = 10.0
