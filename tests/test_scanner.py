import platform
import subprocess
from pathlib import Path

from silicon_archaeology.scanner import HardwareScan, scan_hardware


class FakeCompletedProcess:
    def __init__(self, stdout, returncode=0):
        self.stdout = stdout
        self.returncode = returncode


def test_linux_proc_cpuinfo_powerpc_g4(tmp_path, monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    cpuinfo = tmp_path / "cpuinfo"
    cpuinfo.write_text(
        "processor : 0\n"
        "cpu : 7455, altivec supported\n"
        "machine : PowerBook5,6\n",
        encoding="utf-8",
    )

    result = scan_hardware(cpuinfo_path=cpuinfo)

    assert result == {
        "family": "PowerPC",
        "model": "7455, altivec supported",
        "epoch": 2,
        "year_estimate": 1993,
        "rustchain_multiplier": 2.0,
    }


def test_macos_sysctl_apple_silicon(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")

    def fake_run(args, **kwargs):
        assert args == ["sysctl", "-n", "machdep.cpu.brand_string"]
        return FakeCompletedProcess("Apple M2 Max\n")

    result = scan_hardware(runner=fake_run)

    assert result["family"] == "Apple Silicon"
    assert result["model"] == "Apple M2 Max"
    assert result["epoch"] == 4
    assert result["year_estimate"] == 2021
    assert result["rustchain_multiplier"] == 1.1


def test_linux_proc_cpuinfo_intel_model_name(tmp_path, monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    cpuinfo = tmp_path / "cpuinfo"
    cpuinfo.write_text(
        "vendor_id : GenuineIntel\n"
        "model name : Intel(R) Core(TM) i7-8650U CPU @ 1.90GHz\n",
        encoding="utf-8",
    )

    result = scan_hardware(cpuinfo_path=cpuinfo)

    assert result["family"] == "Intel x86"
    assert result["model"] == "Intel(R) Core(TM) i7-8650U CPU @ 1.90GHz"
    assert result["epoch"] == 4
    assert result["year_estimate"] == 2022


def test_unknown_platform_falls_back_to_platform_processor(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "FreeBSD")
    monkeypatch.setattr(platform, "processor", lambda: "")
    monkeypatch.setattr(platform, "machine", lambda: "riscv64")

    result = scan_hardware()

    assert result["family"] == "RISC-V"
    assert result["model"] == "riscv64"
    assert result["epoch"] == 4
    assert result["year_estimate"] == 2021
    assert result["rustchain_multiplier"] == 1.2


def test_hardware_scan_json_is_structured():
    scan = HardwareScan(
        family="SPARC",
        model="SuperSPARC",
        epoch=2,
        year_estimate=1992,
        rustchain_multiplier=2.0,
    )

    assert scan.to_json() == (
        '{"epoch": 2, "family": "SPARC", "model": "SuperSPARC", '
        '"rustchain_multiplier": 2.0, "year_estimate": 1992}'
    )
