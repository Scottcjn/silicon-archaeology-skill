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

from .scanner import (
    scan_hardware,
    get_cpu_info,
    classify_epoch,
    estimate_year,
    SILICON_EPOCHS
)

__version__ = '0.1.0'
__all__ = [
    # Catalog
    'catalog_asset',
    'catalog_directory', 
    'compute_hashes',
    'detect_epoch',
    'verify_fixity',
    'to_echoes_format',
    # Scanner
    'scan_hardware',
    'get_cpu_info',
    'classify_epoch',
    'estimate_year',
    'SILICON_EPOCHS'
]
