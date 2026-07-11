import random

from app.services.payload_encoder import PayloadEncoder
from app.services.payload_decoder import PayloadDecoder
from app.services.embed_service import EmbedService
from app.services.detect_service import DetectService

enc = PayloadEncoder()
dec = PayloadDecoder()

N = 100

success = 0
decode_failures = 0

for i in range(N):

    identifier = random.getrandbits(64)

    payload = enc.encode(identifier)

    EmbedService.embed(
        "uploads/input.png",
        "outputs/temp.png",
        payload,
    )

    recovered_bits = DetectService.extract(
        "outputs/temp.png"
    )

    recovered_identifier = dec.decode(
        recovered_bits
    )

    if recovered_identifier is None:

        decode_failures += 1

        print(
            f"{i+1:03d}/{N} | BCH Decode Failed"
        )

        continue

    ok = recovered_identifier == identifier

    if ok:
        success += 1

    print(
        f"{i+1:03d}/{N} | "
        f"{'PASS' if ok else 'FAIL'}"
    )

print()

print("=" * 40)

print(f"Successful Recoveries : {success}/{N}")
print(f"Recovery Rate         : {100*success/N:.2f}%")
print(f"BCH Decode Failures   : {decode_failures}")