# Bengaluru SWM Transparency & Incentive Platform

A fully functional local demo of a 4-stream waste segregation tracking system with AI-audited Green Credits.

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Angular 17 · Standalone Components · Signals · Tailwind CSS |
| Backend | Python 3.11 · FastAPI · Beanie (Motor + Pydantic) |
| AI Agent | LangGraph 3-node audit pipeline · optional GPT-4o-mini |
| Database | MongoDB 7 · Mongo-Express GUI |
| Orchestration | Docker Compose |

## Quick Start

### 1. Clone & configure

```bash
cp .env.example .env
# Optional: add your OPENAI_API_KEY to .env for real LLM reasoning
```

### 2. Launch

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Angular Frontend | http://localhost:4200 |
| FastAPI Swagger UI | http://localhost:8000/docs |
| Mongo-Express GUI | http://localhost:8081 (admin / admin123) |
| MongoDB | mongodb://localhost:27017 |

### 3. Explore

- Select a **property** from the dropdown (Ward 174 HSR Layout is pre-selected)
- View the **Impact Metrics** (Diverted from Landfill, Green Credits, Streak)
- Scroll the **Waste Lineage Timeline** — 4 steps: Pickup → In Transit → DWCC → Recycled
- Use the **Mint Credits** form to simulate a new audit event via the LangGraph pipeline

## Architecture

```
┌─────────────┐     HTTP/JSON      ┌──────────────────────┐
│  Angular 17  │ ◄──────────────► │  FastAPI + Beanie     │
│  (port 4200) │                   │  (port 8000)          │
│              │                   │                       │
│  Signals     │                   │  LangGraph Audit:     │
│  BFF Service │                   │  validate_weight      │
└─────────────┘                   │  → check_segregation  │
                                   │  → approve_or_reject  │
                                   └──────────┬───────────┘
                                              │ Motor / Beanie
                                   ┌──────────▼───────────┐
                                   │  MongoDB 7            │
                                   │  - properties         │
                                   │  - batches (lineage)  │
                                   └──────────────────────┘
```

## MongoDB Document Design

### Property
```json
{
  "property_id": "BLR-174-00001",
  "ward_number": 174,
  "ward_name": "HSR Layout",
  "type": "Household",
  "green_credits_balance": 128.5,
  "segregation_streak_days": 14,
  "total_waste_diverted_kg": 85.3
}
```

### Batch (with embedded NodeEvent lineage)
```json
{
  "batch_id": "uuid",
  "property_id": "BLR-174-00001",
  "waste_type": "Dry",
  "initial_weight_kg": 12.5,
  "events": [
    { "node_type": "Auto-Tipper", "status": "Verified",    "weight_kg": 12.5 },
    { "node_type": "Auto-Tipper", "status": "In Transit",  "weight_kg": 12.5 },
    { "node_type": "DWCC",        "status": "Verified",    "weight_kg": 12.1 },
    { "node_type": "Recycler",    "status": "Processed",   "weight_kg": 11.5 }
  ],
  "is_audit_passed": true,
  "credits_minted": 37.5
}
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/properties` | List all properties |
| GET | `/api/v1/properties/{property_id}` | Single property details |
| GET | `/api/v1/lineage/{property_id}` | Most recent batch + full event lineage |
| POST | `/api/v1/ledger/mint` | Trigger LangGraph audit and mint Green Credits |

## LangGraph Audit Pipeline

```
MintRequest → [validate_weight] → [check_segregation] → [approve_or_reject] → MintResponse
```

- **validate_weight**: Rejects batches outside 0.1–150 kg (500 kg for commercial)
- **check_segregation**: Rejects Sanitary/Special Care waste routed directly to Recycler
- **approve_or_reject**: Computes `weight × stream_multiplier` credits; calls GPT-4o-mini if `OPENAI_API_KEY` is set

## Green Credit Multipliers

| Stream | Multiplier |
|--------|-----------|
| Dry | 3.0× |
| Sanitary | 2.0× |
| Special Care | 4.0× |
| Wet | 1.5× |

## Seed Data (Bengaluru Locations)

- Ward 174 · HSR Layout
- Ward 150 · Bellandur
- Ward 168 · Koramangala (Commercial)
- Ward 152 · Marathahalli
- Ward 175 · Agara
