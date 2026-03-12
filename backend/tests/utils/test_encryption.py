"""Tests for encryption utilities."""

import pytest

from app.utils.encryption import decrypt_token, encrypt_token


class TestEncryption:
    """Test AES-256-GCM envelope encryption."""

    def test_roundtrip(self):
        plaintext = "oauth-access-token-abc123"
        encrypted = encrypt_token(plaintext)
        decrypted = decrypt_token(encrypted)
        assert decrypted == plaintext

    def test_different_ciphertexts(self):
        """Each encryption should produce different output (random nonce)."""
        plaintext = "same-token"
        a = encrypt_token(plaintext)
        b = encrypt_token(plaintext)
        assert a != b  # Different nonces → different ciphertext

    def test_tampered_ciphertext_fails(self):
        encrypted = encrypt_token("test-token")
        tampered = encrypted[:-4] + "XXXX"
        with pytest.raises(Exception):
            decrypt_token(tampered)

    def test_empty_string(self):
        encrypted = encrypt_token("")
        assert decrypt_token(encrypted) == ""

    def test_unicode_token(self):
        plaintext = "token-with-émojis-🔑"
        encrypted = encrypt_token(plaintext)
        assert decrypt_token(encrypted) == plaintext
