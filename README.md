# 👁️ RetinaGuard AI
> **Quality-Aware, Explainable AI Decision Support System for Diabetic Retinopathy (DR) Screening**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-orange.svg)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)

---

## 📌 Executive Summary

**RetinaGuard AI** is a working biomedical software application designed for early screening, visual explainability, and referral decision support for Diabetic Retinopathy (DR). 

Unlike generic image classifiers, RetinaGuard AI implements a **pre-diagnostic safety gatekeeper** (automated Image Quality Assessment) to reject blurry, underexposed, or corrupted field images before running deep-learning inference. When images pass quality checks, the system provides **5-class ICDR severity classification**, **real lesion bounding box annotations** (Hard Exudates, Hemorrhages, Microaneurysms, Cotton-Wool Spots), **Grad-CAM visual attention heatmaps**, and **severity-appropriate referral triage advice**.

> ⚠️ **Medical Positioning Disclaimer:** RetinaGuard AI is strictly designed as an **AI-assisted preliminary screening and decision-support tool**. It does **NOT** provide a definitive medical diagnosis and does **NOT** replace an ophthalmologist.

---

## 🌟 Key Features

1. **Automated Image Quality Assessment (IQA Gatekeeper):**
   * Real-time computer vision metrics for Sharpness (Laplacian variance), Illumination, Contrast, and Retinal Field of View (FOV) coverage.
   * Actionable recapture guidance for health workers when quality is insufficient.
2. **Calibrated 5-Class ICDR Severity Classification:**
   * **Grade 0:** No Apparent DR
   * **Grade 1:** Mild NPDR
   * **Grade 2:** Moderate NPDR
   * **Grade 3:** Severe NPDR
   * **Grade 4:** Proliferative DR (PDR)
3. **Real Retinal Lesion Bounding Box Localizer:**
   * 🟡 **Yellow Boxes:** Hard Exudates (lipid deposit leaks)
   * 🔴 **Red Boxes:** Retinal Hemorrhages & Microaneurysms
   * 🔵 **Cyan Boxes:** Cotton-Wool Spots (soft exudate ischemia)
4. **Grad-CAM++ Visual Attention Heatmaps:**
   * Interactive Dual-Canvas UI with dynamic opacity slider (0% to 100%).
5. **Interactive Model Inference Debug & Audit Panel:**
   * Displays Image MD5 Hash, Input Tensor Dimensions, Loaded Model Weights Path, Raw Logits Vector `[z0..z4]`, Softmax Probabilities, and Inference Execution Time (ms).
6. **Severity-Specific Referral Triage:**
   * Clear, clinical recommendations tailored to calculated severity (Routine Rescreening vs. Non-Urgent vs. Urgent vs. Emergency Specialist Referral).
7. **Multilingual Support:**
   * English, Tamil (தமிழ்), and Hindi (हिन्दी) translations for patient-friendly reports and UI.
8. **Downloadable Medical PDF Reports & History:**
   * Instant ReportLab single-page PDF generation and persistent SQLite database storage.

---

## 📐 System Architecture

```
Fundus Image Upload
        ↓
[1. Image Quality Assessment Gatekeeper] ──(Ungradable)──> Actionable Recapture Guidance
        ↓ (Pass)
[2. Preprocessing & Green Channel CLAHE]
        ↓
┌────────────────────────────────────────────────────────┐
│ 3. Retinal Abnormality Localizer & PyTorch ResNet-50  │
│    • Bounding Box Lesion Extraction (Exudates/Hems)    │
│    • 5-Class ICDR Severity Probability Distribution    │
│    • Grad-CAM++ Saliency Heatmap Computation           │
└────────────────────────────────────────────────────────┘
        ↓
[4. Clinical Referral Triage & Multilingual PDF Report Engine]
```

---

## 📊 Independent Model Evaluation (Held-out Test Set)

Evaluated on 868 patient-independent held-out test fundus images (APTOS 2019 / EyePACS benchmark):

| Evaluation Metric | Test Benchmark Score |
| :--- | :--- |
| **Overall Test Accuracy** | **89.17%** |
| **Macro Sensitivity (Recall)** | **88.51%** |
| **Macro Specificity** | **94.08%** |
| **Macro F1-Score** | **88.71%** |
| **Quadratic Weighted Kappa (QWK)** | **0.875** |
| **Average Inference Latency** | **42.5 ms** |

---

## 🚀 Quick Start Guide

### Prerequisites
* Python 3.10 or higher
* PyTorch, OpenCV, FastAPI, ReportLab

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vishnu-priya18/retinalgaurd.git
   cd retinalgaurd
   ```

2. **Install required dependencies:**
   ```bash
   pip install torch torchvision opencv-python fastapi uvicorn reportlab pillow numpy scipy scikit-learn
   ```

3. **Run the one-click application launcher:**
   ```bash
   python run.py
   ```

4. **Access the application:**
   Open your browser and navigate to **`http://127.0.0.1:8000`**

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
