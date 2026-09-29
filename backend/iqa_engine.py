import cv2
import numpy as np

class ImageQualityAnalyzer:
    """
    Real Computer Vision Image Quality Assessment (IQA) for Retinal Fundus Images.
    Evaluates:
    1. Blur / Sharpness (Laplacian variance)
    2. Illumination / Exposure (Mean non-background intensity)
    3. Contrast (RMS contrast / standard deviation)
    4. Retinal Field of View (FOV) Ratio

    Thresholds calibrated to ensure usable normal fundus images PASS quality checks,
    while only genuinely ungradable (out-of-focus, dark, or corrupt) images fail.
    """
    def __init__(self):
        self.blur_threshold = 20.0          # Below this is considered out-of-focus / blurry
        self.min_brightness = 20.0          # Below this is underexposed / too dark
        self.max_brightness = 230.0         # Above this is overexposed / severe glare
        self.min_contrast = 14.0            # Below this is low contrast
        self.min_fov_ratio = 0.20           # Minimum non-black retinal area ratio

    def analyze(self, image_bytes: bytes) -> dict:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {
                "quality_status": "FAIL",
                "overall_score": 0.0,
                "metrics": {},
                "failure_reasons": ["Invalid or corrupt image file"],
                "recapture_guidance": "Please upload a valid image file in JPG or PNG format."
            }

        height, width, _ = img.shape
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Retinal FOV Segmentation (non-black background)
        _, retinal_mask = cv2.threshold(gray, 18, 255, cv2.THRESH_BINARY)
        total_pixels = height * width
        retinal_pixels = np.count_nonzero(retinal_mask)
        fov_ratio = float(retinal_pixels) / float(total_pixels) if total_pixels > 0 else 0.0

        if retinal_pixels > 0:
            retinal_values = gray[retinal_mask > 0]
        else:
            retinal_values = gray.flatten()

        # Blur (Laplacian Variance)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        
        # Brightness (Mean Non-Background Intensity)
        mean_brightness = float(np.mean(retinal_values)) if len(retinal_values) > 0 else 0.0

        # Contrast (Standard Deviation)
        contrast_std = float(np.std(retinal_values)) if len(retinal_values) > 0 else 0.0

        failure_reasons = []
        guidance_notes = []

        if fov_ratio < self.min_fov_ratio:
            failure_reasons.append(f"Insufficient retinal visibility (FOV coverage: {fov_ratio*100:.1f}%)")
            guidance_notes.append("Center the retinal camera view to ensure macula and optic disc are visible within frame.")

        if laplacian_var < self.blur_threshold:
            failure_reasons.append(f"Excessive image blur (Sharpness score: {laplacian_var:.1f})")
            guidance_notes.append("Steady the camera/patient and refocus before capturing the fundus photograph.")

        if mean_brightness < self.min_brightness:
            failure_reasons.append(f"Underexposed / Image too dark (Mean brightness: {mean_brightness:.1f})")
            guidance_notes.append("Increase illumination intensity or adjust flash settings on fundus camera.")
        elif mean_brightness > self.max_brightness:
            failure_reasons.append(f"Overexposed / Excessive glare (Mean brightness: {mean_brightness:.1f})")
            guidance_notes.append("Reduce illumination brightness to prevent corneal glare artifacts.")

        if contrast_std < self.min_contrast:
            failure_reasons.append(f"Low contrast (Contrast score: {contrast_std:.1f})")
            guidance_notes.append("Ensure pupil is adequately dilated and lens opacity is accounted for to improve vascular contrast.")

        is_passed = len(failure_reasons) == 0
        quality_status = "PASS" if is_passed else "FAIL"

        blur_norm = min(1.0, laplacian_var / 100.0)
        bright_norm = 1.0 - abs(mean_brightness - 120.0) / 120.0
        bright_norm = max(0.0, min(1.0, bright_norm))
        contrast_norm = min(1.0, contrast_std / 45.0)
        fov_norm = min(1.0, fov_ratio / 0.65)

        overall_score = float(round((0.35 * blur_norm + 0.25 * bright_norm + 0.25 * contrast_norm + 0.15 * fov_norm) * 100.0, 1))

        if guidance_notes:
            recapture_guidance = " | ".join(guidance_notes)
        else:
            recapture_guidance = "Image quality is optimal for reliable AI-assisted screening analysis."

        return {
            "quality_status": quality_status,
            "is_usable": is_passed,
            "overall_score": overall_score,
            "metrics": {
                "sharpness_laplacian": round(laplacian_var, 2),
                "mean_brightness": round(mean_brightness, 2),
                "contrast_std": round(contrast_std, 2),
                "fov_ratio": round(fov_ratio, 3),
                "image_width": width,
                "image_height": height
            },
            "failure_reasons": failure_reasons,
            "recapture_guidance": recapture_guidance
        }
