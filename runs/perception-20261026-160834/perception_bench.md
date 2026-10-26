# OpenCV 5 perception benchmark (simulated RGB-D, ground truth from the simulator)

30 random layouts per scene. Static = first look, nothing occluded. In use = every look while the reference skill runs.

| scene | static detection | median error | p90 error | max error | yaw error | fixtures | ms per look | in-use detection | in-use median error |
|---|---|---|---|---|---|---|---|---|---|
| lift | 100% | 0.02 mm | 0.09 mm | 0.27 mm | 0.0 deg | None mm | 238.9 | 100% of 120 | 0.03 mm |
| place | 100% | 0.02 mm | 0.09 mm | 0.2 mm | 0.0 deg | 1.33 mm | 247.5 | 100% of 120 | 0.03 mm |
| push | 100% | 0.29 mm | 1.65 mm | 7.85 mm | None deg | 1.45 mm | 240.2 | 96% of 154 | 0.4 mm |
| stack | 100% | 0.02 mm | 0.09 mm | 0.27 mm | 0.0 deg | None mm | 233.6 | 100% of 120 | 0.03 mm |
| tray | 100% | 0.02 mm | 0.1 mm | 0.16 mm | 0.0 deg | 6.28 mm | 247.5 | 100% of 120 | 0.04 mm |
| sort | 100% | 0.03 mm | 0.08 mm | 0.36 mm | 0.0 deg | 6.67 mm | 255.7 | 99% of 238 | 0.04 mm |
