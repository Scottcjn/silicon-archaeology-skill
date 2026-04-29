# Contributing to Silicon Archaeology Skill

This skill enables AI agents to catalog rare/vintage hardware, archive software assets, and bridge findings to the Beacon Protocol and RustChain Proof-of-Antiquity network.

## Getting Started

### Prerequisites

- Python 3.8+
- `requests`, `hashlib`, `json` (stdlib)

### Setup

```bash
git clone https://github.com/Scottcjn/silicon-archaeology-skill.git
cd silicon-archaeology-skill
pip install -e .

# Run tests
python -m pytest tests/
```

## Project Structure

```
silicon_archaeology/
├── __init__.py          # Main exports
├── scanner.py           # Hardware fingerprinting
├── beacon.py            # Beacon Protocol integration
├── archiver.py          # Software asset archival
└── epoch.py            # Silicon epoch classification
```

## Adding Hardware Support

To add support for a new hardware family:

1. Add the detection logic in `scanner.py`
2. Define the epoch multiplier in `epoch.py`
3. Add tests in `tests/`
4. Update README.md silicon epochs table

```python
def detect_mips_hardware() -> Optional[HardwareProfile]:
    """Detect MIPS-based workstations (SGI Indy, Decstation)."""
    if not is_mips_system():
        return None
    return HardwareProfile(
        family="mips", model=read_model(),
        epoch=2, antiquity_multiplier=2.0,
    )
```

## Beacon Integration

```python
from silicon_archaeology import bridge_to_beacon
asset = scan_hardware()
receipt = bridge_to_beacon(asset, beacon_id="bcn_...")
print(f"Attestation: {receipt.attestation_hash}")
```

## Silicon Epochs

| Epoch | Era | Hardware | Multiplier |
|-------|-----|----------|------------|
| 0 | Pre-VLSI (pre-1980) | PDP-11, Altair 8800 | 4.0x |
| 1 | VLSI Dawn (1980-1992) | 68000, 386, Amiga | 3.5x |
| 2 | RISC Wars (1993-2005) | PowerPC G3-G5, SPARC, MIPS | 2.0-2.5x |
| 3 | x86 Dominance (2006-2019) | Core 2, Nehalem, Sandy Bridge | 1.1-1.3x |
| 4 | Post-Moore (2020+) | Apple Silicon, RISC-V | 1.0-1.2x |

## Testing

```bash
python -m pytest tests/ -v
python -c "from silicon_archaeology import scan_hardware; print(scan_hardware())"
```

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
