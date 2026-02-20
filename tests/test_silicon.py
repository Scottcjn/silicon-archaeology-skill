import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to find silicon_archaeology
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)

# rustchain_bridge imports httpx; mock it if unavailable in bare test envs.
try:
    import httpx  # noqa: F401
except Exception:
    sys.modules["httpx"] = MagicMock()

from silicon_archaeology.rustchain_bridge import RustChainBridge
from silicon_archaeology.beacon_bridge import BeaconArchaeologyBridge


class TestSiliconSkill(unittest.TestCase):

    def setUp(self):
        os.environ["RUSTCHAIN_NODE_URL"] = "http://test-node"

    def tearDown(self):
        if "RUSTCHAIN_NODE_URL" in os.environ:
            del os.environ["RUSTCHAIN_NODE_URL"]

    def test_rustchain_init(self):
        bridge = RustChainBridge()
        self.assertEqual(bridge.node_url, "http://test-node")

    def test_antiquity_calculation(self):
        bridge = RustChainBridge(node_url="http://mock-node")
        self.assertEqual(bridge.calculate_antiquity(1975), 10.0)
        self.assertEqual(bridge.calculate_antiquity(1985), 5.0)
        self.assertEqual(bridge.calculate_antiquity(1995), 2.5)
        self.assertEqual(bridge.calculate_antiquity(2005), 1.5)
        self.assertEqual(bridge.calculate_antiquity(2025), 1.0)

    def test_catalog_to_envelope_has_required_fields_and_valid_signature(self):
        bridge = BeaconArchaeologyBridge(scanner_agent_id="scanner_001")
        catalog_entry = {
            "asset_id": "asset-42",
            "name": "PowerPC G4",
            "asset_epoch": 2,
            "fixity_hash": "abc123",
            "format": "disk-image",
        }

        envelope = bridge.catalog_to_envelope(catalog_entry)

        self.assertEqual(envelope["kind"], "silicon_asset_catalog")
        self.assertEqual(envelope["asset"]["asset_epoch"], 2)
        self.assertEqual(envelope["asset"]["fixity_hash"], "abc123")
        self.assertEqual(envelope["provenance"]["scanner_agent_id"], "scanner_001")
        self.assertIn("agent_id", envelope)
        self.assertIn("sig", envelope)
        self.assertTrue(bridge.verify_envelope_signature(envelope))

    @patch("silicon_archaeology.beacon_bridge.requests.post")
    def test_publish_posts_to_atlas_api(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_resp

        bridge = BeaconArchaeologyBridge(atlas_url="http://50.28.86.131:8071")
        result = bridge.publish_catalog_entry({"asset_id": "A1", "asset_epoch": 1, "fixity_hash": "ff"})

        self.assertTrue(result["ok"])
        called_url = mock_post.call_args[0][0]
        self.assertEqual(called_url, "http://50.28.86.131:8071/api/envelopes")

        posted_json = mock_post.call_args[1]["json"]
        self.assertIn("envelope", posted_json)
        self.assertEqual(posted_json["envelope"]["asset"]["asset_epoch"], 1)
        self.assertEqual(posted_json["envelope"]["asset"]["fixity_hash"], "ff")


if __name__ == '__main__':
    unittest.main()
