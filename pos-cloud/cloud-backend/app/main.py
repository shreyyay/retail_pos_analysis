import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import sync, dashboard, insight, udhar, followup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s – %(message)s")

app = FastAPI(title="Retail POS Cloud API", version="1.0.0")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(sync.router,      prefix="/api/sync",      tags=["sync"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(insight.router,   prefix="/api/insight",   tags=["insight"])
app.include_router(udhar.router,     prefix="/api/udhar",     tags=["udhar"])
app.include_router(followup.router,  prefix="/api/followup",  tags=["followup"])


@app.get("/health")
def health():
    return {"status": "ok"}
