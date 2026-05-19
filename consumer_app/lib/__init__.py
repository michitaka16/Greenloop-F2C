"""lib — Adopt a Kale shared library."""

from consumer_app.lib.styles import (
    inject_css,
    inject_gamification_css,
    brand_header,
    eyebrow,
    pill,
    maturity_ring_html,
    progress_card,
    confetti_html,
    badge_card,
    leaderboard_row,
    esg_card_html,
    growth_chart_svg,
    status_badge_html,
    alert_banner_html,
    KALE,
    LEAF,
    LIME,
    CORAL,
    CREAM,
    PAPER,
    HAIR,
    MUTED,
    INK,
    ASSETS,
    img_to_base64,
    recipe_card_html,
    delivery_card_skip_html,
    marriage_card_html,
    donation_receipt_html,
)

from consumer_app.lib.mock_data import (
    SARAH,
    CROPS,
    STATUS,
    UPCOMING_DELIVERIES,
    RECENT_EVENTS,
    MILESTONES,
    SARAH_BADGES,
    LEADERBOARD,
    get_earned_badges,
    get_next_badge,
    get_leaderboard_position,
    SARAH_STATUS,
    WEEKLY_GROWTH_LOG,
    get_status_tier,
    get_next_status_tier,
    get_esg_impact,
    DEMO_ACTIVE_ALERTS,
    RECIPES,
    get_recipe_for_crops,
    SUGGESTED_QUESTIONS,
    mock_response,
)

# Production clients (lazy imports — only when used)
# from consumer_app.lib.llm_client import RAGClient
# from consumer_app.lib.sensor_client import get_latest_readings, get_weather_note
# from consumer_app.lib.weather_client import get_weather_condition, get_weather_note, get_weather_delivery_warning
