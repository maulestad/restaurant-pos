from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlmodel import Session

from app.database import get_session
from app.models.sale import Sale
from app.models.user import User
from app.security import get_current_user
from app.services.printing import get_print_mode
from app.services.pdf_ticket import build_ticket_pdf

router = APIRouter(prefix="/api/printing", tags=["printing"])

@router.get("/mode")
def print_mode(session: Session = Depends(get_session)):
    return {"mode": get_print_mode(session)}

@router.get("/ticket/{sale_id}.pdf")
def ticket_pdf(
    sale_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise HTTPException(404, "Venta no encontrada")
    # Vendedor solo puede descargar SUS tickets
    if user.role == "vendedor" and sale.user_id != user.id:
        raise HTTPException(403, "No autorizado")

    pdf_bytes = build_ticket_pdf(sale)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="ticket-{sale.id}.pdf"'},
    )