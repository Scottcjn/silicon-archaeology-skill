"""Hardware scanner module for silicon-archaeology-skill.

Detects and fingerprints vintage hardware by scanning CPU information
from /proc/cpuinfo, sysctl, or platform module.
Works on Linux, macOS, and PowerPC systems.
"""

from __future__ import annotations

import json
import platform
import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional, Union


# RustChain multipliers per epoch (from README)
RUSTCHAIN_MULTIPLIERS = {
    0: 4.0,    # Pre-VLSI (pre-1980)
    1: 3.5,    # VLSI Dawn (1980-1992)
    2: 2.5,    # RISC Wars (1993-2005) - upper bound
    3: 1.3,    # x86 Dominance (2006-2019) - upper bound
    4: 1.2,    # Post-Moore (2020+) - upper bound
}

# Epoch year ranges
EPOCH_RANGES = {
    0: (None, 1979),      # Pre-VLSI
    1: (1980, 1992),      # VLSI Dawn
    2: (1993, 2005),      # RISC Wars
    3: (2006, 2019),      # x86 Dominance
    4: (2020, None),      # Post-Moore
}


@dataclass(frozen=True)
class HardwareInfo:
    """Hardware detection result."""
    family: str
    model: str
    epoch: int
    year_estimate: int
    rustchain_multiplier: float

    def to_dict(self) -> Dict[str, Union[str, int, float]]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


def _run_command(cmd: list[str]) -> Optional[str]:
    """Run a shell command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _parse_cpuinfo() -> Dict[str, str]:
    """Parse /proc/cpuinfo on Linux systems."""
    info: Dict[str, str] = {}
    cpuinfo_path = Path("/proc/cpuinfo")
    
    if not cpuinfo_path.exists():
        return info
    
    try:
        content = cpuinfo_path.read_text()
        for line in content.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
    except (IOError, OSError):
        pass
    
    return info


def _get_sysctl_info() -> Dict[str, str]:
    """Get CPU info via sysctl on macOS/BSD systems."""
    info: Dict[str, str] = {}
    
    # Get machdep.cpu.brand_string (most reliable on macOS)
    brand = _run_command(["sysctl", "-n", "machdep.cpu.brand_string"])
    if brand:
        info["brand_string"] = brand
    
    # Get CPU family
    family = _run_command(["sysctl", "-n", "machdep.cpu.family"])
    if family:
        info["cpu_family"] = family
    
    # Get model
    model = _run_command(["sysctl", "-n", "hw.model"])
    if model:
        info["hw_model"] = model
    
    # Get machine (useful for PowerPC)
    machine = _run_command(["sysctl", "-n", "hw.machine"])
    if machine:
        info["hw_machine"] = machine
    
    # Get CPU type (PowerPC specific)
    cputype = _run_command(["sysctl", "-n", "hw.cputype"])
    if cputype:
        info["cputype"] = cputype
    
    # Get CPU subtype (PowerPC specific)
    cpusubtype = _run_command(["sysctl", "-n", "hw.cpusubtype"])
    if cpusubtype:
        info["cpusubtype"] = cpusubtype
    
    return info


def _detect_powerpc_info() -> Optional[HardwareInfo]:
    """Detect PowerPC specific hardware info."""
    sysctl_info = _get_sysctl_info()
    
    # Check for PowerPC via hw.machine or cputype
    machine = sysctl_info.get("hw_machine", "")
    cputype = sysctl_info.get("cputype", "")
    brand = sysctl_info.get("brand_string", "")
    
    is_powerpc = (
        "powerpc" in machine.lower() or
        "powerpc" in brand.lower() or
        "ppc" in machine.lower() or
        cputype == "18"  # CPU_TYPE_POWERPC = 18
    )
    
    if not is_powerpc:
        return None
    
    # Parse PowerPC model from brand string or machine
    model = "Unknown"
    year = 2000  # Default for PowerPC
    
    # PowerPC G3 (1997-2003)
    if "g3" in brand.lower() or "750" in brand.lower():
        model = "PowerPC G3"
        year = 1999
    elif "g4" in brand.lower() or "7400" in brand.lower():
        model = "PowerPC G4"
        year = 1999
    elif "g5" in brand.lower() or "970" in brand.lower():
        model = "PowerPC G5"
        year = 2003
    elif "power mac" in machine.lower() or "powermac" in machine.lower():
        model = "Power Macintosh"
        year = 1994
    
    return HardwareInfo(
        family="IBM/Motorola",
        model=model,
        epoch=2,  # RISC Wars
        year_estimate=year,
        rustchain_multiplier=RUSTCHAIN_MULTIPLIERS[2]
    )


def _detect_from_platform() -> HardwareInfo:
    """Detect hardware using Python's platform module as fallback."""
    processor = platform.processor()
    machine = platform.machine()
    system = platform.system()
    
    # Default values
    family = "Unknown"
    model = machine or processor or "Unknown"
    year = 2020  # Default to modern
    
    # x86/x64 detection
    if machine in ("x86_64", "amd64", "AMD64") or "x86" in processor.lower():
        family = "Intel/AMD"
        # Try to detect generation from processor string
        if "intel" in processor.lower():
            family = "Intel"
            # Extract model name
            model_match = re.search(r'Intel\(R\)\s+(\w+)', processor, re.I)
            if model_match:
                model = model_match.group(1)
            else:
                model = processor
        elif "amd" in processor.lower():
            family = "AMD"
            model = processor
    
    # ARM detection (Apple Silicon, etc.)
    elif machine in ("arm64", "aarch64") or "arm" in processor.lower():
        family = "ARM"
        if system == "Darwin":
            # macOS on ARM = Apple Silicon (M1/M2/M3)
            model = "Apple Silicon"
            year = 2020
        else:
            model = machine
    
    # PowerPC detection
    elif "ppc" in machine.lower() or "power" in machine.lower():
        family = "IBM/Motorola"
        model = "PowerPC"
        year = 2000
    
    # Determine epoch from year
    epoch = _year_to_epoch(year)
    
    return HardwareInfo(
        family=family,
        model=model,
        epoch=epoch,
        year_estimate=year,
        rustchain_multiplier=RUSTCHAIN_MULTIPLIERS.get(epoch, 1.0)
    )


def _year_to_epoch(year: int) -> int:
    """Convert year to silicon epoch."""
    for epoch, (start, end) in EPOCH_RANGES.items():
        if start is not None and year < start:
            continue
        if end is not None and year > end:
            continue
        return epoch
    return 4  # Default to Post-Moore


def _parse_linux_cpuinfo(info: Dict[str, str]) -> HardwareInfo:
    """Parse Linux /proc/cpuinfo into HardwareInfo."""
    vendor = info.get("vendor_id", "Unknown")
    model_name = info.get("model name", "Unknown")
    cpu_family = info.get("cpu family", "")
    model = info.get("model", "")
    
    # Map vendor
    if vendor == "GenuineIntel":
        family = "Intel"
    elif vendor == "AuthenticAMD":
        family = "AMD"
    elif "IBM" in vendor:
        family = "IBM"
    else:
        family = vendor
    
    # Estimate year based on CPU family/model
    year = _estimate_year_from_cpu(family, model_name, cpu_family, model)
    epoch = _year_to_epoch(year)
    
    return HardwareInfo(
        family=family,
        model=model_name if model_name != "Unknown" else f"Family {cpu_family} Model {model}",
        epoch=epoch,
        year_estimate=year,
        rustchain_multiplier=RUSTCHAIN_MULTIPLIERS.get(epoch, 1.0)
    )


def _estimate_year_from_cpu(
    family: str,
    model_name: str,
    cpu_family: str,
    model: str
) -> int:
    """Estimate CPU release year from model information."""
    model_lower = model_name.lower()
    family_lower = family.lower()
    
    # Intel processors
    if "intel" in family_lower:
        # Core series
        if "core" in model_lower:
            if "ultra" in model_lower:
                return 2023  # Core Ultra
            if "i9" in model_lower or "i7" in model_lower:
                if "13" in model_lower or "13th" in model_lower:
                    return 2022
                if "12" in model_lower or "12th" in model_lower:
                    return 2021
                if "11" in model_lower or "11th" in model_lower:
                    return 2020
            if "i5" in model_lower or "i3" in model_lower:
                if "13" in model_lower or "12" in model_lower:
                    return 2021
            # Core 2 series
            if "core2" in model_lower or "core 2" in model_lower:
                return 2006
            # Core series (first gen)
            if "core(tm)" in model_lower and "i" not in model_lower:
                return 2006
        
        # Xeon
        if "xeon" in model_lower:
            if "scalable" in model_lower or "platinum" in model_lower:
                return 2020
            if "v4" in model_lower:
                return 2016
            if "v3" in model_lower:
                return 2014
            return 2010
        
        # Pentium
        if "pentium" in model_lower:
            if "4" in model_lower:
                return 2000
            if "iii" in model_lower or "3" in model_lower:
                return 1999
            if "ii" in model_lower or "2" in model_lower:
                return 1997
            return 1993
        
        # Older Intel
        if "486" in model_lower or "80486" in model_lower:
            return 1989
        if "386" in model_lower or "80386" in model_lower:
            return 1985
    
    # AMD processors
    if "amd" in family_lower:
        if "ryzen" in model_lower:
            if "7000" in model_lower:
                return 2022
            if "5000" in model_lower:
                return 2020
            if "3000" in model_lower:
                return 2019
            return 2017
        if "epyc" in model_lower:
            return 2017
        if "athlon" in model_lower:
            if "64" in model_lower:
                return 2003
            return 1999
        if "opteron" in model_lower:
            return 2003
    
    # ARM / Apple
    if "apple" in family_lower or "arm" in family_lower:
        if "m3" in model_lower:
            return 2023
        if "m2" in model_lower:
            return 2022
        if "m1" in model_lower:
            return 2020
        return 2020
    
    # Default to modern if unknown
    return 2020


def scan_hardware() -> HardwareInfo:
    """Scan and detect local hardware.
    
    Detects CPU family from /proc/cpuinfo, sysctl, or platform module.
    Classifies into Silicon Epochs (0-4) per the README table.
    
    Returns:
        HardwareInfo with family, model, epoch, year_estimate, rustchain_multiplier
    
    Works on Linux, macOS, and PowerPC systems.
    """
    system = platform.system()
    
    # Try PowerPC detection first (macOS/Linux on PowerPC)
    ppc_info = _detect_powerpc_info()
    if ppc_info:
        return ppc_info
    
    # Linux: parse /proc/cpuinfo
    if system == "Linux":
        cpuinfo = _parse_cpuinfo()
        if cpuinfo:
            return _parse_linux_cpuinfo(cpuinfo)
    
    # macOS: use sysctl
    if system == "Darwin":
        sysctl_info = _get_sysctl_info()
        brand = sysctl_info.get("brand_string", "")
        
        # Apple Silicon detection
        if "apple" in brand.lower():
            model = "Apple Silicon"
            if "m3" in brand.lower():
                model = "Apple M3"
                year = 2023
            elif "m2" in brand.lower():
                model = "Apple M2"
                year = 2022
            elif "m1" in brand.lower():
                model = "Apple M1"
                year = 2020
            else:
                year = 2020
            
            return HardwareInfo(
                family="Apple",
                model=model,
                epoch=4,  # Post-Moore
                year_estimate=year,
                rustchain_multiplier=RUSTCHAIN_MULTIPLIERS[4]
            )
        
        # Intel Mac
        if "intel" in brand.lower():
            year = _estimate_year_from_cpu("Intel", brand, "", "")
            epoch = _year_to_epoch(year)
            return HardwareInfo(
                family="Intel",
                model=brand,
                epoch=epoch,
                year_estimate=year,
                rustchain_multiplier=RUSTCHAIN_MULTIPLIERS.get(epoch, 1.0)
            )
    
    # Fallback to platform module
    return _detect_from_platform()


def main():
    """CLI entry point for testing."""
    hw = scan_hardware()
    print(hw.to_json())


if __name__ == "__main__":
    main()
