from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models.branding import Branding
from app.models.user import User
from app.security import require_role

router = APIRouter(prefix="/api/branding", tags=["branding"])


class BrandingIn(BaseModel):
    system_name: str = "Restaurant POS"
    logo_base64: str = ""
    primary_color: str = "#2563eb"


def _get_or_create(session: Session) -> Branding:
    b = session.exec(select(Branding)).first()
    if not b:
        b = Branding()
        session.add(b)
        session.commit()
        session.refresh(b)
    return b


@router.get("/")
def get_branding(session: Session = Depends(get_session)):
    b = _get_or_create(session)
    return b


@router.put("/")
def update_branding(
    payload: BrandingIn,
    session: Session = Depends(get_session),
    user: User = Depends(require_role("sysadmin")),
):
    b = _get_or_create(session)
    b.system_name = payload.system_name
    b.logo_base64 = payload.logo_base64
    b.primary_color = payload.primary_color
    b.updated_at = datetime.utcnow().isoformat()
    session.add(b)
    session.commit()
    session.refresh(b)
    return b