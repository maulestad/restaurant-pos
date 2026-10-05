from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models.user import User
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.schemas.sale import SaleCreate, SaleOut, SaleItemOut
from app.security import get_current_user, require_role
from app.services.inventory import validate_stock, apply_stock

router = APIRouter(prefix="/api/sales", tags=["sales"])


def _sale_to_out(s: Sale) -> SaleOut:
    return SaleOut(
        id=s.id,
        user_id=s.user_id,
        total=s.total,
        status=s.status,
        table_number=s.table_number,
        created_at=s.created_at.isoformat(),
        items=[SaleItemOut(
            product_id=i.product_id,
            product_name=i.product_name,
            quantity=i.quantity,
            unit_price=i.unit_price,
            subtotal=i.subtotal,
        ) for i in s.items],
    )


@router.post("/", response_model=SaleOut)
def create_sale(
    payload: SaleCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="La venta no tiene items")

    validate_stock(session, [i.dict() for i in payload.items])

    sale = Sale(user_id=user.id, table_number=payload.table_number)
    session.add(sale)
    session.commit()
    session.refresh(sale)

    total = 0.0
    for item in payload.items:
        product = session.get(Product, item.product_id)
        if not product or not product.active:
            raise HTTPException(status_code=404, detail=f"Producto {item.product_id} no existe")
        subtotal = product.price * item.quantity
        session.add(SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            product_name=product.name,
            quantity=item.quantity,
            unit_price=product.price,
            subtotal=subtotal,
        ))
        total += subtotal

    sale.total = total
    session.add(sale)
    session.commit()
    session.refresh(sale)

    apply_stock(session, sale)
    session.commit()
    session.refresh(sale)

    return _sale_to_out(sale)


@router.get("/my", response_model=List[SaleOut])
def my_sales(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    sales = session.exec(
        select(Sale).where(Sale.user_id == user.id).order_by(Sale.id.desc())
    ).all()
    return [_sale_to_out(s) for s in sales]


@router.get("/all", response_model=List[SaleOut])
def all_sales(
    user: User = Depends(require_role("gerente", "sysadmin")),
    session: Session = Depends(get_session),
):
    sales = session.exec(select(Sale).order_by(Sale.id.desc())).all()
    return [_sale_to_out(s) for s in sales]


@router.get("/filtered", response_model=List[SaleOut])
def filtered_sales(
    user_id: Optional[int] = None,
    cash_session_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user: User = Depends(require_role("gerente", "sysadmin")),
    session: Session = Depends(get_session),
):
    q = select(Sale)
    if user_id:
        q = q.where(Sale.user_id == user_id)

    if cash_session_id:
        from app.models.cash import CashSession
        cs = session.get(CashSession, cash_session_id)
        if cs:
            q = q.where(Sale.user_id == cs.user_id)
            q = q.where(Sale.created_at >= cs.opened_at)
            if cs.closed_at:
                q = q.where(Sale.created_at <= cs.closed_at)

    if date_from:
        q = q.where(Sale.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        q = q.where(Sale.created_at <= datetime.fromisoformat(date_to + "T23:59:59"))

    sales = session.exec(q.order_by(Sale.id.desc())).all()
    return [_sale_to_out(s) for s in sales]


@router.get("/summary/by-user")
def summary_by_user(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user_id: Optional[int] = None,
    cash_session_id: Optional[int] = None,
    user: User = Depends(require_role("gerente", "sysadmin")),
    session: Session = Depends(get_session),
):
    q = select(Sale)
    if user_id:
        q = q.where(Sale.user_id == user_id)
    if cash_session_id:
        from app.models.cash import CashSession
        cs = session.get(CashSession, cash_session_id)
        if cs:
            q = q.where(Sale.user_id == cs.user_id)
            q = q.where(Sale.created_at >= cs.opened_at)
            if cs.closed_at:
                q = q.where(Sale.created_at <= cs.closed_at)
    if date_from:
        q = q.where(Sale.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        q = q.where(Sale.created_at <= datetime.fromisoformat(date_to + "T23:59:59"))

    sales = session.exec(q).all()

    by_user: dict[int, dict] = {}
    for s in sales:
        by_user.setdefault(s.user_id, {"user_id": s.user_id, "count": 0, "total": 0.0})
        by_user[s.user_id]["count"] += 1
        by_user[s.user_id]["total"] += s.total

    users = session.exec(select(User)).all()
    names = {u.id: u.full_name or u.username for u in users}

    result = []
    for uid, data in by_user.items():
        result.append({
            "user_id": uid,
            "user_name": names.get(uid, f"User #{uid}"),
            "count": data["count"],
            "total": round(data["total"], 2),
        })
    result.sort(key=lambda r: r["total"], reverse=True)
    return result


@router.get("/summary/daily")
def summary_daily(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    user_id: Optional[int] = None,
    cash_session_id: Optional[int] = None,
    user: User = Depends(require_role("gerente", "sysadmin")),
    session: Session = Depends(get_session),
):
    q = select(Sale)
    if user_id:
        q = q.where(Sale.user_id == user_id)
    if cash_session_id:
        from app.models.cash import CashSession
        cs = session.get(CashSession, cash_session_id)
        if cs:
            q = q.where(Sale.user_id == cs.user_id)
            q = q.where(Sale.created_at >= cs.opened_at)
            if cs.closed_at:
                q = q.where(Sale.created_at <= cs.closed_at)
    if date_from:
        q = q.where(Sale.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        q = q.where(Sale.created_at <= datetime.fromisoformat(date_to + "T23:59:59"))

    sales = session.exec(q).all()
    by_day: dict[str, dict] = {}
    for s in sales:
        day = s.created_at.strftime("%Y-%m-%d")
        by_day.setdefault(day, {"date": day, "count": 0, "total": 0.0})
        by_day[day]["count"] += 1
        by_day[day]["total"] += s.total

    result = [{"date": k, "count": v["count"], "total": round(v["total"], 2)}
              for k, v in sorted(by_day.items())]
    return result


@router.get("/{sale_id}", response_model=SaleOut)
def get_sale(
    sale_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise HTTPException(404, "Venta no encontrada")
    if user.role == "vendedor" and sale.user_id != user.id:
        raise HTTPException(403, "No autorizado")
    return _sale_to_out(sale)