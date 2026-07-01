import torch
from torchvision import transforms
from PIL import Image
from src.models import CipherVision
from src.crypto import CertificateAuthority

def run_pipeline():
    ca = CertificateAuthority()
    metadata = {"artist": "Artist1", "id": "101", "ts": "2026-07-01"}
    
    encrypted_bytes = ca.encrypt_metadata(metadata)
    bits_payload = ca.bytes_to_bits(encrypted_bytes, target_len=64)
    payload_tensor = torch.tensor([bits_payload]).float()

    model = CipherVision()
    model.eval()

    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor()
    ])
    
    img = Image.new('RGB', (256, 256), color='red') 
    img_tensor = transform(img).unsqueeze(0)

    with torch.no_grad():
        stego, recovered_payload = model(img_tensor, payload_tensor)

    pred_bits = (recovered_payload[0] > 0.5).int().tolist()
    print("Metadata processed successfully.")

if __name__ == "__main__":
    run_pipeline()