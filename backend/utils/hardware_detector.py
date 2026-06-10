"""
AIRA — Hardware Detection
Detects Apple Silicon, NVIDIA CUDA, available memory.
Recommends optimal model size.
"""

import platform
import subprocess
import os

try:
    import psutil
except ImportError:
    psutil = None  # Optional dependency

from utils.logger import get_logger

logger = get_logger("hardware")


def detect_hardware():
    """
    Detect system hardware capabilities.
    Returns dict with CPU, GPU, memory, and recommended model.
    """
    info = {
        "platform": platform.system(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "ram_gb": _get_ram_gb(),
        "gpu": _detect_gpu(),
        "recommended_model": None,
    }

    # Determine recommended model based on hardware
    info["recommended_model"] = _recommend_model(info)
    return info


def _get_ram_gb():
    """Get total RAM in GB."""
    try:
        import psutil
        return round(psutil.virtual_memory().total / (1024 ** 3), 1)
    except ImportError:
        # Fallback for systems without psutil
        try:
            if platform.system() == "Darwin":
                output = subprocess.check_output(
                    ["sysctl", "-n", "hw.memsize"],
                    stderr=subprocess.DEVNULL,
                ).decode().strip()
                return round(int(output) / (1024 ** 3), 1)
            elif platform.system() == "Windows":
                output = subprocess.check_output(
                    ["wmic", "computersystem", "get", "totalphysicalmemory"],
                    stderr=subprocess.DEVNULL,
                ).decode()
                for line in output.strip().split("\n"):
                    line = line.strip()
                    if line.isdigit():
                        return round(int(line) / (1024 ** 3), 1)
            elif platform.system() == "Linux":
                with open("/proc/meminfo") as f:
                    for line in f:
                        if "MemTotal" in line:
                            kb = int(line.split()[1])
                            return round(kb / (1024 ** 2), 1)
        except Exception:
            pass
    return 0


def _detect_gpu():
    """Detect GPU information."""
    gpu_info = {
        "type": "none",
        "name": None,
        "vram_gb": 0,
        "cuda_available": False,
        "apple_silicon": False,
    }

    # Check for Apple Silicon
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        gpu_info["type"] = "apple_silicon"
        gpu_info["apple_silicon"] = True
        gpu_info["name"] = _get_apple_chip_name()
        # Unified memory — shared with RAM
        gpu_info["vram_gb"] = _get_ram_gb()
        return gpu_info

    # Check for NVIDIA GPU
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()

        if output:
            parts = output.split(",")
            gpu_info["type"] = "nvidia"
            gpu_info["cuda_available"] = True
            gpu_info["name"] = parts[0].strip()
            gpu_info["vram_gb"] = round(int(parts[1].strip()) / 1024, 1) if len(parts) > 1 else 0
            return gpu_info

    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # No GPU detected — CPU only
    gpu_info["type"] = "cpu"
    return gpu_info


def _get_apple_chip_name():
    """Get Apple chip name (M1, M2, M3, M4, M5, etc.)."""
    try:
        output = subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
        return output
    except Exception:
        return "Apple Silicon"


def _recommend_model(info):
    """Recommend optimal model based on hardware."""
    ram = info.get("ram_gb", 0)
    gpu = info.get("gpu", {})
    gpu_type = gpu.get("type", "cpu")
    vram = gpu.get("vram_gb", 0)

    # Apple Silicon — can use unified memory
    if gpu_type == "apple_silicon":
        if ram >= 32:
            return "qwen3-coder:30b"
        elif ram >= 16:
            return "qwen3-coder:14b"
        else:
            return "qwen3-coder:7b"

    # NVIDIA GPU — limited by VRAM
    if gpu_type == "nvidia":
        if vram >= 16:
            return "qwen3-coder:14b"
        elif vram >= 8:
            return "qwen3-coder:7b"
        elif vram >= 4:
            return "qwen3-coder:1.5b"
        else:
            return "qwen3-coder:0.6b"

    # CPU only — use smallest model
    if ram >= 16:
        return "qwen3-coder:7b"
    elif ram >= 8:
        return "qwen3-coder:1.5b"
    else:
        return "qwen3-coder:0.6b"
