"""
Silicon Archaeology - Asset Cataloger
Catalog software artifacts with fixity hashes for digital preservation.
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union


def compute_hashes(file_path: str) -> Dict[str, str]:
    """
    Compute SHA-256 and SHA-512 fixity hashes for a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Dict with sha256 and sha512 hash strings
    """
    sha256_hash = hashlib.sha256()
    sha512_hash = hashlib.sha512()
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256_hash.update(chunk)
            sha512_hash.update(chunk)
    
    return {
        'sha256': sha256_hash.hexdigest(),
        'sha512': sha512_hash.hexdigest()
    }


def catalog_asset(
    file_path: str,
    description: str = "",
    epoch: Optional[int] = None,
    output_path: Optional[str] = None
) -> Dict:
    """
    Catalog a single software artifact with fixity hashes.
    
    Args:
        file_path: Path to the file to catalog
        description: Human-readable description of the artifact
        epoch: Silicon epoch classification (0-4), auto-detected if None
        output_path: Optional path to save manifest JSON
        
    Returns:
        Manifest dict with filename, size, hashes, description, epoch, cataloged_at
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    # Compute hashes
    hashes = compute_hashes(str(path))
    
    # Get file size
    size = path.stat().st_size
    
    # Auto-detect epoch if not provided
    if epoch is None:
        epoch = detect_epoch(path)
    
    # Build manifest
    manifest = {
        'filename': path.name,
        'size': size,
        'hashes': hashes,
        'description': description,
        'epoch': epoch,
        'cataloged_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Save to file if output_path provided
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    return manifest


def catalog_directory(
    dir_path: str,
    description_prefix: str = "",
    epoch: Optional[int] = None,
    output_path: Optional[str] = None,
    recursive: bool = True
) -> List[Dict]:
    """
    Batch catalog all files in a directory.
    
    Args:
        dir_path: Path to directory to catalog
        description_prefix: Prefix for auto-generated descriptions
        epoch: Silicon epoch for all files (auto-detected if None)
        output_path: Optional path to save batch manifest JSON
        recursive: Whether to recurse into subdirectories
        
    Returns:
        List of manifest dicts
    """
    path = Path(dir_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {dir_path}")
    
    manifests = []
    
    # Get all files
    if recursive:
        files = path.rglob('*')
    else:
        files = path.glob('*')
    
    for file_path in files:
        if file_path.is_file():
            try:
                # Generate description from filename
                desc = f"{description_prefix}{file_path.name}"
                
                manifest = catalog_asset(
                    str(file_path),
                    description=desc,
                    epoch=epoch
                )
                
                # Add relative path for batch catalogs
                manifest['relative_path'] = str(file_path.relative_to(path))
                manifests.append(manifest)
                
            except Exception as e:
                print(f"Warning: Failed to catalog {file_path}: {e}")
    
    # Save batch manifest if output_path provided
    if output_path:
        batch_manifest = {
            'catalog_type': 'batch',
            'source_directory': str(path),
            'file_count': len(manifests),
            'cataloged_at': datetime.now(timezone.utc).isoformat(),
            'manifests': manifests
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(batch_manifest, f, indent=2, ensure_ascii=False)
    
    return manifests


def detect_epoch(file_path: Path) -> int:
    """
    Auto-detect silicon epoch from file characteristics.
    
    Epochs:
        0: Pre-VLSI (pre-1980)
        1: VLSI Dawn (1980-1992)
        2: RISC Wars (1993-2005)
        3: x86 Dominance (2006-2019)
        4: Post-Moore (2020+)
    
    Args:
        file_path: Path to analyze
        
    Returns:
        Integer epoch (0-4)
    """
    name_lower = file_path.name.lower()
    
    # Pre-VLSI indicators
    pre_vlsi_keywords = ['altair', 'pdq', 'pdp', 'imsai', 'swtpc', 'osborne', 'trs-80', 'apple ii', 'apple][']
    for kw in pre_vlsi_keywords:
        if kw in name_lower:
            return 0
    
    # VLSI Dawn indicators
    vlsi_keywords = ['68000', '68020', '68030', '68040', '68k', 'amiga', 'macintosh', 'system 6', 'system 7', 
                     'mac os 7', 'mac os 8', 'dos 3', 'dos 4', 'dos 5', 'windows 2', 'windows 3']
    for kw in vlsi_keywords:
        if kw in name_lower:
            return 1
    
    # RISC Wars indicators
    risc_keywords = ['powerpc', 'ppc', 'g3', 'g4', 'g5', 'sparc', 'mips', 'irix', 'aix', 'solaris 2',
                     'mac os 9', 'mac os x 10', 'os x 10', 'windows 95', 'windows 98', 'windows xp']
    for kw in risc_keywords:
        if kw in name_lower:
            return 2
    
    # x86 Dominance indicators
    x86_keywords = ['core 2', 'nehalem', 'sandy', 'ivy', 'haswell', 'skylake', 'windows 7', 'windows 10',
                    'mac os x 10.6', 'mac os x 10.7', 'mac os x 10.8', 'mac os x 10.9', 'mac os x 10.10',
                    'mac os x 10.11', 'macos sierra', 'macos high sierra', 'macos mojave']
    for kw in x86_keywords:
        if kw in name_lower:
            return 3
    
    # Default to Post-Moore for modern files
    return 4


def verify_fixity(manifest: Dict, file_path: str) -> bool:
    """
    Verify file fixity against a manifest.
    
    Args:
        manifest: Manifest dict with hashes
        file_path: Path to file to verify
        
    Returns:
        True if hashes match, False otherwise
    """
    current_hashes = compute_hashes(file_path)
    return current_hashes == manifest.get('hashes', {})


# Echoes paper manifest format compatibility
def to_echoes_format(manifest: Dict) -> Dict:
    """
    Convert to Echoes paper manifest format.
    
    Args:
        manifest: Standard manifest dict
        
    Returns:
        Dict in Echoes paper format
    """
    return {
        'artifact': {
            'name': manifest.get('filename', ''),
            'size_bytes': manifest.get('size', 0),
            'fixity': manifest.get('hashes', {}),
            'provenance': {
                'description': manifest.get('description', ''),
                'epoch': manifest.get('epoch', 4),
                'cataloged': manifest.get('cataloged_at', '')
            }
        }
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Catalog software artifacts with fixity hashes')
    parser.add_argument('path', help='File or directory to catalog')
    parser.add_argument('--description', '-d', default='', help='Description of the artifact')
    parser.add_argument('--epoch', '-e', type=int, choices=[0,1,2,3,4], help='Silicon epoch (0-4)')
    parser.add_argument('--output', '-o', help='Output path for manifest JSON')
    parser.add_argument('--recursive', '-r', action='store_true', help='Recursively catalog directories')
    parser.add_argument('--echoes', action='store_true', help='Output in Echoes paper format')
    
    args = parser.parse_args()
    
    path = Path(args.path)
    
    if path.is_file():
        manifest = catalog_asset(
            str(path),
            description=args.description,
            epoch=args.epoch,
            output_path=args.output
        )
        
        if args.echoes:
            manifest = to_echoes_format(manifest)
        
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        
    elif path.is_dir():
        manifests = catalog_directory(
            str(path),
            description_prefix=args.description,
            epoch=args.epoch,
            output_path=args.output,
            recursive=args.recursive
        )
        
        print(f"Cataloged {len(manifests)} files")
        
        if args.echoes:
            manifests = [to_echoes_format(m) for m in manifests]
        
        print(json.dumps(manifests, indent=2, ensure_ascii=False))
        
    else:
        print(f"Error: Path not found: {args.path}")
        exit(1)
