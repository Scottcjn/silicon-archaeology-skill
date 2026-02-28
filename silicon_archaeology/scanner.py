import json
import platform
import subprocess
import re
from typing import Dict, Optional

class HardwareScanner:
    """Scanner for detecting and fingerprinting vintage hardware."""
    
    # Silicon Epochs mapping
    EPOCHS = {
        0: {"name": "Genesis", "years": "1971-1985", "multiplier": 4.0},
        1: {"name": "Classic", "years": "1985-1995", "multiplier": 3.0},
        2: {"name": "Renaissance", "years": "1995-2005", "multiplier": 2.0},
        3: {"name": "Modern", "years": "2005-2015", "multiplier": 1.5},
        4: {"name": "Contemporary", "years": "2015+", "multiplier": 1.0},
    }
    
    # CPU family to epoch mapping (simplified)
    CPU_EPOCH_MAP = {
        # PowerPC G4 (Renaissance)
        "7400": 2, "7410": 2, "7450": 2, "7455": 2, "7447": 2, "7448": 2,
        # PowerPC G5 (Modern)
        "970": 3, "970FX": 3, "970MP": 3,
        # POWER8 (Contemporary)
        "POWER8": 4,
        # x86 vintage
        "i386": 0, "i486": 0, "i586": 1, "i686": 1,
        # AMD/Intel
        "Opteron": 3, "Xeon": 3,
    }
    
    def scan(self) -> Dict:
        """Scan hardware and return structured data."""
        system = platform.system()
        
        if system == "Linux":
            return self._scan_linux()
        elif system == "Darwin":
            return self._scan_macos()
        else:
            return self._scan_generic()
    
    def _scan_linux(self) -> Dict:
        """Scan on Linux systems."""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
            
            # Extract CPU model
            model_match = re.search(r'model name\s*:\s*(.+)', cpuinfo)
            model = model_match.group(1).strip() if model_match else "Unknown"
            
            # Extract CPU family
            family_match = re.search(r'cpu family\s*:\s*(\d+)', cpuinfo)
            family = family_match.group(1) if family_match else "Unknown"
            
            # Detect CPU architecture
            arch = platform.machine()
            
            return self._classify(family, model, arch)
        except Exception as e:
            return self._error_result(str(e))
    
    def _scan_macos(self) -> Dict:
        """Scan on macOS systems."""
        try:
            # Use sysctl on macOS
            result = subprocess.run(
                ['sysctl', '-n', 'machdep.cpu.brand_string'],
                capture_output=True, text=True
            )
            model = result.stdout.strip() if result.returncode == 0 else "Unknown"
            
            # Get CPU family
            result = subprocess.run(
                ['sysctl', '-n', 'machdep.cpu.family'],
                capture_output=True, text=True
            )
            family = result.stdout.strip() if result.returncode == 0 else "Unknown"
            
            arch = platform.machine()
            
            return self._classify(family, model, arch)
        except Exception as e:
            return self._error_result(str(e))
    
    def _scan_generic(self) -> Dict:
        """Generic scan fallback."""
        arch = platform.machine()
        processor = platform.processor()
        
        return self._classify("Unknown", processor or "Unknown", arch)
    
    def _classify(self, family: str, model: str, arch: str) -> Dict:
        """Classify hardware into Silicon Epoch."""
        # Detect epoch from family
        epoch = 4  # Default to contemporary
        
        # Check family mapping
        if family in self.CPU_EPOCH_MAP:
            epoch = self.CPU_EPOCH_MAP[family]
        else:
            # Try to detect from model string
            for key, ep in self.CPU_EPOCH_MAP.items():
                if key in model or key in arch:
                    epoch = ep
                    break
        
        # Special handling for PowerPC
        if "PowerPC" in model or "ppc" in arch.lower():
            if "G4" in model:
                epoch = 2
            elif "G5" in model:
                epoch = 3
            elif "POWER8" in model:
                epoch = 4
        
        epoch_info = self.EPOCHS.get(epoch, self.EPOCHS[4])
        
        return {
            "family": family,
            "model": model,
            "architecture": arch,
            "epoch": epoch,
            "epoch_name": epoch_info["name"],
            "year_estimate": epoch_info["years"],
            "rustchain_multiplier": epoch_info["multiplier"],
            "system": platform.system(),
        }
    
    def _error_result(self, error: str) -> Dict:
        """Return error result."""
        return {
            "family": "Error",
            "model": "Error",
            "architecture": "Unknown",
            "epoch": -1,
            "epoch_name": "Error",
            "year_estimate": "Unknown",
            "rustchain_multiplier": 1.0,
            "error": error,
        }


def main():
    """CLI entry point."""
    scanner = HardwareScanner()
    result = scanner.scan()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
