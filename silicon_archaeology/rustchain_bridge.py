import json
import httpx
import asyncio
from datetime import datetime

class RustChainBridge:
    """
    The SILICON-ARCHAEOLOGIST: Bridges hardware scans to RustChain Proof-of-Antiquity.
    Connects physical silicon legacy to on-chain rewards.
    """
    def __init__(self, node_url="http://50.28.86.131"):
        self.node_url = node_url
        self.epoch_multipliers = {
            "pre-1980": 10.0,
            "1980-1989": 5.0,
            "1990-1999": 2.5,
            "2000-2009": 1.5,
            "modern": 1.0
        }

    def calculate_antiquity(self, manufacturing_year):
        """Maps silicon age to antiquity multiplier."""
        year = int(manufacturing_year)
        if year < 1980: return self.epoch_multipliers["pre-1980"]
        if year < 1990: return self.epoch_multipliers["1980-1989"]
        if year < 2000: return self.epoch_multipliers["1990-1999"]
        if year < 2010: return self.epoch_multipliers["2000-2009"]
        return self.epoch_multipliers["modern"]

    async def submit_attestation(self, hardware_data, wallet_name):
        """
        Formats and submits a PoA attestation shard.
        """
        antiquity_score = self.calculate_antiquity(hardware_data.get('year', 2026))
        
        payload = {
            "wallet": wallet_name,
            "hardware_id": hardware_data.get('id', 'unknown'),
            "model": hardware_data.get('model', 'generic_silicon'),
            "antiquity_multiplier": antiquity_score,
            "timestamp": datetime.now().isoformat(),
            "attestation_type": "Silicon_Archaeology_v1"
        }
        
        print(f"[BRIDGE] Submitting PoA Shard for {payload['model']}...")
        
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(f"{self.node_url}/attest/submit", json=payload)
                if r.status_code == 200:
                    print("[SUCCESS] Attestation accepted by RustChain node.")
                    return True
                else:
                    print(f"[BRIDGE] Node responded with: {r.status_code}")
                    return False
        except Exception as e:
            print(f"[BRIDGE] Connection failed: {str(e)}")
            return False

if __name__ == "__main__":
    # Demo Strike
    bridge = RustChainBridge()
    mock_scan = {"model": "PowerPC G4", "year": 1999, "id": "SN-77182"}
    asyncio.run(bridge.submit_attestation(mock_scan, "MentalOS_Mirror"))
