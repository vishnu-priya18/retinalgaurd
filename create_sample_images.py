import cv2
import numpy as np
import os

os.makedirs("sample_images", exist_ok=True)

def generate_fundus_base(width=512, height=512):
    # Dark background
    img = np.zeros((height, width, 3), dtype=np.uint8)
    center = (width // 2, height // 2)
    radius = 230

    # Draw Orange/Red Retinal Disc Base
    Y, X = np.ogrid[:height, :width]
    dist_from_center = np.sqrt((X - center[0])**2 + (Y - center[1])**2)
    mask = dist_from_center <= radius

    # Retinal color gradient
    retina_bg = np.zeros((height, width, 3), dtype=np.float32)
    retina_bg[mask, 2] = 180 + 40 * (1.0 - dist_from_center[mask]/radius)  # Red channel
    retina_bg[mask, 1] = 70 + 30 * (1.0 - dist_from_center[mask]/radius)   # Green channel
    retina_bg[mask, 0] = 10                                                # Blue channel
    
    img[mask] = np.uint8(retina_bg[mask])

    # Draw Optic Disc (bright yellow-pink ellipse on temporal side)
    disc_center = (width // 2 - 80, height // 2 - 10)
    cv2.ellipse(img, disc_center, (35, 45), 0, 0, 360, (140, 220, 255), -1)

    # Draw Major Retinal Blood Vessels radiating from optic disc
    vessel_color = (15, 20, 110) # Dark red/maroon
    
    # Superior & Inferior Vascular Arcades
    points_sup = np.array([[disc_center[0], disc_center[1]], [disc_center[0]+40, disc_center[1]-80], [disc_center[0]+120, disc_center[1]-130], [disc_center[0]+200, disc_center[1]-140]], np.int32)
    points_inf = np.array([[disc_center[0], disc_center[1]], [disc_center[0]+40, disc_center[1]+80], [disc_center[0]+120, disc_center[1]+130], [disc_center[0]+200, disc_center[1]+140]], np.int32)
    
    cv2.polylines(img, [points_sup], False, vessel_color, 4, cv2.LINE_AA)
    cv2.polylines(img, [points_inf], False, vessel_color, 4, cv2.LINE_AA)

    # Branches
    cv2.line(img, (disc_center[0]+40, disc_center[1]-80), (disc_center[0]+90, disc_center[1]-160), vessel_color, 2, cv2.LINE_AA)
    cv2.line(img, (disc_center[0]+40, disc_center[1]+80), (disc_center[0]+90, disc_center[1]+160), vessel_color, 2, cv2.LINE_AA)

    # Fovea / Macula (darker avascular region)
    macula_center = (width // 2 + 30, height // 2)
    cv2.circle(img, macula_center, 25, (10, 35, 120), -1)

    return img

# 1. Normal Fundus Image (Grade 0)
normal_img = generate_fundus_base()
cv2.imwrite("sample_images/sample_normal_fundus.png", normal_img)

# 2. Exudates & Hemorrhages Fundus Image (NPDR Pattern)
npdr_img = generate_fundus_base()
# Add Hard Exudates (bright yellow dots near macula)
exudate_color = (180, 245, 255)
for pos in [(280, 240), (295, 260), (310, 230), (275, 270), (320, 250), (290, 220)]:
    cv2.circle(npdr_img, pos, np.random.randint(3, 7), exudate_color, -1)

# Add Dot Hemorrhages (small dark red spots)
hem_color = (5, 5, 80)
for pos in [(250, 210), (330, 280), (220, 300), (340, 210)]:
    cv2.circle(npdr_img, pos, np.random.randint(2, 5), hem_color, -1)

cv2.imwrite("sample_images/sample_exudates_fundus.png", npdr_img)

# 3. Low Quality / Blurred Image (Quality Gate FAIL Test Case)
blur_img = cv2.GaussianBlur(normal_img, (31, 31), 15.0)
# Add dark underexposure mask
blur_img = np.uint8(blur_img * 0.35)
cv2.imwrite("sample_images/sample_blurry_low_quality.png", blur_img)

print("Created 3 sample retinal test images in sample_images/")
