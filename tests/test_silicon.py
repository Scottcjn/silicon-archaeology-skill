import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Add parent directory to path to find silicon_archaeology
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock modules if not available in CI environment
sys.modules['beacon_skill'] = MagicMock()
sys.modules['beacon_skill.identity'] = MagicMock()

from silicon_archaeology.rustchain_bridge import RustChainBridge
from silicon_archaeology.beacon_bridge import BeaconArchaeologyBridge

class TestSiliconSkill(unittest.TestCase):

    def setUp(self):
        # Set env var for testing
        os.environ["RUSTCHAIN_NODE_URL"] = "http://test-node"

    def tearDown(self):
        if "RUSTCHAIN_NODE_URL" in os.environ:
            del os.environ["RUSTCHAIN_NODE_URL"]

    def test_rustchain_init(self):
        bridge = RustChainBridge()
        self.assertEqual(bridge.node_url, "http://test-node")

    def test_antiquity_calculation(self):
        bridge = RustChainBridge(node_url="http://mock-node")
        # Test Epoch Multipliers
        self.assertEqual(bridge.calculate_antiquity(1975), 10.0) # Pre-1980
        self.assertEqual(bridge.calculate_antiquity(1985), 5.0)  # 1980s
        self.assertEqual(bridge.calculate_antiquity(1995), 2.5)  # 1990s
        self.assertEqual(bridge.calculate_antiquity(2005), 1.5)  # 2000s
        self.assertEqual(bridge.calculate_antiquity(2025), 1.0)  # Modern

    @patch('silicon_archaeology.beacon_bridge.socket.socket')
    def test_beacon_socket_creation(self, mock_socket_cls):
        # Setup mock socket
        mock_sock_instance = MagicMock()
        mock_socket_cls.return_value = mock_sock_instance
        
        bridge = BeaconArchaeologyBridge()
        
        # Verify socket was created
        self.assertTrue(mock_socket_cls.called)
        
        bridge.close()
        mock_sock_instance.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
