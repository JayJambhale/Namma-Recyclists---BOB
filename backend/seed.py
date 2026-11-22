"""
seed.py — Populates MongoDB with realistic Bengaluru SWM demo data.
Run once at container startup (idempotent — skips if data already exists).
"""

import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from models import (
    Batch,
    NodeEvent,
    NodeStatus,
    NodeType,
    Property,
    PropertyType,
    WasteType,
)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "swm_platform")


# ─── Seed Data ────────────────────────────────────────────────────────────────

PROPERTIES_SEED = [
    {
        "property_id": "BLR-174-00001",
        "ward_number": 174,
        "ward_name": "HSR Layout",
        "address": "42, 7th Cross, Sector 2, HSR Layout, Bengaluru - 560102",
        "type": PropertyType.HOUSEHOLD,
        "green_credits_balance": 128.5,
        "segregation_streak_days": 14,
        "total_waste_diverted_kg": 85.3,
    },
    {
        "property_id": "BLR-150-00007",
        "ward_number": 150,
        "ward_name": "Bellandur",
        "address": "15, Kariyammana Agrahara, Bellandur, Bengaluru - 560103",
        "type": PropertyType.HOUSEHOLD,
        "green_credits_balance": 75.0,
        "segregation_streak_days": 7,
        "total_waste_diverted_kg": 50.1,
    },
    {
        "property_id": "BLR-168-00023",
        "ward_number": 168,
        "ward_name": "Koramangala",
        "address": "88, 80 Feet Road, 6th Block, Koramangala, Bengaluru - 560095",
        "type": PropertyType.COMMERCIAL,
        "green_credits_balance": 320.0,
        "segregation_streak_days": 30,
        "total_waste_diverted_kg": 410.7,
    },
    {
        "property_id": "BLR-152-00011",
        "ward_number": 152,
        "ward_name": "Marathahalli",
        "address": "3A, Outer Ring Road, Marathahalli, Bengaluru - 560037",
        "type": PropertyType.HOUSEHOLD,
        "green_credits_balance": 42.0,
        "segregation_streak_days": 3,
        "total_waste_diverted_kg": 28.9,
    },
    {
        "property_id": "BLR-175-00099",
        "ward_number": 175,
        "ward_name": "Agara",
        "address": "21, Lake View Road, Agara, Bengaluru - 560102",
        "type": PropertyType.HOUSEHOLD,
        "green_credits_balance": 0.0,
        "segregation_streak_days": 0,
        "total_waste_diverted_kg": 5.0,
    },
]


def _make_events(base_time: datetime, waste_type: WasteType, weight_kg: float):
    """Generate a realistic 4-step lineage for a batch."""
    events = []

    # Step 1 — Pickup
    events.append(NodeEvent(
        timestamp=base_time,
        node_type=NodeType.AUTO_TIPPER,
        location="Household Gate",
        weight_kg=weight_kg,
        status=NodeStatus.VERIFIED,
        operator_id="DRV-BLR-0042",
        notes="Segregated correctly. Proceeding to DWCC.",
    ))

    # Step 2 — In Transit
    events.append(NodeEvent(
        timestamp=base_time + timedelta(minutes=25),
        node_type=NodeType.AUTO_TIPPER,
        location="HSR Layout Main Road",
        weight_kg=weight_kg,
        status=NodeStatus.IN_TRANSIT,
        operator_id="DRV-BLR-0042",
    ))

    # Step 3 — DWCC Arrival
    dwcc_weight = round(weight_kg * 0.97, 2)  # ~3% transit loss
    events.append(NodeEvent(
        timestamp=base_time + timedelta(hours=1, minutes=10),
        node_type=NodeType.DWCC,
        location="DWCC Ward 174, HSR Layout",
        weight_kg=dwcc_weight,
        status=NodeStatus.VERIFIED,
        operator_id="DWCC-OP-0017",
        notes=f"Arrived at DWCC. Weight variance: {round(weight_kg - dwcc_weight, 2)} kg.",
    ))

    # Step 4 — End destination
    final_node = NodeType.RECYCLER if waste_type == WasteType.DRY else NodeType.COMPOSTING
    final_location = (
        "Recycle-X Facility, Electronic City"
        if waste_type == WasteType.DRY
        else "Compost Hub, Yelahanka"
    )
    events.append(NodeEvent(
        timestamp=base_time + timedelta(hours=5),
        node_type=final_node,
        location=final_location,
        weight_kg=round(dwcc_weight * 0.95, 2),
        status=NodeStatus.PROCESSED,
        operator_id="RCY-OP-0003",
        notes="Batch fully processed. Mass balance closed.",
    ))

    return events


BATCHES_SEED = []
_now = datetime.now(timezone.utc)

for i, prop_data in enumerate(PROPERTIES_SEED):
    for j, (waste_type, weight) in enumerate([
        (WasteType.DRY, 12.5),
        (WasteType.WET, 8.0),
        (WasteType.SANITARY, 1.2),
    ]):
        batch_time = _now - timedelta(days=j * 2 + i)
        BATCHES_SEED.append({
            "batch_id": str(uuid.uuid4()),
            "property_id": prop_data["property_id"],
            "waste_type": waste_type,
            "initial_weight_kg": weight,
            "collected_on": batch_time,
            "events": _make_events(batch_time, waste_type, weight),
            "is_audit_passed": True,
            "credits_minted": round(weight * 2, 1),
        })


# ─── Main Seed Runner ─────────────────────────────────────────────────────────

async def seed():
    client = AsyncIOMotorClient(MONGO_URI)
    await init_beanie(database=client[MONGO_DB], document_models=[Property, Batch])

    # Idempotent: skip if data already exists
    if await Property.find_one():
        print("✅  Seed data already present — skipping.")
        return

    print("🌱  Seeding SWM platform with Bengaluru demo data …")

    for prop_data in PROPERTIES_SEED:
        prop = Property(**prop_data)
        await prop.insert()

    for batch_data in BATCHES_SEED:
        batch = Batch(**batch_data)
        await batch.insert()

    print(f"✅  Seeded {len(PROPERTIES_SEED)} properties and {len(BATCHES_SEED)} batches.")


if __name__ == "__main__":
    asyncio.run(seed())
