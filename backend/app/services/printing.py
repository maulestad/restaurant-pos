from sqlmodel import Session, select
from app.models.setting import Setting
from app.models.feature import Feature

DEFAULT_PRINT_MODE = "pdf"   # "pdf" | "escpos_direct"

def get_setting(session: Session, key: str, default: str = "") -> str:
    row = session.exec(select(Setting).where(Setting.key == key)).first()
    return row.value if row else default

def set_setting(session: Session, key: str, value: str, description: str = "") -> Setting:
    row = session.exec(select(Setting).where(Setting.key == key)).first()
    if row:
        row.value = value
    else:
        row = Setting(key=key, value=value, description=description)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row

def get_print_mode(session: Session) -> str:
    """
    Devuelve el modo de impresión:
    - "pdf": el POS descarga un PDF del ticket (por defecto).
    - "escpos_direct": el POS manda el ticket al Print Agent local.
    """
    return get_setting(session, "printer_mode", DEFAULT_PRINT_MODE)