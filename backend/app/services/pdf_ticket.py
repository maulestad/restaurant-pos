from io import BytesIO
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas

TICKET_WIDTH = 80 * mm   # ancho típico de térmica 80mm
TICKET_MARGIN = 5 * mm

def build_ticket_pdf(sale, restaurant_name: str = "Restaurante Demo") -> bytes:
    """
    Genera un PDF tamaño ticket 80mm.
    `sale` debe tener: id, table_number, created_at, total, items[].
    Cada item: product_name, quantity, unit_price, subtotal.
    """
    # Alto aproximado: cabecera + items + total. Ajustable.
    line_height = 5 * mm
    items = getattr(sale, "items", []) or []
    height = 60 * mm + line_height * max(len(items), 1)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(TICKET_WIDTH, height))
    width = TICKET_WIDTH
    y = height - 10 * mm

    def center(text, size=10, bold=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawCentredString(width / 2, y, text)
        y -= line_height

    def left_right(left, right, size=9):
        nonlocal y
        c.setFont("Helvetica", size)
        c.drawString(TICKET_MARGIN, y, left)
        c.drawRightString(width - TICKET_MARGIN, y, right)
        y -= line_height

    def line():
        nonlocal y
        c.setDash(1, 2)
        c.line(TICKET_MARGIN, y, width - TICKET_MARGIN, y)
        c.setDash()
        y -= line_height * 0.6

    # Cabecera
    center(restaurant_name, size=12, bold=True)
    center(f"Ticket #{sale.id}", size=9)
    center(sale.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(sale.created_at, "strftime") else str(sale.created_at), size=8)
    if getattr(sale, "table_number", None):
        center(f"Mesa: {sale.table_number}", size=9)
    line()

    # Items
    for it in items:
        left_right(f"{it.quantity} x {it.product_name}", f"${it.subtotal:.2f}", size=9)
    line()

    # Total
    c.setFont("Helvetica-Bold", 11)
    c.drawString(TICKET_MARGIN, y, "TOTAL")
    c.drawRightString(width - TICKET_MARGIN, y, f"${sale.total:.2f}")
    y -= line_height * 1.5

    center("¡Gracias por su visita!", size=9)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()