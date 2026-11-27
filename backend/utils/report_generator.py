import io
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def generate_prediction_pdf(prediction: dict, patient_info: dict, image_path: str | Path | None = None) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#0F3D5E"),
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "ReportSub",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#4B5563"),
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#0F3D5E"),
        spaceBefore=12,
        spaceAfter=6,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#7C2D12"),
        backColor=colors.HexColor("#FFF7ED"),
        borderPadding=8,
    )

    story = []
    story.append(Paragraph("Retinal AI Screening Report", title_style))
    story.append(
        Paragraph(
            f"Prediction ID: <b>{prediction.get('prediction_id', 'N/A')}</b> &nbsp;|&nbsp; "
            f"Date: <b>{prediction.get('prediction_date', 'N/A')}</b> &nbsp;|&nbsp; "
            f"Model Version: <b>{prediction.get('model_version', 'N/A')}</b>",
            subtitle_style,
        )
    )

    story.append(Paragraph("Patient Information", section_style))
    patient_table = Table(
        [
            ["Full Name", patient_info.get("full_name", "N/A"), "Age / Gender", f"{patient_info.get('age', 'N/A')} / {patient_info.get('gender', 'N/A')}"],
            ["Email", patient_info.get("email", "N/A"), "Phone", patient_info.get("phone", "N/A")],
        ],
        colWidths=[1.1 * inch, 2.5 * inch, 1.1 * inch, 2.4 * inch],
    )
    patient_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F1F5F9")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ]
        )
    )
    story.append(patient_table)

    story.append(Paragraph("AI Classification Summary", section_style))
    confidence_pct = float(prediction.get("confidence_score", 0)) * 100
    summary_table = Table(
        [
            ["Predicted Category", prediction.get("predicted_class", "N/A")],
            ["Model Confidence Score", f"{confidence_pct:.2f}%"],
            ["Prediction Status", prediction.get("prediction_status", "Completed")],
        ],
        colWidths=[2.2 * inch, 4.9 * inch],
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E0F2FE")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BAE6FD")),
                ("PADDING", (0, 0), (-1, -1), 7),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(summary_table)

    story.append(Paragraph("Class Score Distribution", section_style))
    class_scores = prediction.get("class_scores", {})
    score_rows = [["Disease Category", "Model Score", "Percentage"]]
    for cls_name, score in class_scores.items():
        score_rows.append([cls_name, f"{float(score):.4f}", f"{float(score) * 100:.2f}%"])
    score_table = Table(score_rows, colWidths=[3.4 * inch, 1.8 * inch, 1.9 * inch])
    score_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F3D5E")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ]
        )
    )
    story.append(score_table)

    if image_path and Path(image_path).is_file():
        story.append(Paragraph("Uploaded Retinal Fundus Image", section_style))
        try:
            rl_img = RLImage(str(image_path), width=2.4 * inch, height=2.4 * inch, kind="proportional")
            story.append(rl_img)
        except Exception:
            story.append(Paragraph("Retinal image thumbnail could not be embedded.", styles["Normal"]))

    assessment = prediction.get("doctor_assessment")
    if assessment:
        story.append(Paragraph("Clinician Assessment", section_style))
        story.append(
            Paragraph(
                f"<b>Doctor:</b> {assessment.get('doctor_name', 'Attending Physician')}<br/>"
                f"<b>Clinical Impression:</b> {assessment.get('clinical_impression', 'N/A')}<br/>"
                f"<b>Notes:</b> {assessment.get('assessment_notes', '')}",
                styles["Normal"],
            )
        )

    story.append(Spacer(1, 16))
    story.append(
        Paragraph(
            "<b>Clinical Decision-Support Disclaimer:</b> This report is generated by an educational and "
            "clinical decision-support prototype. AI confidence scores are not confirmed disease probabilities "
            "and do not replace a comprehensive dilated eye examination or diagnosis by a qualified ophthalmologist.",
            disclaimer_style,
        )
    )

    doc.build(story)
    return buffer.getvalue()
