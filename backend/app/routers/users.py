from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.database import get_session
from app.models.user import User
from app.security import require_role, hash_password

router = APIRouter(prefix="/api/users", tags=["users"])


class UserIn(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    full_name: str = Field(min_length=2, max_length=100)
    password: Optional[str] = None
    role: str = "vendedor"
    active: bool = True


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    active: bool


ALLOWED_BY_CREATOR = {
    "sysadmin": {"sysadmin", "gerente", "vendedor"},
    "gerente": {"vendedor"},
}


def _check_role_permission(creator: User, target_role: str):
    allowed = ALLOWED_BY_CREATOR.get(creator.role, set())
    if target_role not in allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Tu rol '{creator.role}' no puede gestionar el rol '{target_role}'",
        )


@router.get("/", response_model=List[UserOut])
def list_users(
    role: Optional[str] = None,
    session: Session = Depends(get_session),
    user: User = Depends(require_role("gerente", "sysadmin")),
):
    q = select(User)
    if user.role == "gerente":
        q = q.where(User.role == "vendedor")
    if role:
        q = q.where(User.role == role)
    users = session.exec(q.order_by(User.full_name)).all()
    return [UserOut(**u.dict()) for u in users]


@router.post("/", response_model=UserOut)
def create_user(
    payload: UserIn,
    session: Session = Depends(get_session),
    creator: User = Depends(require_role("gerente", "sysadmin")),
):
    _check_role_permission(creator, payload.role)

    if session.exec(select(User).where(User.username == payload.username)).first():
        raise HTTPException(400, "Ese nombre de usuario ya existe")

    if not payload.password or len(payload.password) < 4:
        raise HTTPException(400, "La contraseña debe tener al menos 4 caracteres")

    new_user = User(
        username=payload.username,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=payload.role,
        active=payload.active,
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return UserOut(**new_user.dict())


@router.put("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserIn,
    session: Session = Depends(get_session),
    creator: User = Depends(require_role("gerente", "sysadmin")),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(404, "Usuario no encontrado")

    _check_role_permission(creator, target.role)
    _check_role_permission(creator, payload.role)

    if creator.id == target.id and payload.role != creator.role:
        raise HTTPException(403, "No puedes cambiar tu propio rol")

    target.username = payload.username
    target.full_name = payload.full_name
    target.role = payload.role
    target.active = payload.active
    if payload.password:
        if len(payload.password) < 4:
            raise HTTPException(400, "La contraseña debe tener al menos 4 caracteres")
        target.password_hash = hash_password(payload.password)

    session.add(target)
    session.commit()
    session.refresh(target)
    return UserOut(**target.dict())


@router.delete("/{user_id}")
def deactivate_user(
    user_id: int,
    session: Session = Depends(get_session),
    creator: User = Depends(require_role("gerente", "sysadmin")),
):
    target = session.get(User, user_id)
    if not target:
        raise HTTPException(404, "Usuario no encontrado")
    if creator.id == target.id:
        raise HTTPException(400, "No puedes desactivarte a ti mismo")

    _check_role_permission(creator, target.role)

    target.active = False
    session.add(target)
    session.commit()
    return {"ok": True, "id": user_id}