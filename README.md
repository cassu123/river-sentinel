# River Sentinel

Autonomous Quadruped + Arm Security System based on ROS2 Humble, built as
the first reference implementation of the River Song robotics foundation.

## Overview
River Sentinel is a robust, autonomous security platform for free-roaming
quadruped robots (Spot-like, with a manipulator arm). It leverages ROS2
Humble for high-performance communication, featuring advanced navigation,
computer vision, manipulation, and safety systems.

River Sentinel is one of several robot/device programs in the River Song AI
ecosystem (riversongai.com). The `core/`, `safety/`, `connectivity/`, and
`telemetry/` layers are written to be **platform-agnostic**: a unit profile
(`units/*.json`) declares its `platform_type` and `capabilities`, and
`core/robot_factory.py` wires up the matching locomotion/manipulator plugins.
This lets the same foundation support other River Song unit types (wheeled,
tracked, aerial, arm-equipped chore robots, ...) without changes to the
safety or connectivity layers.

## Key Features
- **Autonomous Patrol:** Intelligent path planning and obstacle avoidance.
- **Quadruped Locomotion + Arm:** Advanced gait control, balance management, and manipulator control.
- **Safety First:** Integrated geofencing, E-Stop, and Watchdog systems.
- **Vision & Detection:** Real-time camera feeds and object detection.
- **Connectivity:** Cellular and VPN support for remote operations.
- **Return to Home (RTH):** Fail-safe return to base mechanism.

## Structure
- `core/`: Profile-driven orchestrator, shared data models (`models.py`), pluggable subsystem interfaces (`interfaces.py`), the platform plugin registry (`robot_factory.py`), configuration, and constants.
- `hardware/`: Drivers and interfaces for servos, IMU, camera, and battery.
- `locomotion/`: Gait control, balance algorithms, and manipulator (arm) control, selected per-platform via `core/robot_factory.py`.
- `navigation/`: Patrol planning, GPS management, and RTH logic.
- `safety/`: Geofence, E-Stop, watchdog, and fault management - platform-agnostic, boots first.
- `vision/`: Camera streaming and object detection.
- `telemetry/`: Data collection, logging, and alerts.
- `connectivity/`: Networking, cellular, and River Song API client.
- `units/`: Unit-specific configuration profiles (platform type, capabilities, geofence, calibration).

## Setup
1. Install ROS2 Humble.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the test suite:
   ```bash
   pytest
   ```
4. Launch the system:
   ```bash
   python3 core/main.py
   ```
