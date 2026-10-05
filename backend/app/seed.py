from sqlmodel import Session, select
from app.database import engine
from app.models.user import User
from app.models.product import Product
from app.models.feature import Feature
from app.models.setting import Setting
from app.models.branding import Branding
from app.security import hash_password
from app.config import settings


def seed():
    with Session(engine) as session:
        # Usuarios
        if not session.exec(select(User).where(User.username == settings.ADMIN_USER)).first():
            session.add(User(
                username=settings.ADMIN_USER,
                full_name="System Admin",
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                role="sysadmin",
            ))
        if not session.exec(select(User).where(User.username == "gerente")).first():
            session.add(User(
                username="gerente",
                full_name="Gerente Demo",
                password_hash=hash_password("gerente123"),
                role="gerente",
            ))
        if not session.exec(select(User).where(User.username == "vendedor")).first():
            session.add(User(
                username="vendedor",
                full_name="Vendedor Demo",
                password_hash=hash_password("vendedor123"),
                role="vendedor",
            ))

        # Productos demo
        if not session.exec(select(Product)).first():
            demo = [
                ("Hamburguesa Clásica", 5.50, "comida"),
                ("Pizza Margarita", 8.00, "comida"),
                ("Papas Fritas", 3.00, "comida"),
                ("Coca-Cola 500ml", 2.00, "bebida"),
                ("Agua Mineral", 1.50, "bebida"),
                ("Cerveza Artesanal", 4.50, "bebida"),
                ("Ensalada César", 6.00, "comida"),
                ("Postre del día", 3.50, "postre"),
            ]
            for name, price, cat in demo:
                session.add(Product(name=name, price=price, category=cat, stock=100, track_stock=False))

        # Features
        default_features = [
            ("inventory_enabled", False, "Módulo de inventario y stock"),
            ("inventory_alerts_enabled", False, "Alertas de stock bajo"),
            ("purchases_enabled", False, "Compras y entradas de mercadería"),
            ("recipes_enabled", False, "Recetas / descuento por insumos"),
            ("quality_checklist_enabled", False, "Checklist de calidad"),
            ("printer_config_enabled", True, "Configuración de impresoras"),
            ("tables_enabled", True, "Gestión de mesas"),
            ("cash_register_enabled", False, "Caja y arqueos"),
        ]
        for name, enabled, desc in default_features:
            if not session.exec(select(Feature).where(Feature.name == name)).first():
                session.add(Feature(name=name, enabled=enabled, description=desc))

        # Settings
        if not session.exec(select(Setting).where(Setting.key == "printer_mode")).first():
            session.add(Setting(
                key="printer_mode",
                value="pdf",
                description="Modo de impresión: 'pdf' o 'escpos_direct'.",
            ))
        if not session.exec(select(Setting).where(Setting.key == "print_agent_url")).first():
            session.add(Setting(
                key="print_agent_url",
                value="http://localhost:5000",
                description="URL del Print Agent local.",
            ))
        if not session.exec(select(Setting).where(Setting.key == "restaurant_name")).first():
            session.add(Setting(
                key="restaurant_name",
                value="Restaurante Demo",
                description="Nombre que aparece en el ticket.",
            ))

        # Branding inicial
        if not session.exec(select(Branding)).first():
            session.add(Branding(
                system_name="Restaurant POS",
                primary_color="#2563eb",
                logo_base64="",
            ))

        session.commit()
        print("✅ Seed completado")