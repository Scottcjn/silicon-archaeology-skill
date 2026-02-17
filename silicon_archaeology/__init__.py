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
    SILICON_EPOCHS as SCANNER_EPOCHS
)

from .stratigraphy import (
    classify_hardware,
    get_epoch_info,
    get_known_hardware,
    to_json as stratigraphy_to_json,
    SILICON_EPOCHS,
    KNOWN_HARDWARE
)

__version__ = '0.2.0'
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
    'SCANNER_EPOCHS',
    # Stratigraphy
    'classify_hardware',
    'get_epoch_info',
    'get_known_hardware',
    'stratigraphy_to_json',
    'SILICON_EPOCHS',
    'KNOWN_HARDWARE'
]
