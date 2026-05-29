"""Hardware scanner for silicon-archaeology-skill.

Detects the host CPU family, classifies it into a Silicon Epoch, and returns
structured JSON suitable for RustChain Proof-of-Antiquity attestation.

Supports Linux (/proc/cpuinfo), macOS (sysctl), and any platform covered by
the standard ``platform`` module as a fallback.
"""

from __future__ import annotations

import json
import platform
import re
import subprocess
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Epoch tables aligned with the README Silicon Epochs
# (0-indexed per bounty spec: README uses 1-5 but bounty uses 0-4)
# ---------------------------------------------------------------------------

# Each entry: (pattern_lower, epoch, year_estimate, multiplier)
# Patterns are matched against combined "<family> <model>" lowercased.
_KNOWN_PATTERNS: list[tuple[str, int, int, float]] = [
    # Epoch 0 -- Pre-VLSI / pre-2000 vintage
    ("pdp", 0, 1970, 2.5),
    ("altair", 0, 1975, 2.5),
    ("6502", 0, 1975, 2.5),
    ("z80", 0, 1976, 2.5),
    ("8080", 0, 1974, 2.5),
    ("8086", 0, 1978, 2.5),
    ("8088", 0, 1979, 2.5),
    ("68000", 0, 1982, 2.5),
    ("68010", 0, 1982, 2.5),
    ("68020", 0, 1984, 2.5),
    ("68030", 0, 1987, 2.5),
    ("68040", 0, 1990, 2.5),
    ("68060", 0, 1994, 2.5),
    ("68k", 0, 1985, 2.5),
    ("sparc", 0, 1990, 2.5),
    ("supersparc", 0, 1992, 2.5),
    ("ultrasparc", 0, 1995, 2.3),
    ("mips r2000", 0, 1985, 2.5),
    ("mips r3000", 0, 1988, 2.5),
    ("r4000", 0, 1991, 2.3),
    ("r4400", 0, 1992, 2.3),
    # Epoch 1 -- PowerPC / POWER4-5 era (2000-2010)
    ("powerpc g4", 1, 2002, 2.2),
    ("powerpc g5", 1, 2003, 2.1),
    ("power4", 1, 2001, 2.2),
    ("power5", 1, 2004, 2.1),
    ("pentium m", 1, 2003, 2.0),
    ("pentium 4", 1, 2000, 2.0),
    ("pentium iii", 1, 1999, 2.2),
    ("athlon 64", 1, 2003, 2.0),
    ("opteron", 1, 2003, 2.0),
    ("powerpc 7400", 1, 1999, 2.2),
    ("powerpc 7450", 1, 2001, 2.1),
    ("powerpc 970", 1, 2002, 2.1),
    ("ppc", 1, 2002, 2.1),
    # Epoch 2 -- Sandy Bridge / Ivy Bridge / POWER7-8 (2010-2015)
    ("sandy bridge", 2, 2011, 1.7),
    ("ivy bridge", 2, 2012, 1.6),
    ("core i3-2", 2, 2011, 1.7),
    ("core i5-2", 2, 2011, 1.7),
    ("core i7-2", 2, 2011, 1.7),
    ("core i3-3", 2, 2012, 1.6),
    ("core i5-3", 2, 2012, 1.6),
    ("core i7-3", 2, 2012, 1.6),
    ("haswell", 2, 2013, 1.55),
    ("broadwell", 2, 2015, 1.5),
    ("power7", 2, 2010, 1.8),
    ("power8", 2, 2013, 1.6),
    ("fx-8", 2, 2011, 1.7),
    ("fx-6", 2, 2011, 1.7),
    ("phenom", 2, 2010, 1.8),
    # Epoch 3 -- Skylake / Zen 2 / POWER9 (2015-2020)
    ("skylake", 3, 2015, 1.4),
    ("kabylake", 3, 2017, 1.35),
    ("kaby lake", 3, 2017, 1.35),
    ("coffee lake", 3, 2017, 1.3),
    ("comet lake", 3, 2020, 1.25),
    ("ice lake", 3, 2019, 1.3),
    ("zen 2", 3, 2019, 1.3),
    ("zen2", 3, 2019, 1.3),
    ("ryzen 3000", 3, 2019, 1.3),
    ("ryzen 4000", 3, 2020, 1.25),
    ("power9", 3, 2017, 1.4),
    # Epoch 4 -- Apple Silicon / Alder Lake / POWER10 (2020+)
    ("apple m1", 4, 2020, 1.1),
    ("apple m2", 4, 2022, 1.08),
    ("apple m3", 4, 2023, 1.06),
    ("apple m4", 4, 2024, 1.05),
    ("m1", 4, 2020, 1.1),
    ("m2", 4, 2022, 1.08),
    ("m3", 4, 2023, 1.06),
    ("m4", 4, 2024, 1.05),
    ("alder lake", 4, 2021, 1.1),
    ("raptor lake", 4, 2022, 1.08),
    ("meteor lake", 4, 2023, 1.07),
    ("zen 3", 4, 2020, 1.1),
    ("zen3", 4, 2020, 1.1),
    ("zen 4", 4, 2022, 1.07),
    ("zen4", 4, 2022, 1.07),
    ("ryzen 5000", 4, 2020, 1.1),
    ("ryzen 7000", 4, 2022, 1.07),
    ("power10", 4, 2021, 1.1),
    ("risc-v", 4, 2021, 1.1),
    ("riscv", 4, 2021, 1.1),
    ("snapdragon x", 4, 2024, 1.05),
    ("grace", 4, 2023, 1.06),
    ("altra", 4, 2020, 1.1),
]

# Human-readable metadata for each epoch
_EPOCH_INFO: dict[int, dict[str, Any]] = {
    0: {"era": "Pre-VLSI / Early RISC (pre-2000)", "year_range": "pre-2000", "multiplier_range": "2.5x+"},
    1: {"era": "PowerPC / Early x86-64 (2000-2010)", "year_range": "2000-2010", "multiplier_range": "2.0-2.5x"},
    2: {"era": "Sandy Bridge / POWER7-8 (2010-2015)", "year_range": "2010-2015", "multiplier_range": "1.5-2.0x"},
    3: {"era": "Skylake / Zen 2 / POWER9 (2015-2020)", "year_range": "2015-2020", "multiplier_range": "1.2-1.5x"},
    4: {"era": "Post-Moore / Apple Silicon (2020+)", "year_range": "2020+", "multiplier_range": "1.05-1.2x"},
}


# ---------------------------------------------------------------------------
# Platform-specific CPU detection
# ---------------------------------------------------------------------------

def _read_proc_cpuinfo() -> Dict[str, str]:
    """Parse /proc/cpuinfo, returning the first processor block as a dict."""
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return {}

    fields: Dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if key not in fields:
                fields[key] = value
        elif not line.strip() and fields:
            # Stop at the first blank line (end of first processor block)
            break
    return fields


def _sysctl(key: str) -> str:
    """Return a sysctl value on macOS/BSD; returns empty string on any error."""
    try:
        result = subprocess.run(
            ["sysctl", "-n", key],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return ""


def detect_cpu() -> Dict[str, str]:
    """Detect the host CPU using the best available method.

    Returns a dict with at minimum:
        family (str): CPU family / brand string
        model  (str): Full model name
        arch   (str): Platform architecture (e.g. "x86_64", "arm64")
        source (str): Detection method used
    """
    system = platform.system()
    arch = platform.machine()
    info: Dict[str, str] = {"arch": arch, "system": system}

    if system == "Linux":
        proc = _read_proc_cpuinfo()
        info["source"] = "/proc/cpuinfo"
        # Field names differ across architectures
        info["family"] = (
            proc.get("cpu family")
            or proc.get("CPU implementer")
            or proc.get("cpu")        # PowerPC Linux
            or proc.get("model name", "")
        )
        info["model"] = proc.get("model name") or proc.get("model", "")
        info["vendor"] = proc.get("vendor_id") or proc.get("Hardware", "")
        # On PowerPC Linux the "cpu" field carries the real name
        if "PowerPC" in info.get("family", "") or "ppc" in arch.lower():
            info["family"] = proc.get("cpu", info["family"])

    elif system == "Darwin":
        info["source"] = "sysctl"
        brand = _sysctl("machdep.cpu.brand_string")
        if not brand:
            # Apple Silicon does not expose machdep.cpu.brand_string
            brand = _sysctl("hw.model")
        info["model"] = brand or platform.processor()
        info["family"] = brand or _sysctl("machdep.cpu.family") or platform.processor()
        info["vendor"] = _sysctl("machdep.cpu.vendor")

    else:
        # Generic fallback: standard library only
        info["source"] = "platform"
        proc_str = platform.processor() or arch
        info["model"] = proc_str
        info["family"] = proc_str

    info.setdefault("family", "")
    info.setdefault("model", "")
    return info


# ---------------------------------------------------------------------------
# Epoch classification
# ---------------------------------------------------------------------------

def classify_epoch(cpu_info: Dict[str, str]) -> Dict[str, Any]:
    """Classify a CPU description into a Silicon Epoch (0-4).

    Args:
        cpu_info: dict as returned by :func:`detect_cpu`.

    Returns:
        Dict with keys: epoch (int), era (str), year_estimate (int),
        rustchain_multiplier (float).
    """
    family = (cpu_info.get("family") or "").strip()
    model = (cpu_info.get("model") or "").strip()
    # Remove trademark/registered markers like (R), (TM), (tm) before matching
    combined = re.sub(r"\([^)]{0,4}\)", "", f"{family} {model}").lower()
    combined = " ".join(combined.split())

    matched_epoch: Optional[int] = None
    matched_year: int = 2022
    matched_mult: float = 1.08

    for pattern, epoch, year, mult in _KNOWN_PATTERNS:
        if pattern in combined:
            matched_epoch = epoch
            matched_year = year
            matched_mult = mult
            break  # first (most-specific) match wins

    if matched_epoch is None:
        arch = (cpu_info.get("arch") or "").lower()
        if any(x in arch for x in ("ppc", "powerpc", "ppc64")):
            matched_epoch, matched_year, matched_mult = 1, 2002, 2.1
        elif "sparc" in arch:
            matched_epoch, matched_year, matched_mult = 0, 1993, 2.3
        elif "mips" in arch:
            matched_epoch, matched_year, matched_mult = 0, 1992, 2.3
        elif any(x in arch for x in ("arm64", "aarch64")):
            matched_epoch, matched_year, matched_mult = 4, 2021, 1.1
        elif "arm" in arch:
            matched_epoch, matched_year, matched_mult = 3, 2018, 1.3
        else:
            matched_epoch, matched_year, matched_mult = 4, 2022, 1.08

    return {
        "epoch": matched_epoch,
        "era": _EPOCH_INFO[matched_epoch]["era"],
        "year_estimate": matched_year,
        "rustchain_multiplier": matched_mult,
    }


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def get_scan() -> Dict[str, Any]:
    """Detect and classify the host CPU.

    Returns a JSON-serializable dict::

        {
            "family":               str,   # CPU family / brand string
            "model":                str,   # Full model name
            "epoch":                int,   # Silicon Epoch 0-4
            "year_estimate":        int,   # Approximate introduction year
            "rustchain_multiplier": float, # PoA reward multiplier
            "era":                  str,   # Human-readable era label
            "arch":                 str,   # Platform architecture
            "detection_source":     str,   # How CPU info was obtained
        }
    """
    cpu = detect_cpu()
    classification = classify_epoch(cpu)
    return {
        "family": cpu.get("family", ""),
        "model": cpu.get("model", ""),
        "epoch": classification["epoch"],
        "year_estimate": classification["year_estimate"],
        "rustchain_multiplier": classification["rustchain_multiplier"],
        "era": classification["era"],
        "arch": cpu.get("arch", ""),
        "detection_source": cpu.get("source", "platform"),
    }


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result = get_scan()
    print(json.dumps(result, indent=2))
