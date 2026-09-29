import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
import cv2
import numpy as np
import os
import math
import hashlib
import time
from PIL import Image

class RetinaGuardNet(nn.Module):
    """
    PyTorch Medical Image Classifier for 5-Class ICDR Diabetic Retinopathy Screening.
    Backbone: ResNet-50
    Classes:
      0 — NO APPARENT DR
      1 — MILD NPDR
      2 — MODERATE NPDR
      3 — SEVERE NPDR
      4 — PROLIFERATIVE DR (PDR)
    """
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

class DREngine:
    """
    Real PyTorch Deep Learning DR Inference Engine with Full Debug Metadata.
    """
    ICDR_CLASSES = [
        {"class_id": 0, "name": "No Apparent DR", "severity": "No apparent DR", "icdr_grade": "Grade 0"},
        {"class_id": 1, "name": "Mild NPDR", "severity": "Mild NPDR", "icdr_grade": "Grade 1"},
        {"class_id": 2, "name": "Moderate NPDR", "severity": "Moderate NPDR", "icdr_grade": "Grade 2"},
        {"class_id": 3, "name": "Severe NPDR", "severity": "Severe NPDR", "icdr_grade": "Grade 3"},
        {"class_id": 4, "name": "Proliferative DR (PDR)", "severity": "Proliferative DR", "icdr_grade": "Grade 4"}
    ]

    def __init__(self, weights_path=None):
        if weights_path is None:
            weights_path = os.path.join(os.path.dirname(__file__), "models", "retinaguard_resnet50.pth")

        self.weights_path = weights_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = RetinaGuardNet(num_classes=5).to(self.device)
        self.model_loaded = False

        if os.path.exists(self.weights_path):
            try:
                state_dict = torch.load(self.weights_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                self.model_loaded = True
                print(f"[DREngine] Successfully loaded fine-tuned PyTorch model weights from {self.weights_path}")
            except Exception as e:
                print(f"[DREngine] Error loading weights: {e}")
                self.model_loaded = False
        else:
            print(f"[DREngine] Warning: Model weights file not found at {self.weights_path}.")

        self.model.eval()

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def preprocess_retina(self, image_bytes: bytes) -> tuple:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("Corrupt image data")

        g_channel = img_bgr[:, :, 1]
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        g_enhanced = clahe.apply(g_channel)

        enhanced_bgr = img_bgr.copy()
        enhanced_bgr[:, :, 1] = g_enhanced

        img_rgb = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        tensor_img = self.transform(pil_img).unsqueeze(0).to(self.device)
        return img_bgr, img_rgb, tensor_img

    def predict(self, image_bytes: bytes, lesion_summary: dict = None) -> dict:
        """
        Executes real PyTorch tensor forward pass and extracts debug metadata.
        """
        start_time = time.time()
        md5_hash = hashlib.md5(image_bytes).hexdigest()

        # Check if trained weights are loaded
        if not self.model_loaded:
            return {
                "predicted_class_id": -1,
                "predicted_class_name": "AI classification unavailable — model validation required",
                "icdr_grade": "N/A",
                "severity_level": "Unavailable",
                "confidence_score": 0.0,
                "uncertainty_index": 1.0,
                "reliability_status": "Uncertain",
                "is_uncertain": True,
                "class_probabilities": [],
                "debug_info": {
                    "md5_hash": md5_hash,
                    "model_name": "ResNet-50 RetinaGuardNet",
                    "model_loaded": False,
                    "weights_path": self.weights_path,
                    "error": "Model weights checkpoint file missing or unvalidated."
                }
            }

        img_bgr, img_rgb, tensor_img = self.preprocess_retina(image_bytes)

        with torch.no_grad():
            raw_logits_tensor = self.model(tensor_img).cpu().squeeze(0)
            raw_logits = raw_logits_tensor.numpy()
            probs_tensor = torch.softmax(raw_logits_tensor, dim=0)
            probabilities = probs_tensor.numpy()

        # If lesion summary is available, combine deep feature logits with spatial lesion features
        bias = np.zeros(5, dtype=np.float32)
        if lesion_summary:
            tot_lesions = lesion_summary.get("total_lesions_count", 0)
            ex_count = lesion_summary.get("hard_exudates_count", 0)
            hem_count = lesion_summary.get("hemorrhages_count", 0) + lesion_summary.get("microaneurysms_count", 0)
            cws_count = lesion_summary.get("cotton_wool_spots_count", 0)
            quad_count = lesion_summary.get("quadrant_count", 0)

            if tot_lesions == 0:
                bias[0] += 2.5
            elif hem_count <= 3 and ex_count == 0 and cws_count == 0:
                bias[1] += 2.2
            elif 1 <= ex_count <= 8 or (3 < hem_count <= 10 and quad_count <= 2):
                bias[2] += 2.4
            elif hem_count > 10 or cws_count > 0 or quad_count >= 3:
                bias[3] += 2.6
            elif tot_lesions > 15 and quad_count >= 3:
                bias[4] += 2.8

        calibrated_logits = raw_logits + bias
        exp_logits = np.exp(calibrated_logits - np.max(calibrated_logits))
        calibrated_probs = exp_logits / np.sum(exp_logits)

        # Strictly select predicted class via Argmax
        predicted_class_id = int(np.argmax(calibrated_probs))
        confidence_score = float(calibrated_probs[predicted_class_id])

        # Compute Shannon Entropy
        entropy = 0.0
        for p in calibrated_probs:
            if p > 1e-7:
                entropy -= p * math.log2(p)
        normalized_uncertainty = float(entropy / math.log2(5))

        if confidence_score >= 0.70 and normalized_uncertainty < 0.45:
            reliability_status = "Reliable"
        elif confidence_score >= 0.50:
            reliability_status = "Review Recommended"
        else:
            reliability_status = "Uncertain"

        class_probabilities = []
        for i, prob in enumerate(calibrated_probs):
            class_info = self.ICDR_CLASSES[i].copy()
            class_info["probability"] = float(round(prob * 100.0, 2))
            class_probabilities.append(class_info)

        predicted_info = self.ICDR_CLASSES[predicted_class_id]
        latency_ms = round((time.time() - start_time) * 1000.0, 1)

        return {
            "predicted_class_id": predicted_class_id,
            "predicted_class_name": predicted_info["name"],
            "icdr_grade": predicted_info["icdr_grade"],
            "severity_level": predicted_info["severity"],
            "confidence_score": round(confidence_score * 100.0, 2),
            "uncertainty_index": round(normalized_uncertainty, 3),
            "reliability_status": reliability_status,
            "is_uncertain": bool(reliability_status == "Uncertain"),
            "class_probabilities": class_probabilities,
            "raw_probabilities": [float(p) for p in calibrated_probs],
            "debug_info": {
                "md5_hash": md5_hash,
                "input_tensor_shape": list(tensor_img.shape),
                "model_name": "ResNet-50 RetinaGuardNet",
                "model_loaded": True,
                "weights_path": self.weights_path,
                "raw_logits": [float(round(z, 4)) for z in raw_logits],
                "softmax_probabilities": [float(round(p * 100, 2)) for p in probabilities],
                "calibrated_probabilities": [float(round(p * 100, 2)) for p in calibrated_probs],
                "argmax_index": predicted_class_id,
                "inference_time_ms": latency_ms
            }
        }
