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
    # Extended for UX expansion
    "tenure_months": 1,
    "joined_date": "2026-04-08",
    "is_founding_gardener": True,
    "water_saved_l": round((20.0 - 2.0) * 12.4, 1),   # 223.2 L saved vs conventional
    "co2_saved_kg": round((2.5 - 0.3) * 12.4, 2),     # 27.28 kg saved
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
    {"date": "May 28", "items": ["Curly Kale (~200g)", "Thai Basil (~80g)"], "status": "scheduled", "can_skip": True},
    {"date": "Jun 04", "items": ["Curly Kale regrowth (~150g)"],             "status": "scheduled", "can_skip": True},
    {"date": "Jun 11", "items": ["Thai Basil (~80g)", "Edible flowers"],     "status": "tentative", "can_skip": False},
]

SKIP_REASONS = [
    "Traveling abroad",
    "Out of town",
    "Donate to NTUC food bank",
    "Pause this week",
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
    "What can I make with my kale this week?",
    "What pairs best with my kale?",
    "Show me the PPO defense report",
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
            "recipes": None,
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
            "recipes": None,
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
            "recipes": None,
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
            "recipes": None,
        }
    if any(w in q for w in ["recipe", "make", "cook", "smoothie", "salad", "pesto", "what can i"]):
        crop_names = ["Curly Kale", "Thai Basil"]
        recipes = get_recipe_for_crops(crop_names)
        recipe_list = "\n".join([f"- **{r['emoji']} {r['name']}** ({r['meal']}): {r['instructions'][:60]}..." for r in recipes])
        return {
            "text": (
                f"Based on your upcoming harvest, here are **3 recipes** you can make this week:\n\n"
                + recipe_list +
                "\n\nThe kale is perfect for a morning smoothie or a sesame salad — I'll show you how below!"
            ),
            "citations": [
                {"source": "Recipe DB", "snippet": "Curly Kale + Thai Basil combinations"},
            ],
            "recipes": recipes,
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
            "recipes": None,
        }
    if any(w in q for w in ["pairing", "pairs with", "what goes with", "k-means", "suggest", "recommend"]):
        pairings = get_sarah_pairings()
        pairing_text = "\n".join([
            f"- **{p['pair']}** with your kale: {p['reason']} (match score: {int(p['score']*100)}%)"
            for p in pairings
        ])
        cluster = SARAH_KMEANS_CLUSTER
        return {
            "text": (
                f"Based on the **K-Means segmentation** of 1,035 Singapore households, you're "
                f"in the **\"{cluster['label']}\"** cluster ({cluster['size']} members) "
                f"with your kale and basil pattern.\n\n"
                f"Here are your **top food pairings**:\n\n"
                f"{pairing_text}\n\n"
                f"_Next delivery will include a free edamame sample to try the top pairing._"
            ),
            "citations": [
                {"source": "K-Means Layer 4", "snippet": f"Cluster {cluster['cluster_id']}: {cluster['label']}, n={cluster['size']}"},
                {"source": "Pairing DB", "snippet": "Top-3 pairings per cluster, updated weekly"},
            ],
            "recipes": None,
        }
    if any(w in q for w in ["defense", "ppo report", "agent report", "climate shield", "24h", "agent action"]):
        return {
            "text": (
                "The **PPO RL agent** has been running your rack's climate 24/7. "
                "Here's the 24-hour defense summary:\n\n"
                "**🛡️ Climate Shield Report (May 18)**\n"
                "- Humidity adjustments: **38×** (all within ±2% of target)\n"
                "- LED intensity changes: **62×** (photoperiod extended 3×)\n"
                "- Nutrient flow corrections: **14×**\n"
                "- Power anomaly responses: **1** (handled autonomously)\n\n"
                "**Reward score: +0.04** — your kale is performing above expected baseline.\n"
                "No human intervention was needed. The AI handled everything."
            ),
            "citations": [
                {"source": "PPO RL agent log", "snippet": "24h episode: 1,247 actions, reward +0.04"},
                {"source": "Climate log", "snippet": "All parameters within defined bounds"},
            ],
            "recipes": None,
        }
    return {
        "text": (
            "I can tell you about your plot, your crops, the schedule, the AI's decisions, "
            "or your subscription. What would you like to know?"
        ),
        "citations": [],
        "recipes": None,
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


# ────────────────────────────────────────────
# ESG & Sustainability Metrics
# ────────────────────────────────────────────
ESG_METRICS = {
    "water_per_kg": 2.0,   # litres/kg (GreenLoop) vs 20 L/kg conventional
    "co2_per_kg": 0.3,     # kg-CO2/kg (GreenLoop) vs 2.5 kg/kg conventional
    "trees_equiv_per_kg": 0.05,  # trees worth of CO2 offset per kg
}

def get_esg_impact(kg_grown: float) -> dict:
    conventional_water = kg_grown * 20.0
    conventional_co2  = kg_grown * 2.5
    saved_water  = conventional_water - (kg_grown * ESG_METRICS["water_per_kg"])
    saved_co2   = conventional_co2  - (kg_grown * ESG_METRICS["co2_per_kg"])
    trees_equiv = kg_grown * ESG_METRICS["trees_equiv_per_kg"]
    return {
        "water_saved_l":  round(saved_water,  1),
        "co2_saved_kg":   round(saved_co2,   2),
        "trees_equiv":    round(trees_equiv, 1),
        "conventional_water_l": round(conventional_water, 1),
        "conventional_co2_kg": round(conventional_co2, 2),
    }

# Weekly growth log (last 8 weeks) — for portfolio chart
WEEKLY_GROWTH_LOG = [
    {"week": "Mar 29", "kg": 0.0},
    {"week": "Apr 05", "kg": 0.3},
    {"week": "Apr 12", "kg": 0.9},
    {"week": "Apr 19", "kg": 1.8},
    {"week": "Apr 26", "kg": 2.4},
    {"week": "May 03", "kg": 3.2},
    {"week": "May 10", "kg": 4.1},
    {"week": "May 17", "kg": 5.1},
]

# ────────────────────────────────────────────
# Founding Gardener + Status Tiers
# ────────────────────────────────────────────
STATUS_TIERS = [
    {"id": "Seedling",    "emoji": "🌱", "min_months": 0,  "color": "#7BA05B",
     "perks": ["Weekly harvest", "2 crop slots"]},
    {"id": "Sprout",      "emoji": "🌿", "min_months": 3,  "color": "#4A7C2E",
     "perks": ["Weekly harvest", "3 crop slots", "Edible Flowers access"]},
    {"id": "Gardener",    "emoji": "🥬", "min_months": 6,  "color": "#2D5016",
     "perks": ["Priority delivery", "4 crop slots", "Yuzu herb access", "Recipe AI"]},
    {"id": "Cultivator",  "emoji": "🏅", "min_months": 9,  "color": "#C7E66B",
     "perks": ["Priority delivery", "5 crop slots", "Wasabi microgreens", "1-on-1 check-in"]},
    {"id": "Master",      "emoji": "👑", "min_months": 12, "color": "#FFD700",
     "perks": ["Dedicated rack", "All varieties", "NFT certificates", "Founder label"]},
]

UNLOCKABLE_CROPS = [
    {"id": "edible-flowers",  "name": "Edible Flowers",   "emoji": "🌸", "unlocked_at": "Sprout"},
    {"id": "yuzu-herb",       "name": "Yuzu Herb",         "emoji": "🍋", "unlocked_at": "Gardener"},
    {"id": "wasabi-micro",    "name": "Wasabi Microgreens", "emoji": "🌿", "unlocked_at": "Cultivator"},
    {"id": "shiso",           "name": "Red Shiso",          "emoji": "🍃", "unlocked_at": "Master"},
]

# Sarah's status (1 month in = Seedling tier)
SARAH_STATUS = {
    "tier": "Seedling",
    "tenure_months": 1,
    "joined_date": "2026-04-08",
    "is_founding_gardener": True,   # pre-launch cohort
    "founding_cohort_date": "2026-04-08",
}

def get_status_tier(months: int):
    applicable = [t for t in STATUS_TIERS if t["min_months"] <= months]
    return max(applicable, key=lambda t: t["min_months"])

def get_next_status_tier(months: int):
    next_tiers = [t for t in STATUS_TIERS if t["min_months"] > months]
    return min(next_tiers, key=lambda t: t["min_months"]) if next_tiers else None

def get_unlocked_crops(tier_id: str):
    tier_order = [t["id"] for t in STATUS_TIERS]
    tier_rank = tier_order.index(tier_id)
    unlocked = []
    for c in UNLOCKABLE_CROPS:
        unlock_tier_rank = tier_order.index(c["unlocked_at"])
        if unlock_tier_rank <= tier_rank:
            unlocked.append(c)
    return unlocked

# ────────────────────────────────────────────
# Recipe Suggestions
# ────────────────────────────────────────────
RECIPES = [
    {
        "id": "kale-smoothie",
        "name": "Kale & Pineapple Smoothie",
        "emoji": "🥤",
        "crops": ["Curly Kale"],
        "ingredients": ["Curly Kale 80g", "Pineapple 100g", "Ginger 5g", "Coconut water 200ml"],
        "instructions": "Blend all ingredients until smooth. Serve chilled.",
        "meal": "Breakfast",
    },
    {
        "id": "basil-pesto",
        "name": "Thai Basil Pesto Pasta",
        "emoji": "🍝",
        "crops": ["Thai Basil"],
        "ingredients": ["Thai Basil 30g", "Pine nuts 20g", "Parmesan 15g", "Pasta 200g", "Olive oil 30ml"],
        "instructions": "Blend basil, nuts, oil, parmesan. Toss with cooked pasta.",
        "meal": "Dinner",
    },
    {
        "id": "kale-salad",
        "name": "Sesame Kale Salad",
        "emoji": "🥗",
        "crops": ["Curly Kale"],
        "ingredients": ["Curly Kale 100g", "Sesame seeds 10g", "Soy sauce 15ml", "Rice vinegar 10ml", "Sesame oil 5ml"],
        "instructions": "Massage kale with sesame oil. Add soy, vinegar, sesame seeds. Toss.",
        "meal": "Lunch",
    },
    {
        "id": "herb-rice",
        "name": "Basil Fried Rice",
        "emoji": "🍚",
        "crops": ["Thai Basil"],
        "ingredients": ["Thai Basil 20g", "Cooked rice 300g", "Eggs 2", "Soy sauce 20ml", "Garlic 10g"],
        "instructions": "Scramble eggs. Fry rice with garlic. Add soy and basil last.",
        "meal": "Dinner",
    },
    {
        "id": "mixed-green",
        "name": "Garden Microgreen Bowl",
        "emoji": "🥣",
        "crops": ["Curly Kale", "Thai Basil"],
        "ingredients": ["Curly Kale 50g", "Thai Basil 15g", "Quinoa 150g", "Avocado ½", "Lemon juice"],
        "instructions": "Cook quinoa. Arrange kale and basil over. Add avocado. Dress with lemon.",
        "meal": "Lunch",
    },
    {
        "id": "kale-chips",
        "name": "Crispy Kale Chips",
        "emoji": "🍿",
        "crops": ["Curly Kale"],
        "ingredients": ["Curly Kale 80g", "Olive oil 10ml", "Sea salt 3g", "Nutritional yeast 5g"],
        "instructions": "Toss kale with oil and salt. Bake at 150°C for 15 min until crispy.",
        "meal": "Snack",
    },
]

def get_recipe_for_crops(crop_names: list) -> list:
    """Return 2-3 recipes that use the given crop names."""
    results = []
    for r in RECIPES:
        if any(c.lower() in r["name"].lower() or c.lower() in " ".join(r["crops"]).lower() for c in crop_names):
            results.append(r)
    return results[:3]

# ────────────────────────────────────────────
# K-Means Food Pairing Suggestions
# (Based on K-Means k=4 customer segmentation from Layer 4)
# ────────────────────────────────────────────
KMEANS_CLUSTERS = [
    {
        "cluster_id": 0,
        "label": "Green Smoothie Lovers",
        "emoji": "🥤",
        "size": 312,
        "top_crops": ["Curly Kale", "Spinach", "Mint"],
        "pairings": [
            {"crop": "Kale", "pair": "Pineapple", "score": 0.94, "reason": "Sweetness balances kale's earthiness"},
            {"crop": "Kale", "pair": "Banana", "score": 0.89, "reason": "Creamy texture, high synergy"},
            {"crop": "Spinach", "pair": "Mango", "score": 0.87, "reason": "Tropical sweetness, low oxalate pairing"},
        ],
    },
    {
        "cluster_id": 1,
        "label": "Herb-Forward Cooks",
        "emoji": "🍝",
        "size": 284,
        "top_crops": ["Thai Basil", "Mint", "Curly Kale"],
        "pairings": [
            {"crop": "Thai Basil", "pair": "Edamame", "score": 0.91, "reason": "Umami bomb — Asian fusion staple"},
            {"crop": "Thai Basil", "pair": "Rice cakes", "score": 0.85, "reason": "Light, aromatic, 78% repeat rate"},
            {"crop": "Mint", "pair": "Lamb", "score": 0.83, "reason": "Classic, high satisfaction score"},
        ],
    },
    {
        "cluster_id": 2,
        "label": "Microgreen Power Users",
        "emoji": "🥗",
        "size": 198,
        "top_crops": ["Edible Flowers", "Arugula", "Spinach"],
        "pairings": [
            {"crop": "Edible Flowers", "pair": "Goat cheese", "score": 0.96, "reason": "Visual + flavor harmony, premium segment"},
            {"crop": "Arugula", "pair": "Pear", "score": 0.88, "reason": "Peppery + sweet, perfect lunch combo"},
            {"crop": "Edible Flowers", "pair": "Sparkling wine", "score": 0.82, "reason": "Celebration dining, gifting potential"},
        ],
    },
    {
        "cluster_id": 3,
        "label": "Comfort Food Flexitarians",
        "emoji": "🍚",
        "size": 241,
        "top_crops": ["Curly Kale", "Spinach", "Thai Basil"],
        "pairings": [
            {"crop": "Kale", "pair": "Potato", "score": 0.93, "reason": "Comfort food remake, 3× more fiber"},
            {"crop": "Spinach", "pair": "Pasta", "score": 0.90, "reason": "Hidden nutrition, family-friendly"},
            {"crop": "Kale", "pair": "Cheese", "score": 0.86, "reason": "Crispy kale chips, 89% satisfaction"},
        ],
    },
]

# Sarah's cluster assignment (based on her subscription + consumption patterns)
SARAH_KMEANS_CLUSTER = KMEANS_CLUSTERS[0]  # Green Smoothie Lovers

def get_sarah_pairings():
    return SARAH_KMEANS_CLUSTER["pairings"]

def get_cluster_pairing_for_crops(crops: list, cluster_id: int = 0) -> list:
    """Get top pairings for given crops from a specific K-Means cluster."""
    cluster = KMEANS_CLUSTERS[cluster_id]
    results = []
    for p in cluster["pairings"]:
        if any(c.lower() in p["crop"].lower() or p["crop"].lower() in c.lower() for c in crops):
            results.append(p)
    return results[:2]

# ────────────────────────────────────────────
# Omakase / Marriage Suggestions
# (Restaurant-quality pairing narratives, not just ingredient combos)
# ────────────────────────────────────────────
MARRYAGE_SUGGESTIONS = [
    {
        "id": "kale-wagyu",
        "crops": ["Curly Kale"],
        "emoji": "🥩",
        "title": "Kale + Premium Wagyu",
        "restaurant": "Ikyu Tokyo-style Beef Dining, MBS",
        "pairing_score": 97,
        "marryage": (
            "This week's kale has an unusually high glucosinolate content — the compound "
            "that gives it that peppery bite. Japanese beef fat dissolves it perfectly, "
            "creating the same contrast that makes wasabi so effective against rich fish. "
            "Sear the wagyu at high heat, let the kale wilt in 30 seconds, and eat them together."
        ),
        "wine": "Slightly chilled Junmai Ginjo, or a crisp Albariño",
        "occasion": "Weekend treat",
    },
    {
        "id": "basil-salmon",
        "crops": ["Thai Basil"],
        "emoji": "🐟",
        "title": "Thai Basil + King Salmon",
        "restaurant": "Walaku, Gillman Barracks",
        "pairing_score": 95,
        "marryage": (
            "Thai basil's eugenol content — the same compound in holy basil — cuts through "
            "the omega-3 richness of king salmon the same way ponzu cuts through fatty tuna. "
            "Light sear on the salmon, finish with torn basil leaves and a squeeze of yuzu. "
            "The aromatics bloom against the heat."
        ),
        "wine": "Riesling Feinherb or chilled Asahi Super Dry",
        "occasion": "Friday dinner",
    },
    {
        "id": "kale-eggplant",
        "crops": ["Curly Kale"],
        "emoji": "🍆",
        "title": "Kale + Miso Glazed Eggplant",
        "restaurant": "Plowers, Tiong Bahru",
        "pairing_score": 91,
        "marryage": (
            "The sweetness of miso-glazed eggplant meets the mineral, slightly bitter edge "
            "of mature kale. The contrast in texture — silky eggplant against the kale's "
            "crisp bite — makes every mouthful interesting. Add a soft-poached egg on top."
        ),
        "wine": "Amabuki Pumpkin Junmai",
        "occasion": "Mid-week comfort",
    },
    {
        "id": "mixed-buddha",
        "crops": ["Curly Kale", "Thai Basil"],
        "emoji": "🥣",
        "title": "Garden Buddha Bowl",
        "restaurant": "Self-prep / Any weekend",
        "pairing_score": 93,
        "marryage": (
            "A bowl that anchors the week's nutrition: quinoa base, raw kale massaged "
            "with sesame, Thai basil added fresh after cooking to preserve aromatics, "
            "roasted sweet potato, pickled radish, and a tahini-lemon dressing. "
            "Every element supports the others. This is the bowl you'll crave."
        ),
        "wine": "Still water with lemon, or a light sparkling.",
        "occasion": "Meal prep Sunday",
    },
]

def get_marriage_suggestion_for_crops(crop_names: list) -> dict:
    """Return the best omakase/marriage suggestion for the given crops."""
    for m in MARRYAGE_SUGGESTIONS:
        if any(c.lower() in " ".join(m["crops"]).lower() for c in crop_names):
            return m
    return MARRYAGE_SUGGESTIONS[3]  # fallback to buddha bowl

def get_sarah_marriage_suggestion():
    """Return Sarah's personalized marriage suggestion for this week's harvest."""
    return get_marriage_suggestion_for_crops(["Curly Kale", "Thai Basil"])

# ────────────────────────────────────────────
# Skip-to-Donate Flow
# ────────────────────────────────────────────
DONATION_RECIPIENTS = {
    "ntuc": {
        "name": "NTUC Food Bank",
        "emoji": "🏠",
        "description": "Singapore's largest food redistribution charity",
        "impact": "2 meals per kg of fresh produce",
    },
    "red_cross": {
        "name": "Singapore Red Cross",
        "emoji": "🩸",
        "description": "Emergency food relief for vulnerable families",
        "impact": "1 meal per S$2 donated value",
    },
    "senior_meals": {
        "name": "AWWA Senior Nutrition",
        "emoji": "👵",
        "description": "Meals-on-wheels for elderly residents",
        "impact": "3 meals per kg of fresh produce",
    },
}

def get_donation_receipt(recipient_key: str, kg_donated: float = 2.1) -> dict:
    """Generate a donation receipt for the skip-to-donate flow."""
    import random
    recipient = DONATION_RECIPIENTS.get(recipient_key, DONATION_RECIPIENTS["ntuc"])
    return {
        "receipt_id": f"DN-{2026}{random.randint(1000, 9999)}",
        "recipient": recipient,
        "kg_donated": kg_donated,
        "meals_provided": round(kg_donated * 2.0),  # ~2 meals per kg
        "co2_saved_kg": round(kg_donated * 2.2, 2),
        "date": "May 2026",
        "badge_earned": "🌍 ESG Guardian",
        "badge_description": "Converted a skip into social impact",
    }

# ────────────────────────────────────────────
# Crisis / Typhoon Alerts
# ────────────────────────────────────────────
ALERT_TEMPLATES = {
    "typhoon_harvest": {
        "type": "typhoon_harvest",
        "severity": "critical",
        "icon": "🌀",
        "title": "Emergency Harvest Complete",
        "body": "Our AI detected a power anomaly near your farm and triggered an emergency harvest to protect your crops. Your kale has been safely harvested 2 days early and stored in our cold room. No action needed — your delivery is fully preserved.",
        "action_label": "View Harvest Details",
        "action": "See receipt",
    },
    "power_outage": {
        "type": "power_outage",
        "severity": "warning",
        "icon": "⚡",
        "title": "Power Fluctuation Detected",
        "body": "A brief power fluctuation was detected at your farm rack at 04:32 SGT. The UPS backup activated instantly and our PPO RL agent is managing the situation. All sensors are nominal.",
        "action_label": "Monitor Status",
        "action": None,
    },
    "delivery_delay": {
        "type": "delivery_delay",
        "severity": "info",
        "icon": "🚚",
        "title": "Delivery Rescheduled",
        "body": "Your Wednesday delivery has been automatically shifted to Thursday 8–10am due to heavy rain advisory. No action needed.",
        "action_label": None,
        "action": None,
    },
    "crop_ready": {
        "type": "crop_ready",
        "severity": "info",
        "icon": "🌿",
        "title": "Your Kale Is Ready!",
        "body": "Your Curly Kale has reached peak biomass at 210g. Harvest window: May 27–29. We'll harvest at the optimal moment automatically.",
        "action_label": "Track Harvest",
        "action": None,
    },
    "defense_report": {
        "type": "defense_report",
        "severity": "info",
        "icon": "🛡️",
        "title": "PPO Defense Report: Climate Shield Active",
        "body": (
            "The PPO RL agent defended your rack 1,247 times in the last 24h: "
            "humidity adjusted 38×, LED intensity 62×, nutrient flow 14×. "
            "Your crop earned a +0.04 reward bonus. "
            "No intervention needed — the AI handled everything autonomously."
        ),
        "action_label": "View 24h Defense Log",
        "action": None,
    },
    "surprise_upgrade": {
        "type": "surprise_upgrade",
        "severity": "info",
        "icon": "🎁",
        "title": "Surprise Upgrade Applied!",
        "body": (
            "Your rack produced a surplus harvest — 23% above the weekly baseline. "
            "The AI automatically upgraded your delivery with free Edible Flowers 🌸 "
            "(normally a Sprout-tier crop). "
            "This is what long-term membership earns."
        ),
        "action_label": "See My Upgraded Delivery",
        "action": None,
    },
    "food_pairing": {
        "type": "food_pairing",
        "severity": "info",
        "icon": "🍽️",
        "title": "K-Means Pairing: Kale + Edamame",
        "body": (
            "Your consumption pattern (847 similar households in the K-Means cluster) "
            "suggests kale + edamame is the top-rated pairing for your taste profile. "
            "Try it this week — the AI will include a free sample in your next delivery."
        ),
        "action_label": "Browse More Pairings",
        "action": None,
    },
    "donation_skipped": {
        "type": "donation_skipped",
        "severity": "info",
        "icon": "💚",
        "title": "Your Skip Became a Donation!",
        "body": (
            "When you skip a delivery, your crops don't go to waste. "
            "2.1kg of fresh produce was donated to NTUC Food Bank on your behalf. "
            "You've earned the 🌍 ESG Guardian badge for turning a skip into social impact."
        ),
        "action_label": "View ESG Impact",
        "action": None,
    },
}

def create_alert(alert_type: str, **params) -> dict:
    template = ALERT_TEMPLATES.get(alert_type, ALERT_TEMPLATES["crop_ready"])
    return {
        "id": f"alert-{alert_type}-{params.get('date', 'today')}",
        **template,
        **params,
    }

# Demo active alerts for Sarah (show typhoon alert as example)
DEMO_ACTIVE_ALERTS = [
    create_alert("typhoon_harvest", date="today"),
]
