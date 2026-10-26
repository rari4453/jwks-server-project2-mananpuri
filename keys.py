# helper functions for the rsa keys
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_private_key():
    # make a new 2048 bit rsa key
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def serialize_private_key(private_key):
    # turn the key into pem bytes so sqlite can store it
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )


def deserialize_private_key(pem_bytes):
    # turn the pem from the db back into a key
    return serialization.load_pem_private_key(bytes(pem_bytes), password=None)


def int_to_base64(value):
    # int -> base64url string for the jwk
    value_hex = format(value, "x")
    # hex needs an even length
    if len(value_hex) % 2 == 1:
        value_hex = "0" + value_hex
    encoded = base64.urlsafe_b64encode(bytes.fromhex(value_hex)).rstrip(b"=")
    return encoded.decode("utf-8")


def private_key_to_jwk(kid, private_key):
    # public part only, never the private numbers
    nums = private_key.public_key().public_numbers()
    return {
        "alg": "RS256",
        "kty": "RSA",
        "use": "sig",
        "kid": str(kid),
        "n": int_to_base64(nums.n),
        "e": int_to_base64(nums.e),
    }
