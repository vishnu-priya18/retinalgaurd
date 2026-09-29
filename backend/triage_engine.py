class TriageEngine:
    """
    Clinical Decision Support & Severity-Specific Referral Triage Engine.
    Maps actual ICDR severity classification (0 to 4) to specific clinical screening recommendations.
    """
    @staticmethod
    def EvaluateTriage(iqa_res: dict, dr_res: dict = None, lesion_res: dict = None, patient_info: dict = None) -> dict:
        # Case 1: Image Quality Assessment Failed
        if iqa_res.get("quality_status") == "FAIL":
            return {
                "triage_state": "RECHECK_IMAGE",
                "referral_priority": "REPEAT_ACQUISITION",
                "urgency_level": "Immediate Re-capture Required",
                "action_code": "RECHECK",
                "recommended_timeline": "Immediate (Before patient leaves clinic)",
                "clinical_summary": "Image quality is insufficient for reliable AI-assisted diabetic retinopathy screening.",
                "next_steps": [
                    "Re-capture fundus image following image quality guidance.",
                    "Ensure adequate room darkening and patient pupil positioning.",
                    "Verify lens cleanliness to remove dust artifacts."
                ]
            }

        if dr_res is None:
            return {
                "triage_state": "RECHECK_IMAGE",
                "referral_priority": "NO_PREDICTION",
                "urgency_level": "Pending Analysis",
                "action_code": "UNKNOWN",
                "recommended_timeline": "N/A",
                "clinical_summary": "No AI prediction available.",
                "next_steps": []
            }

        class_id = dr_res.get("predicted_class_id", 0)
        confidence = dr_res.get("confidence_score", 0.0)
        uncertainty = dr_res.get("uncertainty_index", 0.0)
        reliability = dr_res.get("reliability_status", "Reliable")
        is_uncertain = dr_res.get("is_uncertain", False)

        patient_info = patient_info or {}
        hba1c = float(patient_info.get("hba1c", 0.0)) if patient_info.get("hba1c") else 0.0
        duration_yrs = float(patient_info.get("diabetes_duration_years", 0.0)) if patient_info.get("diabetes_duration_years") else 0.0

        lesion_summary = lesion_res.get("lesion_summary", {}) if lesion_res else {}
        ex_count = lesion_summary.get("hard_exudates_count", 0)
        hem_count = lesion_summary.get("hemorrhages_count", 0) + lesion_summary.get("microaneurysms_count", 0)

        # Check for High Uncertainty State
        if is_uncertain or reliability == "Uncertain":
            return {
                "triage_state": "SPECIALIST_REVIEW_RECOMMENDED",
                "referral_priority": "HIGH_UNCERTAINTY",
                "urgency_level": "Uncertain AI Result — Professional Evaluation Recommended",
                "action_code": "UNCERTAIN_REFERRAL",
                "recommended_timeline": "Within 1 Month",
                "clinical_summary": f"AI result uncertain (Confidence: {confidence}%, Uncertainty Index: {uncertainty:.2f}). Professional ophthalmic evaluation is recommended.",
                "next_steps": [
                    "Schedule formal dilated ophthalmic examination with an eye care specialist.",
                    "Monitor blood glucose control and HbA1c levels."
                ]
            }

        # Severity-Specific Recommendations
        if class_id == 0:
            # NO APPARENT DR
            referral_priority = "ROUTINE_MONITORING"
            urgency_level = "No DR Detected — Continue Routine Screening"
            action_code = "ROUTINE"
            timeline = "Annual Rescreening (12 Months)"
            summary = "No apparent diabetic retinopathy detected by the AI screening model in the analyzed fundus image."
            steps = [
                "Continue appropriate routine diabetic eye screening according to clinical guidance (annual rescreening).",
                "Maintain optimal glycemic and blood pressure control."
            ]

        elif class_id == 1:
            # MILD NPDR
            referral_priority = "EARLY_FOLLOW_UP"
            urgency_level = "Mild DR Detected — Professional Follow-Up Recommended"
            action_code = "MILD_FOLLOW_UP"
            timeline = "Within 6 to 12 Months"
            summary = f"Mild diabetic retinal changes detected ({hem_count} isolated microvascular finding(s)). Professional follow-up recommended."
            steps = [
                "Schedule professional follow-up examination according to clinical guidance (6 to 12 months).",
                "Consult primary care physician regarding glycemic management (Target HbA1c < 7.0%)."
            ]

        elif class_id == 2:
            # MODERATE NPDR
            referral_priority = "OPHTHALMIC_EVALUATION"
            urgency_level = "Moderate Retinal Changes — Professional Eye Evaluation Recommended"
            action_code = "MODERATE_REFERRAL"
            timeline = "Within 3 to 6 Months"
            summary = f"Moderate non-proliferative retinal changes detected ({ex_count} hard exudate deposit(s), {hem_count} hemorrhage/microaneurysm finding(s)). Professional eye evaluation recommended."
            steps = [
                "Schedule formal dilated retinal examination by an optometrist or ophthalmologist.",
                "Evaluate for potential Diabetic Macular Edema (DME) symptoms."
            ]

        elif class_id == 3:
            # SEVERE NPDR
            referral_priority = "URGENT_REFERRAL"
            urgency_level = "Severe Retinal Changes — Prompt Ophthalmic Evaluation Recommended"
            action_code = "SEVERE_REFERRAL"
            timeline = "Within 1 to 4 Weeks"
            summary = f"Severe non-proliferative retinal changes detected ({hem_count} hemorrhages/microvascular abnormalities across affected quadrants). Prompt ophthalmic evaluation recommended."
            steps = [
                "Prompt ophthalmic evaluation recommended with a retina specialist.",
                "Assess need for optical coherence tomography (OCT) or anti-VEGF intervention."
            ]

        else:
            # PROLIFERATIVE DR (PDR)
            referral_priority = "IMMEDIATE_EMERGENCY_REFERRAL"
            urgency_level = "Proliferative DR Findings — Urgent Specialist Evaluation Recommended"
            action_code = "IMMEDIATE_REFERRAL"
            timeline = "Within 1 to 2 Weeks"
            summary = f"Findings concerning for proliferative diabetic retinopathy detected. Urgent professional ophthalmic evaluation recommended."
            steps = [
                "Urgent professional ophthalmic evaluation recommended with an ophthalmologist / retina specialist.",
                "High risk of vision-threatening complications; immediate specialist management required."
            ]

        # Clinical Risk Modulation Note
        risk_notes = []
        if hba1c >= 9.0:
            risk_notes.append(f"Elevated HbA1c ({hba1c}%) increases risk of DR progression.")
        if duration_yrs >= 15.0:
            risk_notes.append(f"Diabetes duration of {duration_yrs} years increases microvascular vulnerability.")

        if risk_notes:
            summary += " Clinical Context: " + " ".join(risk_notes)

        return {
            "triage_state": "SCREENING_RESULT",
            "referral_priority": referral_priority,
            "urgency_level": urgency_level,
            "action_code": action_code,
            "recommended_timeline": timeline,
            "clinical_summary": summary,
            "next_steps": steps,
            "clinical_risk_factors": risk_notes
        }
