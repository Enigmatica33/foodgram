from io import BytesIO

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def pdf_creating(request, objects):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
    p.setFont('DejaVuSans', 16)
    p.drawString(100, height - 50, 'Список покупок')
    y_position = height - 100
    p.setFont('DejaVuSans', 20)
    for ingredient in objects:
        text = f"-{ingredient['ingredient__name']}: {ingredient['amount']}"
        f"{ingredient['ingredient__measurement_unit']}"
        p.drawString(100, y_position, text.encode('utf-8').decode('utf-8'))
        y_position -= 30
        if y_position < 50:
            p.showPage()
            p.setFont('DejaVuSans', 12)
            y_position = height - 100
    p.save()
    buffer.seek(0)
    response = HttpResponse(
        buffer,
        content_type='application/pdf'
    )
    response['Content-Disposition'] = 'attachment; '
    f'filename="{request.user.username}_shopping_list.pdf"'
    return response
