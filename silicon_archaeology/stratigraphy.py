"""
Silicon Archaeology - Stratigraphy Epoch Classifier
Classify hardware into Silicon Epochs based on the Echoes of the Silicon Age paper.
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class EpochInfo:
    """Information about a Silicon Epoch."""
    number: int
    name: str
    era: str
    multiplier: float
    rarity_score: float
    description: str


# Silicon Epochs from the Echoes of the Silicon Age paper
SILICON_EPOCHS: Dict[int, EpochInfo] = {
    0: EpochInfo(
        number=0,
        name='Pre-VLSI',
        era='pre-1980',
        multiplier=4.0,
        rarity_score=0.95,
        description='Before Very Large Scale Integration. Discrete components, early microprocessors.'
    ),
    1: EpochInfo(
        number=1,
        name='VLSI Dawn',
        era='1980-1992',
        multiplier=3.5,
        rarity_score=0.80,
        description='Early VLSI chips. 16/32-bit microprocessors, GUI computers, workstations.'
    ),
    2: EpochInfo(
        number=2,
        name='RISC Wars',
        era='1993-2005',
        multiplier=2.5,
        rarity_score=0.50,
        description='RISC vs CISC competition. PowerPC, SPARC, MIPS, Alpha, early Pentium.'
    ),
    3: EpochInfo(
        number=3,
        name='x86 Dominance',
        era='2006-2019',
        multiplier=1.3,
        rarity_score=0.20,
        description='Intel and AMD x86-64 dominated. Multi-core, hyperthreading, cloud computing.'
    ),
    4: EpochInfo(
        number=4,
        name='Post-Moore',
        era='2020+',
        multiplier=1.0,
        rarity_score=0.05,
        description='Beyond Moore\'s Law. Apple Silicon, RISC-V, heterogeneous computing.'
    ),
}


# Known hardware database - 50+ entries across all epochs
KNOWN_HARDWARE: Dict[str, Dict] = {
    # Epoch 0: Pre-VLSI (pre-1980)
    'altair_8800': {'family': '8080', 'model': 'Altair 8800', 'year': 1975, 'epoch': 0},
    'imsai_8080': {'family': '8080', 'model': 'IMSAI 8080', 'year': 1975, 'epoch': 0},
    'apple_ii': {'family': '6502', 'model': 'Apple II', 'year': 1977, 'epoch': 0},
    'trs80': {'family': 'Z80', 'model': 'TRS-80 Model I', 'year': 1977, 'epoch': 0},
    'pet_2001': {'family': '6502', 'model': 'Commodore PET 2001', 'year': 1977, 'epoch': 0},
    'apple_i': {'family': '6502', 'model': 'Apple I', 'year': 1976, 'epoch': 0},
    'pdp11': {'family': 'PDP-11', 'model': 'DEC PDP-11', 'year': 1970, 'epoch': 0},
    'nova': {'family': 'Nova', 'model': 'Data General Nova', 'year': 1969, 'epoch': 0},
    'ibm_5100': {'family': 'PALM', 'model': 'IBM 5100', 'year': 1975, 'epoch': 0},
    'sol20': {'family': '8080', 'model': 'Processor Technology SOL-20', 'year': 1976, 'epoch': 0},
    
    # Epoch 1: VLSI Dawn (1980-1992)
    'ibm_pc': {'family': '8088', 'model': 'IBM PC', 'year': 1981, 'epoch': 1},
    'ibm_pc_xt': {'family': '8088', 'model': 'IBM PC XT', 'year': 1983, 'epoch': 1},
    'ibm_pc_at': {'family': '80286', 'model': 'IBM PC AT', 'year': 1984, 'epoch': 1},
    'mac_128k': {'family': '68000', 'model': 'Macintosh 128K', 'year': 1984, 'epoch': 1},
    'mac_ii': {'family': '68020', 'model': 'Macintosh II', 'year': 1987, 'epoch': 1},
    'amiga_500': {'family': '68000', 'model': 'Amiga 500', 'year': 1987, 'epoch': 1},
    'amiga_2000': {'family': '68000', 'model': 'Amiga 2000', 'year': 1986, 'epoch': 1},
    'atari_st': {'family': '68000', 'model': 'Atari ST', 'year': 1985, 'epoch': 1},
    'sun3': {'family': '68020', 'model': 'Sun-3', 'year': 1985, 'epoch': 1},
    'sparcstation1': {'family': 'SPARC', 'model': 'SPARCstation 1', 'year': 1989, 'epoch': 1},
    'decstation': {'family': 'MIPS', 'model': 'DECstation 3100', 'year': 1989, 'epoch': 1},
    'next_cube': {'family': '68030', 'model': 'NeXT Cube', 'year': 1988, 'epoch': 1},
    'commodore_128': {'family': '6502/8502', 'model': 'Commodore 128', 'year': 1985, 'epoch': 1},
    
    # Epoch 2: RISC Wars (1993-2005)
    'powermac_g3': {'family': 'PowerPC G3', 'model': 'Power Macintosh G3', 'year': 1997, 'epoch': 2},
    'powermac_g4': {'family': 'PowerPC G4', 'model': 'Power Macintosh G4', 'year': 1999, 'epoch': 2},
    'powermac_g5': {'family': 'PowerPC G5', 'model': 'Power Macintosh G5', 'year': 2003, 'epoch': 2},
    'sun_ultra': {'family': 'SPARC', 'model': 'Sun Ultra 1', 'year': 1995, 'epoch': 2},
    'sgi_octane': {'family': 'MIPS', 'model': 'SGI Octane', 'year': 1997, 'epoch': 2},
    'alpha_xp': {'family': 'Alpha', 'model': 'AlphaStation XP', 'year': 1995, 'epoch': 2},
    'hp_9000': {'family': 'PA-RISC', 'model': 'HP 9000', 'year': 1993, 'epoch': 2},
    'pentium_pro': {'family': 'x86', 'model': 'Pentium Pro', 'year': 1995, 'epoch': 2},
    'pentium_ii': {'family': 'x86', 'model': 'Pentium II', 'year': 1997, 'epoch': 2},
    'pentium_iii': {'family': 'x86', 'model': 'Pentium III', 'year': 1999, 'epoch': 2},
    'pentium_4': {'family': 'x86', 'model': 'Pentium 4', 'year': 2000, 'epoch': 2},
    'athlon_k7': {'family': 'x86', 'model': 'AMD Athlon K7', 'year': 1999, 'epoch': 2},
    'imac_g3': {'family': 'PowerPC G3', 'model': 'iMac G3', 'year': 1998, 'epoch': 2},
    'ibook_g3': {'family': 'PowerPC G3', 'model': 'iBook G3', 'year': 1999, 'epoch': 2},
    'powerbook_g4': {'family': 'PowerPC G4', 'model': 'PowerBook G4', 'year': 2001, 'epoch': 2},
    
    # Epoch 3: x86 Dominance (2006-2019)
    'core2duo': {'family': 'x86-64', 'model': 'Intel Core 2 Duo', 'year': 2006, 'epoch': 3},
    'core_i7': {'family': 'x86-64', 'model': 'Intel Core i7', 'year': 2008, 'epoch': 3},
    'xeon': {'family': 'x86-64', 'model': 'Intel Xeon', 'year': 2006, 'epoch': 3},
    'opteron': {'family': 'x86-64', 'model': 'AMD Opteron', 'year': 2003, 'epoch': 3},
    'phenom': {'family': 'x86-64', 'model': 'AMD Phenom', 'year': 2007, 'epoch': 3},
    'ryzen': {'family': 'x86-64', 'model': 'AMD Ryzen', 'year': 2017, 'epoch': 3},
    'epyc': {'family': 'x86-64', 'model': 'AMD EPYC', 'year': 2017, 'epoch': 3},
    'imac_intel': {'family': 'x86-64', 'model': 'iMac Intel', 'year': 2006, 'epoch': 3},
    'macbook_pro': {'family': 'x86-64', 'model': 'MacBook Pro', 'year': 2006, 'epoch': 3},
    'mac_pro': {'family': 'x86-64', 'model': 'Mac Pro', 'year': 2006, 'epoch': 3},
    'xeon_phi': {'family': 'x86-64', 'model': 'Intel Xeon Phi', 'year': 2012, 'epoch': 3},
    
    # Epoch 4: Post-Moore (2020+)
    'apple_m1': {'family': 'ARM', 'model': 'Apple M1', 'year': 2020, 'epoch': 4},
    'apple_m2': {'family': 'ARM', 'model': 'Apple M2', 'year': 2022, 'epoch': 4},
    'apple_m3': {'family': 'ARM', 'model': 'Apple M3', 'year': 2023, 'epoch': 4},
    'riscv_unmatched': {'family': 'RISC-V', 'model': 'SiFive Unmatched', 'year': 2020, 'epoch': 4},
    'graviton2': {'family': 'ARM', 'model': 'AWS Graviton2', 'year': 2020, 'epoch': 4},
    'graviton3': {'family': 'ARM', 'model': 'AWS Graviton3', 'year': 2022, 'epoch': 4},
    'snapdragon_8cx': {'family': 'ARM', 'model': 'Snapdragon 8cx', 'year': 2019, 'epoch': 4},
    'meteor_lake': {'family': 'x86-64', 'model': 'Intel Meteor Lake', 'year': 2023, 'epoch': 4},
    'ryzen_ai': {'family': 'x86-64', 'model': 'AMD Ryzen AI', 'year': 2023, 'epoch': 4},
}


def classify_hardware(
    family: str,
    model: str,
    year: Optional[int] = None
) -> Tuple[int, str, float]:
    """
    Classify hardware into a Silicon Epoch.
    
    Args:
        family: CPU family name (e.g., 'PowerPC', 'x86', 'ARM')
        model: CPU model string (e.g., 'PowerPC G4', 'Intel Core i7')
        year: Optional manufacturing year for additional classification
        
    Returns:
        Tuple of (epoch_number, era_string, rarity_score)
    """
    family_lower = family.lower()
    model_lower = model.lower()
    
    # Check known hardware database first
    for key, hw_info in KNOWN_HARDWARE.items():
        if hw_info['family'].lower() in family_lower or hw_info['model'].lower() in model_lower:
            epoch = hw_info['epoch']
            return epoch, SILICON_EPOCHS[epoch].era, SILICON_EPOCHS[epoch].rarity_score
    
    # Classification by CPU family
    # Epoch 0: Pre-VLSI
    pre_vlsi_families = ['6502', '6800', '6809', 'z80', '8080', '8086', '8088']
    for f in pre_vlsi_families:
        if f in family_lower or f in model_lower:
            return 0, SILICON_EPOCHS[0].era, SILICON_EPOCHS[0].rarity_score
    
    # Epoch 1: VLSI Dawn
    vlsi_families = ['68000', '68020', '68030', '68040', '80286', '80386', '80486']
    for f in vlsi_families:
        if f in family_lower or f in model_lower:
            return 1, SILICON_EPOCHS[1].era, SILICON_EPOCHS[1].rarity_score
    
    # Epoch 2: RISC Wars
    risc_families = ['powerpc', 'ppc', 'g3', 'g4', 'g5', 'sparc', 'mips', 'alpha', 'pa-risc']
    for f in risc_families:
        if f in family_lower or f in model_lower:
            return 2, SILICON_EPOCHS[2].era, SILICON_EPOCHS[2].rarity_score
    
    # Epoch 3: x86 Dominance
    x86_families = ['core 2', 'core i', 'xeon', 'opteron', 'phenom', 'ryzen', 'epyc']
    for f in x86_families:
        if f in family_lower or f in model_lower:
            return 3, SILICON_EPOCHS[3].era, SILICON_EPOCHS[3].rarity_score
    
    # Epoch 4: Post-Moore
    post_moore_families = ['apple m', 'risc-v', 'riscv', 'aarch64', 'arm', 'graviton', 'snapdragon']
    for f in post_moore_families:
        if f in family_lower or f in model_lower:
            return 4, SILICON_EPOCHS[4].era, SILICON_EPOCHS[4].rarity_score
    
    # Year-based fallback
    if year:
        if year < 1980:
            return 0, SILICON_EPOCHS[0].era, SILICON_EPOCHS[0].rarity_score
        elif year < 1993:
            return 1, SILICON_EPOCHS[1].era, SILICON_EPOCHS[1].rarity_score
        elif year < 2006:
            return 2, SILICON_EPOCHS[2].era, SILICON_EPOCHS[2].rarity_score
        elif year < 2020:
            return 3, SILICON_EPOCHS[3].era, SILICON_EPOCHS[3].rarity_score
        else:
            return 4, SILICON_EPOCHS[4].era, SILICON_EPOCHS[4].rarity_score
    
    # Default to Post-Moore
    return 4, SILICON_EPOCHS[4].era, SILICON_EPOCHS[4].rarity_score


def get_epoch_info(epoch: int) -> EpochInfo:
    """Get detailed information about a Silicon Epoch."""
    return SILICON_EPOCHS.get(epoch, SILICON_EPOCHS[4])


def get_known_hardware(epoch: Optional[int] = None) -> List[Dict]:
    """
    Get list of known hardware entries.
    
    Args:
        epoch: Optional filter by epoch number
        
    Returns:
        List of hardware dicts
    """
    if epoch is not None:
        return [hw for hw in KNOWN_HARDWARE.values() if hw['epoch'] == epoch]
    return list(KNOWN_HARDWARE.values())


def to_json(family: str, model: str, year: Optional[int] = None) -> str:
    """
    Classify hardware and return JSON-serializable output.
    
    Args:
        family: CPU family name
        model: CPU model string
        year: Optional manufacturing year
        
    Returns:
        JSON string with classification results
    """
    epoch, era, rarity = classify_hardware(family, model, year)
    info = get_epoch_info(epoch)
    
    result = {
        'input': {
            'family': family,
            'model': model,
            'year': year
        },
        'classification': {
            'epoch': epoch,
            'era': era,
            'epoch_name': info.name,
            'rarity_score': rarity,
            'rustchain_multiplier': info.multiplier,
            'description': info.description
        }
    }
    
    return json.dumps(result, indent=2)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Classify hardware into Silicon Epochs')
    parser.add_argument('family', help='CPU family (e.g., PowerPC, x86)')
    parser.add_argument('model', help='CPU model (e.g., G4, Core i7)')
    parser.add_argument('--year', '-y', type=int, help='Manufacturing year')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    if args.json:
        print(to_json(args.family, args.model, args.year))
    else:
        epoch, era, rarity = classify_hardware(args.family, args.model, args.year)
        info = get_epoch_info(epoch)
        
        print(f"\n📊 Silicon Stratigraphy Classification")
        print("=" * 50)
        print(f"CPU Family:    {args.family}")
        print(f"CPU Model:     {args.model}")
        if args.year:
            print(f"Year:          {args.year}")
        print(f"\nEpoch:         {epoch} ({info.name})")
        print(f"Era:           {era}")
        print(f"Rarity Score:  {rarity:.2f}")
        print(f"Mining Mult:   {info.multiplier}x")
        print(f"\n{info.description}")
        print()
