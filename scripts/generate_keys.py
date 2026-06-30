import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ciphervision.crypto.crypto_utils import gen_key

if __name__ == "__main__":
    hmac_key = gen_key()
    aes_key = gen_key()
    print("HMAC_KEY=" + hmac_key.hex())
    print("AES_KEY=" + aes_key.hex())
