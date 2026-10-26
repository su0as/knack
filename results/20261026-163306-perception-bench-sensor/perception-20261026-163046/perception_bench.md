# OpenCV 5 perception benchmark (simulated RGB-D, ground truth from the simulator)

30 random layouts per scene. Static = first look, nothing occluded. In use = every look while the reference skill runs.
Sensor model: {'depth_sigma_at_1m': 0.004, 'depth_quant': 0.001, 'rgb_sigma': 4.0, 'calib_trans_m': 0.003, 'calib_rot_deg': 0.4} (depth noise grows with distance squared; extrinsic calibration error drawn once per episode).

| scene | static detection | median error | p90 error | max error | yaw error | fixtures | ms per look | in-use detection | in-use median error |
|---|---|---|---|---|---|---|---|---|---|
| lift | 100% | 4.29 mm | 7.35 mm | 9.17 mm | 0.26 deg | None mm | 174.1 | 100% of 120 | 4.05 mm |
| place | 100% | 4.25 mm | 7.05 mm | 8.86 mm | 0.34 deg | 3.15 mm | 190.0 | 100% of 120 | 3.6 mm |
| push | 100% | 4.3 mm | 8.62 mm | 9.41 mm | None deg | 3.75 mm | 178.3 | 97% of 145 | 3.56 mm |
| stack | 100% | 4.29 mm | 7.35 mm | 9.17 mm | 0.26 deg | None mm | 179.7 | 100% of 120 | 4.05 mm |
| tray | 100% | 4.29 mm | 7.28 mm | 8.94 mm | 0.48 deg | 3.1 mm | 177.1 | 100% of 120 | 3.71 mm |
| sort | 100% | 4.51 mm | 7.4 mm | 9.89 mm | 0.37 deg | 3.38 mm | 186.5 | 99% of 238 | 3.92 mm |
