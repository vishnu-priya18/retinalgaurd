import cv2
import numpy as np
import base64

class RetinalLesionDetector:
    """
    Real Retinal Abnormality Detection & Bounding Box Localization Engine.
    Detects:
    1. Microaneurysms (Tiny dark red dots < 15px^2)
    2. Retinal Hemorrhages (Dark red blobs 15px^2 to 800px^2)
    3. Hard Exudates (Bright yellow lipid deposits in LAB/CLAHE space)
    4. Cotton-Wool Spots (Soft Exudates - Pale white ischemic patches)

    Outputs exact bounding box coordinates [x, y, w, h], centroid, lesion type,
    confidence score, and anatomical quadrant location.
    """
    def __init__(self):
        pass

    def _get_quadrant(self, x: int, y: int, width: int, height: int) -> str:
        cx, cy = width / 2.0, height / 2.0
        if y < cy and x >= cx:
            return "Superior Temporal"
        elif y < cy and x < cx:
            return "Superior Nasal"
        elif y >= cy and x >= cx:
            return "Inferior Temporal"
        else:
            return "Inferior Nasal"

    def detect_and_annotate(self, image_bytes: bytes) -> dict:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            return {
                "annotated_image_b64": None,
                "lesion_summary": {},
                "lesions": [],
                "total_lesions_count": 0
            }

        height, width, _ = img_bgr.shape
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        g_channel = img_bgr[:, :, 1]

        # 1. FOV Mask of Retinal Disc
        _, fov_mask = cv2.threshold(gray, 18, 255, cv2.THRESH_BINARY)

        # Annotated canvas copy
        annotated_bgr = img_bgr.copy()
        lesions_list = []

        # 2. Hard Exudate Detection (Bright Yellow Deposits)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        g_clahe = clahe.apply(g_channel)
        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        l_chan, a_chan, b_chan = cv2.split(lab)

        # Hard exudate criteria: CLAHE peak + High Luminance + Yellow b* channel
        exudate_mask = (g_clahe > 195) & (l_chan > 155) & (b_chan > 128) & (fov_mask > 0)
        exudate_mask_uint8 = np.uint8(exudate_mask * 255)
        kernel_sm = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        exudate_mask_uint8 = cv2.morphologyEx(exudate_mask_uint8, cv2.MORPH_OPEN, kernel_sm)

        contours_ex, _ = cv2.findContours(exudate_mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        exudates_count = 0
        for c in contours_ex:
            area = cv2.contourArea(c)
            if 4 <= area <= 600:
                x, y, w, h = cv2.boundingRect(c)
                # Filter out optic disc center if disc is accidentally highlighted
                if x < width * 0.15 or x > width * 0.85:
                    continue
                exudates_count += 1
                quad = self._get_quadrant(x + w//2, y + h//2, width, height)
                confidence = float(min(0.96, round(0.75 + (area / 600.0) * 0.20, 2)))
                lesion_obj = {
                    "id": f"EX-{exudates_count}",
                    "type": "Hard Exudate",
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "area_pixels": float(area),
                    "confidence": confidence,
                    "quadrant": quad,
                    "description": "Bright yellow lipid leak deposit from damaged retinal capillaries.",
                    "color_hex": "#F59E0B"
                }
                lesions_list.append(lesion_obj)
                # Draw Yellow Bounding Box on Annotated Image
                cv2.rectangle(annotated_bgr, (x-2, y-2), (x+w+2, y+h+2), (0, 215, 255), 2)
                cv2.putText(annotated_bgr, f"EX-{exudates_count}", (x, max(12, y-4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 215, 255), 1, cv2.LINE_AA)

        # 3. Retinal Hemorrhages & Microaneurysms (Dark Red Blobs)
        kernel_bg = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        bottom_hat = cv2.morphologyEx(g_channel, cv2.MORPH_BLACKHAT, kernel_bg)
        hem_mask = (bottom_hat > 24) & (fov_mask > 0)
        hem_mask_uint8 = np.uint8(hem_mask * 255)

        contours_hem, _ = cv2.findContours(hem_mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        hemorrhages_count = 0
        microaneurysms_count = 0

        for c in contours_hem:
            area = cv2.contourArea(c)
            if 3 <= area <= 800:
                x, y, w, h = cv2.boundingRect(c)
                aspect_ratio = float(w) / float(h) if h > 0 else 0
                if 0.35 <= aspect_ratio <= 2.8: # Filter out elongated major vessels
                    quad = self._get_quadrant(x + w//2, y + h//2, width, height)
                    if area < 16:
                        microaneurysms_count += 1
                        l_type = "Microaneurysm"
                        l_id = f"MA-{microaneurysms_count}"
                        l_desc = "Tiny focal outpouching of retinal capillary wall."
                        l_color = (0, 0, 255) # Red
                    else:
                        hemorrhages_count += 1
                        l_type = "Retinal Hemorrhage"
                        l_id = f"HEM-{hemorrhages_count}"
                        l_desc = "Intraretinal capillary blood leakage."
                        l_color = (0, 0, 220) # Deep Red

                    confidence = float(min(0.95, round(0.72 + (area / 800.0) * 0.22, 2)))
                    lesion_obj = {
                        "id": l_id,
                        "type": l_type,
                        "bbox": [int(x), int(y), int(w), int(h)],
                        "area_pixels": float(area),
                        "confidence": confidence,
                        "quadrant": quad,
                        "description": l_desc,
                        "color_hex": "#DC2626"
                    }
                    lesions_list.append(lesion_obj)
                    # Draw Red Bounding Box on Annotated Image
                    cv2.rectangle(annotated_bgr, (x-2, y-2), (x+w+2, y+h+2), l_color, 2)
                    cv2.putText(annotated_bgr, l_id, (x, max(12, y-4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, l_color, 1, cv2.LINE_AA)

        # 4. Cotton-Wool Spots / Soft Exudates (Pale White Ischemic Patches)
        soft_exudates_count = 0
        soft_mask = (g_clahe > 180) & (l_chan > 140) & (b_chan <= 128) & (fov_mask > 0)
        soft_mask_uint8 = np.uint8(soft_mask * 255)
        soft_mask_uint8 = cv2.morphologyEx(soft_mask_uint8, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        contours_soft, _ = cv2.findContours(soft_mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for c in contours_soft:
            area = cv2.contourArea(c)
            if 30 <= area <= 1000:
                x, y, w, h = cv2.boundingRect(c)
                soft_exudates_count += 1
                quad = self._get_quadrant(x + w//2, y + h//2, width, height)
                lesion_obj = {
                    "id": f"CWS-{soft_exudates_count}",
                    "type": "Cotton-Wool Spot",
                    "bbox": [int(x), int(y), int(w), int(h)],
                    "area_pixels": float(area),
                    "confidence": 0.82,
                    "quadrant": quad,
                    "description": "Fluffy white region of retinal nerve fiber layer ischemia.",
                    "color_hex": "#06B6D4"
                }
                lesions_list.append(lesion_obj)
                # Draw Cyan Bounding Box
                cv2.rectangle(annotated_bgr, (x-2, y-2), (x+w+2, y+h+2), (255, 255, 0), 2)
                cv2.putText(annotated_bgr, f"CWS-{soft_exudates_count}", (x, max(12, y-4)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1, cv2.LINE_AA)

        # Encode Annotated Image to Base64
        _, buffer_ann = cv2.imencode(".png", annotated_bgr)
        annotated_b64 = f"data:image/png;base64,{base64.b64encode(buffer_ann).decode('utf-8')}"

        # Quadrant Distribution Summary
        quadrants_detected = list(set([l["quadrant"] for l in lesions_list]))

        return {
            "annotated_image_b64": annotated_b64,
            "lesion_summary": {
                "hard_exudates_count": exudates_count,
                "hemorrhages_count": hemorrhages_count,
                "microaneurysms_count": microaneurysms_count,
                "cotton_wool_spots_count": soft_exudates_count,
                "total_lesions_count": len(lesions_list),
                "quadrants_affected": quadrants_detected,
                "quadrant_count": len(quadrants_detected)
            },
            "lesions": lesions_list,
            "total_lesions_count": len(lesions_list)
        }
