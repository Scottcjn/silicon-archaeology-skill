"""
Silicon Archaeology Skill
Digital archaeology toolkit for AI agents.
"""

from .catalog import (
    catalog_asset,
    catalog_directory,
    compute_hashes,
    detect_epoch,
    verify_fixity,
    to_echoes_format
)

__version__ = '0.1.0'
__all__ = [
    'catalog_asset',
    'catalog_directory', 
    'compute_hashes',
    'detect_epoch',
    'verify_fixity',
    'to_echoes_format'
]
