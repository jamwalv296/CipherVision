import sys
sys.path.insert(0, 'src')
from data.dataset import CipherVisionDataset
from torch.utils.data import DataLoader

ds = CipherVisionDataset('data/DIV2K_train_HR', patch_size=256)
print('dataset size:', len(ds))

img, payload = ds[0]
print('img shape:', img.shape, 'range:', img.min().item(), img.max().item())
print('payload shape:', payload.shape, 'unique vals:', payload.unique())

loader = DataLoader(ds, batch_size=2, shuffle=True)
batch_img, batch_payload = next(iter(loader))
print('batch img:', batch_img.shape, 'batch payload:', batch_payload.shape)
print('OK')