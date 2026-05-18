"""Mock data for Sarah's plot. Replace with real API calls later."""

SARAH = {
    "name": "Sarah Tan",
    "initial": "S",
    "hood": "Tanglin",
    "flat": "4-room HDB",
    "tier": "Standard",
    "plot_id": "042",
    "started_at": "2026-04-08",
    "days_in": 31,
    "total_days": 42,
    "next_harvest": "May 28",
    "total_kg_grown": 12.4,
    "total_deliveries": 18,
}

CROPS = [
    {
        "id": "kale-curly",
        "name": "Curly Kale",
        "variety": "Winterbor",
        "emoji": "🥬",
        "days_in": 31,
        "total_days": 42,
        "status": "growing",
        "yield_kg": 0.8,
    },
    {
        "id": "basil-thai",
        "name": "Thai Basil",
        "variety": "Siam Queen",
        "emoji": "🌿",
        "days_in": 18,
        "total_days": 28,
        "status": "growing",
        "yield_kg": 0.3,
    },
]

STATUS = {
    "maturity": 74,
    "last_tuned": "06:00 SGT",
    "uptime_hrs": 744,
    "energy_kwh": 4.2,
    "water_used_l": 18,
}

UPCOMING_DELIVERIES = [
    {"date": "May 28", "items": ["Curly Kale (~200g)", "Thai Basil (~80g)"], "status": "scheduled"},
    {"date": "Jun 04", "items": ["Curly Kale regrowth (~150g)"],             "status": "scheduled"},
    {"date": "Jun 11", "items": ["Thai Basil (~80g)", "Edible flowers"],     "status": "tentative"},
]

RECENT_EVENTS = [
    {"time": "today 06:00", "text": "Climate auto-tuned: humidity +2%, light +5min"},
    {"time": "yesterday",   "text": "Day 30 milestone — kale entered final growth phase"},
    {"time": "May 5",       "text": "Pest scan complete — no anomalies detected"},
    {"time": "May 3",       "text": "Thai basil germination confirmed (Day 1)"},
    {"time": "May 1",       "text": "Delivery received — kale microleaves 180g"},
]

CAMERA = {
    "status": "live",
    "last_capture": "today 06:00 SGT",
    "interval_hours": 24,
    "rack_id": "RACK-A7",
    "ai_diagnosis": {
        "crop": "Curly Kale",
        "growth_stage": "Vegetative",
        "nutrition_status": "Optimal",
        "health_score": 94,
        "leaf_area_m2": 0.42,
        "biomass_g": 184,
        "anomalies": [],
        "recommendation": "Continue current nutrient protocol. Harvest window opens May 27.",
    },
}

CAMERA_TIMELINE = [
    {
        "day": 1,
        "date": "Mar 29",
        "label": "Day 1 — Germination",
        "status": "normal",
        "health_score": 78,
        "note": "Seeds planted. Humidity dome applied.",
    },
    {
        "day": 8,
        "date": "Apr 5",
        "label": "Day 8 — Seedling",
        "status": "normal",
        "health_score": 81,
        "note": "First true leaves visible. LED intensity increased.",
    },
    {
        "day": 15,
        "date": "Apr 12",
        "label": "Day 15 — Vegetative",
        "status": "normal",
        "health_score": 88,
        "note": "Rapid leaf expansion. Nutrient concentration increased.",
    },
    {
        "day": 22,
        "date": "Apr 19",
        "label": "Day 22 — Mid growth",
        "status": "normal",
        "health_score": 91,
        "note": "Canopy closing. pH adjusted to 5.8.",
    },
    {
        "day": 29,
        "date": "Apr 26",
        "label": "Day 29 — Pre-harvest",
        "status": "normal",
        "health_score": 93,
        "note": "Leaf colour deepening. Final nutrient adjustment.",
    },
    {
        "day": 31,
        "date": "Apr 28",
        "label": "Day 31 — Today",
        "status": "normal",
        "health_score": 94,
        "note": "74% to harvest. Climate auto-tuned this morning.",
    },
]

TIERS = [
    {
        "id": "Standard",
        "price": 40,
        "body": "Shared kale slot. Weekly home delivery. Choose 2 crops.",
        "features": ["Weekly delivery", "Choose 2 crops", "WhatsApp updates", "Pause for travel"],
        "crops": 2,
        "recommended": True,
    },
    {
        "id": "Pro",
        "price": 100,
        "body": "Your own 1m² rack. 4–5 premium crops. Personalised grow log.",
        "features": ["Your own 1m² rack", "4–5 premium crops", "Growth progress reports", "Harvest alerts + sensor data"],
        "crops": 5,
        "recommended": False,
    },
    {
        "id": "Corporate",
        "price": 5000,
        "body": "For teams, offices, and wellness programmes. Named employee slots. Bulk billing.",
        "features": ["Named employee slots", "Wellness programme", "Bulk billing", "Dedicated account manager", "50+ crop varieties", "Priority harvest scheduling"],
        "crops": 50,
        "recommended": False,
        "enterprise": True,
    },
]

CROP_OPTIONS = [
    {"id": "kale-curly",      "name": "Curly Kale",      "emoji": "🥬"},
    {"id": "basil-thai",      "name": "Thai Basil",      "emoji": "🌿"},
    {"id": "spinach",         "name": "Spinach",         "emoji": "🥗"},
    {"id": "arugula",         "name": "Arugula",         "emoji": "🌱"},
    {"id": "mint",            "name": "Mint",            "emoji": "🍃"},
    {"id": "edible-flowers",  "name": "Edible Flowers",  "emoji": "🌸"},
]

SUGGESTED_QUESTIONS = [
    "When will my kale be ready?",
    "Why is the humidity changing today?",
    "Can I add edible flowers to my plot?",
    "Is my Thai basil getting enough light?",
    "How much have I grown so far this year?",
]


def mock_response(question: str) -> dict:
    """Return a mock RAG-style chat response. Wire to real RAG-LLM later."""
    q = question.lower()
    if any(w in q for w in ["ready", "when", "harvest"]):
        return {
            "text": (
                "Your curly kale is on track for harvest on **May 28** — that's 11 days from "
                "today. The MILP harvest scheduler picked this date to maximize biomass while "
                "staying inside your weekly delivery window."
            ),
            "citations": [
                {"source": "Plot 042 sensors", "snippet": "Day 31 of 42, biomass 184g, leaf area 0.42m²"},
                {"source": "Harvest schedule", "snippet": "Optimal harvest window: May 27–30 (48ms MILP solve)"},
            ],
        }
    if any(w in q for w in ["humidity", "light", "temperature", "climate"]):
        return {
            "text": (
                "The **PPO RL controller** raised humidity by 2% and extended light by 5 minutes "
                "this morning. Reason: yesterday's leaf transpiration was 8% above the target curve, "
                "suggesting the kale is in its final-phase growth surge — extra moisture and light "
                "maximize the last 26% of biomass."
            ),
            "citations": [
                {"source": "Climate log", "snippet": "06:00 SGT — humidity 68→70%, photoperiod 14:00→14:05"},
                {"source": "PPO RL agent", "snippet": "Reward signal: +0.04 (transpiration above target)"},
            ],
        }
    if any(w in q for w in ["flower", "add", "crop", "edible"]):
        return {
            "text": (
                "You're on the **Standard tier** (S$40/mo, 2 crops). Edible flowers would need an "
                "upgrade to **Pro** (S$100/mo, 4–5 crops). I can preview what your plot would "
                "look like with edible nasturtiums + viola alongside your existing kale and basil."
            ),
            "citations": [
                {"source": "Subscription",  "snippet": "Standard tier: 2 crop slots active"},
                {"source": "Crop catalog",  "snippet": "Pro-tier additions: nasturtium, viola, mint, oregano"},
            ],
        }
    if "basil" in q:
        return {
            "text": (
                "Your **Thai basil** is getting 14 hours of LED at 240 µmol/m²/s — exactly its "
                "optimal range. Day 18 of 28 is right where we want it. The aroma compounds peak "
                "around day 24, so you'll start to smell it through the camera by next weekend."
            ),
            "citations": [
                {"source": "Plot 042 sensors", "snippet": "Basil PPFD: 240 µmol/m²/s, photoperiod: 14h"},
            ],
        }
    if any(w in q for w in ["how much", "year", "total", "kg"]):
        kg = SARAH["total_kg_grown"]
        return {
            "text": (
                f"You've grown **{kg} kg** of fresh produce since joining — that's about "
                f"{int(kg * 8)} salad servings, or roughly **S${int(kg * 18)}** at supermarket "
                f"prices for the same premium quality."
            ),
            "citations": [],
        }
    return {
        "text": (
            "I can tell you about your plot, your crops, the schedule, the AI's decisions, "
            "or your subscription. What would you like to know?"
        ),
        "citations": [],
    }


# ────────────────────────────────────────────
# Gamification — Milestones (6 levels)
# ────────────────────────────────────────────
MILESTONES = [
    {
        "id": "seed_planted",
        "level": 1,
        "emoji": "🌱",
        "title": "Seed Planted",
        "description": "Your journey begins — a seed is now in the soil.",
        "criterion": "Start your subscription",
        "color": "#7BA05B",
    },
    {
        "id": "germination",
        "level": 2,
        "emoji": "🌿",
        "title": "Germination",
        "description": "First sprouts breaking through — life finds a way.",
        "criterion": "Crop reaches Day 8",
        "color": "#7BA05B",
    },
    {
        "id": "vegetative",
        "level": 3,
        "emoji": "🥬",
        "title": "Vegetative Growth",
        "description": "Leaves stretching wide — photosynthesis in full swing.",
        "criterion": "Crop reaches Day 15",
        "color": "#2D5016",
    },
    {
        "id": "pre_harvest",
        "level": 4,
        "emoji": "✨",
        "title": "Pre-Harvest",
        "description": "Final growth spurt — harvest window is close.",
        "criterion": "Crop reaches Day 29",
        "color": "#C7E66B",
    },
    {
        "id": "first_harvest",
        "level": 5,
        "emoji": "🏆",
        "title": "First Harvest",
        "description": "You did it — fresh produce from your own plot.",
        "criterion": "Complete first delivery",
        "color": "#E07856",
    },
    {
        "id": "harvest_master",
        "level": 6,
        "emoji": "👑",
        "title": "Harvest Master",
        "description": "5+ successful harvests. You're a natural.",
        "criterion": "Complete 5 deliveries",
        "color": "#C7E66B",
    },
]

# Sarah's earned badges (matches her Day 31, 18 deliveries)
SARAH_BADGES = [
    {**MILESTONES[0], "earned": True,  "earned_date": "2026-04-08"},
    {**MILESTONES[1], "earned": True,  "earned_date": "2026-04-15"},
    {**MILESTONES[2], "earned": True,  "earned_date": "2026-04-22"},
    {**MILESTONES[3], "earned": True,  "earned_date": "2026-05-03"},
    {**MILESTONES[4], "earned": True,  "earned_date": "2026-04-28"},
    {**MILESTONES[5], "earned": False, "earned_date": None},
]

# ────────────────────────────────────────────
# Gamification — Leaderboard
# ────────────────────────────────────────────
LEADERBOARD = [
    {"rank": 1,  "name": "Priya M.",       "plot": "Plot #017", "badges": 6, "kg_grown": 31.2, "deliveries": 52, "tier": "Pro",      "hood": "Bishan"},
    {"rank": 2,  "name": "Wei L.",         "plot": "Plot #003", "badges": 6, "kg_grown": 28.7, "deliveries": 48, "tier": "Corporate", "hood": "Jurong"},
    {"rank": 3,  "name": "Sarah T.",      "plot": "Plot #042", "badges": 5, "kg_grown": 12.4, "deliveries": 18, "tier": "Standard",  "hood": "Tanglin"},
    {"rank": 4,  "name": "Ahmad F.",      "plot": "Plot #009", "badges": 4, "kg_grown":  9.1, "deliveries": 14, "tier": "Pro",      "hood": "Ang Mo Kio"},
    {"rank": 5,  "name": "Li H.",         "plot": "Plot #031", "badges": 3, "kg_grown":  6.3, "deliveries":  9, "tier": "Standard",  "hood": "Tampines"},
]

# ────────────────────────────────────────────
# Gamification — Harvest NFT Certificates
# ────────────────────────────────────────────
# Certificate to be minted (next harvest)
HARVEST_CERTIFICATE_NFT = {
    "id": "gl-nft-pending-001",
    "crop": "Curly Kale",
    "variety": "Winterbor",
    "harvest_date": "2026-05-28",
    "biomass_g": 210,
    "total_kg_grown": 13.2,
    "delivery_count": 19,
    "wallet_address": "0x71C...3F2E",
    "tx_hash": "0x9a4b...7c21",
    "token_id": 4282,
    "plot_id": "042",
    "status": "pending",
}

# Already-minted NFTs
MINTED_NFTS = [
    {
        "id": "gl-nft-2026-0428-001",
        "crop": "Curly Kale",
        "variety": "Winterbor",
        "harvest_date": "2026-04-28",
        "biomass_g": 184,
        "total_kg_grown": 12.4,
        "delivery_count": 18,
        "wallet_address": "0x71C...3F2E",
        "tx_hash": "0x9a4b...7c21",
        "token_id": 4281,
        "plot_id": "042",
        "status": "minted",
    }
]

# ────────────────────────────────────────────
# Helper functions
# ────────────────────────────────────────────
def get_earned_badges():
    return [b for b in SARAH_BADGES if b["earned"]]

def get_next_badge():
    for b in SARAH_BADGES:
        if not b["earned"]:
            return b
    return None

def get_leaderboard_position():
    return next(r for r in LEADERBOARD if r["name"] == "Sarah T.")["rank"]

def get_share_card_data():
    return {
        "crop": "Curly Kale",
        "variety": "Winterbor",
        "kg_grown": SARAH["total_kg_grown"],
        "deliveries": SARAH["total_deliveries"],
        "badges": len(get_earned_badges()),
        "plot_id": SARAH["plot_id"],
        "date": "May 2026",
        "name": SARAH["name"],
        "tier": SARAH["tier"],
    }
