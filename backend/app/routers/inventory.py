from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models.product import Product
from app.models.user import User
from app.security import require_role
from app.services.inventory import inventory_enabled, low_stock_products

router = APIRouter(prefix="/api/inventory", tags=["inventory"])

@router.get("/status")
def status(session: Session = Depends(get_session)):
    return {"enabled": inventory_enabled(session)}

@router.get("/low-stock", response_model=List[Product])
def low_stock(
    session: Session = Depends(get_session),
    user: User = Depends(require_role("gerente", "sysadmin")),
):
    return low_stock_products(session)

@router.post("/products/{product_id}/stock")
def adjust_stock(
    product_id: int,
    quantity: float,
    reason: str = "manual",
    session: Session = Depends(get_session),
    user: User = Depends(require_role("gerente", "sysadmin")),
):
    if not inventory_enabled(session):
        raise HTTPException(400, "El módulo de inventario está desactivado")
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Producto no encontrado")
    product.stock += quantity
    session.add(product)
    session.commit()
    session.refresh(product)
    return {"product": product.name, "new_stock": product.stock, "reason": reason}