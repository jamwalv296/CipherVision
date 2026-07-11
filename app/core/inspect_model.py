from pixelseal import model

print("=" * 80)
print(type(model))
print("=" * 80)

for name in dir(model):
    if not name.startswith("_"):
        print(name)