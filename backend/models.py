"""
models.py — Beanie ODM document models for the SWM Platform.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from beanie import Document, Indexed
from pydantic import BaseModel, Field
import uuid


# ─── Enumerations ─────────────────────────────────────────────────────────────

class PropertyType(str, Enum):
    HOUSEHOLD = "Household"
    COMMERCIAL = "Commercial"


class WasteType(str, Enum):
    WET = "Wet"
    DRY = "Dry"
    SANITARY = "Sanitary"
    SPECIAL_CARE = "Special Care"


class NodeType(str, Enum):
    AUTO_TIPPER = "Auto-Tipper"
    DWCC = "DWCC"           # Dry Waste Collection Centre
    RECYCLER = "Recycler"
    COMPOSTING = "Composting"


class NodeStatus(str, Enum):
    VERIFIED = "Verified"
    CONTAMINATED = "Contaminated"
    PROCESSED = "Processed"
    IN_TRANSIT = "In Transit"


# ─── Embedded Sub-Document ────────────────────────────────────────────────────

class NodeEvent(BaseModel):
    """An immutable event record as waste moves through the supply chain."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    node_type: NodeType
    location: str
    weight_kg: float = Field(ge=0.0, description="Weight recorded at this node in kg")
    status: NodeStatus
    operator_id: Optional[str] = None
    notes: Optional[str] = None


# ─── Top-Level Documents ──────────────────────────────────────────────────────

class Property(Document):
    """Represents a registered household or commercial property."""
    property_id: Indexed(str, unique=True)        # e.g. "BLR-174-00042"
    ward_number: int
    ward_name: str
    address: str
    type: PropertyType = PropertyType.HOUSEHOLD
    green_credits_balance: float = 0.0
    segregation_streak_days: int = 0
    total_waste_diverted_kg: float = 0.0
    registered_on: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "properties"


class Batch(Document):
    """
    Represents a physical load of waste.
    Embeds the full NodeEvent lineage for immutable audit.
    """
    batch_id: Indexed(str, unique=True)
    property_id: str                              # FK → Property.property_id
    waste_type: WasteType
    initial_weight_kg: float = Field(ge=0.0)
    collected_on: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    events: List[NodeEvent] = []
    is_audit_passed: bool = False
    credits_minted: float = 0.0

    class Settings:
        name = "batches"


# ─── API Request / Response Payloads ─────────────────────────────────────────

class MintRequest(BaseModel):
    """Payload sent to POST /api/v1/ledger/mint"""
    property_id: str
    batch_id: str
    waste_type: WasteType
    weight_kg: float
    node_type: NodeType
    location: str
    operator_id: Optional[str] = None
    notes: Optional[str] = None


class MintResponse(BaseModel):
    batch_id: str
    audit_passed: bool
    credits_minted: float
    new_balance: float
    audit_reasoning: str
