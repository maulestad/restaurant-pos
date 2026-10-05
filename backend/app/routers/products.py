from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models.product import Product
from app.security import require_role, get_current_user

router = APIRouter(prefix="/api/products", tags=["products"])


class ProductIn(BaseModel):
    name: str
    price: float
    category: str = "general"
    active: bool = True
    track_stock: bool = False
    stock: float = 0.0
    min_stock: float = 0.0
    unit: str = "unidad"


@router.get("/", response_model=List[Product])
def list_products(
    include_inactive: bool = False,
    session: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    q = select(Product)
    if not include_inactive:
        q = q.where(Product.active == True)
    return session.exec(q.order_by(Product.name)).all()


@router.post("/", response_model=Product)
def create_product(
    payload: ProductIn,
    session: Session = Depends(get_session),
    user=Depends(require_role("gerente", "sysadmin")),
):
    product = Product(**payload.dict())
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    payload: ProductIn,
    session: Session = Depends(get_session),
    user=Depends(require_role("gerente", "sysadmin")),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Producto no encontrado")
    for k, v in payload.dict().items():
        setattr(product, k, v)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
    user=Depends(require_role("gerente", "sysadmin")),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Producto no encontrado")
    product.active = False
    session.add(product)
    session.commit()
    return {"ok": True, "id": product_id}