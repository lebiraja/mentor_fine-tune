"""Memory and CUDA utilities for monitoring and debugging."""

import torch
import gc
from typing import Dict, Any


class MemoryMonitor:
    """Monitor GPU and CPU memory usage."""

    def __init__(self):
        """Initialize memory monitor."""
        self.cuda_available = torch.cuda.is_available()
        self.memory_snapshots = []

    def get_memory_info(self) -> Dict[str, float]:
        """
        Get current memory usage.

        Returns:
            Dict with memory info in GB
        """
        info = {}

        if self.cuda_available:
            # GPU memory
            allocated = torch.cuda.memory_allocated() / (1024**3)
            reserved = torch.cuda.memory_reserved() / (1024**3)
            total = torch.cuda.get_device_properties(0).total_memory / (1024**3)

            info.update({
                "gpu_allocated_gb": allocated,
                "gpu_reserved_gb": reserved,
                "gpu_total_gb": total,
                "gpu_free_gb": total - allocated,
                "gpu_utilization_percent": (allocated / total) * 100,
            })

        return info

    def print_memory_info(self, label: str = "") -> None:
        """Print current memory info."""
        info = self.get_memory_info()

        label_str = f" [{label}]" if label else ""
        print(f"\nMemory Info{label_str}:")

        if "gpu_allocated_gb" in info:
            print(f"  GPU allocated: {info['gpu_allocated_gb']:.2f}GB / "
                  f"{info['gpu_total_gb']:.2f}GB "
                  f"({info['gpu_utilization_percent']:.1f}%)")

    def take_snapshot(self, label: str = "") -> None:
        """Take a memory snapshot for debugging."""
        snapshot = {
            "label": label,
            "memory": self.get_memory_info(),
        }
        self.memory_snapshots.append(snapshot)

    def compare_snapshots(self, label1: str, label2: str) -> Dict[str, float]:
        """
        Compare two memory snapshots.

        Args:
            label1: Label of first snapshot
            label2: Label of second snapshot

        Returns:
            Dict with memory differences
        """
        snap1 = None
        snap2 = None

        for snap in self.memory_snapshots:
            if snap["label"] == label1:
                snap1 = snap["memory"]
            if snap["label"] == label2:
                snap2 = snap["memory"]

        if snap1 is None or snap2 is None:
            return {}

        differences = {}
        for key in snap1:
            if key in snap2:
                differences[key] = snap2[key] - snap1[key]

        return differences

    def clear_cuda_cache(self) -> None:
        """Aggressively clear CUDA cache."""
        if self.cuda_available:
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

    def report_memory_leak(self) -> None:
        """Generate memory leak report."""
        if len(self.memory_snapshots) < 2:
            print("Need at least 2 snapshots to check for leaks")
            return

        first = self.memory_snapshots[0]["memory"]
        last = self.memory_snapshots[-1]["memory"]

        print("\nMemory Leak Report:")
        print(f"  First snapshot: {first}")
        print(f"  Last snapshot: {last}")

        if "gpu_allocated_gb" in first and "gpu_allocated_gb" in last:
            diff = last["gpu_allocated_gb"] - first["gpu_allocated_gb"]
            print(f"  Difference: {diff:+.2f}GB")

            if abs(diff) > 0.5:
                print(f"  ⚠ Potential memory leak detected!")
