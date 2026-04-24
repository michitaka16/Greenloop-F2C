#!/usr/bin/env node
/**
 * GreenLoop F2C — Pitch Deck v3 Generator
 * Inserts Governance slide between Typhoon (slide 9) and Sustainability.
 * Run: node scripts/generate_pitch_deck_v3.js
 */

const PptxGenJS = require("/tmp/node_modules/pptxgenjs");
const path = require("path");
const fs = require("fs");

// ── Palette ──────────────────────────────────────────────────────────────────
const C = {
  darkGreen:  "1B4332",   // deep forest
  midGreen:   "2D6A4F",   // forest
  lightGreen: "40916C",   // moss
  accent:     "52B788",    // bright moss
  cream:      "F8F9FA",   // background
  white:      "FFFFFF",
  darkText:   "1B1B1B",
  lightText:  "F8F9FA",
  gold:       "D4A843",
  cardBg:     "D8F3DC",   // light mint card
  cardBorder: "74C69D",
};

// ── Helpers ──────────────────────────────────────────────────────────────────
function makeShadow() {
  return { type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.12 };
}

function slideHeader(slide, title, subtitle, bgColor = C.darkGreen) {
  slide.background = { color: bgColor };

  // Top accent bar
  slide.addShape("rect", {
    x: 0, y: 0, w: 10, h: 0.08,
    fill: { color: C.accent }, line: { color: C.accent },
  });

  // Title
  slide.addText(title, {
    x: 0.5, y: 0.3, w: 9, h: 0.75,
    fontSize: 32, bold: true, color: C.lightText,
    fontFace: "Trebuchet MS", margin: 0,
  });

  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.5, y: 1.0, w: 9, h: 0.4,
      fontSize: 14, color: C.accent, fontFace: "Trebuchet MS",
      margin: 0,
    });
  }
}

function sectionTag(slide, text) {
  slide.addText(text, {
    x: 0.5, y: 0.2, w: 1.6, h: 0.28,
    fontSize: 9, bold: true, color: C.darkGreen,
    fill: { color: C.accent }, align: "center",
    fontFace: "Trebuchet MS", margin: 0,
  });
}

function footer(slide, pageNum, total) {
  slide.addText(`${pageNum} / ${total}`, {
    x: 9.0, y: 7.2, w: 0.8, h: 0.3,
    fontSize: 9, color: C.midGreen, align: "right",
    fontFace: "Trebuchet MS", margin: 0,
  });
  // thin bottom line
  slide.addShape("rect", {
    x: 0, y: 7.5, w: 10, h: 0.04,
    fill: { color: C.accent }, line: { color: C.accent },
  });
}

// ── Deck ─────────────────────────────────────────────────────────────────────
const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.title = "GreenLoop F2C — Pitch Deck v3";
pptx.author = "GreenLoop Team";

// Slide dimensions: 10 × 7.5 inches
const TOTAL = 17;

function addSlide(fn) {
  const slide = pptx.addSlide();
  fn(slide);
  return slide;
}

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 1 — COVER
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slide.background = { color: C.darkGreen };

  // Left accent bar
  slide.addShape("rect", { x: 0, y: 0, w: 0.12, h: 7.5, fill: { color: C.accent }, line: { color: C.accent } });

  // Logo area placeholder
  slide.addText("🌿 GreenLoop", {
    x: 0.6, y: 0.5, w: 4, h: 0.6,
    fontSize: 22, bold: true, color: C.accent, fontFace: "Trebuchet MS", margin: 0,
  });

  // Main title
  slide.addText("Farm-to-Consumer\nVertical Hydroponics OS", {
    x: 0.6, y: 1.4, w: 7.5, h: 2.0,
    fontSize: 44, bold: true, color: C.lightText,
    fontFace: "Trebuchet MS", margin: 0,
  });

  // Tagline
  slide.addText("5 AI Layers · Seed to Delivery · Every Decision Optimised", {
    x: 0.6, y: 3.5, w: 7, h: 0.5,
    fontSize: 16, color: C.accent, fontFace: "Trebuchet MS", margin: 0,
  });

  // Rule
  slide.addShape("rect", { x: 0.6, y: 4.1, w: 3.5, h: 0.05, fill: { color: C.gold }, line: { color: C.gold } });

  // Course / date
  slide.addText("MGMT 655 — AI & Machine Learning  |  Week 8 Capstone  |  2026-04-24", {
    x: 0.6, y: 4.3, w: 8, h: 0.35,
    fontSize: 11, color: C.lightGreen, fontFace: "Trebuchet MS", margin: 0,
  });

  footer(slide, 1, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 2 — THE PROBLEM
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slideHeader(slide, "The Problem", "Singapore's food security gap is structural — not seasonal");
  sectionTag(slide, "ACT 1");

  // Big stat
  slide.addText(">90%", {
    x: 0.5, y: 1.5, w: 4, h: 1.4,
    fontSize: 80, bold: true, color: C.gold, fontFace: "Trebuchet MS", margin: 0,
  });
  slide.addText("of food imported", {
    x: 0.5, y: 2.9, w: 4, h: 0.4,
    fontSize: 18, color: C.lightText, fontFace: "Trebuchet MS", margin: 0,
  });

  // Crisis timeline
  const events = [
    ["2020", "COVID-19 — supply chains disrupted for months"],
    ["2022", "Egg shortage — prices +40% in 6 weeks"],
    ["2024", "Singapore commits SGD 70M ACTF fund"],
    ["Jan 2025", "Swiss competitor Greenphyto AG raises CHF 12M"],
  ];
  events.forEach(([year, text], i) => {
    slide.addText(year, {
      x: 5.2, y: 1.5 + i * 0.75, w: 0.9, h: 0.5,
      fontSize: 13, bold: true, color: C.gold, fontFace: "Trebuchet MS", margin: 0,
    });
    slide.addText(text, {
      x: 6.1, y: 1.5 + i * 0.75, w: 3.4, h: 0.5,
      fontSize: 12, color: C.lightText, fontFace: "Trebuchet MS", margin: 0,
    });
  });

  footer(slide, 2, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 3 — THE OPPORTUNITY
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slideHeader(slide, "The Gap", "Competitors plan by hand — we plan by AI");
  sectionTag(slide, "ACT 1");

  const cards = [
    { title: "Traditional Farm", items: ["Spreadsheet planning", "Weekly cycles", "Human bottlenecks", "No real-time re-plan"], color: C.midGreen },
    { title: "GreenLoop F2C", items: ["5 AI layers", "< 50 ms re-plan", "Automated responses", "Full resilience cascade"], color: C.accent },
  ];

  cards.forEach((card, i) => {
    const x = 0.5 + i * 4.7;
    slide.addShape("roundRect", {
      x, y: 1.5, w: 4.3, h: 4.5,
      fill: { color: card.color }, rectRadius: 0.12,
      shadow: makeShadow(),
    });
    slide.addText(card.title, {
      x: x + 0.2, y: 1.7, w: 3.9, h: 0.6,
      fontSize: 20, bold: true, color: C.darkGreen, fontFace: "Trebuchet MS", margin: 0,
    });
    slide.addText(
      card.items.map((item, idx) => ({
        text: item,
        options: { bullet: true, breakLine: idx < card.items.length - 1 },
      })),
      { x: x + 0.3, y: 2.4, w: 3.7, h: 3.2, fontSize: 14, color: C.darkText, fontFace: "Trebuchet MS", paraSpaceAfter: 8 }
    );
  });

  footer(slide, 3, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 4 — LAYER 1 DEMAND FORECASTING
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slideHeader(slide, "Layer 1 — Demand Forecasting", "XGBoost quantile regression: what sells tomorrow");
  sectionTag(slide, "ACT 2");

  slide.addText("9 indoor-farm features", {
    x: 0.5, y: 1.45, w: 5, h: 0.35,
    fontSize: 13, bold: true, color: C.lightGreen, fontFace: "Trebuchet MS", margin: 0,
  });

  const features = [
    ["Lag shipments", "7d / 14d / 28d volumes"],
    ["Rolling mean/std", "28-day window"],
    ["Cyclical encoding", "Week pattern sin/cos"],
    ["Day-of-week", "Mon–Sun dummies"],
    ["SG holiday flags", "CNY, Deepavali, Hari Raya"],
    ["Rainy-day signal", "Monsoon month proxy"],
    ["Climate", "Temp, humidity, CO₂ deviation"],
    ["Tariff tier", "Peak / off-peak electricity"],
    ["Crop density", "Cross-crop market density"],
  ];

  features.forEach(([title, desc], i) => {
    const col = i < 5 ? 0 : 1;
    const row = i < 5 ? i : i - 5;
    const x = 0.5 + col * 4.7;
    const y = 1.9 + row * 0.62;
    slide.addText(title, { x, y, w: 2.2, h: 0.4, fontSize: 11, bold: true, color: C.accent, fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(desc, { x: x + 2.2, y, w: 2.3, h: 0.4, fontSize: 11, color: C.lightText, fontFace: "Trebuchet MS", margin: 0 });
  });

  // Quantile callout
  slide.addShape("roundRect", {
    x: 0.5, y: 5.1, w: 9, h: 1.4,
    fill: { color: C.cardBg }, rectRadius: 0.1,
  });
  slide.addText("Quantile regression: q = 0.05 / 0.50 / 0.95", {
    x: 0.7, y: 5.2, w: 8.6, h: 0.4,
    fontSize: 13, bold: true, color: C.darkGreen, fontFace: "Trebuchet MS", margin: 0,
  });
  slide.addText("Upper CI (q=0.95) becomes Layer 2 production target → robust plan even at 95th demand percentile. 18 features × 10 crops × 3 quantiles.", {
    x: 0.7, y: 5.6, w: 8.6, h: 0.8,
    fontSize: 11, color: C.darkText, fontFace: "Trebuchet MS", margin: 0,
  });

  footer(slide, 4, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 5 — LAYER 2 MILP FARM OPTIMISATION
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slideHeader(slide, "Layer 2 — Farm Optimisation", "OR-Tools MILP: profit-maximising plan in < 50 ms");
  sectionTag(slide, "ACT 2");

  // Constraints table
  const constraints = [
    ["MOM Hours", "Max 8h LED/day per tier"],
    ["Water Tank", "≤ 500 L/day capacity"],
    ["Delivery Window", "06:00–22:00 (16h nominal / 6h typhoon)"],
    ["Rack Assignment", "1 crop per tier, min harvest 2 kg"],
    ["Crop LED Needs", "Species-specific PPFD requirements"],
    ["Harvest Labour", "≥ 5 kg combined per day"],
  ];

  slide.addText("7 Hard Constraints", {
    x: 0.5, y: 1.45, w: 4, h: 0.35,
    fontSize: 13, bold: true, color: C.lightGreen, fontFace: "Trebuchet MS", margin: 0,
  });

  constraints.forEach(([c, d], i) => {
    const col = i < 3 ? 0 : 1;
    const row = i < 3 ? i : i - 3;
    const x = 0.5 + col * 4.7;
    const y = 1.9 + row * 0.75;
    slide.addShape("roundRect", { x, y, w: 4.3, h: 0.65, fill: { color: C.cardBg }, rectRadius: 0.08 });
    slide.addText(c, { x: x + 0.15, y: y + 0.05, w: 1.8, h: 0.28, fontSize: 10, bold: true, color: C.midGreen, fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(d, { x: x + 0.15, y: y + 0.32, w: 4.0, h: 0.28, fontSize: 10, color: C.darkText, fontFace: "Trebuchet MS", margin: 0 });
  });

  // Metric callout
  slide.addShape("roundRect", { x: 0.5, y: 5.0, w: 9, h: 1.5, fill: { color: C.darkGreen }, rectRadius: 0.1 });
  slide.addText("< 50 ms", { x: 0.7, y: 5.1, w: 3, h: 0.7, fontSize: 36, bold: true, color: C.gold, fontFace: "Trebuchet MS", margin: 0 });
  slide.addText("solve time  ·  0% optimality gap  ·  proven optimal", { x: 0.7, y: 5.75, w: 8.5, h: 0.3, fontSize: 12, color: C.accent, fontFace: "Trebuchet MS", margin: 0 });
  slide.addText("Tariff-aware LED scheduling: peak LED OFF → off-peak ON. Electricity cost minimised, revenue maximised.", { x: 0.7, y: 6.1, w: 8.5, h: 0.35, fontSize: 10, color: C.lightText, fontFace: "Trebuchet MS", margin: 0 });

  footer(slide, 5, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 6 — LOGISTICS (VRP)
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slideHeader(slide, "Layer 2b — Delivery Logistics", "CVRPTW: 30 Singapore customers, Jurong depot");
  sectionTag(slide, "ACT 2");

  const metrics = [
    ["30 / 30", "customers served"],
    ["147 km",   "total route"],
    ["SGD 188.87", "logistics cost"],
    ["< 2 s",    "solve time"],
  ];
  metrics.forEach(([val, label], i) => {
    const x = 0.5 + i * 2.35;
    slide.addShape("roundRect", { x, y: 1.5, w: 2.15, h: 1.6, fill: { color: C.cardBg }, rectRadius: 0.1, shadow: makeShadow() });
    slide.addText(val, { x, y: 1.6, w: 2.15, h: 0.8, fontSize: 28, bold: true, color: C.midGreen, align: "center", fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(label, { x, y: 2.4, w: 2.15, h: 0.5, fontSize: 11, color: C.darkText, align: "center", fontFace: "Trebuchet MS", margin: 0 });
  });

  // Constraints
  const vrpNotes = [
    ["Depot", "Jurong Innovation District (1.3328°N, 103.7436°E)"],
    ["Customers", "30 SG locations: supermarkets, restaurants, hotels"],
    ["Time windows", "06:00–10:00 (supermarkets) / 10:00–14:00 (restaurants) / 08:00–11:00 (hotels)"],
    ["Fleet", "3 trucks × 200 kg capacity = 600 kg total"],
    ["Haversine", "×1.4 factor for road-network distance vs great-circle"],
  ];
  vrpNotes.forEach(([k, v], i) => {
    slide.addText(k + ":", { x: 0.5, y: 3.35 + i * 0.55, w: 1.4, h: 0.4, fontSize: 11, bold: true, color: C.midGreen, fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(v, { x: 1.9, y: 3.35 + i * 0.55, w: 7.6, h: 0.4, fontSize: 11, color: C.lightText, fontFace: "Trebuchet MS", margin: 0 });
  });

  footer(slide, 6, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 7 — LAYER 3 RL CLIMATE CONTROL
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slideHeader(slide, "Layer 3 — Climate Control", "PPO RL: autonomous environment management");
  sectionTag(slide, "ACT 2");

  // Environment targets
  const targets = [
    ["Temperature", "22°C"],
    ["Humidity",    "65%"],
    ["CO₂",         "800 ppm"],
    ["Moisture",    "0.6"],
  ];
  targets.forEach(([k, v], i) => {
    const x = 0.5 + i * 2.35;
    slide.addShape("roundRect", { x, y: 1.5, w: 2.15, h: 1.2, fill: { color: C.cardBg }, rectRadius: 0.1 });
    slide.addText(v, { x, y: 1.55, w: 2.15, h: 0.65, fontSize: 24, bold: true, color: C.midGreen, align: "center", fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(k, { x, y: 2.2, w: 2.15, h: 0.4, fontSize: 11, color: C.darkText, align: "center", fontFace: "Trebuchet MS", margin: 0 });
  });

  // Reward structure
  slide.addText("Reward function — escalating penalty weights", {
    x: 0.5, y: 2.9, w: 9, h: 0.35,
    fontSize: 13, bold: true, color: C.lightGreen, fontFace: "Trebuchet MS", margin: 0,
  });

  const penalties = [
    ["Safety violation", "×1000"],
    ["Wastewater exceedance", "×50"],
    ["Temperature deviation", "×10"],
    ["Energy waste", "×5"],
    ["Yield progress", "×1"],
  ];
  penalties.forEach(([label, weight], i) => {
    const x = 0.5 + i * 1.85;
    slide.addShape("roundRect", { x, y: 3.3, w: 1.7, h: 1.1, fill: { color: i === 0 ? C.darkGreen : C.cardBg }, rectRadius: 0.08 });
    slide.addText(weight, { x, y: 3.35, w: 1.7, h: 0.6, fontSize: 20, bold: true, color: i === 0 ? C.gold : C.midGreen, align: "center", fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(label, { x, y: 3.9, w: 1.7, h: 0.4, fontSize: 9, color: i === 0 ? C.lightText : C.darkText, align: "center", fontFace: "Trebuchet MS", margin: 0 });
  });

  slide.addText("Gymnasium simulation  ·  500K timesteps  ·  Stable-Baselines3 PPO  ·  < 1 hr training on laptop GPU", {
    x: 0.5, y: 4.65, w: 9, h: 0.35,
    fontSize: 11, color: C.lightText, fontFace: "Trebuchet MS", margin: 0,
  });

  footer(slide, 7, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 8 — LAYER 4 CUSTOMER SEGMENTATION
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slideHeader(slide, "Layer 4 — Customer Segmentation", "K-Means k=4 + UMAP: 4 behavioural clusters");
  sectionTag(slide, "ACT 2");

  const segments = [
    ["🌿 Organic Subscribers",   "≥6 orders/month · >60% organic · weekly subscription"],
    ["📦 Bulk Buyers",           ">SGD 60 basket · >40% bulk · quarterly contract"],
    ["📱 Live Commerce Fans",    ">45% live purchases · engagement-driven"],
    ["🛒 Casual Shoppers",       "<5 orders · <SGD 35 basket · retargeting targets"],
  ];

  segments.forEach(([name, desc], i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 4.7;
    const y = 1.5 + row * 1.75;
    slide.addShape("roundRect", { x, y, w: 4.3, h: 1.55, fill: { color: C.cardBg }, rectRadius: 0.1, shadow: makeShadow() });
    slide.addText(name, { x: x + 0.2, y: y + 0.15, w: 3.9, h: 0.45, fontSize: 14, bold: true, color: C.midGreen, fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(desc, { x: x + 0.2, y: y + 0.6, w: 3.9, h: 0.8, fontSize: 11, color: C.darkText, fontFace: "Trebuchet MS", margin: 0 });
  });

  // Stats bar
  slide.addShape("roundRect", { x: 0.5, y: 5.2, w: 9, h: 1.3, fill: { color: C.darkGreen }, rectRadius: 0.1 });
  slide.addText("Silhouette 0.765", { x: 0.7, y: 5.3, w: 3.5, h: 0.6, fontSize: 24, bold: true, color: C.gold, fontFace: "Trebuchet MS", margin: 0 });
  slide.addText("k=4 beats k=3 (0.698) and k=5 (0.742). UMAP preserves local + global cluster structure for dashboard scatter plot.", {
    x: 0.7, y: 5.9, w: 8.5, h: 0.5, fontSize: 11, color: C.lightText, fontFace: "Trebuchet MS", margin: 0,
  });

  footer(slide, 8, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 9 — TYPHOON SCENARIO (compressed)
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slideHeader(slide, "Typhoon Resilience Cascade", "Press the button. Watch every layer respond.");
  sectionTag(slide, "ACT 2");

  const steps = [
    ["⏱ Press Typhoon", "Delivery window 12h → 6h. 30% grid outage probability."],
    ["🔋 UPS Activates", "4-hour battery. Red countdown banner. RL agent forced OFF."],
    ["🌾 Emergency Harvest", "MILP re-solves. 12 crops early-harvested. Cold storage ON."],
    ["📈 Demand Surge", "+20% applied to tomorrow (rainy-day consumer behaviour)."],
  ];

  steps.forEach(([title, desc], i) => {
    const y = 1.5 + i * 1.0;
    slide.addShape("roundRect", { x: 0.5, y, w: 5.8, h: 0.85, fill: { color: i === 1 ? C.darkGreen : C.cardBg }, rectRadius: 0.08 });
    slide.addText(title, { x: 0.7, y: y + 0.08, w: 5.4, h: 0.35, fontSize: 13, bold: true, color: i === 1 ? C.gold : C.midGreen, fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(desc, { x: 0.7, y: y + 0.43, w: 5.4, h: 0.35, fontSize: 11, color: i === 1 ? C.lightText : C.darkText, fontFace: "Trebuchet MS", margin: 0 });
  });

  // Right side — metrics
  slide.addShape("roundRect", { x: 6.6, y: 1.5, w: 2.9, h: 3.9, fill: { color: C.darkGreen }, rectRadius: 0.1 });
  slide.addText("Cascade Metrics", { x: 6.8, y: 1.6, w: 2.5, h: 0.4, fontSize: 12, bold: true, color: C.accent, fontFace: "Trebuchet MS", margin: 0 });

  const metrics = [
    ["Window", "12h → 6h"],
    ["Outage risk", "30%"],
    ["UPS life", "4 hours"],
    ["Crops saved", "12 tiers"],
    ["Demand", "+20%"],
    ["MILP re-solve", "< 50 ms"],
  ];
  metrics.forEach(([k, v], i) => {
    slide.addText(k + ":", { x: 6.8, y: 2.1 + i * 0.55, w: 1.3, h: 0.35, fontSize: 10, bold: true, color: C.lightGreen, fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(v, { x: 8.1, y: 2.1 + i * 0.55, w: 1.2, h: 0.35, fontSize: 10, color: C.lightText, fontFace: "Trebuchet MS", margin: 0 });
  });

  slide.addText("This is not a delivery delay simulator. Every layer re-optimises autonomously.", {
    x: 0.5, y: 5.55, w: 9, h: 0.4,
    fontSize: 12, italic: true, color: C.lightGreen, fontFace: "Trebuchet MS", margin: 0,
  });

  footer(slide, 9, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 10 — GOVERNANCE FRAMEWORK (NEW)
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slide.background = { color: C.darkGreen };

  // Top accent
  slide.addShape("rect", { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.accent }, line: { color: C.accent } });

  // Section tag
  slide.addShape("rect", { x: 0.5, y: 0.2, w: 2.8, h: 0.28, fill: { color: C.accent }, rectRadius: 0.05 });
  slide.addText("ACT 2.5  ·  GOVERNANCE", { x: 0.5, y: 0.2, w: 2.8, h: 0.28, fontSize: 9, bold: true, color: C.darkGreen, align: "center", fontFace: "Trebuchet MS", margin: 0 });

  // Title
  slide.addText("Governance Framework", {
    x: 0.5, y: 0.6, w: 9, h: 0.7,
    fontSize: 34, bold: true, color: C.lightText, fontFace: "Trebuchet MS", margin: 0,
  });
  slide.addText("Production readiness — not just a demo. 13 of 14 MGMT 655 phases complete.", {
    x: 0.5, y: 1.25, w: 9, h: 0.4,
    fontSize: 14, color: C.accent, fontFace: "Trebuchet MS", margin: 0,
  });

  // 2×2 Grid of governance pillars
  const pillars = [
    {
      icon: "🛡",
      title: "Phase 7 Red-Team",
      lines: [
        "38 adversarial tests",
        "15 scenarios × 6 layers",
        "100% passing",
        "",
        "Data poisoning · Prompt injection",
        "Constraint stress · Reward hacking",
      ],
      tag: "GATE 3 PASS",
      tagColor: C.accent,
    },
    {
      icon: "🚦",
      title: "Phase 8 Deployment Gate",
      lines: [
        "5 gates × 25 criteria",
        "4 PASS · 1 CONDITIONAL",
        "Conditional ship for pilot",
        "",
        "Technical · Business · Risk",
        "Compliance · Monitoring",
      ],
      tag: "GATE 5 PASS",
      tagColor: C.accent,
    },
    {
      icon: "⚖",
      title: "Phase 5 Implications Audit",
      lines: [
        "6 stakeholders mapped",
        "1 HIGH bias identified",
        "Mitigation in Gate 4",
        "",
        "Farm workers: automation anxiety",
        "Mitigated via Advisory mode",
      ],
      tag: "GATE 4 PASS",
      tagColor: C.accent,
    },
    {
      icon: "📊",
      title: "Phase 13 Drift Monitor",
      lines: [
        "14 checks × 3 drift types",
        "KS tests · Reward drift",
        "Ready for Phase 1 prod",
        "",
        "Feature · Performance · Concept",
        "YAML-scheduled hourly to weekly",
      ],
      tag: "14 CHECKS ACTIVE",
      tagColor: C.gold,
    },
  ];

  pillars.forEach((p, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 4.7;
    const y = 1.85 + row * 2.25;

    slide.addShape("roundRect", { x, y, w: 4.3, h: 2.05, fill: { color: C.cardBg }, rectRadius: 0.1, shadow: makeShadow() });

    // Icon + Title
    slide.addText(p.icon + "  " + p.title, {
      x: x + 0.2, y: y + 0.12, w: 3.9, h: 0.45,
      fontSize: 14, bold: true, color: C.midGreen, fontFace: "Trebuchet MS", margin: 0,
    });

    // Lines
    slide.addText(
      p.lines.filter(l => l).map((l, idx, arr) => ({
        text: l,
        options: { breakLine: idx < arr.filter(x => x).length - 1 },
      })),
      { x: x + 0.25, y: y + 0.6, w: 3.8, h: 1.1, fontSize: 10, color: C.darkText, fontFace: "Trebuchet MS" }
    );

    // Tag badge
    slide.addShape("rect", { x: x + 0.15, y: y + 1.72, w: 1.55, h: 0.25, fill: { color: p.tagColor }, line: { color: p.tagColor } });
    slide.addText(p.tag, { x: x + 0.15, y: y + 1.72, w: 1.55, h: 0.25, fontSize: 8, bold: true, color: C.darkGreen, align: "center", fontFace: "Trebuchet MS", margin: 0 });
  });

  // Bottom banner
  slide.addShape("roundRect", { x: 0.5, y: 6.45, w: 9, h: 0.55, fill: { color: C.midGreen }, rectRadius: 0.08 });
  slide.addText("Retrospective documentation (analyze + redteam × 4 phases) — time-constrained but transparent", {
    x: 0.7, y: 6.5, w: 8.6, h: 0.4,
    fontSize: 11, italic: true, color: C.lightText, fontFace: "Trebuchet MS", margin: 0,
  });

  footer(slide, 10, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 11 — SUSTAINABILITY
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slideHeader(slide, "Sustainability — Live Computed", "95% less water · 87% less CO₂");
  sectionTag(slide, "ACT 3");

  const metrics = [
    ["95%", "less water vs.\nconventional farming", "2 L/kg vs 20 L/kg\nAVA Singapore 2019"],
    ["87%", "less CO₂ vs.\nconventional farming", "0.3 vs 2.5 kg-CO₂/kg\nSFA 2023 lifecycle analysis"],
  ];
  metrics.forEach(([val, headline, source], i) => {
    const x = 0.5 + i * 4.7;
    slide.addShape("roundRect", { x, y: 1.5, w: 4.3, h: 3.5, fill: { color: C.cardBg }, rectRadius: 0.12, shadow: makeShadow() });
    slide.addText(val, { x, y: 1.65, w: 4.3, h: 1.0, fontSize: 56, bold: true, color: C.midGreen, align: "center", fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(headline, { x: x + 0.2, y: 2.7, w: 3.9, h: 0.9, fontSize: 13, color: C.darkText, align: "center", fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(source, { x: x + 0.2, y: 3.7, w: 3.9, h: 1.1, fontSize: 10, italic: true, color: C.lightGreen, align: "center", fontFace: "Trebuchet MS", margin: 0 });
  });

  slide.addText("Computed live from Layer 2 plan: LED schedule × rack count × watering frequency × engineering formulas. Not hardcoded.", {
    x: 0.5, y: 5.2, w: 9, h: 0.5,
    fontSize: 11, italic: true, color: C.lightText, fontFace: "Trebuchet MS", margin: 0,
  });

  footer(slide, 11, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 12 — LAYER 5 RAG MEDIA AI
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slideHeader(slide, "Layer 5 — Investor Q&A", "RAG: ChromaDB + sentence-transformers + Claude");
  sectionTag(slide, "ACT 2");

  const tech = [
    ["ChromaDB", "Local vector DB · 50 docs · MMR search"],
    ["MiniLM-L6-v2", "384-dim embeddings · 22M params · local"],
    ["Claude Haiku", "$0.25/1M tokens · 200K context · Constitutional AI"],
    ["Demo Mode", "Pre-cached answers when API unavailable"],
  ];
  tech.forEach(([k, v], i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 4.7;
    const y = 1.5 + row * 1.2;
    slide.addShape("roundRect", { x, y, w: 4.3, h: 1.0, fill: { color: C.cardBg }, rectRadius: 0.08 });
    slide.addText(k, { x: x + 0.2, y: y + 0.1, w: 3.9, h: 0.35, fontSize: 13, bold: true, color: C.midGreen, fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(v, { x: x + 0.2, y: y + 0.45, w: 3.9, h: 0.45, fontSize: 11, color: C.darkText, fontFace: "Trebuchet MS", margin: 0 });
  });

  slide.addText("Example queries answered live:", {
    x: 0.5, y: 4.0, w: 9, h: 0.35,
    fontSize: 13, bold: true, color: C.lightGreen, fontFace: "Trebuchet MS", margin: 0,
  });

  const queries = [
    "Where is the farm located? → Jurong Innovation District, 15km from CBD",
    "How much water do you save? → 95% less than conventional (2 L/kg vs 20 L/kg)",
    "Is it pesticide-free? → Yes — integrated pest management, zero pesticide residue",
    "Do you have food safety certification? → HACCP plan in progress, SFA inspection Q3",
  ];
  queries.forEach((q, i) => {
    slide.addText(q, {
      x: 0.5, y: 4.4 + i * 0.52, w: 9, h: 0.42,
      fontSize: 10, color: C.lightText, fontFace: "Trebuchet MS", margin: 0,
    });
  });

  footer(slide, 12, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 13 — BUSINESS MODEL
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slideHeader(slide, "Business Model", "B2B SaaS + B2C subscription + AI licensing");
  sectionTag(slide, "ACT 3");

  const streams = [
    ["B2B SaaS",    "Farm OS License", "SGD 8K/rack/year",    "SGD 480K ARR"],
    ["B2C Boxes",   "Subscription boxes", "15% GMV commission",  "SGD 180K ARR"],
    ["AI Licensing", "Model licensing",  "One-time + support",  "SGD 60K ARR"],
  ];
  streams.forEach(([type, model, price, arr], i) => {
    const y = 1.5 + i * 1.15;
    slide.addShape("roundRect", { x: 0.5, y, w: 5.5, h: 1.0, fill: { color: C.cardBg }, rectRadius: 0.1 });
    slide.addText(type, { x: 0.7, y: y + 0.1, w: 2.0, h: 0.35, fontSize: 13, bold: true, color: C.midGreen, fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(model, { x: 0.7, y: y + 0.45, w: 2.5, h: 0.35, fontSize: 11, color: C.darkText, fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(price, { x: 3.0, y: y + 0.1, w: 1.5, h: 0.35, fontSize: 12, bold: true, color: C.darkText, fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(arr, { x: 4.5, y: y + 0.1, w: 1.4, h: 0.35, fontSize: 12, bold: true, color: C.midGreen, fontFace: "Trebuchet MS", margin: 0 });
  });

  // Unit economics box
  slide.addShape("roundRect", { x: 6.3, y: 1.5, w: 3.2, h: 3.5, fill: { color: C.darkGreen }, rectRadius: 0.1 });
  slide.addText("Unit Economics", { x: 6.5, y: 1.6, w: 2.8, h: 0.4, fontSize: 13, bold: true, color: C.accent, fontFace: "Trebuchet MS", margin: 0 });

  const econ = [
    ["ACV",        "SGD 8,000/rack/yr"],
    ["Farm size",  "20 racks"],
    ["Gross margin","82%"],
    ["Payback",    "11 months"],
    ["CAC/LTV",    "0.15"],
  ];
  econ.forEach(([k, v], i) => {
    slide.addText(k + ":", { x: 6.5, y: 2.1 + i * 0.55, w: 1.4, h: 0.35, fontSize: 11, bold: true, color: C.lightGreen, fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(v, { x: 7.9, y: 2.1 + i * 0.55, w: 1.5, h: 0.35, fontSize: 11, color: C.lightText, fontFace: "Trebuchet MS", margin: 0 });
  });

  slide.addShape("rect", { x: 0.5, y: 5.15, w: 9, h: 0.04, fill: { color: C.accent }, line: { color: C.accent } });
  slide.addText("Total Year 1 ARR: SGD 720K", {
    x: 0.5, y: 5.25, w: 9, h: 0.5,
    fontSize: 22, bold: true, color: C.gold, fontFace: "Trebuchet MS", margin: 0,
  });

  footer(slide, 13, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 14 — GO-TO-MARKET
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slideHeader(slide, "Go-to-Market", "Phase 1 pilot → Phase 2 scale → Phase 3 licensing");
  sectionTag(slide, "ACT 3");

  const phases = [
    { num: "Phase 1", title: "Pilot", sub: "3 farms · Jurong/Lim Chu Kang/Woodlands", detail: "20% equity · SGD 80K · 12 weeks", color: C.accent },
    { num: "Phase 2", title: "Scale", sub: "10 farms · SG + Malaysia", detail: "SGD 500K ARR · B2C subscription", color: C.lightGreen },
    { num: "Phase 3", title: "APAC", sub: "AI model licensing", detail: "SFA national monitoring partnership", color: C.midGreen },
  ];
  phases.forEach((p, i) => {
    const x = 0.5 + i * 3.1;
    slide.addShape("roundRect", { x, y: 1.5, w: 2.9, h: 3.8, fill: { color: C.cardBg }, rectRadius: 0.12, shadow: makeShadow() });
    slide.addShape("rect", { x, y: 1.5, w: 2.9, h: 0.6, fill: { color: p.color }, line: { color: p.color } });
    slide.addText(p.num, { x, y: 1.55, w: 2.9, h: 0.5, fontSize: 14, bold: true, color: C.darkGreen, align: "center", fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(p.title, { x, y: 2.25, w: 2.9, h: 0.55, fontSize: 22, bold: true, color: C.midGreen, align: "center", fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(p.sub, { x: x + 0.15, y: 2.9, w: 2.6, h: 0.8, fontSize: 11, color: C.darkText, align: "center", fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(p.detail, { x: x + 0.15, y: 3.75, w: 2.6, h: 0.7, fontSize: 11, bold: true, color: C.midGreen, align: "center", fontFace: "Trebuchet MS", margin: 0 });
  });

  slide.addText("Swiss competitor Greenphyto entered Singapore January 2025. ACTF fund open. First-mover advantage in AI-native farm OS.", {
    x: 0.5, y: 5.55, w: 9, h: 0.45,
    fontSize: 12, italic: true, color: C.lightGreen, fontFace: "Trebuchet MS", margin: 0,
  });

  footer(slide, 14, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 15 — TRACTION
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slideHeader(slide, "Traction", "Evidence of technical and commercial readiness");
  sectionTag(slide, "ACT 4");

  const stats = [
    ["434", "tests passing"],
    ["0.765", "silhouette score"],
    ["30/30", "VRP customers served"],
    ["< 50 ms", "MILP solve time"],
  ];
  stats.forEach(([val, label], i) => {
    const x = 0.5 + i * 2.35;
    slide.addShape("roundRect", { x, y: 1.5, w: 2.15, h: 1.6, fill: { color: C.cardBg }, rectRadius: 0.1, shadow: makeShadow() });
    slide.addText(val, { x, y: 1.6, w: 2.15, h: 0.8, fontSize: 28, bold: true, color: C.midGreen, align: "center", fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(label, { x, y: 2.4, w: 2.15, h: 0.5, fontSize: 11, color: C.darkText, align: "center", fontFace: "Trebuchet MS", margin: 0 });
  });

  // Test suite breakdown
  slide.addShape("roundRect", { x: 0.5, y: 3.35, w: 4.5, h: 3.1, fill: { color: C.cardBg }, rectRadius: 0.1 });
  slide.addText("Test Suite — 434 tests", { x: 0.7, y: 3.45, w: 4.1, h: 0.4, fontSize: 13, bold: true, color: C.midGreen, fontFace: "Trebuchet MS", margin: 0 });

  const testLines = [
    ["Unit tests", "Tier 1 · mocking allowed · < 1s"],
    ["Adversarial tests", "Tier 1 · 38 hostile-input scenarios"],
    ["Governance tests", "Tier 1 · deployment gate criteria"],
    ["Drift tests", "Tier 1 · 22 monitoring checks"],
    ["Monitoring tests", "Tier 1 · 14 drift checks"],
  ];
  testLines.forEach(([k, v], i) => {
    slide.addText(k + ":", { x: 0.7, y: 3.9 + i * 0.5, w: 1.8, h: 0.35, fontSize: 10, bold: true, color: C.darkText, fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(v, { x: 2.5, y: 3.9 + i * 0.5, w: 2.3, h: 0.35, fontSize: 10, color: C.lightGreen, fontFace: "Trebuchet MS", margin: 0 });
  });

  // Decision log
  slide.addShape("roundRect", { x: 5.2, y: 3.35, w: 4.3, h: 3.1, fill: { color: C.darkGreen }, rectRadius: 0.1 });
  slide.addText("Decision Log — 26 decisions", { x: 5.4, y: 3.45, w: 3.9, h: 0.4, fontSize: 13, bold: true, color: C.accent, fontFace: "Trebuchet MS", margin: 0 });

  const dlLines = [
    ["Design decisions", "26 documented"],
    ["Retrospective docs", "8 (analyze + redteam × 4)"],
    ["Phases completed", "13 of 14 MGMT 655"],
    ["Drift checks", "14 across 6 layers"],
    ["Implications", "6 stakeholders × 3 categories"],
  ];
  dlLines.forEach(([k, v], i) => {
    slide.addText(k + ":", { x: 5.4, y: 3.9 + i * 0.5, w: 2.2, h: 0.35, fontSize: 10, bold: true, color: C.lightGreen, fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(v, { x: 7.6, y: 3.9 + i * 0.5, w: 1.8, h: 0.35, fontSize: 10, color: C.lightText, fontFace: "Trebuchet MS", margin: 0 });
  });

  footer(slide, 15, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 16 — THE ASK
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slideHeader(slide, "The Ask", "Phase 1 Pilot — 3 farms, 12 weeks, SGD 80K");
  sectionTag(slide, "ACT 4");

  // Deal terms
  const terms = [
    ["Amount",      "SGD 80,000"],
    ["Equity",      "20%"],
    ["Duration",    "12 weeks"],
    ["Farms",       "3 pilot farms"],
    ["Purpose",     "Hardware + dataset + monitoring infra"],
  ];
  terms.forEach(([k, v], i) => {
    const y = 1.5 + i * 0.72;
    slide.addShape("roundRect", { x: 0.5, y, w: 4.3, h: 0.62, fill: { color: i === 0 ? C.darkGreen : C.cardBg }, rectRadius: 0.08 });
    slide.addText(k, { x: 0.7, y: y + 0.12, w: 1.8, h: 0.38, fontSize: 12, bold: true, color: i === 0 ? C.lightGreen : C.midGreen, fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(v, { x: 2.5, y: y + 0.12, w: 2.1, h: 0.38, fontSize: 13, bold: true, color: i === 0 ? C.gold : C.darkText, fontFace: "Trebuchet MS", margin: 0 });
  });

  // Use of funds
  slide.addShape("roundRect", { x: 5.2, y: 1.5, w: 4.3, h: 3.65, fill: { color: C.darkGreen }, rectRadius: 0.1 });
  slide.addText("Use of Funds", { x: 5.4, y: 1.6, w: 3.9, h: 0.4, fontSize: 13, bold: true, color: C.accent, fontFace: "Trebuchet MS", margin: 0 });

  const uses = [
    ["Hardware sensors", "SGD 25K"],
    ["SG training data", "SGD 20K"],
    ["Monitoring infra", "SGD 15K"],
    ["Pilot operations", "SGD 12K"],
    ["Contingency",      "SGD 8K"],
  ];
  uses.forEach(([k, v], i) => {
    slide.addText(k, { x: 5.4, y: 2.1 + i * 0.6, w: 2.6, h: 0.38, fontSize: 12, color: C.lightText, fontFace: "Trebuchet MS", margin: 0 });
    slide.addText(v, { x: 8.0, y: 2.1 + i * 0.6, w: 1.3, h: 0.38, fontSize: 12, bold: true, color: C.gold, fontFace: "Trebuchet MS", margin: 0 });
  });

  // What happens next
  slide.addText("What happens next", {
    x: 0.5, y: 5.3, w: 9, h: 0.4,
    fontSize: 13, bold: true, color: C.lightGreen, fontFace: "Trebuchet MS", margin: 0,
  });
  const next = [
    "Week 2: Install sensors on 3 pilot farms",
    "Week 6: First Singapore-specific model retraining",
    "Week 12: Governance review → Phase 2 decision gate",
  ];
  next.forEach((step, i) => {
    slide.addText(step, { x: 0.5, y: 5.75 + i * 0.4, w: 9, h: 0.35, fontSize: 11, color: C.lightText, fontFace: "Trebuchet MS", margin: 0 });
  });

  footer(slide, 16, TOTAL);
});

// ═══════════════════════════════════════════════════════════════════════════════
// SLIDE 17 — THANK YOU
// ═══════════════════════════════════════════════════════════════════════════════
addSlide(slide => {
  slide.background = { color: C.darkGreen };

  slide.addShape("rect", { x: 0, y: 0, w: 10, h: 0.08, fill: { color: C.accent }, line: { color: C.accent } });
  slide.addShape("rect", { x: 0, y: 7.42, w: 10, h: 0.08, fill: { color: C.accent }, line: { color: C.accent } });

  slide.addText("Thank you", {
    x: 0.5, y: 1.8, w: 9, h: 1.0,
    fontSize: 56, bold: true, color: C.lightText, align: "center", fontFace: "Trebuchet MS", margin: 0,
  });

  slide.addShape("rect", { x: 3.5, y: 2.95, w: 3, h: 0.05, fill: { color: C.gold }, line: { color: C.gold } });

  slide.addText("GreenLoop F2C — Farm-to-Consumer Vertical Hydroponics OS", {
    x: 0.5, y: 3.2, w: 9, h: 0.5,
    fontSize: 14, color: C.accent, align: "center", fontFace: "Trebuchet MS", margin: 0,
  });

  slide.addText([
    { text: "Takahide Kawabe  ·  QN  ·  Claude AI agent", options: { breakLine: true } },
    { text: "MGMT 655 — AI & Machine Learning  |  Week 8 Capstone  |  2026-04-24", options: { breakLine: true } },
    { text: "github.com/michitaka16/Greenloop-F2C", options: {} },
  ], {
    x: 0.5, y: 3.9, w: 9, h: 1.5,
    fontSize: 12, color: C.lightGreen, align: "center", fontFace: "Trebuchet MS",
  });

  slide.addText("🌿 Grow smarter. Plan faster. Ship everywhere.", {
    x: 0.5, y: 5.6, w: 9, h: 0.5,
    fontSize: 16, italic: true, color: C.accent, align: "center", fontFace: "Trebuchet MS", margin: 0,
  });

  footer(slide, 17, TOTAL);
});

// ── Write ────────────────────────────────────────────────────────────────────
const outPath = path.resolve(__dirname, "../deliverables/GreenLoop_Pitch_Deck_v3.pptx");
pptx.writeFile({ fileName: outPath })
  .then(() => console.log("✓ Written:", outPath))
  .catch(e => { console.error(e); process.exit(1); });
