"""Memory guard to prevent OOM from too many Docker containers."""

import math
import os

import psutil


def check_memory_before_launch(required_gb: float | None = None, reserve_gb: float | None = None) -> None:
    """Raise RuntimeError if insufficient memory to launch a new container.

    Args:
        required_gb: Estimated memory needed by the new environment. Defaults to
            DTAP_MEMORY_REQUIRED_GB, or 4 GB.
        reserve_gb: Memory to keep free for the OS and other processes. Defaults
            to DTAP_MEMORY_RESERVE_GB, or 2 GB.
    """
    if required_gb is None:
        required_gb = float(os.getenv("DTAP_MEMORY_REQUIRED_GB", "4"))
    if reserve_gb is None:
        reserve_gb = float(os.getenv("DTAP_MEMORY_RESERVE_GB", "2"))
    for name, value in (("required_gb", required_gb), ("reserve_gb", reserve_gb)):
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be a finite, non-negative number")
    available_gb = psutil.virtual_memory().available / (1024 ** 3)
    if available_gb < required_gb + reserve_gb:
        raise RuntimeError(
            f"Available memory {available_gb:.1f}GB < needed {required_gb}GB + reserve {reserve_gb}GB. "
            "Close other applications or reduce parallelism. Memory estimates can be "
            "configured with DTAP_MEMORY_REQUIRED_GB and DTAP_MEMORY_RESERVE_GB."
        )
