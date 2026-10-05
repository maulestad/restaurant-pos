from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.seed import seed
from app.routers import (
    auth, sales, products, inventory,
    printing, admin, cash, users, branding,
)

app = FastAPI(title="Restaurant POS API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    seed()


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(sales.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(printing.router)
app.include_router(admin.router)
app.include_router(cash.router)
app.include_router(users.router)
app.include_router(branding.router)