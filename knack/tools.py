"""Robot tools in OpenAI function-calling format, shared by the probe phase and the MCP server."""
from __future__ import annotations

import json

from .robot import MotionError
from .safety import RobotHalt

TOOL_SPECS = [
    {"type": "function", "function": {
        "name": "observe", "description": "Snapshot of the scene: gripper state, objects (centre positions, yaw, size, colour) and fixtures.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {
        "name": "get_pose", "description": "Pose of one object or fixture by name.",
        "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {
        "name": "move_to", "description": "Move the gripper tool point in a straight line to x, y, z (metres). Optional yaw (radians) of the finger closing direction and speed (m/s).",
        "parameters": {"type": "object", "properties": {
            "x": {"type": "number"}, "y": {"type": "number"}, "z": {"type": "number"},
            "yaw": {"type": "number"}, "speed": {"type": "number"}}, "required": ["x", "y", "z"]}}},
    {"type": "function", "function": {
        "name": "grasp", "description": "Close the fingers. Returns whether an object is held.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {
        "name": "release", "description": "Open the fingers.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {
        "name": "home", "description": "Move to a safe pose above the table.",
        "parameters": {"type": "object", "properties": {}, "required": []}}},
]


def dispatch(robot, name: str, args) -> dict:
    if isinstance(args, str):
        try:
            args = json.loads(args or "{}")
        except json.JSONDecodeError:
            return {"error": "arguments were not valid JSON"}
    args = args or {}
    try:
        if name == "observe":
            return robot.observe()
        if name == "get_pose":
            return robot.get_pose(str(args.get("name", "")))
        if name == "move_to":
            return robot.move_to(args.get("x"), args.get("y"), args.get("z"), yaw=args.get("yaw"), speed=args.get("speed"))
        if name == "grasp":
            return {"holding": robot.grasp()}
        if name == "release":
            robot.release()
            return {"ok": True}
        if name == "home":
            robot.home()
            return {"ok": True}
        return {"error": f"unknown tool {name}"}
    except (MotionError, KeyError) as e:
        return {"error": f"{type(e).__name__}: {e}"}
    except RobotHalt as e:
        return {"error": f"HALTED by safety layer: {e}", "halted": True}
