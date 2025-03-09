import uuid
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file

def generate_donor_code():
    """Generate a unique donor code"""
    return f"DN{uuid.uuid4().hex[:8].upper()}"

def create_pdf_report(campaign, donors):
    """Create a PDF report for campaign donors"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Add campaign information
    elements.append(Paragraph(f"Campaign: {campaign.name}", styles['Heading1']))
    elements.append(Paragraph(f"Date: {campaign.start_date.strftime('%Y-%m-%d')} - {campaign.end_date.strftime('%Y-%m-%d')}", styles['Normal']))
    elements.append(Paragraph(f"Location: {campaign.location}", styles['Normal']))
    
    # Create donor table
    data = [['Donor Code', 'Name', 'Blood Type', 'Age', 'Gender', 'Eligible']]
    for donor in donors:
        data.append([
            donor.unique_code,
            donor.name,
            donor.blood_type,
            str(donor.age),
            donor.gender,
            'Yes' if donor.is_eligible else 'No'
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return send_file(
        buffer,
        download_name=f'campaign_{campaign.id}_report.pdf',
        mimetype='application/pdf'
    )
