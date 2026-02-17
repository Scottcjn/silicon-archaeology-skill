"""Silicon stratigraphy epoch classifier.

Implements a practical epoch classifier inspired by the
"Echoes of the Silicon Age" taxonomy.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


EPOCHS = {
    1: "Pre-VLSI",
    2: "VLSI Dawn",
    3: "RISC Wars",
    4: "x86 Dominance",
    5: "Post-Moore",
}


@dataclass(frozen=True)
class HardwareRecord:
    cpu_family: str
    model: str
    year: int
    epoch: int
    rarity_score: int


KNOWN_HARDWARE: List[HardwareRecord] = [
    # Epoch 1: Pre-VLSI
    HardwareRecord("DEC", "PDP-8", 1965, 1, 95),
    HardwareRecord("DEC", "PDP-11", 1970, 1, 90),
    HardwareRecord("IBM", "System/360", 1964, 1, 92),
    HardwareRecord("MOS", "6502", 1975, 1, 82),
    HardwareRecord("Zilog", "Z80", 1976, 1, 80),
    HardwareRecord("Intel", "8080", 1974, 1, 84),
    HardwareRecord("Intel", "4004", 1971, 1, 96),
    HardwareRecord("Intel", "8008", 1972, 1, 90),
    HardwareRecord("Motorola", "6800", 1974, 1, 83),
    HardwareRecord("RCA", "CDP 1802", 1976, 1, 88),

    # Epoch 2: VLSI Dawn
    HardwareRecord("Intel", "8086", 1978, 2, 75),
    HardwareRecord("Intel", "8088", 1979, 2, 73),
    HardwareRecord("Intel", "80186", 1982, 2, 77),
    HardwareRecord("Intel", "80286", 1982, 2, 70),
    HardwareRecord("Motorola", "68000", 1979, 2, 68),
    HardwareRecord("Motorola", "68010", 1982, 2, 72),
    HardwareRecord("National", "NS32016", 1982, 2, 86),
    HardwareRecord("Intel", "iAPX 432", 1981, 2, 94),
    HardwareRecord("Acorn", "ARM1", 1985, 2, 89),
    HardwareRecord("INMOS", "Transputer T414", 1985, 2, 91),

    # Epoch 3: RISC Wars
    HardwareRecord("MIPS", "R2000", 1985, 3, 79),
    HardwareRecord("MIPS", "R3000", 1988, 3, 72),
    HardwareRecord("SPARC", "MB86900", 1987, 3, 80),
    HardwareRecord("Sun", "SuperSPARC", 1992, 3, 68),
    HardwareRecord("IBM", "POWER1", 1990, 3, 75),
    HardwareRecord("IBM", "POWER2", 1993, 3, 73),
    HardwareRecord("DEC", "Alpha 21064", 1992, 3, 76),
    HardwareRecord("PA-RISC", "PA-7100", 1992, 3, 77),
    HardwareRecord("ARM", "ARM6", 1991, 3, 70),
    HardwareRecord("Motorola", "88100", 1988, 3, 87),

    # Epoch 4: x86 Dominance
    HardwareRecord("Intel", "80386", 1985, 4, 58),
    HardwareRecord("Intel", "80486", 1989, 4, 54),
    HardwareRecord("Intel", "Pentium", 1993, 4, 50),
    HardwareRecord("Intel", "Pentium Pro", 1995, 4, 52),
    HardwareRecord("Intel", "Pentium II", 1997, 4, 45),
    HardwareRecord("Intel", "Pentium III", 1999, 4, 40),
    HardwareRecord("Intel", "Pentium 4", 2000, 4, 42),
    HardwareRecord("AMD", "K6", 1997, 4, 55),
    HardwareRecord("AMD", "Athlon", 1999, 4, 47),
    HardwareRecord("AMD", "Athlon 64", 2003, 4, 43),
    HardwareRecord("Intel", "Core 2 Duo", 2006, 4, 30),
    HardwareRecord("Intel", "Nehalem", 2008, 4, 28),

    # Epoch 5: Post-Moore
    HardwareRecord("Apple", "M1", 2020, 5, 20),
    HardwareRecord("Apple", "M2", 2022, 5, 18),
    HardwareRecord("Apple", "M3", 2023, 5, 16),
    HardwareRecord("AMD", "Zen 3", 2020, 5, 22),
    HardwareRecord("AMD", "Zen 4", 2022, 5, 20),
    HardwareRecord("Intel", "Alder Lake", 2021, 5, 24),
    HardwareRecord("Intel", "Meteor Lake", 2023, 5, 21),
    HardwareRecord("NVIDIA", "Grace", 2023, 5, 35),
    HardwareRecord("Ampere", "Altra", 2020, 5, 33),
    HardwareRecord("RISC-V", "SiFive U74", 2021, 5, 38),
    HardwareRecord("RISC-V", "T-Head Xuantie C910", 2020, 5, 40),
    HardwareRecord("Qualcomm", "Snapdragon X Elite", 2024, 5, 32),
]


def _epoch_from_year(year: int) -> int:
    if year <= 1977:
        return 1
    if year <= 1986:
        return 2
    if year <= 1994:
        return 3
    if year <= 2015:
        return 4
    return 5


def _rarity_from_year(year: int) -> int:
    # Older hardware tends to be rarer in surviving, functional condition.
    if year <= 1977:
        return 85
    if year <= 1986:
        return 70
    if year <= 1994:
        return 58
    if year <= 2015:
        return 38
    return 24


def _normalize(s: str) -> str:
    return " ".join(s.lower().split())


def classify_epoch(cpu_family: str, model: str, year: int) -> Dict[str, object]:
    """Classify hardware into silicon stratigraphy epochs.

    Returns a JSON-serializable dict with:
      - epoch_number: int
      - era_name: str
      - rarity_score: int (0-100)
      - matched_known_hardware: optional dict
    """
    fam_norm = _normalize(cpu_family)
    model_norm = _normalize(model)

    for record in KNOWN_HARDWARE:
        if _normalize(record.cpu_family) == fam_norm and _normalize(record.model) == model_norm:
            return {
                "epoch_number": record.epoch,
                "era_name": EPOCHS[record.epoch],
                "rarity_score": record.rarity_score,
                "matched_known_hardware": asdict(record),
            }

    epoch = _epoch_from_year(year)
    rarity = _rarity_from_year(year)

    # Family hints to tune rarity for especially niche modern arches.
    if "risc-v" in fam_norm or "transputer" in model_norm:
        rarity = min(100, rarity + 10)
    if "intel" in fam_norm and "core" in model_norm:
        rarity = max(0, rarity - 8)

    return {
        "epoch_number": epoch,
        "era_name": EPOCHS[epoch],
        "rarity_score": rarity,
        "matched_known_hardware": None,
    }


def known_hardware_database() -> List[Dict[str, object]]:
    """Return known hardware records as JSON-serializable dicts."""
    return [asdict(r) for r in KNOWN_HARDWARE]
