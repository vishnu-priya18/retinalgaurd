import torch
import torch.nn.functional as F
import cv2
import numpy as np
import base64
from PIL import Image
import io

class GradCAMEngine:
    """
    Real PyTorch Grad-CAM (Gradient-weighted Class Activation Mapping) Engine.
    Extracts actual feature map activations and backpropagates class gradients
    from the target layer of the neural network to produce a spatial heatmap.
    """
    def __init__(self, dr_engine):
        self.dr_engine = dr_engine
        self.device = dr_engine.device
        self.model = dr_engine.model
        self.gradients = None
        self.activations = None
        self._register_hooks()

    def _register_hooks(self):
        # Target the final convolutional block of ResNet-50 backbone
        target_layer = self.model.backbone.layer4[2].conv3

        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0].detach()

        target_layer.register_forward_hook(forward_hook)
        target_layer.register_full_backward_hook(backward_hook)

    def generate_heatmap(self, image_bytes: bytes, target_class_id: int = None) -> dict:
        """
        Executes real Grad-CAM computation on input image tensor.
        Returns base64 encoded original image, heatmap overlay, and raw heatmap array.
        """
        img_bgr, img_rgb, tensor_img = self.dr_engine.preprocess_retina(image_bytes)
        tensor_img.requires_grad = True

        self.model.eval()
        self.model.zero_grad()

        # Forward pass
        logits = self.model(tensor_img)
        
        if target_class_id is None:
            target_class_id = int(torch.argmax(logits, dim=1).item())

        # Target class score
        score = logits[0, target_class_id]
        score.backward()

        if self.gradients is None or self.activations is None:
            # Fallback in case hooks failed: return empty map
            cam = np.zeros((img_bgr.shape[0], img_bgr.shape[1]), dtype=np.float32)
        else:
            # Global Average Pooling of gradients
            gradients = self.gradients.cpu().data.numpy()[0]
            activations = self.activations.cpu().data.numpy()[0]
            weights = np.mean(gradients, axis=(1, 2))

            # Weighted combination of activation maps
            cam = np.zeros(activations.shape[1:], dtype=np.float32)
            for i, w in enumerate(weights):
                cam += w * activations[i, :, :]

            # Apply ReLU to keep positive contributions
            cam = np.maximum(cam, 0)
            
            # Normalize to [0, 1]
            if np.max(cam) > 0:
                cam = cam / np.max(cam)

        # Resize CAM to match original image dimensions
        orig_h, orig_w, _ = img_bgr.shape
        cam_resized = cv2.resize(cam, (orig_w, orig_h))

        # Apply JET Colormap
        heatmap_uint8 = np.uint8(255 * cam_resized)
        heatmap_bgr = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

        # Blend Heatmap with Original Image (50/50 blend)
        overlay_bgr = cv2.addWeighted(img_bgr, 0.55, heatmap_bgr, 0.45, 0)

        # Encode to Base64 strings for frontend rendering
        _, buffer_orig = cv2.imencode(".png", img_bgr)
        orig_b64 = base64.b64encode(buffer_orig).decode("utf-8")

        _, buffer_heatmap = cv2.imencode(".png", heatmap_bgr)
        heatmap_b64 = base64.b64encode(buffer_heatmap).decode("utf-8")

        _, buffer_overlay = cv2.imencode(".png", overlay_bgr)
        overlay_b64 = base64.b64encode(buffer_overlay).decode("utf-8")

        return {
            "original_image_b64": f"data:image/png;base64,{orig_b64}",
            "heatmap_only_b64": f"data:image/png;base64,{heatmap_b64}",
            "overlay_image_b64": f"data:image/png;base64,{overlay_b64}",
            "target_class_id": target_class_id,
            "explanation_text": (
                "Grad-CAM visual heatmap highlights retinal pixel regions (warm red/yellow colors) "
                "that contributed most strongly to the neural network's feature activation score."
            )
        }
