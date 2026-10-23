"""Static checks and restricted execution for AI-written skill code.

This is a guardrail, not a security boundary: an AST allowlist, restricted
builtins, an import allowlist, process isolation (runner.py) and a wall-clock
kill. Run untrusted code in a container (as the Nebius job runner does).
"""
from __future__ import annotations

import ast
import builtins
import linecache
import traceback

ALLOWED_MODULES = {"math", "numpy", "itertools", "functools", "collections"}
FORBIDDEN_NAMES = {
    "open", "exec", "eval", "compile", "__import__", "globals", "locals", "vars",
    "getattr", "setattr", "delattr", "input", "breakpoint", "exit", "quit", "help",
    "memoryview", "object", "type", "super", "classmethod", "staticmethod", "property",
    "BaseException", "RobotHalt", "SafetyViolation", "EpisodeTimeout", "KeyboardInterrupt", "SystemExit",
}
FORBIDDEN_ATTRS = {
    "load", "save", "savez", "savez_compressed", "fromfile", "tofile", "loadtxt", "savetxt",
    "genfromtxt", "memmap", "ctypeslib", "f2py", "testing", "distutils", "lib", "system",
}
SAFE_BUILTINS = [
    "abs", "all", "any", "bool", "dict", "divmod", "enumerate", "filter", "float", "frozenset",
    "int", "isinstance", "iter", "len", "list", "map", "max", "min", "next", "pow", "range",
    "repr", "reversed", "round", "set", "slice", "sorted", "str", "sum", "tuple", "zip", "hasattr",
    "Exception", "ValueError", "RuntimeError", "KeyError", "IndexError", "TypeError",
    "ZeroDivisionError", "StopIteration", "AssertionError", "ArithmeticError", "LookupError",
    "NotImplementedError", "True", "False", "None",
]
MAX_CODE_CHARS = 24_000
SKILL_FILENAME = "skill.py"


class SkillCompileError(Exception):
    pass


def validate(code: str) -> list[str]:
    """Return a list of problems (empty if the code is acceptable)."""
    problems: list[str] = []
    if len(code) > MAX_CODE_CHARS:
        problems.append(f"code is {len(code)} characters; limit is {MAX_CODE_CHARS}")
    try:
        tree = ast.parse(code, filename=SKILL_FILENAME)
    except SyntaxError as e:
        return [f"SyntaxError at line {e.lineno}: {e.msg}"]
    has_run = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_MODULES:
                    problems.append(f"line {node.lineno}: import of '{a.name}' is not allowed (allowed: {sorted(ALLOWED_MODULES)})")
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if node.level or mod not in ALLOWED_MODULES:
                problems.append(f"line {node.lineno}: import from '{node.module}' is not allowed")
        elif isinstance(node, ast.Name):
            if node.id in FORBIDDEN_NAMES or node.id.startswith("__"):
                problems.append(f"line {node.lineno}: use of '{node.id}' is not allowed")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                problems.append(f"line {node.lineno}: access to private attribute '.{node.attr}' is not allowed")
            elif node.attr in FORBIDDEN_ATTRS:
                problems.append(f"line {node.lineno}: '.{node.attr}' is not allowed")
        elif isinstance(node, ast.ExceptHandler):
            if node.type is None:
                problems.append(f"line {node.lineno}: bare 'except:' is not allowed; catch Exception (safety halts must propagate)")
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            pass
        elif isinstance(node, ast.FunctionDef) and node.name == "run" and node in tree.body:
            if len(node.args.args) >= 1:
                has_run = True
        elif isinstance(node, (ast.AsyncFunctionDef, ast.Await, ast.AsyncFor, ast.AsyncWith)):
            problems.append(f"line {node.lineno}: async code is not allowed")
    if not has_run:
        problems.append("the code must define a top-level function `def run(robot):`")
    return problems


def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level or name.split(".")[0] not in ALLOWED_MODULES:
        raise ImportError(f"import of '{name}' is not allowed")
    return builtins.__import__(name, globals, locals, fromlist, level)


def compile_skill(code: str, printer=None):
    """Validate, compile and exec the skill module; return its run() function."""
    problems = validate(code)
    if problems:
        raise SkillCompileError("; ".join(problems[:8]))
    safe = {n: getattr(builtins, n) for n in SAFE_BUILTINS if hasattr(builtins, n)}
    safe["__import__"] = _guarded_import
    safe["__build_class__"] = builtins.__build_class__
    safe["print"] = printer or (lambda *a, **k: None)
    g = {"__builtins__": safe, "__name__": "skill"}
    linecache.cache[SKILL_FILENAME] = (len(code), None, code.splitlines(True), SKILL_FILENAME)
    try:
        exec(compile(code, SKILL_FILENAME, "exec"), g)  # noqa: S102 - restricted globals, validated AST
    except Exception as e:
        raise SkillCompileError(f"error while loading the skill module: {type(e).__name__}: {e}") from e
    fn = g.get("run")
    if not callable(fn):
        raise SkillCompileError("run is not callable")
    return fn


def skill_traceback(exc: BaseException, limit_lines: int = 14) -> str:
    """Traceback restricted to frames inside the skill plus the exception line."""
    frames = traceback.extract_tb(exc.__traceback__)
    lines = []
    for fr in frames:
        if fr.filename == SKILL_FILENAME:
            lines.append(f'  skill.py line {fr.lineno}, in {fr.name}: {(fr.line or "").strip()}')
    lines.append(f"{type(exc).__name__}: {exc}")
    return "\n".join(lines[-limit_lines:])


def extract_code(text: str) -> str | None:
    """Pull the last ```python fenced block (or a bare module containing def run) out of an LLM reply."""
    import re

    blocks = re.findall(r"```(?:python|py)?[ \t]*\n(.*?)```", text, flags=re.S)
    blocks = [b for b in blocks if "def run" in b]
    if blocks:
        return blocks[-1].strip() + "\n"
    if "def run(" in text:
        start = text.find("import ") if "import " in text[: text.find("def run(")] else text.find("def run(")
        return text[start:].strip() + "\n"
    return None
