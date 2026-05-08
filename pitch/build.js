// Adopt a Kale v3 — Self-grow pivot
// "80% of Singaporeans want to grow their own. They can't." narrative
// Adopt a Cow demoted to Why Now proof point. Slide 4 = SG Garden Gap analysis.

const pptxgen = require("pptxgenjs");
const path = require("path");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3" × 7.5"
pres.author = "Queenie · Takahide · Dingyao";
pres.title = "Adopt a Kale — Singapore's AI-managed garden share";

// ===== Design tokens =====
const C = {
  bg: "FFFFFF", paper: "FAF7F0", cream: "F8F4EC",
  ink: "1A1A1A", muted: "6B7280", hairline: "E5E1D8",
  kale: "2D5016", leaf: "7BA05B", lime: "C7E66B", coral: "E07856",
};
const F = { head: "Calibri", body: "Calibri", mono: "Consolas" };
const W = 13.3, H = 7.5, M = 0.7;

const ASSETS = path.join(__dirname, "assets");
const LEAF = {
  dark:         path.join(ASSETS, "leaf-dark.png"),
  mid:          path.join(ASSETS, "leaf-mid.png"),
  lime:         path.join(ASSETS, "leaf-lime.png"),
  outline_lime: path.join(ASSETS, "leaf-outline-lime.png"),
  outline_mid:  path.join(ASSETS, "leaf-outline-mid.png"),
};

function brandMark(slide, opts = {}) {
  const onDark = opts.onDark || false;
  slide.addImage({
    path: onDark ? LEAF.lime : LEAF.dark,
    x: W - M - 2.0, y: 0.27, w: 0.32, h: 0.38,
  });
  slide.addText("ADOPT A KALE", {
    x: W - M - 1.6, y: 0.36, w: 1.6, h: 0.22,
    fontSize: 9, color: onDark ? C.lime : C.kale, bold: true,
    fontFace: F.head, charSpacing: 3, margin: 0,
  });
}
function header(slide, num, label) {
  slide.addText([
    { text: `${num}`, options: { color: C.coral, bold: true, fontFace: F.head } },
    { text: `   ${label}`, options: { color: C.muted, fontFace: F.head, charSpacing: 4 } },
  ], { x: M, y: 0.4, w: 8, h: 0.4, fontSize: 11, margin: 0 });
}
function footer(slide) {
  slide.addText("greenloop.f2c", {
    x: M, y: H - 0.4, w: 4, h: 0.25,
    fontSize: 8, color: C.muted, fontFace: F.body, charSpacing: 2, margin: 0,
  });
}
function pageFrame(slide, num, label) { header(slide, num, label); brandMark(slide); footer(slide); }
function bigTitle(slide, text, y = 1.0, color = C.ink) {
  slide.addText(text, {
    x: M, y, w: W - 2*M, h: 1.7,
    fontSize: 48, bold: true, color, fontFace: F.head,
    valign: "top", margin: 0,
  });
}

// ============================================================
// SLIDE 1 — TITLE
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.bg };

  s.addImage({ path: LEAF.dark, x: 8.4, y: 0.9, w: 4.0, h: 4.8 });
  s.addImage({ path: LEAF.lime, x: 7.2, y: 4.0, w: 1.8, h: 2.16, transparency: 15 });

  s.addImage({ path: LEAF.dark, x: M, y: 0.55, w: 0.35, h: 0.42 });
  s.addText("ADOPT A KALE", {
    x: M + 0.45, y: 0.65, w: 4, h: 0.3,
    fontSize: 13, color: C.kale, bold: true, fontFace: F.head, charSpacing: 6, margin: 0,
  });

  s.addText("Adopt", {
    x: M, y: 1.7, w: 8, h: 1.5,
    fontSize: 100, bold: true, color: C.kale, fontFace: F.head, margin: 0,
  });
  s.addText("a Kale.", {
    x: M, y: 3.0, w: 8, h: 1.5,
    fontSize: 100, bold: true, color: C.kale, fontFace: F.head, margin: 0,
  });

  s.addText("Singapore's first AI-managed garden share.", {
    x: M, y: 4.6, w: 8, h: 0.5,
    fontSize: 22, italic: true, color: C.coral, fontFace: F.head, margin: 0,
  });
  s.addText("Your vegetables. Grown by AI. Eaten by you.", {
    x: M, y: 5.15, w: 8, h: 0.4,
    fontSize: 16, color: C.ink, fontFace: F.body, margin: 0,
  });

  s.addShape(pres.shapes.LINE, { x: M, y: H - 1.5, w: W - 2*M, h: 0, line: { color: C.hairline, width: 1 }});
  s.addText("MGMT 655   ·   Capstone Pitch   ·   May 14, 2026", {
    x: M, y: H - 1.35, w: 8, h: 0.3,
    fontSize: 10, color: C.muted, fontFace: F.body, charSpacing: 4, margin: 0,
  });
  s.addText("Queenie   ·   Takahide KAWABE   ·   Dingyao CHU", {
    x: M, y: H - 1.0, w: 9, h: 0.3,
    fontSize: 14, color: C.ink, bold: true, fontFace: F.head, margin: 0,
  });
}

// ============================================================
// SLIDE 2 — PROBLEM (reframed: garden gap, not gifting gap)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  pageFrame(s, "01", "THE PROBLEM");

  bigTitle(s, "80% of Singaporeans want to grow\ntheir own food. They can't.", 1.0);

  s.addText("HDB life means no garden. Allotment plots are ballot-only. Smart kits die in tropical heat. The result: 90% imported produce, anonymous and disconnected.", {
    x: M, y: 3.2, w: W - 2*M, h: 0.7,
    fontSize: 16, color: C.muted, italic: true, fontFace: F.body, margin: 0,
  });

  const cardY = 4.3, cardH = 2.3, cardW = 3.85, gap = 0.25;
  const cards = [
    { tag: "NO SPACE", h: "Apartment life.", body: "80% of Singaporeans live in HDB flats. No garden. Corridor gardening is restricted to 1.2m clearance — and the sun rarely cooperates." },
    { tag: "NO ACCESS", h: "Allotment ballots.", body: "Just 2,400 NParks plots for 5.9M people. Allocated by lottery. 3-year lease. Demand structurally exceeds supply." },
    { tag: "NO HELP",   h: "Devices that die.", body: "Click & Grow needs care + electricity. Tropical humidity wrecks them. No quality guarantee. No help when plants fail." },
  ];
  cards.forEach((card, i) => {
    const x = M + i*(cardW + gap);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: cardY, w: cardW, h: cardH,
      fill: { color: C.paper }, line: { color: C.paper },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: cardY, w: cardW, h: 0.06,
      fill: { color: C.coral }, line: { color: C.coral },
    });
    s.addText(card.tag, {
      x: x + 0.3, y: cardY + 0.3, w: cardW - 0.6, h: 0.3,
      fontSize: 10, bold: true, color: C.coral, fontFace: F.head, charSpacing: 6, margin: 0,
    });
    s.addText(card.h, {
      x: x + 0.3, y: cardY + 0.65, w: cardW - 0.6, h: 0.6,
      fontSize: 22, bold: true, color: C.ink, fontFace: F.head, margin: 0,
    });
    s.addText(card.body, {
      x: x + 0.3, y: cardY + 1.4, w: cardW - 0.6, h: 0.85,
      fontSize: 12, color: C.ink, fontFace: F.body, margin: 0,
    });
  });
}

// ============================================================
// SLIDE 3 — WHY NOW (Garden Gap + Wellness + Proven Model + Policy)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  pageFrame(s, "02", "WHY NOW");

  bigTitle(s, "Four forces converge\nin 2026.", 1.0);

  s.addText("Singapore's structural housing reality + dietary shift + proven business model + government tailwind.", {
    x: M, y: 3.2, w: W - 2*M, h: 0.5,
    fontSize: 16, italic: true, color: C.muted, fontFace: F.body, margin: 0,
  });

  const colY = 4.0, colH = 2.7, colW = 2.85, colGap = 0.25;
  const cols = [
    { tag: "GARDEN GAP",   stat: "80%",      label: "HDB residents",        body: "80% of Singaporeans in HDB flats with no garden. NParks allotments are ballot-only. Structural unmet demand to grow your own." },
    { tag: "WELLNESS",     stat: "Now",      label: "SG diet shift",        body: "Microgreens, kale, edible flowers, herbs trending in SG diet. Premium produce as wellness signal. Post-COVID home-grown surge." },
    { tag: "PROVEN MODEL", stat: "KKR\n+DCP",label: "Adopt a Cow B-round", body: "KKR + DCP backed Adopt a Cow's named-adoption model in China. We apply ownership mechanics to daily-consumption produce in SG." },
    { tag: "POLICY",       stat: "30%",      label: "30 by 30 target",      body: "SG targets 30% local production by 2030 (currently <10%). S$309M research fund. NParks 'Gardening with Edibles' free seed initiative." },
  ];
  cols.forEach((c, i) => {
    const x = M + i*(colW + colGap);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: colY, w: colW, h: colH,
      fill: { color: C.kale }, line: { color: C.kale },
    });
    s.addText(c.tag, {
      x: x + 0.3, y: colY + 0.3, w: colW - 0.6, h: 0.3,
      fontSize: 10, bold: true, color: C.lime, fontFace: F.head, charSpacing: 6, margin: 0,
    });
    s.addText(c.stat, {
      x: x + 0.3, y: colY + 0.7, w: colW - 0.6, h: 0.85,
      fontSize: c.stat.includes("\n") ? 30 : 44, bold: true, color: C.bg, fontFace: F.head,
      valign: "top", margin: 0,
    });
    s.addText(c.label, {
      x: x + 0.3, y: colY + 1.65, w: colW - 0.6, h: 0.3,
      fontSize: 12, bold: true, color: C.bg, fontFace: F.head, margin: 0,
    });
    s.addText(c.body, {
      x: x + 0.3, y: colY + 2.0, w: colW - 0.6, h: 0.65,
      fontSize: 9.5, color: C.lime, fontFace: F.body, margin: 0,
    });
  });
}

// ============================================================
// SLIDE 4 — INSIGHT (NEW: SG Garden Gap analysis, not Adopt a Cow)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  pageFrame(s, "03", "INSIGHT");

  bigTitle(s, "Singapore's garden gap.\nNobody fills it.", 1.0);

  s.addText("Allotment, Click & Grow, Sustenir, corridor gardening — each solves part. None solve all.", {
    x: M, y: 3.2, w: W - 2*M, h: 0.5,
    fontSize: 16, italic: true, color: C.muted, fontFace: F.body, margin: 0,
  });

  // Left table: 4 alternatives × what they have / what they lack
  const tblX = M, tblY = 3.95, tblW = 7.4;
  const rowH = 0.62;

  // Header row
  s.addShape(pres.shapes.LINE, { x: tblX, y: tblY, w: tblW, h: 0, line: { color: C.kale, width: 1.5 }});
  s.addText("ALTERNATIVE", {
    x: tblX, y: tblY + 0.08, w: 2.2, h: 0.3,
    fontSize: 9, bold: true, color: C.kale, fontFace: F.head, charSpacing: 4, margin: 0,
  });
  s.addText("WHAT IT HAS", {
    x: tblX + 2.2, y: tblY + 0.08, w: 2.5, h: 0.3,
    fontSize: 9, bold: true, color: C.kale, fontFace: F.head, charSpacing: 4, margin: 0,
  });
  s.addText("WHAT'S MISSING", {
    x: tblX + 4.7, y: tblY + 0.08, w: 2.7, h: 0.3,
    fontSize: 9, bold: true, color: C.coral, fontFace: F.head, charSpacing: 4, margin: 0,
  });
  s.addShape(pres.shapes.LINE, { x: tblX, y: tblY + 0.42, w: tblW, h: 0, line: { color: C.hairline, width: 0.5 }});

  const alts = [
    { name: "NParks allotment",    has: "Real plot, ownership", miss: "Ballot-only · 3-yr lease · weather-exposed · ~2,400 plots only" },
    { name: "Click & Grow / kits", has: "Home control",         miss: "Tropical humidity kills them · requires care · no expertise" },
    { name: "Sustenir / NTUC",     has: "Convenience, fresh",   miss: "No ownership · no story · no choice · same as supermarket" },
    { name: "HDB corridor",        has: "Free, simple",         miss: "1.2m clearance rule · limited sun · hobbyist-scale only" },
  ];
  const rowY0 = tblY + 0.5;
  alts.forEach((a, i) => {
    const y = rowY0 + i*rowH;
    if (i % 2 === 0) {
      s.addShape(pres.shapes.RECTANGLE, {
        x: tblX, y, w: tblW, h: rowH,
        fill: { color: C.cream, transparency: 50 }, line: { color: C.cream, transparency: 100 },
      });
    }
    s.addText(a.name, {
      x: tblX + 0.05, y: y + 0.08, w: 2.15, h: rowH - 0.16,
      fontSize: 12, bold: true, color: C.ink, fontFace: F.head, valign: "middle", margin: 0,
    });
    s.addText(a.has, {
      x: tblX + 2.25, y: y + 0.08, w: 2.4, h: rowH - 0.16,
      fontSize: 10, color: C.muted, fontFace: F.body, valign: "middle", margin: 0,
    });
    s.addText(a.miss, {
      x: tblX + 4.7, y: y + 0.08, w: 2.7, h: rowH - 0.16,
      fontSize: 10, color: C.coral, fontFace: F.body, valign: "middle", margin: 0,
    });
    s.addShape(pres.shapes.LINE, { x: tblX, y: y + rowH, w: tblW, h: 0, line: { color: C.hairline, width: 0.3 }});
  });

  // Right card: "Adopt a Kale fills the gap"
  const cX = M + 7.9, cY = 3.95, cW = W - M - cX, cH = 3.0;
  s.addShape(pres.shapes.RECTANGLE, {
    x: cX, y: cY, w: cW, h: cH,
    fill: { color: C.kale }, line: { color: C.kale },
  });
  s.addImage({
    path: LEAF.lime,
    x: cX + cW - 1.05, y: cY + 0.25, w: 0.85, h: 1.02,
    transparency: 30,
  });
  s.addText("ADOPT A KALE", {
    x: cX + 0.3, y: cY + 0.3, w: cW - 1.4, h: 0.3,
    fontSize: 10, bold: true, color: C.lime, fontFace: F.head, charSpacing: 6, margin: 0,
  });
  s.addText("All four,\nin one plot.", {
    x: cX + 0.3, y: cY + 0.65, w: cW - 0.6, h: 1.0,
    fontSize: 24, bold: true, color: C.bg, fontFace: F.head, valign: "top", margin: 0,
  });
  s.addText([
    { text: "Real ownership", options: { bold: true, color: C.lime, breakLine: true } },
    { text: "Zero space — vertical farm slot", options: { color: C.bg, fontSize: 11, breakLine: true } },
    { text: "Zero effort — AI does the work", options: { color: C.bg, fontSize: 11, breakLine: true } },
    { text: "Real choice — multi-crop", options: { color: C.bg, fontSize: 11 } },
  ], {
    x: cX + 0.3, y: cY + 1.95, w: cW - 0.6, h: 1.0,
    fontSize: 11, fontFace: F.body, margin: 0, paraSpaceAfter: 2,
  });
}

// ============================================================
// SLIDE 5 — SOLUTION (Sarah, self-eat narrative)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  pageFrame(s, "04", "THE SOLUTION");

  bigTitle(s, "Meet Sarah. Her HDB.\nHer kale. Her dinner.", 1.0);

  s.addText("Sarah lives in a 4-room HDB in Tanglin. No garden. She wants fresh kale, basil, and edible flowers for her family meals. GreenLoop runs her vertical-farm patch — automatically.", {
    x: M, y: 3.2, w: W - 2*M - 1, h: 0.7,
    fontSize: 16, italic: true, color: C.muted, fontFace: F.body, margin: 0,
  });

  const steps = [
    { n: "01", t: "Diagnose", d: "Watches her plot 24/7" },
    { n: "02", t: "Forecast", d: "Predicts harvest schedule" },
    { n: "03", t: "Optimise", d: "Times harvest for Sunday" },
    { n: "04", t: "Control",  d: "Premium-grade kale auto" },
    { n: "05", t: "Deliver",  d: "Saturday morning fresh box" },
    { n: "06", t: "Promote",  d: "WhatsApp updates <500ms" },
  ];
  const sY = 4.3, sH = 1.55, sW = 1.95, sGap = 0.05;
  steps.forEach((step, i) => {
    const x = M + i*(sW + sGap);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: sY, w: sW, h: sH,
      fill: { color: C.bg }, line: { color: C.hairline, width: 1 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: sY, w: sW, h: 0.05,
      fill: { color: C.leaf }, line: { color: C.leaf },
    });
    s.addText(step.n, {
      x: x + 0.2, y: sY + 0.2, w: sW - 0.4, h: 0.25,
      fontSize: 9, color: C.coral, bold: true, fontFace: F.mono, charSpacing: 4, margin: 0,
    });
    s.addText(step.t, {
      x: x + 0.2, y: sY + 0.5, w: sW - 0.4, h: 0.4,
      fontSize: 18, bold: true, color: C.kale, fontFace: F.head, margin: 0,
    });
    s.addText(step.d, {
      x: x + 0.2, y: sY + 0.95, w: sW - 0.4, h: 0.55,
      fontSize: 10, color: C.ink, fontFace: F.body, margin: 0,
    });
  });

  const qY = 6.05;
  s.addShape(pres.shapes.RECTANGLE, {
    x: M, y: qY, w: W - 2*M, h: 0.8,
    fill: { color: C.cream }, line: { color: C.cream },
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: M, y: qY, w: 0.06, h: 0.8,
    fill: { color: C.coral }, line: { color: C.coral },
  });
  s.addText([
    { text: "SARAH TAN", options: { bold: true, color: C.coral, charSpacing: 4 } },
    { text: "    Marketing Director, Tanglin", options: { color: C.muted } },
  ], {
    x: M + 0.25, y: qY + 0.1, w: W - 2*M - 0.5, h: 0.25,
    fontSize: 9, fontFace: F.head, margin: 0,
  });
  s.addText("\u201CI always wanted my own garden. HDB life made it impossible. I named my plot, watched my kale grow, and now I cook with it every Sunday. The birthday gift was a bonus.\u201D", {
    x: M + 0.25, y: qY + 0.35, w: W - 2*M - 0.5, h: 0.4,
    fontSize: 12, color: C.ink, italic: true, fontFace: F.body, margin: 0,
  });
}

// ============================================================
// SLIDE 6 — PRODUCT
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  pageFrame(s, "05", "PRODUCT");

  bigTitle(s, "Six AI layers. Invisible.\nEvery meal, perfect.", 1.0);

  const tX = M, tY = 3.3, tW = W - 2*M;
  const colWs = [0.7, 1.7, 1.4, 3.0, 5.1];
  const headers = ["#", "LAYER", "WEEK", "AI · COURSE CONCEPT", "VALUE FOR SARAH"];
  const rowsP = [
    ["01","Diagnose","Wk 7","EfficientNet · Transfer Learning","Catches stress before Sarah's kale wilts · alerts via app"],
    ["02","Forecast","Wk 5","XGBoost + K-means · Supervised + Unsupervised ML","Predicts harvest schedule · auto-plants her next preferred crop"],
    ["03","Optimise","Wk 4","OR-Tools MILP · Hard Constraints","Times harvest exactly for Sunday dinner · 48ms solve"],
    ["04","Control", "Wk 7","PPO RL · Reinforcement Learning","Premium-grade kale every cycle · climate auto-tuned"],
    ["05","Deliver", "Wk 4","OR-Tools VRP · Vehicle Routing","Saturday morning fresh box · time-window precise"],
    ["06","Promote", "Wk 6","RAG-grounded LLM · Retrieval Augmentation","Sarah asks 'how's my kale?' on WhatsApp · <500ms answer"],
  ];

  let cx = tX;
  s.addShape(pres.shapes.LINE, { x: tX, y: tY, w: tW, h: 0, line: { color: C.kale, width: 1.5 }});
  headers.forEach((h, i) => {
    s.addText(h, {
      x: cx, y: tY + 0.1, w: colWs[i], h: 0.35,
      fontSize: 9, bold: true, color: C.kale, fontFace: F.head, charSpacing: 4, margin: 0,
    });
    cx += colWs[i];
  });
  s.addShape(pres.shapes.LINE, { x: tX, y: tY + 0.5, w: tW, h: 0, line: { color: C.hairline, width: 0.5 }});

  const rowY0 = tY + 0.55;
  const rowH = 0.55;
  rowsP.forEach((row, i) => {
    const y = rowY0 + i*rowH;
    if (i % 2 === 0) {
      s.addShape(pres.shapes.RECTANGLE, {
        x: tX, y, w: tW, h: rowH,
        fill: { color: C.cream, transparency: 50 }, line: { color: C.cream, transparency: 100 },
      });
    }
    let cx2 = tX;
    row.forEach((cell, j) => {
      let opts = {
        x: cx2 + 0.05, y: y + 0.05, w: colWs[j] - 0.1, h: rowH - 0.1,
        fontSize: 10, color: C.ink, fontFace: F.body, valign: "middle", margin: 0,
      };
      if (j === 0) { opts.color = C.coral; opts.bold = true; opts.fontFace = F.mono; }
      if (j === 1) { opts.bold = true; opts.color = C.kale; }
      if (j === 2) { opts.color = C.muted; opts.fontSize = 9; }
      if (j === 3) { opts.color = C.muted; opts.fontSize = 10; }
      if (j === 4) { opts.color = C.ink; opts.fontSize = 11; }
      s.addText(cell, opts);
      cx2 += colWs[j];
    });
    s.addShape(pres.shapes.LINE, { x: tX, y: y + rowH, w: tW, h: 0, line: { color: C.hairline, width: 0.3 }});
  });
}

// ============================================================
// SLIDE 7 — BUSINESS MODEL (self-eat tier framing)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  pageFrame(s, "06", "BUSINESS MODEL");

  bigTitle(s, "Three tiers. One brand.", 1.0);

  s.addText("Adopt a Cow's ownership ladder, applied to weekly self-grown produce. Plus corporate wellness as anchor revenue.", {
    x: M, y: 2.7, w: W - 2*M, h: 0.5,
    fontSize: 16, italic: true, color: C.muted, fontFace: F.body, margin: 0,
  });

  const tY = 3.5, tH = 3.0, tW = 2.95, tGap = 0.2;
  const tiers = [
    { tag: "CLOUD",  price: "S$10",  unit: "/ month", body: "Virtual herb plot. Live camera. Weekly micro-harvest sample.",   note: "Entry tier · low-friction trial",  color: C.leaf,  leafImg: LEAF.mid },
    { tag: "JOINT",  price: "S$80",  unit: "/ month", body: "Shared kale slot. Weekly home delivery. Choose 2 crops.",      note: "Most popular · weekly meals",      color: C.kale,  leafImg: LEAF.dark },
    { tag: "REAL",   price: "S$200", unit: "/ month", body: "Dedicated multi-crop rack. Weekly delivery. Choose 4–5 crops.", note: "Premium tier · serious cooks",     color: C.coral, leafImg: LEAF.dark },
  ];
  tiers.forEach((t, i) => {
    const x = M + i*(tW + tGap);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: tY, w: tW, h: tH,
      fill: { color: C.bg }, line: { color: C.hairline, width: 1 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: tY, w: 0.08, h: tH,
      fill: { color: t.color }, line: { color: t.color },
    });
    s.addImage({
      path: t.leafImg,
      x: x + tW - 0.7, y: tY + 0.25, w: 0.5, h: 0.6,
      transparency: i === 2 ? 70 : 60,
    });
    s.addText(t.tag, {
      x: x + 0.35, y: tY + 0.3, w: tW - 0.6, h: 0.3,
      fontSize: 10, bold: true, color: t.color, fontFace: F.head, charSpacing: 6, margin: 0,
    });
    s.addText([
      { text: t.price, options: { fontSize: 44, bold: true, color: C.ink, fontFace: F.head } },
      { text: ` ${t.unit}`, options: { fontSize: 12, color: C.muted, fontFace: F.body } },
    ], { x: x + 0.35, y: tY + 0.7, w: tW - 0.6, h: 0.85, margin: 0 });
    s.addText(t.body, {
      x: x + 0.35, y: tY + 1.7, w: tW - 0.6, h: 0.7,
      fontSize: 13, color: C.ink, fontFace: F.body, margin: 0,
    });
    s.addText(t.note, {
      x: x + 0.35, y: tY + 2.5, w: tW - 0.6, h: 0.35,
      fontSize: 10, italic: true, color: C.muted, fontFace: F.body, margin: 0,
    });
  });

  {
    const x = M + 3*(tW + tGap);
    const cw = W - M - x;
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: tY, w: cw, h: tH,
      fill: { color: C.kale }, line: { color: C.kale },
    });
    s.addImage({
      path: LEAF.lime,
      x: x + cw - 0.85, y: tY + 0.3, w: 0.65, h: 0.78,
      transparency: 40,
    });
    s.addText("CORPORATE", {
      x: x + 0.3, y: tY + 0.3, w: cw - 1.0, h: 0.3,
      fontSize: 10, bold: true, color: C.lime, fontFace: F.head, charSpacing: 6, margin: 0,
    });
    s.addText([
      { text: "S$5K", options: { fontSize: 44, bold: true, color: C.bg, fontFace: F.head } },
      { text: "+", options: { fontSize: 24, color: C.lime, fontFace: F.head } },
    ], { x: x + 0.3, y: tY + 0.7, w: cw - 0.6, h: 0.85, margin: 0 });
    s.addText("/ bulk order", {
      x: x + 0.3, y: tY + 1.45, w: cw - 0.6, h: 0.3,
      fontSize: 12, color: C.lime, fontFace: F.body, margin: 0,
    });
    s.addText("50–200 named slots / company. Employee wellness program. Recurring B2B2C revenue.", {
      x: x + 0.3, y: tY + 1.85, w: cw - 0.6, h: 0.65,
      fontSize: 11, color: C.bg, fontFace: F.body, margin: 0,
    });
    s.addText("Phase 1: 5–10 clients", {
      x: x + 0.3, y: tY + 2.55, w: cw - 0.6, h: 0.3,
      fontSize: 10, italic: true, color: C.lime, fontFace: F.body, margin: 0,
    });
  }
}

// ============================================================
// SLIDE 8 — UNIT ECONOMICS (with verified competitor failures)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  pageFrame(s, "07", "UNIT ECONOMICS");

  bigTitle(s, "Premium prices.\nSoftware margins.", 1.0);

  s.addText("Where IFFI failed (May 2024). Where Apollo failed (judicial mgmt 2024). Where Sustenir lost years to break-even.", {
    x: M, y: 3.0, w: W - 2*M, h: 0.5,
    fontSize: 14, italic: true, color: C.coral, fontFace: F.head, margin: 0,
  });

  const sY = 3.85, sH = 1.4, sW = 2.95, sGap = 0.05;
  const stats = [
    { n: "S$1.2K", l: "LTV (12-mo / customer)", note: "S$80–200/mo, recurring food spend" },
    { n: "S$50",   l: "CAC (target)",            note: "Organic + paid social, SG focus" },
    { n: "<2 mo",  l: "Payback period",          note: "Stripe captures fee day 1" },
    { n: ">65%",   l: "Gross margin",            note: "Premium D2C, no Shopee fee" },
  ];
  stats.forEach((st, i) => {
    const x = M + i*(sW + sGap);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: sY, w: sW, h: sH,
      fill: { color: C.cream }, line: { color: C.cream },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: sY, w: sW, h: 0.05,
      fill: { color: C.coral }, line: { color: C.coral },
    });
    s.addText(st.n, {
      x: x + 0.3, y: sY + 0.2, w: sW - 0.6, h: 0.6,
      fontSize: 32, bold: true, color: C.kale, fontFace: F.head, margin: 0,
    });
    s.addText(st.l, {
      x: x + 0.3, y: sY + 0.85, w: sW - 0.6, h: 0.25,
      fontSize: 10, bold: true, color: C.ink, fontFace: F.head, charSpacing: 2, margin: 0,
    });
    s.addText(st.note, {
      x: x + 0.3, y: sY + 1.1, w: sW - 0.6, h: 0.25,
      fontSize: 9, color: C.muted, fontFace: F.body, margin: 0,
    });
  });

  s.addText("Why this works where SG vertical farms failed:", {
    x: M, y: 5.45, w: W - 2*M, h: 0.3,
    fontSize: 12, bold: true, color: C.ink, fontFace: F.head, margin: 0,
  });

  const fY = 5.85, fH = 1.2, fW = 2.95, fGap = 0.05;
  const fails = [
    { tag: "OLD WHOLESALE", n: "5–15%",       d: "Margin too low for vertical-farm energy cost (IFFI, 2024)" },
    { tag: "NO D2C",        n: "Lost margin", d: "Couldn't capture full margin via wholesalers (Apollo, 2024)" },
    { tag: "NO RECURRING",  n: "One-shot",    d: "No subscription = no LTV. Every sale starts from zero." },
    { tag: "LTV : CAC",     n: "24 : 1",      d: "Premium D2C subscription + AI quality + customer data — defensible" },
  ];
  fails.forEach((f, i) => {
    const x = M + i*(fW + fGap);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: fY, w: fW, h: fH,
      fill: { color: C.kale }, line: { color: C.kale },
    });
    s.addText(f.tag, {
      x: x + 0.25, y: fY + 0.15, w: fW - 0.5, h: 0.25,
      fontSize: 9, bold: true, color: C.lime, fontFace: F.head, charSpacing: 4, margin: 0,
    });
    s.addText(f.n, {
      x: x + 0.25, y: fY + 0.4, w: fW - 0.5, h: 0.4,
      fontSize: 18, bold: true, color: C.bg, fontFace: F.head, margin: 0,
    });
    s.addText(f.d, {
      x: x + 0.25, y: fY + 0.8, w: fW - 0.5, h: 0.35,
      fontSize: 9, color: C.lime, fontFace: F.body, margin: 0,
    });
  });
}

// ============================================================
// SLIDE 9 — GTM (HDB-resident framing)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  pageFrame(s, "08", "GO-TO-MARKET");

  bigTitle(s, "Wedge: Crowdfunding.\nThen SG. Then ASEAN.", 1.0);

  s.addText("Three phases. Crowdfunding builds founding gardener community + first revenue (Adopt a Cow playbook). Then scale.", {
    x: M, y: 3.2, w: W - 2*M, h: 0.5,
    fontSize: 14, italic: true, color: C.muted, fontFace: F.body, margin: 0,
  });

  const pY = 3.95, pH = 3.0, pW = 3.95, pGap = 0.2;
  const phases = [
    { tag: "PHASE 1", time: "0–6 months", title: "SG D2C launch",
      bullets: [
        "Kickstarter SG / Indiegogo (Adopt-a-Cow style)",
        "Target: 200 HDB households pre-sold in month 1",
        "1 partner farm (Greenphyto / Sustenir candidate)",
        "50 slots live · 100 paying households",
      ],
      out: "MRR S$10k+ · founding gardeners established" },
    { tag: "PHASE 2", time: "6–18 months", title: "SG scale + corporate",
      bullets: [
        "Scale to 500 slots · 2nd partner farm",
        "Launch Real tier (S$200/mo) · multi-crop choice",
        "10+ corporate wellness clients",
        "TikTok / Insta organic content engine",
      ],
      out: "MRR S$50–100k · brand recognition in SG" },
    { tag: "PHASE 3", time: "18+ months", title: "ASEAN expansion",
      bullets: [
        "Bangkok · Jakarta · Kuala Lumpur localized",
        "Premium auction tier (saffron · rare herbs)",
        "Brand collabs (SIA in-flight, Raffles wellness)",
        "Series A funding round",
      ],
      out: "First-mover named-grow brand in ASEAN" },
  ];

  phases.forEach((ph, i) => {
    const x = M + i*(pW + pGap);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: pY, w: pW, h: pH,
      fill: { color: C.kale }, line: { color: C.kale },
    });
    s.addText(ph.tag, {
      x: x + 0.3, y: pY + 0.25, w: pW - 0.6, h: 0.25,
      fontSize: 10, bold: true, color: C.lime, fontFace: F.head, charSpacing: 6, margin: 0,
    });
    s.addText(ph.time, {
      x: x + 0.3, y: pY + 0.5, w: pW - 0.6, h: 0.25,
      fontSize: 10, color: C.lime, italic: true, fontFace: F.body, margin: 0,
    });
    s.addText(ph.title, {
      x: x + 0.3, y: pY + 0.8, w: pW - 0.6, h: 0.5,
      fontSize: 20, bold: true, color: C.bg, fontFace: F.head, margin: 0,
    });
    s.addShape(pres.shapes.LINE, {
      x: x + 0.3, y: pY + 1.35, w: pW - 0.6, h: 0,
      line: { color: C.leaf, width: 0.5 },
    });
    const bullets = ph.bullets.map((b, j) => ({
      text: b, options: { bullet: { code: "25A0" }, breakLine: j < ph.bullets.length - 1 },
    }));
    s.addText(bullets, {
      x: x + 0.3, y: pY + 1.45, w: pW - 0.6, h: 1.2,
      fontSize: 10.5, color: C.bg, fontFace: F.body,
      paraSpaceAfter: 4, margin: 0,
    });
    s.addText(ph.out, {
      x: x + 0.3, y: pY + 2.65, w: pW - 0.6, h: 0.3,
      fontSize: 10, italic: true, color: C.lime, bold: true, fontFace: F.body, margin: 0,
    });
  });
}

// ============================================================
// SLIDE 10 — DEMO (Sarah's plot, multi-crop)
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  pageFrame(s, "09", "DEMO");

  bigTitle(s, "Sarah's app.\nRunning today.", 1.0);

  const mX = M, mY = 3.2, mW = 4.5, mH = 3.7;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: mX, y: mY, w: mW, h: mH,
    fill: { color: C.kale }, line: { color: C.kale }, rectRadius: 0.18,
  });
  const iX = mX + 0.2, iY = mY + 0.25, iW = mW - 0.4, iH = mH - 0.5;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: iX, y: iY, w: iW, h: iH,
    fill: { color: C.bg }, line: { color: C.bg }, rectRadius: 0.08,
  });
  s.addText("SARAH'S PLOT", {
    x: iX + 0.3, y: iY + 0.2, w: iW - 0.6, h: 0.25,
    fontSize: 9, color: C.coral, bold: true, fontFace: F.head, charSpacing: 4, margin: 0,
  });
  s.addText("Plot #042  ·  Day 31 of 42", {
    x: iX + 0.3, y: iY + 0.45, w: iW - 0.6, h: 0.25,
    fontSize: 10, color: C.muted, fontFace: F.body, margin: 0,
  });

  s.addImage({ path: LEAF.dark, x: iX + iW/2 - 0.7, y: iY + 0.8, w: 1.4, h: 1.68 });

  s.addText("74% mature", {
    x: iX, y: iY + 2.55, w: iW, h: 0.3,
    fontSize: 14, bold: true, color: C.kale, align: "center", fontFace: F.head, margin: 0,
  });
  s.addText("Curly kale + Thai basil  ·  ready May 28", {
    x: iX + 0.3, y: iY + 2.85, w: iW - 0.6, h: 0.25,
    fontSize: 10, color: C.muted, align: "center", fontFace: F.body, margin: 0,
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: iX + 0.3, y: iY + 3.15, w: iW - 0.6, h: 0.3,
    fill: { color: C.cream }, line: { color: C.cream }, rectRadius: 0.05,
  });
  s.addText("\u2713 Auto-tuned 06:00 SGT  ·  next harvest May 28", {
    x: iX + 0.3, y: iY + 3.15, w: iW - 0.6, h: 0.3,
    fontSize: 9, color: C.kale, bold: true, align: "center", fontFace: F.body, margin: 0,
  });

  const rX = M + 5.0;
  const rW = W - M - rX;
  s.addText("WHAT WORKS TODAY", {
    x: rX, y: 3.2, w: rW, h: 0.3,
    fontSize: 10, bold: true, color: C.coral, fontFace: F.head, charSpacing: 6, margin: 0,
  });

  const features = [
    { k: "Live AI control",    v: "PPO RL agent · 500K training steps · climate auto-tuned per crop" },
    { k: "Optimisation",       v: "OR-Tools MILP · 48ms solve · 5 hard constraints" },
    { k: "Fault recovery",     v: "Power-outage rollback in <250ms · 5 deployment gates" },
    { k: "Customer Q&A",       v: "RAG-grounded LLM · <500ms answer · Sarah asks on WhatsApp" },
    { k: "Quality assurance",  v: "434 unit tests · 38 adversarial tests · production-grade" },
  ];

  features.forEach((f, i) => {
    const y = 3.65 + i*0.72;
    s.addText(f.k, {
      x: rX, y, w: rW, h: 0.3,
      fontSize: 14, bold: true, color: C.kale, fontFace: F.head, margin: 0,
    });
    s.addText(f.v, {
      x: rX, y: y + 0.3, w: rW, h: 0.4,
      fontSize: 11, color: C.muted, fontFace: F.body, margin: 0,
    });
  });
}

// ============================================================
// SLIDE 11 — MOAT
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  pageFrame(s, "10", "MOAT");

  bigTitle(s, "Four ways we hold this.\nNot a feature — a defense.", 1.0);

  s.addText("Each layer alone is replicable. Combined, they compound. None of these can be built by a software-only startup or a Sustenir clone.", {
    x: M, y: 3.2, w: W - 2*M, h: 0.5,
    fontSize: 14, italic: true, color: C.muted, fontFace: F.body, margin: 0,
  });

  const gY = 4.0, gW = 5.95, gH = 1.25, gGapX = 0.15, gGapY = 0.15;
  const moats = [
    { n: "01", t: "BRAND",          h: "First-mover in named-grow", b: "Adopt a Cow scaled to 2.566B CNY revenue (2021) on this exact playbook. We're 6–18 months ahead in SG named-grow. Story + name + ownership cannot be retroactively built." },
    { n: "02", t: "AI QUALITY",     h: "Where SG farms keep failing", b: "IFFI ceased ops May 2024. Apollo in judicial mgmt. Sustenir lost years before profit. PPO RL + 24/7 CV deliver consistent quality others can't match." },
    { n: "03", t: "DATA FLYWHEEL",  h: "Customer behavior compounds",b: "Every harvest = behavioral data (preference · timing · variety). K-means → better crop recommendations → higher LTV. Adopt a Cow had this; SG farms don't." },
    { n: "04", t: "NETWORK EFFECT", h: "Volume → variety → volume",  b: "More customers → more crop variety viable → more reasons to subscribe. Corporate clients lock recurring revenue. Each cohort makes the next easier to land." },
  ];
  moats.forEach((m, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = M + col*(gW + gGapX);
    const y = gY + row*(gH + gGapY);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: gW, h: gH,
      fill: { color: C.bg }, line: { color: C.hairline, width: 1 },
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.06, h: gH,
      fill: { color: C.coral }, line: { color: C.coral },
    });
    s.addText(`${m.n}    ${m.t}`, {
      x: x + 0.25, y: y + 0.18, w: gW - 0.5, h: 0.3,
      fontSize: 10, bold: true, color: C.coral, fontFace: F.head, charSpacing: 4, margin: 0,
    });
    s.addText(m.h, {
      x: x + 0.25, y: y + 0.45, w: gW - 0.5, h: 0.3,
      fontSize: 16, bold: true, color: C.kale, fontFace: F.head, margin: 0,
    });
    s.addText(m.b, {
      x: x + 0.25, y: y + 0.78, w: gW - 0.5, h: 0.45,
      fontSize: 9.5, color: C.ink, fontFace: F.body, margin: 0,
    });
  });

  s.addText("Plus: 434 unit tests   ·   38 adversarial tests   ·   5 deployment gates   ·   power-outage recovery <250ms   —   production-grade governance under the experience.", {
    x: M, y: H - 0.7, w: W - 2*M, h: 0.3,
    fontSize: 9.5, italic: true, color: C.muted, fontFace: F.body, margin: 0,
  });
}

// ============================================================
// SLIDE 12 — TEAM
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.bg };
  pageFrame(s, "11", "TEAM");

  bigTitle(s, "Three founders. One brand.", 1.0);

  s.addText("Each founder owns one face of the brand end-to-end.", {
    x: M, y: 2.5, w: W - 2*M, h: 0.4,
    fontSize: 14, italic: true, color: C.muted, fontFace: F.body, margin: 0,
  });

  const tY = 3.3, tH = 3.5, tW = 3.95, tGap = 0.2;
  const team = [
    { initial: "Q", name: "Queenie",         role: "Brand & GTM",   owns: "Customer segmentation · Brand voice", domain: "Consumer marketing, premium gifting market knowledge, brand storytelling. Designs how Sarah finds, falls for, and refers GreenLoop." },
    { initial: "T", name: "Takahide KAWABE", role: "Product & AI",  owns: "PPO RL · MILP · RAG-LLM",            domain: "Six-layer AI orchestration, customer-facing app, technical integration. Owns the technology that makes premium quality consistent." },
    { initial: "D", name: "Dingyao CHU",     role: "Ops & Finance", owns: "Multi-objective optimisation · Unit econ", domain: "Unit economics, partner farm contracts, capital strategy. Holds 65% gross margin and 24:1 LTV/CAC." },
  ];
  team.forEach((p, i) => {
    const x = M + i*(tW + tGap);
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: tY, w: tW, h: tH,
      fill: { color: C.cream }, line: { color: C.cream },
    });
    s.addShape(pres.shapes.OVAL, {
      x: x + 0.4, y: tY + 0.4, w: 1.0, h: 1.0,
      fill: { color: C.kale }, line: { color: C.kale },
    });
    s.addText(p.initial, {
      x: x + 0.4, y: tY + 0.4, w: 1.0, h: 1.0,
      fontSize: 36, bold: true, color: C.lime, align: "center", valign: "middle", fontFace: F.head, margin: 0,
    });
    s.addText(p.name, {
      x: x + 0.4, y: tY + 1.55, w: tW - 0.8, h: 0.35,
      fontSize: 16, bold: true, color: C.ink, fontFace: F.head, margin: 0,
    });
    s.addText(p.role, {
      x: x + 0.4, y: tY + 1.9, w: tW - 0.8, h: 0.3,
      fontSize: 12, bold: true, color: C.coral, fontFace: F.head, charSpacing: 3, margin: 0,
    });
    s.addText("OWNS", {
      x: x + 0.4, y: tY + 2.35, w: tW - 0.8, h: 0.2,
      fontSize: 8, bold: true, color: C.muted, fontFace: F.head, charSpacing: 4, margin: 0,
    });
    s.addText(p.owns, {
      x: x + 0.4, y: tY + 2.55, w: tW - 0.8, h: 0.35,
      fontSize: 10, color: C.kale, bold: true, fontFace: F.body, margin: 0,
    });
    s.addText(p.domain, {
      x: x + 0.4, y: tY + 2.95, w: tW - 0.8, h: 0.5,
      fontSize: 9.5, color: C.ink, fontFace: F.body, margin: 0,
    });
  });
}

// ============================================================
// SLIDE 13 — CLOSING
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: C.kale };
  brandMark(s, { onDark: true });

  s.addImage({
    path: LEAF.outline_lime,
    x: 8.6, y: 1.0, w: 4.0, h: 4.8,
    transparency: 20,
  });

  s.addText("Adopt", {
    x: M, y: 1.7, w: 8, h: 1.5,
    fontSize: 100, bold: true, color: C.bg, fontFace: F.head, margin: 0,
  });
  s.addText("a Kale.", {
    x: M, y: 3.0, w: 8, h: 1.5,
    fontSize: 100, bold: true, color: C.bg, fontFace: F.head, margin: 0,
  });

  s.addText("Singapore's first AI-managed garden share.", {
    x: M, y: 4.6, w: 8, h: 0.5,
    fontSize: 22, italic: true, color: C.lime, fontFace: F.head, margin: 0,
  });

  s.addText("Your perspective on our moat, our unit economics, and our wedge.   Thank you.", {
    x: M, y: 5.8, w: W - 2*M, h: 0.4,
    fontSize: 14, color: C.lime, fontFace: F.body, margin: 0,
  });

  s.addShape(pres.shapes.LINE, {
    x: M, y: H - 1.2, w: W - 2*M, h: 0,
    line: { color: C.leaf, width: 0.5 },
  });
  s.addText("Queenie   ·   Takahide KAWABE   ·   Dingyao CHU", {
    x: M, y: H - 1.0, w: W - 2*M, h: 0.4,
    fontSize: 14, color: C.bg, bold: true, fontFace: F.head, margin: 0,
  });
}

pres.writeFile({ fileName: path.join(__dirname, "output", "AdoptAKale.pptx") }).then(f => {
  console.log("Wrote", f);
});
