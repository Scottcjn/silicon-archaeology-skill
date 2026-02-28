import unittest
import json
from unittest.mock import mock_open, patch, MagicMock
from scanner import HardwareScanner


class TestHardwareScanner(unittest.TestCase):
    """Test cases for HardwareScanner."""
    
    def setUp(self):
        self.scanner = HardwareScanner()
    
    def test_classify_powerpc_g4(self):
        """Test PowerPC G4 classification."""
        result = self.scanner._classify("7455", "PowerPC G4 (7455)", "ppc")
        self.assertEqual(result["epoch"], 2)
        self.assertEqual(result["epoch_name"], "Renaissance")
        self.assertEqual(result["rustchain_multiplier"], 2.0)
    
    def test_classify_powerpc_g5(self):
        """Test PowerPC G5 classification."""
        result = self.scanner._classify("970", "PowerPC G5 (970)", "ppc64")
        self.assertEqual(result["epoch"], 3)
        self.assertEqual(result["epoch_name"], "Modern")
        self.assertEqual(result["rustchain_multiplier"], 1.5)
    
    def test_classify_power8(self):
        """Test POWER8 classification."""
        result = self.scanner._classify("POWER8", "IBM POWER8", "ppc64le")
        self.assertEqual(result["epoch"], 4)
        self.assertEqual(result["epoch_name"], "Contemporary")
        self.assertEqual(result["rustchain_multiplier"], 1.0)
    
    def test_classify_vintage_x86(self):
        """Test vintage x86 classification."""
        result = self.scanner._classify("i486", "Intel 486", "i386")
        self.assertEqual(result["epoch"], 0)
        self.assertEqual(result["epoch_name"], "Genesis")
        self.assertEqual(result["rustchain_multiplier"], 4.0)
    
    def test_classify_modern(self):
        """Test modern CPU classification (default)."""
        result = self.scanner._classify("Unknown", "Intel Core i7", "x86_64")
        self.assertEqual(result["epoch"], 4)
        self.assertEqual(result["rustchain_multiplier"], 1.0)
    
    def test_scan_linux(self):
        """Test Linux scanning."""
        mock_cpuinfo = """
processor   : 0
vendor_id   : GenuineIntel
cpu family  : 6
model       : 158
model name  : Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz
stepping    : 10
microcode   : 0xb4
cpu MHz     : 2600.000
cache size  : 12288 KB
"""
        with patch('builtins.open', mock_open(read_data=mock_cpuinfo)):
            with patch('platform.system', return_value='Linux'):
                with patch('platform.machine', return_value='x86_64'):
                    result = self.scanner.scan()
                    self.assertIn("family", result)
                    self.assertIn("model", result)
                    self.assertIn("epoch", result)
    
    def test_scan_macos(self):
        """Test macOS scanning."""
        with patch('platform.system', return_value='Darwin'):
            with patch('platform.machine', return_value='x86_64'):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0,
                        stdout="Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz"
                    )
                    result = self.scanner.scan()
                    self.assertIn("family", result)
                    self.assertIn("model", result)
    
    def test_json_output(self):
        """Test JSON output format."""
        result = self.scanner._classify("7455", "PowerPC G4", "ppc")
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["epoch"], 2)


if __name__ == '__main__':
    unittest.main()
