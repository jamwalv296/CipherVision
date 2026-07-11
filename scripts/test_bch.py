import random

from app.services.payload_encoder import PayloadEncoder
from app.services.payload_decoder import PayloadDecoder

enc = PayloadEncoder()
dec = PayloadDecoder()

identifier = random.getrandbits(64)

payload = enc.encode(identifier)

for errors in range(9):

    corrupted = payload.clone()

    positions = random.sample(range(120), errors)

    for p in positions:
        corrupted[0, p] ^= 1

    recovered = dec.decode(corrupted)

    print(
        f"Errors: {errors:2d} | "
        f"Recovered: {recovered == identifier}"
    )