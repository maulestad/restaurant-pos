import json
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Print Agent")

CONFIG_PATH = Path(__file__).parent / "config.json"
CONFIG = json.loads(CONFIG_PATH.read_text())

class TicketItem(BaseModel):
    name: str
    price: float

class Ticket(BaseModel):
    header: str
    items: list[TicketItem]
    total: float

def _print_dummy(ticket: Ticket):
    print("=" * CONFIG.get("width", 32))
    print(ticket.header)
    print("-" * CONFIG.get("width", 32))
    for i in ticket.items:
        print(f"{i.name:<20} ${i.price:>8.2f}")
    print("-" * CONFIG.get("width", 32))
    print(f"{'TOTAL':<20} ${ticket.total:>8.2f}")
    print("=" * CONFIG.get("width", 32))

def _print_real(ticket: Ticket):
    from escpos.printer import Usb, Network
    if CONFIG["type"] == "usb":
        printer = Usb(int(CONFIG["vendor_id"], 16), int(CONFIG["product_id"], 16))
    else:
        printer = Network(CONFIG["ip"], port=CONFIG["port"])
    printer.text(ticket.header + "\n")
    printer.text("-" * CONFIG.get("width", 32) + "\n")
    for i in ticket.items:
        printer.text(f"{i.name:<20} ${i.price:>8.2f}\n")
    printer.text("-" * CONFIG.get("width", 32) + "\n")
    printer.text(f"{'TOTAL':<20} ${ticket.total:>8.2f}\n\n")
    printer.cut()

@app.post("/print")
def print_ticket(ticket: Ticket):
    if CONFIG["type"] == "dummy":
        _print_dummy(ticket)
    else:
        _print_real(ticket)
    return {"status": "printed"}

@app.get("/health")
def health():
    return {"status": "ok", "mode": CONFIG["type"]}