# Aurora Robotics Products

## NovaArm

NovaArm is a six-axis robotic arm developed by Aurora Robotics for warehouse
picking tasks. NovaArm is developed by the Manipulation Team. It uses
**PyTorch** for its grasp-detection models and relies on **ROS2** as its
underlying robotics middleware.

NovaArm was designed from the outset to handle irregular, unstructured
inventory rather than the fixed, pre-sorted items assumed by traditional
industrial arms. Each NovaArm unit is fitted with a wrist-mounted camera and
a force-sensing gripper, and its grasp-detection models, built with
PyTorch, are trained to estimate a stable grip point on an item before the
arm moves toward it. The Manipulation Team retrains these grasp-detection
models periodically as new item categories are added to a customer's
warehouse, using data collected from NovaArm units already deployed in the
field.

Under the hood, NovaArm communicates between its perception camera, grasp
planner, and motor controllers using ROS2, the same middleware used by
PathFinder. Standardizing on ROS2 across both products lets the
Manipulation Team and the Perception Team share tooling, message formats,
and debugging utilities, even though the two products serve different
functions on the robot.

## PathFinder

PathFinder is a navigation and mapping stack developed by the Perception
Team. It is used by Aurora Robotics' mobile platforms to move safely around
a warehouse floor. PathFinder uses **ROS2** for message passing between
components and uses **LiDAR Fusion**, a sensor-fusion technique combining
lidar and camera data, for obstacle detection.

PathFinder builds and continuously updates a map of the warehouse floor as
the mobile platform moves, combining data from a spinning lidar unit and a
forward-facing camera array. The LiDAR Fusion technique used by PathFinder
was developed in-house by the Perception Team specifically to handle the
narrow aisles and frequently rearranged shelving common in mid-sized
warehouses, where a purely camera-based or purely lidar-based system tends
to lose track of obstacles. PathFinder's obstacle-detection pipeline runs
locally on the mobile platform rather than relying on a cloud connection, so
that navigation continues to function even if a warehouse's network
connectivity is unreliable.

## AuroraBot-1

Both NovaArm and PathFinder are developed by Aurora Robotics and are used
together on the company's mobile picking robot, the AuroraBot-1. On the
AuroraBot-1, PathFinder handles navigation to a target shelving location
while NovaArm handles the actual picking of an item once the robot has
arrived. This combination lets a single AuroraBot-1 unit both move around a
warehouse and manipulate inventory, rather than requiring a separate fixed
picking station. Aurora Robotics considers the AuroraBot-1 its primary
product for the small and mid-sized warehouse customers described in the
company overview.

A typical AuroraBot-1 deployment starts with PathFinder mapping the
warehouse floor during an initial walkthrough, before any picking begins.
Once that map is built, a warehouse operator can queue picking tasks for
the AuroraBot-1 through a simple task list, and the robot alternates
between PathFinder-driven navigation to a shelving location and
NovaArm-driven picking once it arrives. Because both NovaArm and PathFinder
communicate over the same ROS2 middleware, the two subsystems can share
timing and coordinate handoffs, for example pausing navigation while
NovaArm completes a grasp, without a separate integration layer written
specifically for the AuroraBot-1 platform.

Aurora Robotics' product roadmap calls for a second-generation AuroraBot
that would extend the same NovaArm-plus-PathFinder architecture to taller
shelving units, which requires the Manipulation Team to design a longer-
reach variant of NovaArm and the Perception Team to extend PathFinder's
mapping to account for vertical obstacles as well as floor-level ones. Both
teams have described this as a natural extension of their existing work
rather than a new product line, since it reuses the same PyTorch
grasp-detection approach, the same ROS2 messaging layer, and the same LiDAR
Fusion technique already validated on the current AuroraBot-1.
