"""
main.py — FastAPI application entry point.
"""

import os
from contextlib import asynccontextmanager

from beanie import init_beanie
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from models import Batch, Property
from routes import router

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "swm_platform")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise Beanie ODM on startup; close connection on shutdown."""
    client = AsyncIOMotorClient(MONGO_URI)
    await init_beanie(
        database=client[MONGO_DB],
        document_models=[Property, Batch],
    )
    print(f"✅  Connected to MongoDB at {MONGO_URI}/{MONGO_DB}")
    yield
    client.close()
    print("🛑  MongoDB connection closed.")


app = FastAPI(
    title="SWM Transparency & Incentive Platform",
    description=(
        "Bengaluru Solid Waste Management — 4-stream tracking, "
        "mass-balance lineage, and AI-audited Green Credits."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS (allow Angular dev server + localhost) ──────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://frontend:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "swm-backend"}
