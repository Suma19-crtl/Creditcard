from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def generate_report(path, summary):
    doc = SimpleDocTemplate(path)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Credit Card Fraud Detection Report</b>", styles["Title"]))
    story.append(Paragraph(f"Total Transactions: {summary['total']}", styles["BodyText"]))
    story.append(Paragraph(f"Fraud Transactions: {summary['fraud']}", styles["BodyText"]))
    story.append(Paragraph(f"Genuine Transactions: {summary['genuine']}", styles["BodyText"]))
    story.append(Paragraph(f"Fraud Percentage: {summary['fraud_percentage']}%", styles["BodyText"]))
    story.append(Paragraph(f"Risk Level: {summary['risk_level']}", styles["BodyText"]))

    doc.build(story)