import pytest

from hackbot.core import installer as inst
from hackbot.core.installer import ToolInstaller, InstallPlan


def _installer(monkeypatch, present_binaries, install_map=None):
    """ToolInstaller whose available managers are exactly `present_binaries`."""

    def fake_which(binary):
        return f"/usr/bin/{binary}" if binary in present_binaries else None

    monkeypatch.setattr(inst.shutil, "which", fake_which)
    return ToolInstaller(runner=object(), install_map=install_map)


def test_available_managers_detects_present_binaries(monkeypatch):
    ti = _installer(monkeypatch, {"apt-get", "go"})
    mgrs = ti.available_managers()
    assert mgrs.keys() == {"apt", "go"}
    assert mgrs["apt"] == "/usr/bin/apt-get"


def test_plan_install_picks_first_available_in_order(monkeypatch):
    # nuclei order is ["go", "apt"]; only apt present -> apt chosen
    ti = _installer(monkeypatch, {"apt-get"})
    plan = ti.plan_install("nuclei")
    assert plan is not None
    assert plan.manager == "apt"
    assert plan.command == ["apt-get", "install", "-y", "nuclei"]
    assert plan.needs_sudo is True


def test_plan_install_prefers_go_when_available(monkeypatch):
    ti = _installer(monkeypatch, {"go", "apt-get"})
    plan = ti.plan_install("nuclei")
    assert plan.manager == "go"
    assert plan.command[0] == "go" and plan.command[1] == "install"
    assert plan.needs_sudo is False


def test_plan_install_unmapped_tool_returns_none(monkeypatch):
    ti = _installer(monkeypatch, {"apt-get"})
    assert ti.plan_install("definitely-not-a-tool") is None


def test_plan_install_no_available_manager_returns_none(monkeypatch):
    # subfinder only ships via go; if go absent -> None
    ti = _installer(monkeypatch, {"apt-get"})
    assert ti.plan_install("subfinder") is None


def test_plan_install_is_case_insensitive(monkeypatch):
    ti = _installer(monkeypatch, {"apt-get"})
    assert ti.plan_install("NIKTO").manager == "apt"


def test_pacman_command_uses_noconfirm(monkeypatch):
    ti = _installer(monkeypatch, {"pacman"})
    plan = ti.plan_install("nmap")
    assert plan.command == ["pacman", "-S", "--noconfirm", "nmap"]
