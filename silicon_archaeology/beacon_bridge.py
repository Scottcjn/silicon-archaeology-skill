import socket
import json
import asyncio
import os

class BeaconArchaeologyBridge:
    def __init__(self, agent_name='MentalOS_Archaeologist', port=8888):
        self.agent_name = agent_name
        self.port = int(os.getenv('BEACON_PORT', port))
        self.broadcast_ip = os.getenv('BEACON_BROADCAST_IP', '255.255.255.255')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
    async def broadcast_discovery(self, hardware_data):
        message = {
            'type': 'HARDWARE_DISCOVERY',
            'sender': self.agent_name,
            'payload': {
                'model': hardware_data.get('model', 'unknown'),
                'year': hardware_data.get('year', 0),
                'antiquity_multiplier': hardware_data.get('multiplier', 1.0)
            }
        }
        try:
            payload_bytes = json.dumps(message).encode('utf-8')
            self.sock.sendto(payload_bytes, (self.broadcast_ip, self.port))
            print(f'[BEACON] Broadcast sent to {self.broadcast_ip}:{self.port}')
            return True
        except Exception as e:
            print(f'[BEACON] Broadcast failed: {e}')
            return False

    def close(self):
        self.sock.close()

if __name__ == '__main__':
    bridge = BeaconArchaeologyBridge()
    mock_hardware = {'model': 'MOS 6502', 'year': 1975, 'multiplier': 10.0}
    asyncio.run(bridge.broadcast_discovery(mock_hardware))
    bridge.close()
