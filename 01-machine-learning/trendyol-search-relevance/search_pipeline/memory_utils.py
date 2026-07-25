"""Platform-safe memory measurement utilities for V5."""
from __future__ import annotations

import os
import platform
import resource
from typing import Any

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


def bytes_to_mib(value_bytes: float) -> float:
    """Convert bytes to mebibytes (MiB)."""
    return value_bytes / (1024.0 * 1024.0)


def get_rss_mib(pid: int | None = None) -> float:
    """Get resident set size in MiB for a process.

    Uses psutil if available, falls back to resource.getrusage.
    On macOS, ru_maxrss is in bytes; on Linux it is in kilobytes.
    """
    if pid is None:
        pid = os.getpid()

    if _HAS_PSUTIL:
        try:
            proc = psutil.Process(pid)
            return bytes_to_mib(proc.memory_info().rss)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Fallback to resource module
    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss = usage.ru_maxrss

    # On macOS (Darwin), ru_maxrss is in bytes
    # On Linux, ru_maxrss is in kilobytes
    if platform.system() == "Darwin":
        return bytes_to_mib(rss)
    else:
        return bytes_to_mib(rss * 1024)


def get_process_tree_rss() -> dict[str, Any]:
    """Get RSS for the current process and all children.

    Returns a dict with:
    - main_pid: int
    - main_rss_mib: float
    - children: list of {pid, rss_mib, status}
    - total_rss_mib: float
    """
    if not _HAS_PSUTIL:
        return {
            "main_pid": os.getpid(),
            "main_rss_mib": get_rss_mib(),
            "children": [],
            "total_rss_mib": get_rss_mib(),
        }

    main_proc = psutil.Process(os.getpid())
    main_rss = bytes_to_mib(main_proc.memory_info().rss)
    children = []
    total = main_rss

    for child in main_proc.children(recursive=True):
        try:
            child_rss = bytes_to_mib(child.memory_info().rss)
            children.append({
                "pid": child.pid,
                "rss_mib": child_rss,
                "status": child.status(),
            })
            total += child_rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return {
        "main_pid": os.getpid(),
        "main_rss_mib": main_rss,
        "children": children,
        "total_rss_mib": total,
    }


def get_child_process_info() -> list[dict[str, Any]]:
    """Get info about child processes."""
    if not _HAS_PSUTIL:
        return []

    main_proc = psutil.Process(os.getpid())
    result = []
    for child in main_proc.children(recursive=True):
        try:
            result.append({
                "pid": child.pid,
                "rss_mib": bytes_to_mib(child.memory_info().rss),
                "status": child.status(),
                "name": child.name(),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return result
