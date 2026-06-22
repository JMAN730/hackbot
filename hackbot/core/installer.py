"""Autonomous installation of missing security tools.

ToolInstaller turns a logical tool name into a verified install by choosing an
available package manager from config.TOOL_INSTALL_MAP and executing the
constructed argv through the existing ToolRunner (shell-free, sudo-aware).
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Dict, List, Optional

from hackbot.config import TOOL_INSTALL_MAP

# Logical manager key -> binary probed via shutil.which.
_MANAGER_BINARY: Dict[str, str] = {
    "apt": "apt-get",
    "dnf": "dnf",
    "pacman": "pacman",
    "brew": "brew",
    "pipx": "pipx",
    "pip": "pip",
    "go": "go",
}

# System managers that require root for a system-wide install.
_SUDO_MANAGERS = {"apt", "dnf", "pacman"}


@dataclass
class InstallPlan:
    tool: str
    manager: str
    package: str
    command: List[str]
    needs_sudo: bool


@dataclass
class InstallResult:
    tool: str
    success: bool
    manager: str = ""
    path: Optional[str] = None
    message: str = ""
    stdout: str = ""
    stderr: str = ""


def _build_command(manager: str, package: str) -> List[str]:
    if manager == "apt":
        return ["apt-get", "install", "-y", package]
    if manager == "dnf":
        return ["dnf", "install", "-y", package]
    if manager == "pacman":
        return ["pacman", "-S", "--noconfirm", package]
    if manager == "brew":
        return ["brew", "install", package]
    if manager == "pipx":
        return ["pipx", "install", package]
    if manager == "pip":
        return ["pip", "install", package]
    if manager == "go":
        return ["go", "install", package]
    raise ValueError(f"unknown manager: {manager}")


class ToolInstaller:
    def __init__(self, runner, install_map: Optional[Dict] = None):
        self.runner = runner
        self.install_map = install_map if install_map is not None else TOOL_INSTALL_MAP
        self._available: Optional[Dict[str, str]] = None

    def available_managers(self) -> Dict[str, str]:
        if self._available is None:
            found: Dict[str, str] = {}
            for mgr, binary in _MANAGER_BINARY.items():
                path = shutil.which(binary)
                if path:
                    found[mgr] = path
            self._available = found
        return self._available

    def plan_install(self, tool: str) -> Optional[InstallPlan]:
        recipe = self.install_map.get(tool.lower())
        if not recipe:
            return None
        available = self.available_managers()
        order = recipe.get("order") or [k for k in recipe if k != "order"]
        for mgr in order:
            package = recipe.get(mgr)
            if package and mgr in available:
                return InstallPlan(
                    tool=tool,
                    manager=mgr,
                    package=str(package),
                    command=_build_command(mgr, str(package)),
                    needs_sudo=mgr in _SUDO_MANAGERS,
                )
        return None
