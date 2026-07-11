from app.core.pixelseal import model
from app.services.detect_service import DetectService
from app.services.embed_service import EmbedService

message = model.get_random_msg(1)

EmbedService.embed(
    "uploads/input.png",
    "outputs/watermarked.png",
    message,
)

result = DetectService.detect(
    "outputs/watermarked.png"
)

recovered = DetectService.extract(
    "outputs/watermarked.png"
)

print("\nOriginal\n")
print(message)

print("\nRecovered\n")
print(recovered)

print("\nConfidence\n")
print(result["confidence"])

bit_accuracy = (message == recovered).float().mean()

print("\nBit Accuracy")

print(bit_accuracy.item())