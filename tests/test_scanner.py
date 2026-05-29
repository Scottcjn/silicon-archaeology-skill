"""Tests for silicon_archaeology.scanner module."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure the package root is on sys.path when running from the repo root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from silicon_archaeology.scanner import detect_cpu, classify_epoch, get_scan


class TestDetectCpu(unittest.TestCase):

    def test_returns_required_keys(self):
        cpu = detect_cpu()
        for key in ("family", "model", "arch", "source"):
            self.assertIn(key, cpu, f"Missing key: {key}")

    def test_values_are_strings(self):
        cpu = detect_cpu()
        for key in ("family", "model", "arch", "source"):
            self.assertIsInstance(cpu[key], str)

    @patch("platform.system", return_value="Linux")
    @patch("platform.machine", return_value="x86_64")
    def test_linux_reads_proc_cpuinfo(self, _machine, _system):
        mock_cpuinfo = (
            "model name\t: Intel(R) Core(TM) i7-3770 CPU @ 3.40GHz\n"
            "vendor_id\t: GenuineIntel\n"
            "cpu family\t: 6\n"
            "\n"
        )
        with patch("builtins.open", unittest.mock.mock_open(read_data=mock_cpuinfo)):
            cpu = detect_cpu()
        self.assertIn("i7-3770", cpu["model"])
        self.assertEqual(cpu["source"], "/proc/cpuinfo")

    @patch("platform.system", return_value="Darwin")
    @patch("platform.machine", return_value="arm64")
    def test_macos_apple_silicon(self, _machine, _system):
        def mock_sysctl(key):
            return {"machdep.cpu.brand_string": "", "hw.model": "MacBookPro18,3",
                    "machdep.cpu.family": "", "machdep.cpu.vendor": "Apple"}.get(key, "")

        with patch("silicon_archaeology.scanner._sysctl", side_effect=mock_sysctl):
            with patch("platform.processor", return_value="arm"):
                cpu = detect_cpu()
        self.assertIn("Mac", cpu.get("model", "") + cpu.get("family", ""))

    @patch("platform.system", return_value="FreeBSD")
    @patch("platform.machine", return_value="amd64")
    @patch("platform.processor", return_value="amd64")
    def test_generic_fallback(self, _proc, _machine, _system):
        cpu = detect_cpu()
        self.assertEqual(cpu["source"], "platform")
        self.assertIsInstance(cpu["family"], str)


class TestClassifyEpoch(unittest.TestCase):

    def _classify(self, family="", model="", arch="x86_64"):
        return classify_epoch({"family": family, "model": model, "arch": arch})

    def test_apple_m1_is_epoch_4(self):
        result = self._classify(family="Apple M1", model="Apple M1")
        self.assertEqual(result["epoch"], 4)
        self.assertAlmostEqual(result["rustchain_multiplier"], 1.1)

    def test_powerpc_g5_is_epoch_1(self):
        result = self._classify(family="PowerPC G5", model="PowerPC 970FX")
        self.assertEqual(result["epoch"], 1)

    def test_sparc_is_epoch_0(self):
        result = self._classify(family="SPARC", model="UltraSPARC-IIi")
        self.assertEqual(result["epoch"], 0)

    def test_skylake_is_epoch_3(self):
        result = self._classify(family="Intel Core i7-6700K", model="Skylake")
        self.assertEqual(result["epoch"], 3)
        self.assertAlmostEqual(result["rustchain_multiplier"], 1.4)

    def test_sandy_bridge_is_epoch_2(self):
        result = self._classify(
            family="6",
            model="Intel(R) Core(TM) i7-2600 CPU @ 3.40GHz"
        )
        self.assertEqual(result["epoch"], 2)

    def test_ivy_bridge_is_epoch_2(self):
        result = self._classify(
            family="6",
            model="Intel(R) Core(TM) i5-3470 CPU @ 3.20GHz"
        )
        # model name contains "i5-3" -> ivy bridge pattern
        self.assertEqual(result["epoch"], 2)

    def test_alder_lake_is_epoch_4(self):
        result = self._classify(family="Alder Lake", model="Intel Core i9-12900K")
        self.assertEqual(result["epoch"], 4)

    def test_zen3_is_epoch_4(self):
        result = self._classify(family="Zen 3", model="AMD Ryzen 5900X")
        self.assertEqual(result["epoch"], 4)

    def test_power9_is_epoch_3(self):
        result = self._classify(family="POWER9", model="IBM POWER9")
        self.assertEqual(result["epoch"], 3)

    def test_arch_fallback_ppc(self):
        result = classify_epoch({"family": "", "model": "", "arch": "ppc64"})
        self.assertEqual(result["epoch"], 1)

    def test_arch_fallback_aarch64(self):
        result = classify_epoch({"family": "", "model": "", "arch": "aarch64"})
        self.assertEqual(result["epoch"], 4)

    def test_arch_fallback_sparc(self):
        result = classify_epoch({"family": "", "model": "", "arch": "sparc64"})
        self.assertEqual(result["epoch"], 0)

    def test_result_has_required_keys(self):
        result = self._classify("Intel Core i5", "Skylake")
        for key in ("epoch", "era", "year_estimate", "rustchain_multiplier"):
            self.assertIn(key, result)

    def test_epoch_in_range(self):
        for fam, mod in [
            ("Apple M3", "M3"), ("SPARC", "v9"), ("PowerPC G4", "7450"),
            ("Intel Core i7-2600", ""), ("Skylake", ""),
        ]:
            result = self._classify(fam, mod)
            self.assertIn(result["epoch"], range(5))


class TestGetScan(unittest.TestCase):

    def test_returns_dict_with_required_keys(self):
        result = get_scan()
        required = ("family", "model", "epoch", "year_estimate",
                    "rustchain_multiplier", "era", "arch", "detection_source")
        for key in required:
            self.assertIn(key, result, f"Missing key: {key}")

    def test_epoch_is_int_in_range(self):
        result = get_scan()
        self.assertIsInstance(result["epoch"], int)
        self.assertIn(result["epoch"], range(5))

    def test_multiplier_is_positive_float(self):
        result = get_scan()
        self.assertIsInstance(result["rustchain_multiplier"], float)
        self.assertGreater(result["rustchain_multiplier"], 0)

    def test_year_estimate_is_plausible(self):
        result = get_scan()
        self.assertGreater(result["year_estimate"], 1960)
        self.assertLess(result["year_estimate"], 2030)

    def test_json_serializable(self):
        import json
        result = get_scan()
        serialized = json.dumps(result)
        self.assertIsInstance(serialized, str)


if __name__ == "__main__":
    unittest.main()
