import os
import base64
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image as PILImage

class PDFReportGenerator:
    """
    Real ReportLab Medical PDF Screening Report Generator for RetinaGuard AI.
    Generates downloadable, printable single-page PDF reports containing patient info,
    processed fundus images, Grad-CAM heatmap overlays, quality scores, and clinical recommendations.
    """
    @staticmethod
    def generate_pdf(screening_data: dict, output_path: str = None) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            output_path if output_path else buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        story = []
        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=2
        )
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=colors.HexColor('#2563EB'),
            spaceAfter=10
        )
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=11,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=8,
            spaceAfter=4
        )
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.HexColor('#334155'),
            leading=12
        )
        disclaimer_style = ParagraphStyle(
            'DisclaimerStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=7.5,
            textColor=colors.HexColor('#64748B'),
            leading=10
        )

        # 1. Header Banner
        screening_id = screening_data.get("screening_id", "RG-UNKNOWN")
        created_at = screening_data.get("created_at", "N/A")
        
        header_table_data = [
            [
                Paragraph("<b>RetinaGuard AI</b><br/><font size=8 color='#475569'>AI-Assisted Diabetic Retinopathy Screening System</font>", title_style),
                Paragraph(f"<b>Report ID:</b> {screening_id}<br/><b>Date:</b> {created_at}", ParagraphStyle('RightText', parent=normal_style, alignment=2))
            ]
        ]
        header_table = Table(header_table_data, colWidths=[340, 200])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 4))

        # Divider Line
        story.append(Table([['']], colWidths=[540], rowHeights=[1.5], style=[('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#CBD5E1'))]))
        story.append(Spacer(1, 8))

        # 2. Patient & Clinical Context Table
        story.append(Paragraph("PATIENT & CLINICAL DEMOGRAPHICS", section_heading))
        
        patient_id = screening_data.get("patient_id", "N/A")
        name = screening_data.get("patient_name", "N/A")
        age = screening_data.get("age", "N/A")
        sex = screening_data.get("sex", "N/A")
        hba1c = f"{screening_data.get('hba1c')}%" if screening_data.get('hba1c') else "Not Recorded"
        duration = f"{screening_data.get('diabetes_duration')} Years" if screening_data.get('diabetes_duration') else "Not Recorded"
        htn = "Yes" if screening_data.get("hypertension") else "No"

        pat_table_data = [
            [Paragraph(f"<b>Patient ID:</b> {patient_id}", normal_style), Paragraph(f"<b>Name:</b> {name}", normal_style), Paragraph(f"<b>Age / Sex:</b> {age} / {sex}", normal_style)],
            [Paragraph(f"<b>HbA1c (%):</b> {hba1c}", normal_style), Paragraph(f"<b>Diabetes Duration:</b> {duration}", normal_style), Paragraph(f"<b>Hypertension:</b> {htn}", normal_style)]
        ]
        pat_table = Table(pat_table_data, colWidths=[180, 180, 180])
        pat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(pat_table)
        story.append(Spacer(1, 8))

        # 3. Retinal Images View (Raw vs Grad-CAM Overlay)
        story.append(Paragraph("RETINAL IMAGE ANALYSIS & VISUAL EXPLAINABILITY", section_heading))
        
        orig_b64 = screening_data.get("original_image_b64")
        overlay_b64 = screening_data.get("overlay_image_b64")

        img_cells = []
        if orig_b64:
            try:
                header, data = orig_b64.split(",", 1) if "," in orig_b64 else ("", orig_b64)
                img_bytes = base64.b64decode(data)
                rl_img1 = RLImage(BytesIO(img_bytes), width=240, height=180)
                img_cells.append([rl_img1, Paragraph("<b>Original Retinal Fundus Photograph</b>", ParagraphStyle('ImgLabel', parent=normal_style, alignment=1))])
            except Exception:
                img_cells.append([Paragraph("Original Image Unavailable", normal_style), ""])
        else:
            img_cells.append([Paragraph("Original Image Unavailable", normal_style), ""])

        if overlay_b64:
            try:
                header, data = overlay_b64.split(",", 1) if "," in overlay_b64 else ("", overlay_b64)
                img_bytes = base64.b64decode(data)
                rl_img2 = RLImage(BytesIO(img_bytes), width=240, height=180)
                img_cells.append([rl_img2, Paragraph("<b>Grad-CAM Visual Attention Overlay</b>", ParagraphStyle('ImgLabel', parent=normal_style, alignment=1))])
            except Exception:
                img_cells.append([Paragraph("Overlay Unavailable", normal_style), ""])
        else:
            img_cells.append([Paragraph("Overlay Unavailable", normal_style), ""])

        if len(img_cells) == 2:
            img_table_data = [
                [img_cells[0][0], img_cells[1][0]],
                [img_cells[0][1], img_cells[1][1]]
            ]
            img_table = Table(img_table_data, colWidths=[270, 270])
            img_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(img_table)

        story.append(Spacer(1, 8))

        # 4. Image Quality & AI DR Screening Findings
        story.append(Paragraph("AI SCREENING & QUALITY ASSESSMENT RESULTS", section_heading))
        
        q_status = screening_data.get("quality_status", "PASS")
        q_score = screening_data.get("quality_score", 0.0)
        icdr = screening_data.get("icdr_grade", "N/A")
        pred_class = screening_data.get("predicted_class_name", "N/A")
        conf = f"{screening_data.get('confidence_score', 0.0)}%"
        uncertainty = screening_data.get("uncertainty_index", 0.0)

        res_table_data = [
            [Paragraph("<b>Image Quality Gate:</b>", normal_style), Paragraph(f"<font color='{'green' if q_status=='PASS' else 'red'}'><b>{q_status}</b></font> (Score: {q_score}/100)", normal_style)],
            [Paragraph("<b>Preliminary DR Grade:</b>", normal_style), Paragraph(f"<b>{icdr} - {pred_class}</b>", normal_style)],
            [Paragraph("<b>Model Confidence Score:</b>", normal_style), Paragraph(f"<b>{conf}</b>", normal_style)],
            [Paragraph("<b>Uncertainty Index:</b>", normal_style), Paragraph(f"{uncertainty} (Scale 0.0 to 1.0)", normal_style)]
        ]
        res_table = Table(res_table_data, colWidths=[180, 360])
        res_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(res_table)
        story.append(Spacer(1, 8))

        # 5. Clinical Referral Triage Recommendation
        story.append(Paragraph("CLINICAL REFERRAL TRIAGE & NEXT STEPS", section_heading))
        
        urgency = screening_data.get("urgency_level", "N/A")
        timeline = screening_data.get("recommended_timeline", "N/A")
        summary = screening_data.get("clinical_summary", "")

        triage_table_data = [
            [Paragraph(f"<b>Referral Urgency:</b> <font color='#0369A1'><b>{urgency}</b></font>", normal_style)],
            [Paragraph(f"<b>Recommended Action Timeline:</b> {timeline}", normal_style)],
            [Paragraph(f"<b>Clinical Summary Narrative:</b> {summary}", normal_style)]
        ]
        triage_table = Table(triage_table_data, colWidths=[540])
        triage_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EFF6FF')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#93C5FD')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(triage_table)
        story.append(Spacer(1, 10))

        # 6. Safety Disclaimer Box
        story.append(Paragraph(
            "<b>IMPORTANT CLINICAL SAFETY NOTICE:</b> RetinaGuard AI is an artificial-intelligence-assisted preliminary screening "
            "and decision-support software. It is NOT a definitive diagnostic device and does NOT replace evaluation by a qualified "
            "ophthalmologist or optometrist. All screening decisions must be confirmed clinically.",
            disclaimer_style
        ))

        doc.build(story)

        if output_path:
            return None
        return buffer.getvalue()
