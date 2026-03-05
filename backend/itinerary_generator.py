from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Frame, PageTemplate
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime
import os

def generate_itinerary_pdf(trip_data: dict, output_path: str = None):
    """
    Generate a beautiful, professional PDF itinerary using ReportLab
    
    trip_data structure:
    {
        "trip_name": "8 Days Sri Lanka Tour",
        "destination_country": "Sri Lanka",
        "start_date": "2024-03-15",
        "end_date": "2024-03-23",
        "days": [
            {
                "day": 1,
                "title": "Arrival in Colombo",
                "city": "Colombo",
                "activities": [
                    {
                        "time": "2:00 PM",
                        "description": "Arrive at airport",
                        "type": "activity"  # optional: activity, meal, hotel
                    }
                ],
                "meals": {  # optional
                    "breakfast": "Hotel breakfast",
                    "lunch": "Local restaurant",
                    "dinner": "Beachside dining"
                },
                "hotel": {
                    "name": "Hotel Name",
                    "description": "Description",
                    "rating": 5  # optional
                }
            }
        ]
    }
    """
    
    # Generate output path if not provided
    if not output_path:
        trip_name = trip_data['trip_name'].replace(' ', '_').lower()
        itineraries_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'itineraries')
        output_path = os.path.join(itineraries_dir, f"{trip_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create PDF document with custom page template
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for PDF elements
    elements = []
    
    # Define custom styles
    styles = getSampleStyleSheet()
    
    # Cover page title style
    cover_title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontSize=36,
        textColor=white,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        leading=42
    )
    
    cover_subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontSize=18,
        textColor=white,
        alignment=TA_CENTER,
        fontName='Helvetica',
        spaceAfter=8
    )
    
    cover_info_style = ParagraphStyle(
        'CoverInfo',
        parent=styles['Normal'],
        fontSize=14,
        textColor=white,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=20,
        textColor=HexColor('#2c3e50'),
        spaceAfter=16,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderColor=HexColor('#3498db'),
        borderPadding=8,
        leftIndent=0
    )
    
    day_number_style = ParagraphStyle(
        'DayNumber',
        parent=styles['Normal'],
        fontSize=24,
        textColor=white,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    day_title_style = ParagraphStyle(
        'DayTitle',
        parent=styles['Heading3'],
        fontSize=16,
        textColor=HexColor('#2c3e50'),
        spaceAfter=4,
        fontName='Helvetica-Bold',
        leading=20
    )
    
    day_subtitle_style = ParagraphStyle(
        'DaySubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=HexColor('#7f8c8d'),
        spaceAfter=12,
        fontName='Helvetica-Oblique'
    )
    
    activity_time_style = ParagraphStyle(
        'ActivityTime',
        parent=styles['Normal'],
        fontSize=11,
        textColor=HexColor('#3498db'),
        fontName='Helvetica-Bold',
        spaceAfter=2
    )
    
    activity_desc_style = ParagraphStyle(
        'ActivityDesc',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#34495e'),
        spaceAfter=8,
        leftIndent=0.3*inch,
        leading=14
    )
    
    meal_style = ParagraphStyle(
        'Meal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=HexColor('#16a085'),
        spaceAfter=4,
        leftIndent=0.3*inch
    )
    
    hotel_title_style = ParagraphStyle(
        'HotelTitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=HexColor('#e67e22'),
        fontName='Helvetica-Bold',
        spaceAfter=4,
        leftIndent=0.15*inch
    )
    
    hotel_desc_style = ParagraphStyle(
        'HotelDesc',
        parent=styles['Normal'],
        fontSize=9,
        textColor=HexColor('#7f8c8d'),
        spaceAfter=8,
        leftIndent=0.3*inch
    )
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#95a5a6'),
        alignment=TA_CENTER
    )
    
    # ====== COVER PAGE ======
    # Create gradient background effect using table
    cover_spacer_before = Spacer(1, 1.5*inch)
    elements.append(cover_spacer_before)
    
    # Cover page content
    cover_content = [
        [Paragraph(trip_data['trip_name'], cover_title_style)],
        [Paragraph(f"Explore {trip_data['destination_country']}", cover_subtitle_style)],
        [Spacer(1, 0.5*inch)],
        [Paragraph(f"{trip_data['start_date']} to {trip_data['end_date']}", cover_info_style)],
    ]
    
    cover_table = Table(cover_content, colWidths=[6*inch])
    cover_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#3498db')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 0.5*inch),
        ('TOPPADDING', (0, 0), (-1, 0), 0.8*inch),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 0.8*inch),
        ('ROUNDEDCORNERS', [10, 10, 10, 10]),
    ]))
    elements.append(cover_table)
    
    # Trip summary box
    elements.append(Spacer(1, 0.5*inch))
    
    total_days = len(trip_data['days'])
    num_cities = len(set(day['city'] for day in trip_data['days']))
    
    summary_data = [
        [
            Paragraph("📅", styles['Normal']),
            Paragraph(f"<b>{total_days} Days</b><br/><font size=8>Duration</font>", styles['Normal']),
            Paragraph("🌍", styles['Normal']),
            Paragraph(f"<b>{num_cities} Cities</b><br/><font size=8>Destinations</font>", styles['Normal']),
            Paragraph("✈️", styles['Normal']),
            Paragraph(f"<b>{trip_data['destination_country']}</b><br/><font size=8>Country</font>", styles['Normal'])
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[0.4*inch, 1.6*inch, 0.4*inch, 1.6*inch, 0.4*inch, 1.6*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#ecf0f1')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 0.2*inch),
        ('FONTSIZE', (0, 0), (-1, -1), 18),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    elements.append(summary_table)
    
    elements.append(PageBreak())
    
    # ====== ITINERARY SECTION ======
    elements.append(Paragraph("Your Itinerary", section_heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Add a separator line
    line_data = [['']]
    line_table = Table(line_data, colWidths=[6.5*inch], rowHeights=[0.05*inch])
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#3498db')),
        ('ROUNDEDCORNERS', [2, 2, 2, 2]),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Itinerary days
    for idx, day_info in enumerate(trip_data['days']):
        # Day header with colored background
        day_header_data = [[
            Paragraph(str(day_info['day']), day_number_style),
            Paragraph(f"<b>{day_info['title']}</b><br/><font size=10>{day_info['city']}</font>", day_title_style)
        ]]
        
        day_header_table = Table(day_header_data, colWidths=[0.7*inch, 5.8*inch])
        day_header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), HexColor('#3498db')),
            ('BACKGROUND', (1, 0), (1, 0), HexColor('#ecf0f1')),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 0.15*inch),
            ('ROUNDEDCORNERS', [8, 8, 8, 8]),
        ]))
        elements.append(day_header_table)
        elements.append(Spacer(1, 0.15*inch))
        
        # Activities
        if day_info.get('activities'):
            elements.append(Paragraph("🗓 <b>Schedule</b>", activity_time_style))
            for activity in day_info['activities']:
                time_text = f"<b>{activity['time']}</b>" if activity.get('time') else ""
                desc_text = activity.get('description', '')
                activity_full = f"{time_text} {desc_text}" if time_text else desc_text
                elements.append(Paragraph(f"• {activity_full}", activity_desc_style))
            elements.append(Spacer(1, 0.1*inch))
        
        # Meals (if provided)
        meals = day_info.get('meals', {})
        if meals:
            meal_texts = []
            if meals.get('breakfast'):
                meal_texts.append(f"🍳 <b>Breakfast:</b> {meals['breakfast']}")
            if meals.get('lunch'):
                meal_texts.append(f"🍽 <b>Lunch:</b> {meals['lunch']}")
            if meals.get('dinner'):
                meal_texts.append(f"🍷 <b>Dinner:</b> {meals['dinner']}")
            
            if meal_texts:
                for meal_text in meal_texts:
                    elements.append(Paragraph(meal_text, meal_style))
                elements.append(Spacer(1, 0.1*inch))
        
        # Hotel info
        if day_info.get('hotel'):
            hotel = day_info['hotel']
            rating_stars = "⭐" * hotel.get('rating', 3) if hotel.get('rating') else ""
            hotel_title = f"🏨 <b>{hotel['name']}</b> {rating_stars}"
            elements.append(Paragraph(hotel_title, hotel_title_style))
            if hotel.get('description'):
                elements.append(Paragraph(hotel['description'], hotel_desc_style))
        
        # Add spacing between days
        elements.append(Spacer(1, 0.25*inch))
        
        # Page break after every 2 days (except last)
        if ((idx + 1) % 2 == 0) and (idx + 1) < total_days:
            elements.append(PageBreak())
    
    # ====== FOOTER ======
    elements.append(Spacer(1, 0.4*inch))
    footer_line = Table([['']], colWidths=[6.5*inch], rowHeights=[0.02*inch])
    footer_line.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#bdc3c7')),
    ]))
    elements.append(footer_line)
    elements.append(Spacer(1, 0.15*inch))
    
    elements.append(Paragraph(
        f"<i>Your personalized travel itinerary · Generated {datetime.now().strftime('%B %d, %Y')}</i>",
        footer_style
    ))
    elements.append(Paragraph(
        "<i>Travel Planner AI · Creating memorable journeys</i>",
        footer_style
    ))
    
    # Build PDF
    doc.build(elements)
    
    return output_path
