# River Sentinel

Autonomous Quadruped Security System based on ROS2 Humble.

## Overview
River Sentinel is a robust, autonomous security platform designed for quadruped robots. It leverages ROS2 Humble for high-performance communication, featuring advanced navigation, computer vision, and safety systems.

## Key Features
- **Autonomous Patrol:** Intelligent path planning and obstacle avoidance.
- **Quadruped Locomotion:** Advanced gait control and balance management.
- **Safety First:** Integrated geofencing, E-Stop, and Watchdog systems.
- **Vision & Detection:** Real-time camera feeds and object detection.
- **Connectivity:** Cellular and VPN support for remote operations.
- **Return to Home (RTH):** Fail-safe return to base mechanism.

## Structure
- `core/`: System core, configuration, and constants.
- `hardware/`: Drivers and interfaces for servos, IMU, camera, and battery.
- `locomotion/`: Gait control and balance algorithms.
- `navigation/`: Patrol planning, GPS management, and RTH logic.
- `safety/`: Geofence, fault management, and emergency systems.
- `vision/`: Camera streaming and object detection.
- `telemetry/`: Data collection, logging, and alerts.
- `connectivity/`: Networking, cellular, and API clients.
- `units/`: Unit-specific configuration profiles.

## Setup
1. Install ROS2 Humble.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the system:
   ```bash
   python3 core/main.py
   ```
