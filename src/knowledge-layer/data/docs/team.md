# Aurora Robotics Teams

Aurora Robotics' engineering organization is made up of two teams: the
Perception Team and the Manipulation Team. Both teams are part of Aurora
Robotics.

## Perception Team

The Perception Team is led by Maya Chen, who is also the company's CEO.
**Priya Nair** works at Aurora Robotics as a member of the Perception Team,
where she works on the PathFinder navigation stack.

The Perception Team is responsible for everything the AuroraBot-1 needs to
understand its surroundings: lidar processing, camera-based obstacle
detection, and the LiDAR Fusion technique used by PathFinder. Priya Nair
joined Aurora Robotics as one of the Perception Team's early engineers and
has focused primarily on PathFinder's mapping pipeline, tuning how the
system merges lidar and camera data as a warehouse's shelving layout
changes. She works closely with Maya Chen on evaluating PathFinder's
performance in new warehouse deployments before a customer's AuroraBot-1
units go into full production use.

Beyond PathFinder, the Perception Team also maintains the wrist-mounted
camera software used by NovaArm's grasp-detection models, since accurate
perception is a prerequisite for both navigation and manipulation. This
means the Perception Team, although organizationally distinct from the
Manipulation Team, contributes directly to NovaArm as well as PathFinder.

## Manipulation Team

The Manipulation Team is led by Diego Ortiz, who is also the company's CTO.
**Sam Okafor** works at Aurora Robotics as a member of the Manipulation
Team, where he works on the NovaArm robotic arm.

Sam Okafor joined Aurora Robotics after several years building end-effector
hardware at a warehouse automation supplier, and now focuses on NovaArm's
gripper design and the PyTorch-based grasp-detection models that decide how
NovaArm approaches an item. He works closely with Diego Ortiz on
retraining those grasp-detection models whenever a customer's warehouse
introduces new item categories that NovaArm has not encountered before, and
on validating that NovaArm's ROS2 messaging stays compatible with the
Perception Team's software as both products evolve.

Priya Nair and Sam Okafor both report to their respective team leads, Maya
Chen and Diego Ortiz, and both attend a weekly cross-team sync where the
Perception Team and the Manipulation Team coordinate on shared dependencies
such as ROS2 message formats and the wrist-mounted camera software used by
NovaArm.

## Hiring and growth

Both teams have grown steadily since Aurora Robotics' Series A round. The
Perception Team started as a single role held by Maya Chen alongside her
CEO responsibilities, and Priya Nair was one of the first dedicated
engineering hires added once PathFinder moved from an internal prototype to
a product used in real customer warehouses. The Manipulation Team followed
a similar path: Diego Ortiz handled early NovaArm prototyping himself, and
Sam Okafor was brought on once the Manipulation Team needed a dedicated
engineer focused specifically on gripper hardware and grasp-detection
models rather than splitting that work with CTO duties.

Aurora Robotics' leadership has said in planning discussions that future
hiring on both the Perception Team and the Manipulation Team will track
how many warehouse customers adopt the AuroraBot-1, since each new customer
deployment tends to surface new navigation edge cases for the Perception
Team and new item categories for the Manipulation Team's grasp-detection
models to learn.

## Cross-team dependencies

Because NovaArm and PathFinder share both ROS2 messaging and the
wrist-mounted camera software maintained by the Perception Team, the two
teams cannot fully plan their roadmaps in isolation. Maya Chen and Diego
Ortiz review upcoming Perception Team and Manipulation Team work together
each quarter specifically to catch cases where a planned PathFinder change,
such as a new LiDAR Fusion parameter, might affect NovaArm's camera-based
grasp detection, or where a planned NovaArm change might introduce a new
ROS2 message type that PathFinder's navigation stack would also need to
handle. Priya Nair and Sam Okafor are typically the first engineers to flag
this kind of cross-team dependency, since they are the ones most directly
touching PathFinder and NovaArm's respective codebases day to day.
