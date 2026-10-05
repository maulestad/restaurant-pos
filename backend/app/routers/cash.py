from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models.cash import CashSession
from app.models.sale import Sale
from app.models.user import User
from app.security import get_current_user, require_role

router = APIRouter(prefix="/api/cash", tags=["cash"])


class OpenCashIn(BaseModel):
    opening_amount: float
    notes: str = ""


class CloseCashIn(BaseModel):
    closing_amount: float
    notes: str = ""


def _get_open_session(session: Session, user_id: int) -> Optional[CashSession]:
    return session.exec(
        select(CashSession)
        .where(CashSession.user_id == user_id)
        .where(CashSession.status == "open")
        .order_by(CashSession.id.desc())
    ).first()


@router.get("/current")
def current_cash(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    cs = _get_open_session(session, user.id)
    if not cs:
        return {"open": False}

    sales = session.exec(
        select(Sale)
        .where(Sale.user_id == user.id)
        .where(Sale.created_at >= cs.opened_at)
    ).all()

    total_sales = sum(s.total for s in sales)
    return {
        "open": True,
        "session": cs,
        "total_sales": total_sales,
        "sales_count": len(sales),
        "expected_amount": cs.opening_amount + total_sales,
    }


@router.post("/open")
def open_cash(
    payload: OpenCashIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if _get_open_session(session, user.id):
        raise HTTPException(400, "Ya tienes una caja abierta")
    cs = CashSession(
        user_id=user.id,
        opening_amount=payload.opening_amount,
        notes=payload.notes,
    )
    session.add(cs)
    session.commit()
    session.refresh(cs)
    return cs


@router.post("/close")
def close_cash(
    payload: CloseCashIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    cs = _get_open_session(session, user.id)
    if not cs:
        raise HTTPException(400, "No tienes una caja abierta")

    sales = session.exec(
        select(Sale)
        .where(Sale.user_id == user.id)
        .where(Sale.created_at >= cs.opened_at)
    ).all()
    total_sales = sum(s.total for s in sales)
    expected = cs.opening_amount + total_sales

    cs.closed_at = datetime.utcnow()
    cs.closing_amount = payload.closing_amount
    cs.expected_amount = expected
    cs.difference = payload.closing_amount - expected
    cs.status = "closed"
    if payload.notes:
        cs.notes = (cs.notes + "\n" + payload.notes).strip()

    session.add(cs)
    session.commit()
    session.refresh(cs)
    return cs


@router.get("/history", response_model=List[CashSession])
def cash_history(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return session.exec(
        select(CashSession)
        .where(CashSession.user_id == user.id)
        .order_by(CashSession.id.desc())
    ).all()


@router.get("/all", response_model=List[CashSession])
def all_cash(
    user: User = Depends(require_role("gerente", "sysadmin")),
    session: Session = Depends(get_session),
):
    return session.exec(select(CashSession).order_by(CashSession.id.desc())).all()