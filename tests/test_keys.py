# tests for the key helpers

import base64

from keys import (deserialize_private_key, generate_private_key,
                  int_to_base64, private_key_to_jwk, serialize_private_key)


def test_pem_round_trip_preserves_key():
    key = generate_private_key()
    pem = serialize_private_key(key)
    assert pem.startswith(b"-----BEGIN RSA PRIVATE KEY-----")
    loaded = deserialize_private_key(pem)
    assert loaded.private_numbers() == key.private_numbers()


def test_deserialize_accepts_memoryview_style_blob():
    pem = serialize_private_key(generate_private_key())
    assert deserialize_private_key(memoryview(pem)) is not None


def test_int_to_base64_pads_odd_length_hex():
    assert int_to_base64(0x1FF) == "Af8"  # 0x01FF -> bytes 01 FF


def test_int_to_base64_exponent():
    assert int_to_base64(65537) == "AQAB"


def test_jwk_fields():
    key = generate_private_key()
    jwk = private_key_to_jwk(7, key)
    assert jwk["kid"] == "7"
    assert jwk["kty"] == "RSA"
    assert jwk["alg"] == "RS256"
    assert jwk["use"] == "sig"
    assert jwk["e"] == "AQAB"
    n_bytes = base64.urlsafe_b64decode(jwk["n"] + "==")
    assert int.from_bytes(n_bytes, "big") == key.public_key().public_numbers().n
    assert "d" not in jwk  # no private stuff in the jwk
