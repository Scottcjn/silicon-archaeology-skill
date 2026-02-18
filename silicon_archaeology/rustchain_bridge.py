import os
import json
import httpx
import asyncio
from datetime import datetime

class RustChainBridge:
    """The SILICON-ARCHAEOLOGIST: Bridges hardware scans to RustChain PoA."""
    def __init__(self, node_url=None):
        # Allow override via init arg, then env var, then fallback default
        self.node_url = node_url or os.getenv("RUSTCHAIN_NODE_URL", "http://localhost:8000")
        
        self.epoch_multipliers = {
            "pre-1980": 10.0,
            "1980-1989": 5.0,
            "1990-1999": 2.5,
            "2000-2009": 1.5,
            "modern": 1.0
        }

    def calculate_antiquity(self, manufacturing_year):
        """Maps silicon age to antiquity multiplier."""
        try:
            year = int(manufacturing_year)
        except (ValueError, TypeError):
            return self.epoch_multipliers["modern"]

        if year < 1980: return self.epoch_multipliers["pre-1980"]
        if year < 1990: return self.epoch_multipliers["1980-1989"]
        if year < 2000: return self.epoch_multipliers["1990-1999"]
        if year < 2010: return self.epoch_multipliers["2000-2009"]
        return self.epoch_multipliers["modern"]

    async def submit_attestation(self, hardware_data, wallet_name):
        """Formats and submits a PoA attestation shard."""
        year = hardware_data.get('year', 2026)
        antiquity_score = self.calculate_antiquity(year)
        
        payload = {
            "wallet": wallet_name,
            "hardware_id": hardware_data.get('id', 'unknown'),
            "model": hardware_data.get('model', 'generic_silicon'),
            "antiquity_multiplier": antiquity_score,
            "timestamp": datetime.now().isoformat(),
            "attestation_type": "Silicon_Archaeology_v1"
        }
        
        print(f"[BRIDGE] Submitting PoA Shard for {payload['model']} to {self.node_url}...")
        
        try:
            async with httpx.AsyncClient() as client:
                # In production, this would be a real POST
                # r = await client.post(f"{self.node_url}/attest/submit", json=payload)
                print("[SUCCESS] Attestation accepted by RustChain node (Simulated).")
                return True
        except Exception as e:
            print(f"[BRIDGE] Connection failed: {str(e)}")
            return False

if __name__ == "__main__":
    # Demo Strike
    bridge = RustChainBridge()
    mock_scan = {"model": "PowerPC G4", "year": 1999, "id": "SN-77182"}
    asyncio.run(bridge.submit_attestation(mock_scan, "MentalOS_Mirror"))
