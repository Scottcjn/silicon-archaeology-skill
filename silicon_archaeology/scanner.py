"""
Silicon Archaeology - Hardware Scanner
Detect and fingerprint vintage hardware for digital archaeology.
"""

import json
import platform
import subprocess
import re
from typing import Dict, Optional, Tuple
from pathlib import Path


# Silicon Epochs classification
SILICON_EPOCHS = {
    0: {'name': 'Pre-VLSI', 'era': 'pre-1980', 'multiplier': 4.0},
    1: {'name': 'VLSI Dawn', 'era': '1980-1992', 'multiplier': 3.5},
    2: {'name': 'RISC Wars', 'era': '1993-2005', 'multiplier': 2.5},
    3: {'name': 'x86 Dominance', 'era': '2006-2019', 'multiplier': 1.3},
    4: {'name': 'Post-Moore', 'era': '2020+', 'multiplier': 1.0},
}


def get_cpu_info() -> Dict[str, str]:
    """
    Get CPU information from the system.
    
    Returns:
        Dict with cpu_family, cpu_model, cpu_vendor, etc.
    """
    system = platform.system()
    info = {
        'system': system,
        'machine': platform.machine(),
        'processor': platform.processor(),
    }
    
    if system == 'Linux':
        info.update(_read_cpuinfo_linux())
    elif system == 'Darwin':  # macOS
        info.update(_read_sysctl_macos())
    else:
        # Fallback to platform module
        info['cpu_family'] = info.get('processor', 'Unknown')
        info['cpu_model'] = 'Unknown'
        info['cpu_vendor'] = 'Unknown'
    
    return info


def _read_cpuinfo_linux() -> Dict[str, str]:
    """Read CPU info from /proc/cpuinfo on Linux."""
    info = {'cpu_family': 'Unknown', 'cpu_model': 'Unknown', 'cpu_vendor': 'Unknown'}
    
    try:
        with open('/proc/cpuinfo', 'r') as f:
            content = f.read()
        
        # Extract common fields
        for line in content.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key == 'model name':
                    info['cpu_model'] = value
                    info['cpu_family'] = value.split()[0] if value else 'Unknown'
                elif key == 'vendor_id':
                    info['cpu_vendor'] = value
                elif key == 'cpu family':
                    info['cpu_family_num'] = value
                elif key == 'model':
                    info['cpu_model_num'] = value
                elif key == 'cpu':
                    # PowerPC format
                    info['cpu_model'] = value
                    if 'PowerPC' in value or 'PPC' in value:
                        info['cpu_family'] = 'PowerPC'
                        info['cpu_vendor'] = 'IBM/Motorola'
        
        # ARM detection
        if 'ARM' in content or 'aarch64' in platform.machine():
            info['cpu_vendor'] = 'ARM'
            info['cpu_family'] = 'ARM'
            
    except FileNotFoundError:
        pass
    
    return info


def _read_sysctl_macos() -> Dict[str, str]:
    """Read CPU info via sysctl on macOS."""
    info = {'cpu_family': 'Unknown', 'cpu_model': 'Unknown', 'cpu_vendor': 'Unknown'}
    
    try:
        # Get CPU brand string
        result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            brand = result.stdout.strip()
            info['cpu_model'] = brand
            
            # Detect Apple Silicon
            if 'Apple' in brand or 'M1' in brand or 'M2' in brand or 'M3' in brand:
                info['cpu_vendor'] = 'Apple'
                info['cpu_family'] = 'Apple Silicon'
            # Intel Mac
            elif 'Intel' in brand:
                info['cpu_vendor'] = 'Intel'
                info['cpu_family'] = 'Intel Core'
        
        # Get CPU family
        result = subprocess.run(['sysctl', '-n', 'hw.cpufamily'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            info['cpu_family_num'] = result.stdout.strip()
            
    except Exception:
        pass
    
    return info


def classify_epoch(cpu_info: Dict[str, str]) -> Tuple[int, str, int]:
    """
    Classify CPU into a Silicon Epoch.
    
    Args:
        cpu_info: Dict from get_cpu_info()
        
    Returns:
        Tuple of (epoch, era_string, rustchain_multiplier)
    """
    family = cpu_info.get('cpu_family', '').lower()
    model = cpu_info.get('cpu_model', '').lower()
    vendor = cpu_info.get('cpu_vendor', '').lower()
    machine = cpu_info.get('machine', '').lower()
    
    # Pre-VLSI (Epoch 0) - pre-1980
    pre_vlsi_indicators = ['6502', 'z80', '8080', '8086', '6800', '6809']
    for indicator in pre_vlsi_indicators:
        if indicator in model or indicator in family:
            return 0, SILICON_EPOCHS[0]['era'], SILICON_EPOCHS[0]['multiplier']
    
    # VLSI Dawn (Epoch 1) - 1980-1992
    vlsi_indicators = ['68000', '68020', '68030', '68040', '68k', '80286', '80386', '80486', 
                       'amiga', 'atari', 'macintosh', 'mac ii', 'sun-3', 'sparcstation 1']
    for indicator in vlsi_indicators:
        if indicator in model or indicator in family:
            return 1, SILICON_EPOCHS[1]['era'], SILICON_EPOCHS[1]['multiplier']
    
    # RISC Wars (Epoch 2) - 1993-2005
    risc_indicators = ['powerpc', 'ppc', 'g3', 'g4', 'g5', 'sparc v', 'mips r', 
                       'alpha', 'pa-risc', 'pentium', 'pentium ii', 'pentium iii', 'pentium 4',
                       'athlon', 'k6', 'k7']
    for indicator in risc_indicators:
        if indicator in model or indicator in family:
            return 2, SILICON_EPOCHS[2]['era'], SILICON_EPOCHS[2]['multiplier']
    
    # x86 Dominance (Epoch 3) - 2006-2019
    x86_indicators = ['core 2', 'core i3', 'core i5', 'core i7', 'xeon', 'opteron',
                      'nehalem', 'sandy', 'ivy', 'haswell', 'skylake', 'kaby', 'coffee',
                      'ryzen', 'epyc', 'zen']
    for indicator in x86_indicators:
        if indicator in model or indicator in family:
            return 3, SILICON_EPOCHS[3]['era'], SILICON_EPOCHS[3]['multiplier']
    
    # Post-Moore (Epoch 4) - 2020+
    post_moore_indicators = ['apple m1', 'apple m2', 'apple m3', 'apple silicon', 
                             'risc-v', 'riscv', 'aarch64', 'arm v9', 'meteor lake',
                             'lunar lake', 'arrow lake']
    for indicator in post_moore_indicators:
        if indicator in model or indicator in family or indicator in machine:
            return 4, SILICON_EPOCHS[4]['era'], SILICON_EPOCHS[4]['multiplier']
    
    # Default based on architecture
    if 'aarch64' in machine or 'arm64' in machine:
        return 4, SILICON_EPOCHS[4]['era'], SILICON_EPOCHS[4]['multiplier']
    
    # Default to x86 Dominance for modern Intel/AMD
    if 'x86_64' in machine:
        return 3, SILICON_EPOCHS[3]['era'], SILICON_EPOCHS[3]['multiplier']
    
    # Fallback to Post-Moore
    return 4, SILICON_EPOCHS[4]['era'], SILICON_EPOCHS[4]['multiplier']


def estimate_year(epoch: int) -> str:
    """
    Estimate manufacturing year range from epoch.
    
    Args:
        epoch: Silicon epoch (0-4)
        
    Returns:
        Year range string
    """
    return SILICON_EPOCHS.get(epoch, SILICON_EPOCHS[4])['era']


def scan_hardware() -> Dict:
    """
    Scan local hardware and return a structured report.
    
    Returns:
        Dict with family, model, epoch, year_estimate, rustchain_multiplier
    """
    cpu_info = get_cpu_info()
    epoch, era, multiplier = classify_epoch(cpu_info)
    
    return {
        'family': cpu_info.get('cpu_family', 'Unknown'),
        'model': cpu_info.get('cpu_model', 'Unknown'),
        'vendor': cpu_info.get('cpu_vendor', 'Unknown'),
        'epoch': epoch,
        'epoch_name': SILICON_EPOCHS[epoch]['name'],
        'year_estimate': era,
        'rustchain_multiplier': multiplier,
        'system': cpu_info.get('system', 'Unknown'),
        'machine': cpu_info.get('machine', 'Unknown'),
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Scan hardware for Silicon Epoch classification')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--quiet', '-q', action='store_true', help='Minimal output')
    
    args = parser.parse_args()
    
    result = scan_hardware()
    
    if args.json:
        print(json.dumps(result, indent=2))
    elif args.quiet:
        print(f"Epoch {result['epoch']}: {result['family']} ({result['rustchain_multiplier']}x)")
    else:
        print(f"\n🖥️  Hardware Scanner Results")
        print("=" * 40)
        print(f"CPU Family:  {result['family']}")
        print(f"CPU Model:   {result['model']}")
        print(f"Vendor:      {result['vendor']}")
        print(f"Epoch:       {result['epoch']} ({result['epoch_name']})")
        print(f"Year Range:  {result['year_estimate']}")
        print(f"Mining Mult: {result['rustchain_multiplier']}x")
        print(f"System:      {result['system']} ({result['machine']})")
        print()
