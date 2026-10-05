from typing import List
from sqlmodel import Session, select
from fastapi import HTTPException

from app.models.product import Product
from app.models.sale import Sale
from app.models.feature import Feature

def inventory_enabled(session: Session) -> bool:
    f = session.exec(select(Feature).where(Feature.name == "inventory_enabled")).first()
    return bool(f and f.enabled)

def validate_stock(session: Session, items: List[dict]) -> None:
    if not inventory_enabled(session):
        return
    for it in items:
        product = session.get(Product, it["product_id"])
        if not product or not product.track_stock:
            continue
        if product.stock < it["quantity"]:
            raise HTTPException(
                status_code=409,
                detail=f"Stock insuficiente para {product.name}: "
                       f"disponible {product.stock}, solicitado {it['quantity']}",
            )

def apply_stock(session: Session, sale: Sale) -> None:
    enabled = inventory_enabled(session)
    for item in sale.items:
        product = session.get(Product, item.product_id)
        if not product:
            continue
        item.stock_before = product.stock
        if enabled and product.track_stock:
            product.stock -= item.quantity
            item.stock_after = product.stock
            item.stock_applied = True
            session.add(product)
        else:
            item.stock_after = product.stock
            item.stock_applied = False
        session.add(item)
    sale.stock_applied = enabled
    session.add(sale)

def low_stock_products(session: Session) -> List[Product]:
    if not inventory_enabled(session):
        return []
    products = session.exec(select(Product).where(Product.track_stock == True)).all()
    return [p for p in products if p.stock <= p.min_stock]