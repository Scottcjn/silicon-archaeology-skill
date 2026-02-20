import hashlib
import json
import os
import time
from typing import Any, Dict, Optional

import requests
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


def _canonical_json(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _agent_id_from_pubkey(pubkey_hex: str) -> str:
    digest = hashlib.sha256(bytes.fromhex(pubkey_hex)).hexdigest()[:12]
    return f"bcn_{digest}"


class LocalIdentity:
    """Minimal Ed25519 identity compatible with Beacon signing patterns."""

    def __init__(self, private_key: Optional[Ed25519PrivateKey] = None):
        self._sk = private_key or Ed25519PrivateKey.generate()
        self._pk = self._sk.public_key()
        self.public_key_hex = self._pk.public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
        self.agent_id = _agent_id_from_pubkey(self.public_key_hex)

    def sign_hex(self, data: bytes) -> str:
        return self._sk.sign(data).hex()


class BeaconArchaeologyBridge:
    """Bridge silicon catalog entries into signed Beacon envelopes and publish to Atlas."""

    def __init__(
        self,
        atlas_url: Optional[str] = None,
        identity: Optional[Any] = None,
        scanner_agent_id: Optional[str] = None,
        timeout_s: int = 15,
        endpoint_path: str = "/api/envelopes",
    ):
        self.atlas_url = (atlas_url or os.getenv("BEACON_ATLAS_URL", "http://50.28.86.131:8071")).rstrip("/")
        self.endpoint_path = os.getenv("BEACON_ATLAS_ENDPOINT", endpoint_path)
        self.timeout_s = timeout_s
        self.identity = identity or LocalIdentity()
        self.scanner_agent_id = scanner_agent_id or os.getenv("SCANNER_AGENT_ID", self.identity.agent_id)

    @staticmethod
    def _fixity_hash(catalog_entry: Dict[str, Any]) -> str:
        if catalog_entry.get("fixity_hash"):
            return str(catalog_entry["fixity_hash"])
        canonical = _canonical_json(catalog_entry)
        return hashlib.sha256(canonical).hexdigest()

    @staticmethod
    def _asset_epoch(catalog_entry: Dict[str, Any]) -> Any:
        return catalog_entry.get("asset_epoch", catalog_entry.get("epoch", "unknown"))

    def catalog_to_envelope(self, catalog_entry: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "v": 2,
            "kind": "silicon_asset_catalog",
            "ts": int(time.time()),
            "nonce": hashlib.sha256(os.urandom(16)).hexdigest()[:12],
            "agent_id": self.identity.agent_id,
            "pubkey": self.identity.public_key_hex,
            "asset": {
                "asset_id": catalog_entry.get("asset_id", catalog_entry.get("id", "unknown")),
                "name": catalog_entry.get("name", catalog_entry.get("model", "unknown")),
                "asset_epoch": self._asset_epoch(catalog_entry),
                "fixity_hash": self._fixity_hash(catalog_entry),
                "metadata": catalog_entry,
            },
            "provenance": {
                "scanner_agent_id": self.scanner_agent_id,
                "bridge_agent_id": self.identity.agent_id,
            },
        }
        payload["sig"] = self.identity.sign_hex(_canonical_json(payload))
        return payload

    @staticmethod
    def verify_envelope_signature(envelope: Dict[str, Any]) -> bool:
        sig_hex = envelope.get("sig")
        pubkey_hex = envelope.get("pubkey")
        agent_id = envelope.get("agent_id")
        if not sig_hex or not pubkey_hex:
            return False
        if agent_id != _agent_id_from_pubkey(pubkey_hex):
            return False
        message = {k: v for k, v in envelope.items() if k != "sig"}
        try:
            pk = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pubkey_hex))
            pk.verify(bytes.fromhex(sig_hex), _canonical_json(message))
            return True
        except Exception:
            return False

    def post_envelope(self, envelope: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.atlas_url}{self.endpoint_path}"
        response = requests.post(
            url,
            json={"envelope": envelope},
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Silicon-Archaeology-Bridge/1.0",
            },
            timeout=self.timeout_s,
        )

        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text}

        return {
            "ok": response.status_code < 400,
            "status_code": response.status_code,
            "url": url,
            "response": body,
        }

    def publish_catalog_entry(self, catalog_entry: Dict[str, Any]) -> Dict[str, Any]:
        envelope = self.catalog_to_envelope(catalog_entry)
        return self.post_envelope(envelope)
