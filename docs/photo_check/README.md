# Photoreal stress test of the OpenCV 5 colour pipeline

**These six images are AI-generated (photorealistic), not real camera captures.** They test whether the colour
pipeline tuned on simulator renders survives photo-like conditions: light-brown wood (hue close to red and orange),
plastic glare, warm and dim light, hard shadow, distractors, touching objects and a gripper covering a cube.
Ground-truth counts in `truth.json` were labelled by eye.

Run (on the AWS instance, OpenCV 5.0.0, arm64):

    python -m knack.photo_check docs/photo_check/images docs/photo_check/output --truth docs/photo_check/truth.json

Result with the simulator's HSV ranges unchanged: 23 of 24 objects found, no false detections. Small blobs from a pink
pencil eraser and a blue cable were rejected by size gating. Miss: a navy cube deep in a hard shadow (too dark for the
value threshold), which the pipeline reports as missing rather than guessing. Image-space detection only: no depth and
no calibration, so no metric error is claimed. A real-camera check on a physical setup is still outstanding.
