import os
import json
import base64
import io
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from typing import Optional

from iqa_engine import ImageQualityAnalyzer
from dr_engine import DREngine
from gradcam_engine import GradCAMEngine
from lesion_engine import RetinalLesionDetector
from triage_engine import TriageEngine
from database import Database
from pdf_generator import PDFReportGenerator
from multilingual_data import TRANSLATIONS
from model_validation import ModelValidationReport

app = FastAPI(
    title="RetinaGuard AI - Backend API",
    description="Real AI-Assisted Diabetic Retinopathy Screening & Decision Support System",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Engines
db = Database()
iqa_engine = ImageQualityAnalyzer()
dr_engine = DREngine()
gradcam_engine = GradCAMEngine(dr_engine)
lesion_detector = RetinalLesionDetector()

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "ONLINE",
        "system": "RetinaGuard AI Decision Support Server",
        "pytorch_device": str(dr_engine.device),
        "model_architecture": "ResNet-50 RetinaGuardNet Calibrated Multi-Class",
        "iqa_engine": "Real CV Laplacian/Illumination Analyzer",
        "lesion_detector": "Real Morphological & Color Bounding Box Localizer",
        "explainability": "Grad-CAM++ Activation Engine"
    }

@app.get("/api/v1/validation")
def get_validation_report_endpoint():
    """
    Returns independent model validation metrics, 5x5 confusion matrix, and audit data.
    """
    return ModelValidationReport.get_validation_report()

@app.post("/api/v1/quality-check")
async def quality_check_endpoint(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image format.")

    image_bytes = await file.read()
    iqa_result = iqa_engine.analyze(image_bytes)
    return iqa_result

@app.post("/api/v1/screen")
async def full_screening_endpoint(
    file: UploadFile = File(...),
    patient_id: str = Form("ANONYMOUS"),
    patient_name: Optional[str] = Form("N/A"),
    age: Optional[int] = Form(None),
    sex: Optional[str] = Form(None),
    hba1c: Optional[float] = Form(None),
    diabetes_duration_years: Optional[float] = Form(None),
    has_hypertension: Optional[bool] = Form(False),
    lang: Optional[str] = Form("en")
):
    image_bytes = await file.read()

    # Step 1: Real Image Quality Assessment Gatekeeper
    iqa_res = iqa_engine.analyze(image_bytes)

    patient_info = {
        "patient_id": patient_id,
        "patient_name": patient_name,
        "age": age,
        "sex": sex,
        "hba1c": hba1c,
        "diabetes_duration_years": diabetes_duration_years,
        "has_hypertension": has_hypertension
    }

    # If IQA Fails -> Stop DR Pipeline
    if iqa_res["quality_status"] == "FAIL":
        triage_res = TriageEngine.EvaluateTriage(iqa_res, None, None, patient_info)
        
        record_data = {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "age": age,
            "sex": sex,
            "hba1c": hba1c,
            "diabetes_duration": diabetes_duration_years,
            "hypertension": has_hypertension,
            "quality_status": "FAIL",
            "quality_score": iqa_res["overall_score"],
            "quality_metrics": iqa_res["metrics"],
            "failure_reasons": iqa_res["failure_reasons"],
            "icdr_grade": "Ungradable",
            "predicted_class_name": "Insufficient Quality",
            "triage_state": "RECHECK_IMAGE",
            "referral_priority": "REPEAT_ACQUISITION",
            "urgency_level": triage_res["urgency_level"],
            "clinical_summary": iqa_res["recapture_guidance"]
        }
        screening_id = db.save_screening(record_data)
        orig_b64 = f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"

        return {
            "screening_id": screening_id,
            "patient_info": patient_info,
            "quality_assessment": iqa_res,
            "dr_analysis": None,
            "lesions_analysis": {
                "annotated_image_b64": orig_b64,
                "lesion_summary": {},
                "lesions": [],
                "total_lesions_count": 0
            },
            "explainability": {
                "original_image_b64": orig_b64,
                "heatmap_only_b64": None,
                "overlay_image_b64": orig_b64
            },
            "triage": triage_res,
            "why_this_severity": "Image quality is insufficient for reliable AI analysis.",
            "translations": TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        }

    # Step 2: Real Retinal Lesion Detection & Localization
    lesion_res = lesion_detector.detect_and_annotate(image_bytes)

    # Step 3: Real PyTorch Calibrated DR Prediction
    dr_res = dr_engine.predict(image_bytes, lesion_summary=lesion_res["lesion_summary"])

    # Step 4: Real Grad-CAM Heatmap Computation
    gradcam_res = gradcam_engine.generate_heatmap(image_bytes, target_class_id=max(0, dr_res["predicted_class_id"]))

    # Step 5: Severity-Specific Referral Triage Evaluation
    triage_res = TriageEngine.EvaluateTriage(iqa_res, dr_res, lesion_res, patient_info)

    # Step 6: Construct "Why This Severity?" Rationale Explanation
    les_sum = lesion_res["lesion_summary"]
    findings_bullets = []
    if les_sum.get("hard_exudates_count", 0) > 0:
        findings_bullets.append(f"{les_sum['hard_exudates_count']} Hard Exudate deposit region(s)")
    if les_sum.get("hemorrhages_count", 0) > 0:
        findings_bullets.append(f"{les_sum['hemorrhages_count']} Retinal Hemorrhage region(s)")
    if les_sum.get("microaneurysms_count", 0) > 0:
        findings_bullets.append(f"{les_sum['microaneurysms_count']} Microaneurysm region(s)")
    if les_sum.get("cotton_wool_spots_count", 0) > 0:
        findings_bullets.append(f"{les_sum['cotton_wool_spots_count']} Cotton-Wool Spot region(s)")

    if not findings_bullets:
        why_text = "The AI model detected normal microvascular structure with zero significant lesion clusters."
    else:
        why_text = f"Classified as {dr_res['predicted_class_name']} based on neural feature activations supported by: " + ", ".join(findings_bullets) + f" distributed across {les_sum.get('quadrant_count', 0)} quadrant(s)."

    # Step 7: Persistent SQLite Storage
    record_data = {
        "patient_id": patient_id,
        "patient_name": patient_name,
        "age": age,
        "sex": sex,
        "hba1c": hba1c,
        "diabetes_duration": diabetes_duration_years,
        "hypertension": has_hypertension,
        "quality_status": "PASS",
        "quality_score": iqa_res["overall_score"],
        "quality_metrics": iqa_res["metrics"],
        "failure_reasons": [],
        "icdr_grade": dr_res["icdr_grade"],
        "predicted_class_name": dr_res["predicted_class_name"],
        "confidence_score": dr_res["confidence_score"],
        "uncertainty_index": dr_res["uncertainty_index"],
        "class_probabilities": dr_res["class_probabilities"],
        "triage_state": triage_res["triage_state"],
        "referral_priority": triage_res["referral_priority"],
        "urgency_level": triage_res["urgency_level"],
        "clinical_summary": triage_res["clinical_summary"]
    }
    screening_id = db.save_screening(record_data)

    return {
        "screening_id": screening_id,
        "patient_info": patient_info,
        "quality_assessment": iqa_res,
        "dr_analysis": dr_res,
        "lesions_analysis": lesion_res,
        "explainability": gradcam_res,
        "triage": triage_res,
        "why_this_severity": why_text,
        "translations": TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    }

@app.get("/api/v1/dashboard")
def get_dashboard_metrics():
    return db.get_dashboard_stats()

@app.get("/api/v1/history")
def get_screening_history(search: Optional[str] = None, filter: Optional[str] = None):
    return db.get_all_screenings(search=search, result_filter=filter)

@app.get("/api/v1/screening/{screening_id}")
def get_screening_detail(screening_id: str):
    rec = db.get_screening_by_id(screening_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Screening record not found.")
    return rec

@app.get("/api/v1/report/pdf/{screening_id}")
def download_pdf_report(screening_id: str):
    rec = db.get_screening_by_id(screening_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Screening record not found.")

    pdf_bytes = PDFReportGenerator.generate_pdf(rec)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=RetinaGuard_{screening_id}.pdf"}
    )

@app.get("/api/v1/translations/{lang}")
def get_language_dictionary(lang: str = "en"):
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
