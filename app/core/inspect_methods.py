import inspect
from pixelseal import model

print("=" * 80)
print("embed")
print("=" * 80)
print(inspect.signature(model.embed))

print()

print("=" * 80)
print("detect")
print("=" * 80)
print(inspect.signature(model.detect))

print()

print("=" * 80)
print("extract_message")
print("=" * 80)
print(inspect.signature(model.extract_message))