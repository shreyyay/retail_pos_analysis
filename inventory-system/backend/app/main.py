import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import stock_in, stock_out, dashboard, sales, udhar, followup

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.SQLITE_DB_PATH), exist_ok=True)

app = FastAPI(
    title="Inventory Management System",
    description="ERPNext Integration with OCR + AI Invoice Processing",
    version="1.0.0",
)

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


app.include_router(stock_in.router, prefix="/api/stock-in", tags=["Stock In"])
app.include_router(stock_out.router, prefix="/api/stock-out", tags=["Stock Out"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])
app.include_router(udhar.router, prefix="/api/udhar", tags=["Udhar"])
app.include_router(followup.router, prefix="/api/followup", tags=["Follow-up"])


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Inventory Management System"}
