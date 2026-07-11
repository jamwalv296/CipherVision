import torch

from pixelseal import model

image = torch.rand(1, 3, 512, 512)

message = model.get_random_msg(1)

print("Message shape:", message.shape)

embedded = model.embed(
    imgs=image,
    msgs=message,
    is_video=False
)

print("\nEmbed output keys:")
print(embedded.keys())

for k, v in embedded.items():
    if torch.is_tensor(v):
        print(k, v.shape)
    else:
        print(k, type(v))

print("\nRunning detector...")

detected = model.detect(
    embedded["imgs_w"],
    is_video=False
)

print("\nDetect output keys:")
print(detected.keys())

for k, v in detected.items():
    if torch.is_tensor(v):
        print(k, v.shape)
    else:
        print(k, type(v))

print("\nExtracting message...")

msg = model.extract_message(
    embedded["imgs_w"]
)

print(msg.shape)