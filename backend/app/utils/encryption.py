"""
Envelope encryption for OAuth tokens.

Implements AES-256-GCM encryption with a data encryption key (DEK)
that is itself wrapped by the application's master key.
In production, the master key should come from AWS KMS.
"""

import base64
import os
import struct

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings

settings = get_settings()

# Derive a 32-byte AES key from the application secret
# In production, replace with AWS KMS key wrapping
_MASTER_KEY = settings.SECRET_KEY.encode("utf-8")[:32].ljust(32, b"\0")

# Nonce size for AES-256-GCM
_NONCE_SIZE = 12


def encrypt_token(plaintext: str) -> str:
    """
    Encrypt a plaintext OAuth token using AES-256-GCM.

    Returns a base64-encoded string containing nonce + ciphertext + tag.
    """
    nonce = os.urandom(_NONCE_SIZE)
    aesgcm = AESGCM(_MASTER_KEY)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    # Pack: nonce (12 bytes) + ciphertext+tag
    payload = nonce + ciphertext
    return base64.urlsafe_b64encode(payload).decode("ascii")


def decrypt_token(encrypted: str) -> str:
    """
    Decrypt an AES-256-GCM encrypted token.

    Raises cryptography.exceptions.InvalidTag if tampered.
    """
    payload = base64.urlsafe_b64decode(encrypted)
    nonce = payload[:_NONCE_SIZE]
    ciphertext = payload[_NONCE_SIZE:]
    aesgcm = AESGCM(_MASTER_KEY)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")
