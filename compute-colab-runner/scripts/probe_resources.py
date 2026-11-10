"""Read-only resource inventory; no ML imports, allocation, installation or network."""
import argparse
import csv
import ctypes
import importlib.metadata
import io
import json
import os
import platform
from pathlib import Path
import shutil
import subprocess
import sys


def query_gpu(runner=subprocess.run, finder=shutil.which):
    executable = finder("nvidia-smi")
    if not executable:
        return {"status": "unavailable", "reason": "nvidia-smi not found", "devices": None}
    try:
        result = runner(
            [executable, "--query-gpu=name,memory.total,memory.free,driver_version",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10, check=False,
        )
        if result.returncode:
            return {"status": "error", "reason": "nvidia-smi failed", "devices": None}
        devices = []
        for row in csv.reader(io.StringIO(result.stdout)):
            if not row:
                continue
            if len(row) != 4:
                raise ValueError("unexpected GPU fields")
            name, total, free, driver = (v.strip() for v in row)
            def memory(value):
                try:
                    return float(value) if float(value) >= 0 else None
                except ValueError:
                    return None
            devices.append({"name": name, "total_mib": memory(total),
                            "free_mib": memory(free), "driver": driver})
        return {"status": "ok" if devices else "unknown", "devices": devices or None}
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return {"status": "error", "reason": type(exc).__name__, "devices": None}


def memory_bytes():
    try:
        if platform.system() == "Windows":
            class MemoryStatus(ctypes.Structure):
                _fields_ = [("length", ctypes.c_uint32), ("load", ctypes.c_uint32)] + [
                    (name, ctypes.c_uint64) for name in
                    ("total", "available", "page_total", "page_available",
                     "virtual_total", "virtual_available", "extended")]
            state = MemoryStatus()
            state.length = ctypes.sizeof(state)
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):
                raise OSError("memory query failed")
            return {"total": state.total, "available": state.available}
        size = os.sysconf("SC_PAGE_SIZE")
        total = size * os.sysconf("SC_PHYS_PAGES")
        try:
            available = size * os.sysconf("SC_AVPHYS_PAGES")
        except (OSError, ValueError):
            available = None
        return {"total": total, "available": available}
    except (OSError, ValueError, AttributeError):
        return {"total": None, "available": None}


def decode_power(ac, flag, percent, seconds, saver):
    present = None if flag == 255 else not bool(flag & 128)
    return {
        "status": "ok", "ac_connected": {0: False, 1: True}.get(ac),
        "battery_present": present,
        "battery_percent": percent if present is not False and 0 <= percent <= 100 else None,
        "charging": bool(flag & 8) if present is True else None,
        "battery_low": bool(flag & 6) if present is True else None,
        "remaining_seconds": seconds if present is True and seconds != 0xffffffff else None,
        "battery_saver": {0: False, 1: True}.get(saver),
    }


def query_power():
    unknown = {"status": "unknown", "ac_connected": None, "battery_present": None,
               "battery_percent": None, "charging": None, "battery_low": None,
               "remaining_seconds": None, "battery_saver": None}
    if platform.system() != "Windows":
        return {**unknown, "reason": "No power probe implemented for this platform"}
    try:
        class PowerStatus(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ubyte) for name in ("ac", "flag", "percent", "saver")] + [
                (name, ctypes.c_uint32) for name in ("seconds", "full_seconds")]
        state = PowerStatus()
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(state)):
            raise OSError("power query failed")
        return decode_power(state.ac, state.flag, state.percent, state.seconds, state.saver)
    except (OSError, AttributeError):
        return {**unknown, "reason": "Power query unavailable"}


def collect(disk_path, gpu_query=query_gpu, power_query=query_power):
    target = Path(disk_path).resolve(strict=True)
    if not target.is_dir():
        raise ValueError("disk-path must be an existing directory")
    disk = shutil.disk_usage(target)
    versions = {}
    for package in ("torch", "numpy", "Pillow", "tensorflow", "jax"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return {
        "schema_version": 1,
        "mode": "read-only-inventory-not-benchmark",
        "system": platform.system(), "machine": platform.machine(),
        "python_version": platform.python_version(), "python_executable": sys.executable,
        "logical_cpu_count": os.cpu_count(), "memory_bytes": memory_bytes(),
        "disk_bytes": {"path": str(target), "total": disk.total, "free": disk.free},
        "installed_packages": versions, "nvidia_gpu": gpu_query(),
        "power": power_query(),
        "workload_fit": "unknown: requires authorized workload-specific benchmark",
        "cloud_quota": "not_checked",
        "warnings": ["Missing package metadata is not evidence of unsuitable hardware.",
                     "GPU inventory does not establish framework CUDA compatibility.",
                     "Available resources are an instantaneous snapshot."],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disk-path", required=True, help="Existing project directory")
    args = parser.parse_args()
    try:
        report = collect(args.disk_path)
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": type(exc).__name__, "reason": "Invalid or unreadable disk-path"}))
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
