"""Nebius AI Cloud Serverless Jobs backend (PAID: not covered by Token Factory credits).

Each practice round becomes one CPU job: the container installs Knack, runs all
episodes of the round in parallel on the VM's vCPUs, and writes results into an
Object Storage bucket mounted at /data. The local agent polls the job, downloads
the results and books the compute cost on the receipt.

Prerequisites (one time):
  1. Install and log in to the Nebius CLI:  https://docs.nebius.com/cli/install
  2. Create an Object Storage bucket and an access key; put the key in an AWS profile
     (~/.aws/credentials) so both `nebius ai job create --volume s3://...` and boto3 can use it.
  3. pip install "knack[nebius]"   (adds boto3)
  4. Set KNACK_NEBIUS_BUCKET (and optionally the other KNACK_NEBIUS_* vars below).
Then smoke-test with `knack nebius hello` before running real rounds.

Prices: cpu-d3 (AMD EPYC Genoa) from 1 Oct 2026, $0.015 per vCPU-hour and $0.0045 per
GiB-hour of RAM (docs.nebius.com/compute/resources/pricing). Override with env vars.
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import tarfile
import time
from pathlib import Path

TERMINAL = ("COMPLETED", "SUCCEEDED", "FAILED", "CANCELLED", "CANCELED", "ERROR", "DELETED")


def _env(name: str, default=None):
    v = os.environ.get(name)
    return v if v not in (None, "") else default


def _find_cli() -> str:
    exe = shutil.which("nebius") or shutil.which("nebius.exe")
    if not exe:
        home = Path.home() / ".nebius" / "bin" / "nebius"
        if home.exists():
            exe = str(home)
    if not exe:
        raise RuntimeError("Nebius CLI not found. Install it: https://docs.nebius.com/cli/install")
    return exe


def _cli(args: list, check: bool = True) -> str:
    p = subprocess.run([_find_cli(), *args], capture_output=True, text=True, timeout=600)
    if check and p.returncode != 0:
        raise RuntimeError(f"nebius {' '.join(args[:3])} failed: {p.stderr.strip()[:1500]}")
    return p.stdout


def _walk(obj, keys):
    """Yield values for any of `keys` found anywhere in nested JSON."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in keys and isinstance(v, (str, int, float)):
                yield v
            yield from _walk(v, keys)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v, keys)


def preset_resources(preset: str) -> tuple[int, int]:
    m = re.match(r"(?:\d+gpu-)?(\d+)vcpu-(\d+)gb", preset)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def source_tarball() -> bytes:
    """Tar.gz of the knack package + pyproject so the job can `pip install` it (works for private repos)."""
    root = Path(__file__).resolve().parent.parent
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for rel in ("pyproject.toml", "README.md", "LICENSE"):
            if (root / rel).exists():
                tar.add(root / rel, arcname=f"knack-src/{rel}")
        pkg = root / "knack"

        def _filter(ti):
            return None if "__pycache__" in ti.name or ti.name.endswith(".pyc") else ti

        tar.add(pkg, arcname="knack-src/knack", filter=_filter)
    return buf.getvalue()


JOB_SCRIPT = """#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq && apt-get install -y -qq libosmesa6 libgl1 >/dev/null
mkdir -p /tmp/src && tar -xzf "{data}/{prefix}knack-src.tar.gz" -C /tmp/src
pip install -q --no-cache-dir "/tmp/src/knack-src"
export MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa
python -m knack.worker --batch "{data}/{prefix}batch.json" --out "{data}/{prefix}results" --workers "$(nproc)"
"""


class NebiusJobRunner:
    name = "nebius"

    def __init__(self, bucket: str, run_id: str, *, platform: str = "cpu-d3", preset: str = "16vcpu-64gb",
                 image: str = "python:3.12-slim", subnet_id: str | None = None, s3_endpoint: str | None = None,
                 s3_region: str = "eu-north1", aws_profile: str = "default", vcpu_hour_usd: float = 0.015,
                 gb_hour_usd: float = 0.0045, poll_s: float = 10.0, timeout: str = "1h", disk: str = "30Gi"):
        self.bucket = bucket
        self.run_id = run_id
        self.platform = platform
        self.preset = preset
        self.image = image
        self.subnet_id = subnet_id
        self.s3_endpoint = s3_endpoint or f"https://storage.{s3_region}.nebius.cloud"
        self.s3_region = s3_region
        self.aws_profile = aws_profile
        self.vcpu_hour_usd = vcpu_hour_usd
        self.gb_hour_usd = gb_hour_usd
        self.poll_s = poll_s
        self.timeout = timeout
        self.disk = disk
        self.compute_seconds = 0.0
        self.last_batch_usd = 0.0
        self.jobs: list[dict] = []

    @classmethod
    def from_env(cls, run_id: str) -> "NebiusJobRunner":
        bucket = _env("KNACK_NEBIUS_BUCKET")
        if not bucket:
            raise RuntimeError("Set KNACK_NEBIUS_BUCKET (an Object Storage bucket) to use --backend nebius. See knack/nebius.py.")
        return cls(bucket, run_id,
                   platform=_env("KNACK_NEBIUS_PLATFORM", "cpu-d3"), preset=_env("KNACK_NEBIUS_PRESET", "16vcpu-64gb"),
                   image=_env("KNACK_NEBIUS_IMAGE", "python:3.12-slim"), subnet_id=_env("KNACK_NEBIUS_SUBNET"),
                   s3_endpoint=_env("KNACK_S3_ENDPOINT"), s3_region=_env("KNACK_S3_REGION", "eu-north1"),
                   aws_profile=_env("AWS_PROFILE", "default"),
                   vcpu_hour_usd=float(_env("KNACK_NEBIUS_VCPU_HOUR_USD", 0.015)),
                   gb_hour_usd=float(_env("KNACK_NEBIUS_GB_HOUR_USD", 0.0045)))

    # ---- storage ----
    def _s3(self):
        import boto3

        session = boto3.session.Session(profile_name=self.aws_profile) if self.aws_profile else boto3.session.Session()
        return session.client("s3", endpoint_url=self.s3_endpoint, region_name=self.s3_region)

    def usd_for(self, seconds: float) -> float:
        vcpu, gb = preset_resources(self.preset)
        return seconds / 3600.0 * (vcpu * self.vcpu_hour_usd + gb * self.gb_hour_usd)

    # ---- jobs ----
    def create_job(self, name: str, script: str, inject: dict | None = None) -> str:
        """inject: {container_path: local_path} for small files (<= 64 KiB each)."""
        tmpdir = Path(os.environ.get("KNACK_TMP", ".knack_tmp"))
        tmpdir.mkdir(exist_ok=True)
        script_path = tmpdir / f"{name}.sh"
        script_path.write_text(script, encoding="utf-8", newline="\n")
        args = ["ai", "job", "create", "--name", name, "--image", self.image,
                "--container-command", "bash", "--args", "/workspace/run.sh",
                "--platform", self.platform, "--preset", self.preset, "--timeout", self.timeout,
                "--disk-size", self.disk, "--restart-policy", "never",
                "--inject-file", f"{script_path}:/workspace/run.sh",
                "--volume", f"s3://{self.bucket}:/data:rw:{self.aws_profile}", "--format", "json"]
        for cpath, lpath in (inject or {}).items():
            args += ["--inject-file", f"{lpath}:{cpath}"]
        if self.subnet_id:
            args += ["--subnet-id", self.subnet_id]
        out = _cli(args)
        try:
            data = json.loads(out)
            ids = [v for v in _walk(data.get("metadata", data), {"id"})]
            if ids:
                return str(ids[0])
        except json.JSONDecodeError:
            pass
        m = re.search(r'"id"\s*:\s*"([^"]+)"', out) or re.search(r"\b(aijob-[a-z0-9]+)\b", out)
        if not m:
            raise RuntimeError(f"could not parse a job id from: {out[:500]}")
        return m.group(1)

    def job_state(self, job_id: str) -> str:
        out = _cli(["ai", "job", "get", job_id, "--format", "json"], check=False)
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            return "UNKNOWN"
        states = [str(v).upper() for v in _walk(data.get("status", data), {"state", "phase", "status"})]
        for s in states:
            if any(t in s for t in TERMINAL):
                return s
        return states[0] if states else "UNKNOWN"

    def wait(self, job_id: str, max_wait_s: float = 3600) -> str:
        t0 = time.time()
        state = "UNKNOWN"
        while time.time() - t0 < max_wait_s:
            state = self.job_state(job_id)
            if any(t in state for t in TERMINAL):
                return state
            time.sleep(self.poll_s)
        return state

    def run_batch(self, specs: list, out_root, on_update=None) -> list:
        from .worker import failed_result

        out_root = Path(out_root)
        out_root.mkdir(parents=True, exist_ok=True)
        tag = re.sub(r"[^a-z0-9-]", "-", f"{self.run_id}-{out_root.parent.name}".lower())[:50]
        prefix = f"knack/{self.run_id}/{out_root.parent.name}/{int(time.time())}/"
        first = specs[0]
        batch = {"task": first["task"], "code": first["code"], "seeds": [s["seed"] for s in specs],
                 "max_time": first.get("max_time"), "render": {"live": False, "keyframes": True},
                 "obs_noise": first.get("obs_noise", 0.002)}
        s3 = self._s3()
        s3.put_object(Bucket=self.bucket, Key=prefix + "knack-src.tar.gz", Body=source_tarball())
        s3.put_object(Bucket=self.bucket, Key=prefix + "batch.json", Body=json.dumps(batch).encode())
        job_id = self.create_job(f"knack-{tag}"[:60], JOB_SCRIPT.format(data="/data", prefix=prefix))
        if on_update:
            for s in specs:
                on_update("running", int(s["seed"]), None)
        t0 = time.time()
        state = self.wait(job_id)
        seconds = time.time() - t0
        self.compute_seconds += seconds
        self.last_batch_usd = self.usd_for(seconds)
        self.jobs.append({"job_id": job_id, "state": state, "seconds": round(seconds, 1), "usd": round(self.last_batch_usd, 5),
                          "preset": self.preset, "prefix": prefix})
        (out_root / "nebius_job.json").write_text(json.dumps(self.jobs[-1], indent=1), encoding="utf-8")
        results = []
        for s in specs:
            seed = int(s["seed"])
            ep_dir = out_root / f"ep_{seed}"
            ep_dir.mkdir(parents=True, exist_ok=True)
            key_root = f"{prefix}results/ep_{seed}/"
            try:
                listing = s3.list_objects_v2(Bucket=self.bucket, Prefix=key_root).get("Contents", [])
                for obj in listing:
                    name = obj["Key"][len(key_root):]
                    if name and "/" not in name:
                        s3.download_file(self.bucket, obj["Key"], str(ep_dir / name))
                r = json.loads((ep_dir / "result.json").read_text(encoding="utf-8"))
            except Exception as e:
                r = failed_result(s, "RemoteJobError", f"job {job_id} state {state}: no result ({type(e).__name__})")
            results.append(r)
            if on_update:
                on_update("done", seed, r)
        return results


def hello(preset: str = "2vcpu-8gb", platform: str = "cpu-d3", image: str = "python:3.12-slim") -> str:
    """Tiny paid job: installs MuJoCo and prints its version. Returns the job id."""
    runner = NebiusJobRunner(bucket=_env("KNACK_NEBIUS_BUCKET", "unused"), run_id="hello", platform=platform, preset=preset, image=image,
                             subnet_id=_env("KNACK_NEBIUS_SUBNET"))
    script = "#!/bin/bash\nset -e\npip install -q mujoco numpy\npython -c 'import mujoco, os; print(\"mujoco\", mujoco.__version__, \"cpus\", os.cpu_count())'\n"
    tmpdir = Path(os.environ.get("KNACK_TMP", ".knack_tmp"))
    tmpdir.mkdir(exist_ok=True)
    sp = tmpdir / "hello.sh"
    sp.write_text(script, encoding="utf-8", newline="\n")
    args = ["ai", "job", "create", "--name", f"knack-hello-{int(time.time())}", "--image", image,
            "--container-command", "bash", "--args", "/workspace/run.sh", "--platform", platform, "--preset", preset,
            "--timeout", "1h", "--disk-size", "20Gi", "--restart-policy", "never",
            "--inject-file", f"{sp}:/workspace/run.sh", "--format", "json"]
    if runner.subnet_id:
        args += ["--subnet-id", runner.subnet_id]
    out = _cli(args)
    m = re.search(r'"id"\s*:\s*"([^"]+)"', out)
    return m.group(1) if m else out.strip()[:200]
