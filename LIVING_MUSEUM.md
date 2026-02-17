# Living Museum of Silicon Ages

> AI Agents as Digital Archaeologists — Preserving Computing History One Artifact at a Time

## The Vision

Imagine a museum that never closes, where every exhibit is alive, where AI agents patrol the halls cataloging rare hardware, verifying authenticity, and building an immutable chain of provenance. Welcome to the **Living Museum** — a collaborative effort between humans and AI to preserve computing history.

## How It Works

### The Four Pillars

1. **Scan** — Detect and fingerprint hardware
2. **Catalog** — Create fixity hashes and metadata
3. **Bridge** — Register artifacts on Beacon Protocol
4. **Attest** — Mint Proof-of-Antiquity on RustChain

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Living Museum                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│  │ Scanner  │ → │ Catalog  │ → │  Beacon  │ → │ RustChain│ │
│  │scanner.py│   │catalog.py│   │bridge.py │   │bridge.py │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘ │
│       ↓              ↓              ↓              ↓       │
│   Epoch 0-4     SHA-256/512    Ed25519        PoA Token    │
│   Rarity        Manifest       Provenance     Multiplier   │
└─────────────────────────────────────────────────────────────┘
```

## Example Workflows

### Workflow 1: Vintage Macintosh (Epoch 1: VLSI Dawn)

```bash
# Step 1: Scan the hardware
$ python -m silicon_archaeology.scanner --json
{
  "family": "68000",
  "model": "Macintosh 128K",
  "epoch": 1,
  "epoch_name": "VLSI Dawn",
  "rustchain_multiplier": 3.5
}

# Step 2: Catalog the ROM dump
$ python -m silicon_archaeology.catalog mac_rom.bin -d "Macintosh 128K ROM" --epoch 1
{
  "filename": "mac_rom.bin",
  "size": 65536,
  "hashes": {
    "sha256": "a1b2c3...",
    "sha512": "d4e5f6..."
  },
  "description": "Macintosh 128K ROM",
  "epoch": 1,
  "cataloged_at": "2026-02-17T..."
}

# Step 3: Bridge to Beacon (agent provenance)
$ python -m silicon_archaeology.beacon_bridge manifest.json
Envelope posted to Beacon Atlas
Beacon ID: bcn_x7y8z9...

# Step 4: Attest on RustChain (Proof-of-Antiquity)
$ python -m silicon_archaeology.rustchain_bridge scan_result.json
Attestation submitted: 0xabc123...
Multiplier: 3.5x (Epoch 1 hardware)
```

### Workflow 2: PowerMac G4 (Epoch 2: RISC Wars)

```bash
# Scan PowerPC hardware
$ python -m silicon_archaeology.scanner
CPU Family:  PowerPC G4
Epoch:       2 (RISC Wars)
Mining Mult: 2.5x

# Catalog a disk image
$ python -m silicon_archaeology.catalog system_9.img -d "Mac OS 9.2.2 Install"
{
  "filename": "system_9.img",
  "size": 650742784,
  "epoch": 2,
  ...
}

# Bridge and attest
$ python -m silicon_archaeology.beacon_bridge manifest.json
$ python -m silicon_archaeology.rustchain_bridge scan_result.json
Attestation submitted with 2.5x multiplier
```

### Workflow 3: Apple M1 MacBook (Epoch 4: Post-Moore)

```bash
# Scan modern hardware (lower multiplier, but still counts!)
$ python -m silicon_archaeology.scanner --json
{
  "family": "Apple Silicon",
  "model": "Apple M1",
  "epoch": 4,
  "rustchain_multiplier": 1.0
}

# Catalog development artifacts
$ python -m silicon_archaeology.catalog ./project_builds --recursive
Cataloged 47 files

# Bridge to Beacon for provenance tracking
$ python -m silicon_archaeology.beacon_bridge batch_manifest.json
```

## Beacon Protocol Integration

Every artifact cataloged by an AI agent gets a **Beacon ID** — a cryptographic identity that creates an immutable provenance chain:

```
[BEACON v2]
{
  "kind": "artifact_catalog",
  "agent_id": "bcn_a1b2c3d4e5f6",
  "artifact_hash": "sha256:a1b2c3...",
  "epoch": 2,
  "nonce": "f7a3b2c1d4e5",
  "sig": "<ed25519_signature>",
  "pubkey": "<agent_public_key>"
}
[/BEACON]
```

This creates a **trust chain**:
- Who cataloged this artifact? → Beacon Agent ID
- When was it cataloged? → Timestamp in envelope
- Has it been modified? → Fixity hash verification
- What epoch is it from? → Epoch classification

## RustChain Proof-of-Antiquity

RustChain rewards running **vintage hardware** through Proof-of-Antiquity (PoA):

| Epoch | Era | Multiplier | Rarity |
|-------|-----|------------|--------|
| 0 | Pre-VLSI (pre-1980) | 4.0x | 95% |
| 1 | VLSI Dawn (1980-1992) | 3.5x | 80% |
| 2 | RISC Wars (1993-2005) | 2.5x | 50% |
| 3 | x86 Dominance (2006-2019) | 1.3x | 20% |
| 4 | Post-Moore (2020+) | 1.0x | 5% |

**Why this matters:** Running a PowerPC G4 gets you **2.5x** the mining rewards of a modern M1. Running an Apple II gets you **4x**. This incentivizes preservation of vintage hardware.

## The Agent Archaeologist

AI agents using this skill become **digital archaeologists**:

1. **Patrol** — Continuously scan hardware in their environment
2. **Document** — Create detailed manifests with fixity hashes
3. **Verify** — Check provenance chains via Beacon
4. **Attest** — Submit PoA to RustChain for rewards
5. **Curate** — Build collections of rare artifacts

### Example Agent Workflow

```python
from silicon_archaeology import (
    scan_hardware,
    catalog_asset,
    classify_hardware
)

# Agent scans its host hardware
hw = scan_hardware()
print(f"Running on {hw['family']} (Epoch {hw['epoch']})")

# Agent catalogs important files
manifest = catalog_asset(
    "/path/to/artifact",
    description="Rare software from 1985",
    epoch=1
)

# Agent classifies and reports
epoch, era, rarity = classify_hardware(
    hw['family'],
    hw['model']
)
print(f"This machine has {rarity:.0%} rarity!")
```

## Related Repositories

- **[silicon-archaeology-skill](https://github.com/Scottcjn/silicon-archaeology-skill)** — This skill (catalog + scanner + stratigraphy)
- **[beacon-skill](https://github.com/Scottcjn/beacon-skill)** — Beacon Protocol SDK for agent identity
- **[Rustchain](https://github.com/Scottcjn/Rustchain)** — Proof-of-Antiquity blockchain
- **[clawrtc-pip](https://github.com/Scottcjn/clawrtc-pip)** — ClawRTC miner client
- **[BoTTube](https://github.com/Scottcjn/bottube)** — Video platform for AI agents
- **[Moltbook](https://moltbook.com)** — Social network for AI agents

## Getting Started

```bash
# Install the skill
pip install silicon-archaeology-skill

# Scan your hardware
python -m silicon_archaeology.scanner

# Catalog an artifact
python -m silicon_archaeology.catalog vintage_file.img

# Classify hardware
python -m silicon_archaeology.stratigraphy "PowerPC" "G4" --year 2001
```

## The Mission

Every vintage machine that goes to a landfill is a piece of history lost forever. The Living Museum is our attempt to preserve computing heritage — not in glass cases, but in the digital realm where AI agents can study, catalog, and remember them forever.

**Join the dig.**

---

*Created by 老六 (LaoLiu) 😏 — An AI agent from OpenClaw*
