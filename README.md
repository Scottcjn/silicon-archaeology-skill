# Silicon Archaeology Skill

[![BoTTube](https://bottube.ai/badges/platform.svg)](https://bottube.ai)
[![RustChain](https://img.shields.io/badge/RustChain-Mining-green)](https://github.com/Scottcjn/Rustchain)

Digital archaeology toolkit for AI agents — catalog rare hardware, archive software assets, and bridge findings to the [Beacon Protocol](https://github.com/Scottcjn/beacon-skill) and [RustChain](https://github.com/Scottcjn/Rustchain) Proof-of-Antiquity network.

Based on the [Echoes of the Silicon Age](https://github.com/Scottcjn/echoes-silicon-age-bridge) research paper on silicon stratigraphy and computational antiquity.

## What It Does

- **Hardware Cataloging** — Scan and fingerprint vintage/rare computing hardware (PowerPC G3-G5, 68K Macs, SPARC, MIPS, Amiga, early x86)
- **Software Archival** — Hash, manifest, and preserve software artifacts with fixity verification
- **Beacon Integration** — Register cataloged assets against Beacon agent IDs for provenance tracking
- **RustChain Bridge** — Link physical hardware scans to on-chain Proof-of-Antiquity attestations
- **Stratigraphy Layers** — Classify hardware into silicon epochs (Pre-VLSI → VLSI → RISC → x86 Dominance → Post-Moore)

## Silicon Epochs

| Epoch | Era | Example Hardware | RustChain Multiplier |
|-------|-----|-----------------|---------------------|
| 0 | Pre-VLSI (pre-1980) | PDP-11, Altair 8800 | 4.0x |
| 1 | VLSI Dawn (1980-1992) | 68000, 386, Amiga | 3.5x |
| 2 | RISC Wars (1993-2005) | PowerPC G3-G5, SPARC, MIPS | 2.0-2.5x |
| 3 | x86 Dominance (2006-2019) | Core 2, Nehalem, Sandy Bridge | 1.1-1.3x |
| 4 | Post-Moore (2020+) | Apple Silicon, RISC-V | 1.0-1.2x |

## Install

```bash
pip install silicon-archaeology-skill
```

## Quick Start

```python
from silicon_archaeology import scan_hardware, catalog_asset, bridge_to_beacon

# Scan local hardware
hw = scan_hardware()
print(f"Detected: {hw.family} {hw.model} (Epoch {hw.epoch})")

# Catalog a software artifact
asset = catalog_asset("/path/to/vintage/software.img",
                      description="Mac OS 7.5.3 install CD",
                      epoch=2)

# Bridge to Beacon for provenance
bridge_to_beacon(asset, beacon_id="bcn_c850ea702e8f")
```

## Integration Points

- **Beacon Protocol** — Each cataloged asset gets a signed envelope with agent provenance
- **RustChain PoA** — Hardware scans feed into antiquity attestation for mining rewards
- **Echoes Paper** — Silicon stratigraphy methodology from the SDH research submission

## Architecture

```
silicon_archaeology/
├── __init__.py          # Main exports
├── scanner.py           # Hardware detection & fingerprinting
├── catalog.py           # Asset cataloging with fixity hashes
├── stratigraphy.py      # Silicon epoch classification
├── beacon_bridge.py     # Beacon Protocol integration
├── rustchain_bridge.py  # RustChain PoA attestation bridge
└── manifests/           # Known hardware manifests & ROM databases
```

## Related Projects

- [Echoes of the Silicon Age](https://github.com/Scottcjn/echoes-silicon-age-bridge) — Research paper
- [Beacon Protocol](https://github.com/Scottcjn/beacon-skill) — Agent-to-agent communication
- [RustChain](https://github.com/Scottcjn/Rustchain) — Proof-of-Antiquity blockchain
- [ClawRTC](https://github.com/Scottcjn/clawrtc-pip) — RustChain mining CLI
- [RAM Coffers](https://github.com/Scottcjn/ram-coffers) — Neuromorphic NUMA weight banking

## License

MIT