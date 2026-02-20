"""Tests for the scanner module."""

import json
import platform
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from silicon_archaeology.scanner import (
    HardwareInfo,
    scan_hardware,
    _parse_cpuinfo,
    _get_sysctl_info,
    _detect_powerpc_info,
    _year_to_epoch,
    _estimate_year_from_cpu,
    RUSTCHAIN_MULTIPLIERS,
)


class TestHardwareInfo(unittest.TestCase):
    """Test HardwareInfo dataclass."""
    
    def test_to_dict(self):
        hw = HardwareInfo(
            family="Intel",
            model="Core i7",
            epoch=3,
            year_estimate=2015,
            rustchain_multiplier=1.3
        )
        d = hw.to_dict()
        self.assertEqual(d["family"], "Intel")
        self.assertEqual(d["model"], "Core i7")
        self.assertEqual(d["epoch"], 3)
        self.assertEqual(d["year_estimate"], 2015)
        self.assertEqual(d["rustchain_multiplier"], 1.3)
    
    def test_to_json(self):
        hw = HardwareInfo(
            family="AMD",
            model="Ryzen 9",
            epoch=4,
            year_estimate=2022,
            rustchain_multiplier=1.2
        )
        json_str = hw.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["family"], "AMD")
        self.assertEqual(parsed["epoch"], 4)


class TestYearToEpoch(unittest.TestCase):
    """Test year to epoch conversion."""
    
    def test_pre_vlsi(self):
        self.assertEqual(_year_to_epoch(1975), 0)
        self.assertEqual(_year_to_epoch(1979), 0)
    
    def test_vlsi_dawn(self):
        self.assertEqual(_year_to_epoch(1980), 1)
        self.assertEqual(_year_to_epoch(1990), 1)
        self.assertEqual(_year_to_epoch(1992), 1)
    
    def test_risc_wars(self):
        self.assertEqual(_year_to_epoch(1993), 2)
        self.assertEqual(_year_to_epoch(2000), 2)
        self.assertEqual(_year_to_epoch(2005), 2)
    
    def test_x86_dominance(self):
        self.assertEqual(_year_to_epoch(2006), 3)
        self.assertEqual(_year_to_epoch(2015), 3)
    
    def test_post_moore(self):
        self.assertEqual(_year_to_epoch(2020), 4)
        self.assertEqual(_year_to_epoch(2024), 4)


class TestEstimateYearFromCPU(unittest.TestCase):
    """Test CPU model to year estimation."""
    
    def test_intel_core_modern(self):
        year = _estimate_year_from_cpu("Intel", "Intel(R) Core(TM) i7-12700K", "6", "151")
        self.assertGreaterEqual(year, 2020)
    
    def test_intel_pentium(self):
        year = _estimate_year_from_cpu("Intel", "Pentium 4", "15", "0")
        self.assertEqual(year, 2000)
    
    def test_amd_ryzen(self):
        year = _estimate_year_from_cpu("AMD", "AMD Ryzen 9 5950X", "25", "33")
        self.assertGreaterEqual(year, 2017)  # Ryzen series started in 2017
    
    def test_apple_silicon(self):
        year = _estimate_year_from_cpu("Apple", "Apple M1", "", "")
        self.assertEqual(year, 2020)


class TestParseCpuinfo(unittest.TestCase):
    """Test /proc/cpuinfo parsing."""
    
    @patch.object(Path, 'exists')
    @patch.object(Path, 'read_text')
    def test_parse_intel_cpuinfo(self, mock_read_text, mock_exists):
        mock_exists.return_value = True
        mock_read_text.return_value = """
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 158
model name	: Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz
stepping	: 10
"""
        info = _parse_cpuinfo()
        self.assertEqual(info["vendor_id"], "GenuineIntel")
        self.assertEqual(info["model name"], "Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz")
    
    @patch.object(Path, 'exists')
    def test_parse_cpuinfo_not_exists(self, mock_exists):
        mock_exists.return_value = False
        info = _parse_cpuinfo()
        self.assertEqual(info, {})


class TestGetSysctlInfo(unittest.TestCase):
    """Test sysctl info retrieval."""
    
    @patch('silicon_archaeology.scanner._run_command')
    def test_get_sysctl_info(self, mock_run):
        def side_effect(cmd):
            if cmd == ["sysctl", "-n", "machdep.cpu.brand_string"]:
                return "Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz"
            if cmd == ["sysctl", "-n", "hw.model"]:
                return "MacBookPro16,1"
            return None
        
        mock_run.side_effect = side_effect
        info = _get_sysctl_info()
        self.assertEqual(info["brand_string"], "Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz")
        self.assertEqual(info["hw_model"], "MacBookPro16,1")


class TestDetectPowerPC(unittest.TestCase):
    """Test PowerPC detection."""
    
    @patch('silicon_archaeology.scanner._get_sysctl_info')
    def test_detect_powerpc_g5(self, mock_sysctl):
        mock_sysctl.return_value = {
            "hw_machine": "Power Macintosh",
            "brand_string": "PowerPC G5",
            "cputype": "18"
        }
        info = _detect_powerpc_info()
        self.assertIsNotNone(info)
        self.assertEqual(info.family, "IBM/Motorola")
        self.assertEqual(info.model, "PowerPC G5")
        self.assertEqual(info.epoch, 2)
    
    @patch('silicon_archaeology.scanner._get_sysctl_info')
    def test_not_powerpc(self, mock_sysctl):
        mock_sysctl.return_value = {
            "hw_machine": "x86_64",
            "brand_string": "Intel(R) Core(TM) i7"
        }
        info = _detect_powerpc_info()
        self.assertIsNone(info)


class TestScanHardware(unittest.TestCase):
    """Test main scan_hardware function."""
    
    @patch('silicon_archaeology.scanner.platform.system')
    @patch('silicon_archaeology.scanner._detect_powerpc_info')
    @patch('silicon_archaeology.scanner._parse_cpuinfo')
    @patch('silicon_archaeology.scanner._parse_linux_cpuinfo')
    def test_scan_linux_intel(self, mock_parse_linux, mock_parse_cpuinfo, 
                               mock_detect_ppc, mock_system):
        mock_system.return_value = "Linux"
        mock_detect_ppc.return_value = None
        mock_parse_cpuinfo.return_value = {
            "vendor_id": "GenuineIntel",
            "model name": "Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz",
            "cpu family": "6",
            "model": "158"
        }
        mock_parse_linux.return_value = HardwareInfo(
            family="Intel",
            model="Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz",
            epoch=3,
            year_estimate=2019,
            rustchain_multiplier=RUSTCHAIN_MULTIPLIERS[3]
        )
        
        hw = scan_hardware()
        self.assertEqual(hw.family, "Intel")
        self.assertIn("i7", hw.model)
    
    @patch('silicon_archaeology.scanner.platform.system')
    @patch('silicon_archaeology.scanner._detect_powerpc_info')
    @patch('silicon_archaeology.scanner._get_sysctl_info')
    def test_scan_macos_apple_silicon(self, mock_sysctl, mock_detect_ppc, mock_system):
        mock_system.return_value = "Darwin"
        mock_detect_ppc.return_value = None
        mock_sysctl.return_value = {
            "brand_string": "Apple M1 Pro"
        }
        
        hw = scan_hardware()
        self.assertEqual(hw.family, "Apple")
        self.assertIn("M1", hw.model)
        self.assertEqual(hw.epoch, 4)
    
    def test_output_structure(self):
        """Verify output JSON structure matches requirements."""
        hw = scan_hardware()
        data = hw.to_dict()
        
        # Required fields per bounty spec
        self.assertIn("family", data)
        self.assertIn("model", data)
        self.assertIn("epoch", data)
        self.assertIn("year_estimate", data)
        self.assertIn("rustchain_multiplier", data)
        
        # Type checks
        self.assertIsInstance(data["family"], str)
        self.assertIsInstance(data["model"], str)
        self.assertIsInstance(data["epoch"], int)
        self.assertIsInstance(data["year_estimate"], int)
        self.assertIsInstance(data["rustchain_multiplier"], float)


if __name__ == '__main__':
    unittest.main()
