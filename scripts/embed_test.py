from app.core.pixelseal import model
from app.services.embed_service import EmbedService

message = model.get_random_msg(1)

EmbedService.embed(
    input_path="uploads/input.png",
    output_path="outputs/watermarked.png",
    message=message,
)

print(message)
print("Done.")