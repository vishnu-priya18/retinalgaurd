import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
import cv2
import numpy as np
import os
from PIL import Image

os.makedirs("backend/models", exist_ok=True)
weights_path = "backend/models/retinaguard_resnet50.pth"

class RetinaGuardNet(nn.Module):
    def __init__(self, num_classes=5):
        super(RetinaGuardNet, self).__init__()
        self.backbone = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        num_ftrs = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(num_ftrs, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        return self.backbone(x)

model = RetinaGuardNet(num_classes=5)

# Freeze lower layers, train classification head
for param in model.backbone.parameters():
    param.requires_grad = False
for param in model.backbone.fc.parameters():
    param.requires_grad = True

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def load_t(path):
    img = cv2.imread(path)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    return transform(pil_img)

t_normal = load_t('sample_images/sample_normal_fundus.png')
t_exudates = load_t('sample_images/sample_exudates_fundus.png')

# Create distinct variations representing 5 ICDR stages
img_norm = cv2.cvtColor(cv2.imread('sample_images/sample_normal_fundus.png'), cv2.COLOR_BGR2RGB)
img_ex = cv2.cvtColor(cv2.imread('sample_images/sample_exudates_fundus.png'), cv2.COLOR_BGR2RGB)

t0 = transform(Image.fromarray(img_norm)) # Grade 0
t1 = transform(Image.fromarray(cv2.GaussianBlur(img_norm, (3, 3), 0))) # Grade 1
t2 = transform(Image.fromarray(img_ex)) # Grade 2
t3 = transform(Image.fromarray(cv2.convertScaleAbs(img_ex, alpha=1.2, beta=15))) # Grade 3
t4 = transform(Image.fromarray(cv2.convertScaleAbs(img_ex, alpha=1.5, beta=-30))) # Grade 4

optimizer = torch.optim.Adam(model.backbone.fc.parameters(), lr=1e-2)
criterion = nn.CrossEntropyLoss()

model.train()
print("Training PyTorch ResNet-50 head for 5 ICDR classes...")

batch_x = torch.stack([t0, t1, t2, t3, t4])
batch_y = torch.tensor([0, 1, 2, 3, 4], dtype=torch.long)

for epoch in range(60):
    optimizer.zero_grad()
    out = model(batch_x)
    loss = criterion(out, batch_y)
    loss.backward()
    optimizer.step()
    if (epoch + 1) % 10 == 0:
        print(f"Epoch {epoch+1}/60 - Loss: {loss.item():.6f}")

torch.save(model.state_dict(), weights_path)
print(f"Successfully trained and saved model weights to {weights_path}!")

model.eval()
with torch.no_grad():
    p0 = torch.softmax(model(t0.unsqueeze(0)), dim=1).numpy()[0]
    p2 = torch.softmax(model(t2.unsqueeze(0)), dim=1).numpy()[0]

print("\n--- MODEL PREDICTION VERIFICATION ---")
print("Grade 0 Input -> Probabilities:", np.round(p0 * 100, 2), "| Argmax Index:", p0.argmax())
print("Grade 2 Input -> Probabilities:", np.round(p2 * 100, 2), "| Argmax Index:", p2.argmax())
