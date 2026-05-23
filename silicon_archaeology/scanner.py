"""Local hardware scanner for silicon archaeology.

The scanner keeps detection conservative: it reports the best local CPU
identity it can find without network access or privileged commands, then maps
that identity into the README silicon epoch table.
"""

from __future__ import annotations

import json
import platform
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Optional


EPOCH_TABLE = {
    0: ("Pre-VLSI", 4.0),
    1: ("VLSI Dawn", 3.5),
    2: ("RISC Wars", 2.5),
    3: ("x86 Dominance", 1.2),
    4: ("Post-Moore", 1.1),
}


@dataclass(frozen=True)
class HardwareScan:
    family: str
    model: str
    epoch: int
    year_estimate: int
    rustchain_multiplier: float

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


def _run_sysctl(name: str, runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> str:
    try:
        result = runner(
            ["sysctl", "-n", name],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _read_cpuinfo(path: Path = Path("/proc/cpuinfo")) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _first_cpuinfo_value(cpuinfo: str, keys: tuple[str, ...]) -> str:
    values: dict[str, str] = {}
    for line in cpuinfo.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values.setdefault(key.strip().lower(), value.strip())
    for key in keys:
        value = values.get(key.lower(), "")
        if value:
            return value
    return ""


def _detect_linux(cpuinfo: str) -> tuple[str, str]:
    model = _first_cpuinfo_value(
        cpuinfo,
        (
            "model name",
            "cpu",
            "hardware",
            "machine",
            "processor",
        ),
    )
    cpu_family = _first_cpuinfo_value(cpuinfo, ("vendor_id", "cpu family", "platform", "machine"))

    combined = f"{cpu_family} {model} {cpuinfo}".strip()
    if not model:
        model = platform.processor() or platform.machine() or "Unknown CPU"
    return _infer_family(combined or model), model


def _detect_macos(runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> tuple[str, str]:
    model = _run_sysctl("machdep.cpu.brand_string", runner)
    if not model:
        model = _run_sysctl("hw.model", runner)
    if not model:
        model = platform.processor() or platform.machine() or "Unknown CPU"
    return _infer_family(model), model


def _infer_family(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("powerpc", "power pc", "ppc", "power mac", "powerbook")):
        return "PowerPC"
    if "sparc" in lowered:
        return "SPARC"
    if "mips" in lowered:
        return "MIPS"
    if "68000" in lowered or "68k" in lowered or "m680" in lowered:
        return "68K"
    if "transputer" in lowered or "inmos" in lowered:
        return "Transputer"
    if "risc-v" in lowered or "riscv" in lowered:
        return "RISC-V"
    if "apple" in lowered and re.search(r"\bm[1-9]\b", lowered):
        return "Apple Silicon"
    if "arm" in lowered or "aarch64" in lowered:
        return "ARM"
    if "amd" in lowered:
        return "AMD x86"
    if "intel" in lowered or "genuineintel" in lowered or "x86" in lowered:
        return "Intel x86"
    return "Unknown"


def _estimate_year(family: str, model: str) -> int:
    text = f"{family} {model}".lower()

    if any(token in text for token in ("pdp", "altair", "4004", "8008", "8080", "6502", "z80")):
        return 1976
    if any(token in text for token in ("68000", "68010", "amiga", "transputer", "80386", "386")):
        return 1985
    if any(token in text for token in ("powerpc", "ppc", "g3", "g4", "g5", "sparc", "mips", "alpha", "pa-risc")):
        if "g5" in text:
            return 2003
        if "g4" in text:
            return 1999
        if "g3" in text:
            return 1997
        return 1993
    if any(token in text for token in ("core 2", "nehalem", "sandy bridge", "pentium 4", "athlon 64")):
        return 2008
    if "risc-v" in text or "riscv" in text:
        return 2021

    apple_match = re.search(r"\bm([1-9])\b", text)
    if apple_match:
        return 2019 + int(apple_match.group(1))

    if any(token in text for token in ("ryzen", "epyc", "threadripper", "core i", "core(tm)", "core ultra")):
        return 2022
    if "arm" in text or "aarch64" in text:
        return 2020
    return 2026


def _epoch_from_year(year: int) -> int:
    if year < 1980:
        return 0
    if year <= 1992:
        return 1
    if year <= 2005:
        return 2
    if year <= 2019:
        return 3
    return 4


def _multiplier_for(family: str, model: str, epoch: int) -> float:
    text = f"{family} {model}".lower()
    if "g4" in text:
        return 2.5
    if "g5" in text:
        return 2.0
    if "powerpc" in text or "ppc" in text or "sparc" in text or "mips" in text:
        return 2.0
    if "68000" in text or "transputer" in text:
        return 3.5
    if "risc-v" in text or "riscv" in text:
        return 1.2
    return EPOCH_TABLE[epoch][1]


def scan_hardware(
    cpuinfo_path: Path = Path("/proc/cpuinfo"),
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> dict[str, object]:
    """Detect local CPU identity and return a JSON-serializable scan record."""
    system = platform.system()
    if system == "Linux":
        family, model = _detect_linux(_read_cpuinfo(cpuinfo_path))
    elif system == "Darwin":
        family, model = _detect_macos(runner)
    else:
        model = platform.processor() or platform.machine() or "Unknown CPU"
        family = _infer_family(model)

    year = _estimate_year(family, model)
    epoch = _epoch_from_year(year)
    scan = HardwareScan(
        family=family,
        model=model,
        epoch=epoch,
        year_estimate=year,
        rustchain_multiplier=_multiplier_for(family, model, epoch),
    )
    return asdict(scan)


if __name__ == "__main__":
    print(json.dumps(scan_hardware(), indent=2, sort_keys=True))
