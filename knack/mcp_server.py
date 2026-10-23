"""MCP server exposing the Knack robot tools (stdio).

Any MCP client (Claude Code, an IDE agent, or a Nemotron agent framework) can
drive the simulated arm through the same safety shield the skills use:

    knack mcp --task stack --seed 3

Client config example:
    {"mcpServers": {"knack": {"command": "knack", "args": ["mcp", "--task", "lift"]}}}

Needs: pip install "knack[mcp]".
"""
# No `from __future__ import annotations` here: FastMCP reads the real annotation objects.


def main(task: str = "lift", seed: int = 0) -> int:
    try:
        from mcp.server.fastmcp import FastMCP, Image
    except ImportError:
        print("The MCP SDK is not installed: pip install \"knack[mcp]\"")
        return 1
    from .recorder import encode_jpeg
    from .robot import SimRobot
    from .sim import SimEnv
    from .tasks import get_task
    from .tools import dispatch

    state = {"env": None, "robot": None, "task": get_task(task), "seed": seed}

    def _reset(task_id: str | None = None, seed_: int | None = None):
        if state["env"] is not None:
            state["env"].close()
        if task_id:
            state["task"] = get_task(task_id)
        if seed_ is not None:
            state["seed"] = int(seed_)
        state["env"] = SimEnv(state["task"], state["seed"])
        state["robot"] = SimRobot(state["env"], max_time=10_000.0)

    _reset()
    mcp = FastMCP("knack-robot")

    @mcp.tool()
    def reset(task_id: str = "", seed: int = -1) -> dict:
        """Start a fresh randomised scene. task_id: lift|place|push|stack|tray|sort."""
        _reset(task_id or None, seed if seed >= 0 else None)
        return {"task": state["task"].id, "instruction": state["task"].instruction, "seed": state["seed"]}

    @mcp.tool()
    def observe() -> dict:
        """Gripper state, objects and fixtures (metres, radians)."""
        return dispatch(state["robot"], "observe", {})

    @mcp.tool()
    def get_pose(name: str) -> dict:
        """Pose of one object or fixture."""
        return dispatch(state["robot"], "get_pose", {"name": name})

    @mcp.tool()
    def move_to(x: float, y: float, z: float, yaw: float | None = None, speed: float | None = None) -> dict:
        """Move the tool point in a straight line (through the safety shield)."""
        return dispatch(state["robot"], "move_to", {"x": x, "y": y, "z": z, "yaw": yaw, "speed": speed})

    @mcp.tool()
    def grasp() -> dict:
        """Close the fingers; reports whether something is held."""
        return dispatch(state["robot"], "grasp", {})

    @mcp.tool()
    def release() -> dict:
        """Open the fingers."""
        return dispatch(state["robot"], "release", {})

    @mcp.tool()
    def home() -> dict:
        """Safe pose above the table."""
        return dispatch(state["robot"], "home", {})

    @mcp.tool()
    def check_success() -> dict:
        """Ground-truth check for the current task (simulation only)."""
        ok, metrics = state["task"].success(state["env"])
        return {"success": ok, "metrics": metrics}

    @mcp.tool()
    def camera(view: str = "front") -> Image:
        """Camera frame: front | side | overhead."""
        img = state["env"].render(view, (480, 360))
        if img is None:
            raise RuntimeError(f"rendering unavailable: {state['env'].render_error}")
        return Image(data=encode_jpeg(img), format="jpeg")

    mcp.run()
    return 0
