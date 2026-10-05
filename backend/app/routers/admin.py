from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models.feature import Feature
from app.models.setting import Setting
from app.models.user import User
from app.security import require_role
from app.services.printing import set_setting

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/features", response_model=List[Feature])
def list_features(session: Session = Depends(get_session), user: User = Depends(require_role("sysadmin"))):
    return session.exec(select(Feature)).all()

@router.post("/features/{name}/toggle", response_model=Feature)
def toggle_feature(name: str, session: Session = Depends(get_session), user: User = Depends(require_role("sysadmin"))):
    feature = session.exec(select(Feature).where(Feature.name == name)).first()
    if not feature:
        raise HTTPException(404, "Feature no existe")
    feature.enabled = not feature.enabled
    session.add(feature)
    session.commit()
    session.refresh(feature)
    return feature

@router.get("/settings", response_model=List[Setting])
def list_settings(session: Session = Depends(get_session), user: User = Depends(require_role("sysadmin"))):
    return session.exec(select(Setting)).all()

@router.post("/settings/{key}")
def update_setting(
    key: str,
    value: str,
    description: str = "",
    session: Session = Depends(get_session),
    user: User = Depends(require_role("sysadmin")),
):
    row = set_setting(session, key, value, description)
    return row

@router.get("/users", response_model=List[User])
def list_users(session: Session = Depends(get_session), user: User = Depends(require_role("sysadmin"))):
    return session.exec(select(User)).all()