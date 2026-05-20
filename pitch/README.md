# Adopt a Kale — Pitch Deck

**Singapore's first AI-managed garden share.** MGMT 655 Capstone (Adopt a Kale, formerly GreenLoop F2C). May 14, 2026 提出。

13 スライドのプログラム的に生成されるピッチデッキ。pptxgenjs でビルド、custom curly-kale leaf SVG → PNG via sharp、ビルド後に SHA-256 で画像重複を排除してスリム化。

---

## クイックスタート

```bash
# 1. 依存をインストール
npm install

# 2. デッキをビルド + スリム化 (output/AdoptAKale.pptx を生成)
npm run all

# 3. (任意) PDF も生成 — 要 LibreOffice
npm run pdf
```

`output/AdoptAKale.pptx` を PowerPoint / Keynote / LibreOffice で開いてください。

### 個別スクリプト

| コマンド | 用途 |
|---|---|
| `npm run leaves` | ケール葉 PNG を再生成 (色や形を変えるとき) |
| `npm run build`  | デッキを生成 (約 1.5MB) |
| `npm run slim`   | 画像重複を排除 (約 290KB に圧縮) |
| `npm run pdf`    | PDF にエクスポート (LibreOffice 必要) |
| `npm run all`    | build → slim を一括実行 |

---

## ディレクトリ構成

```
adopt-a-kale/
├── README.md          ← この文書
├── package.json
├── build.js           ← メインのデッキ生成 (~700 行 / 13 スライド)
├── leaves.js          ← ケール葉 SVG → PNG 変換
├── slim.js            ← 画像重複排除 (post-build)
├── .gitignore
├── assets/            ← ケール葉 PNG (5 ファイル, 各 ~70KB)
│   ├── leaf-dark.png            濃いケール (主にロゴ)
│   ├── leaf-mid.png             中間色 (Cloud tier)
│   ├── leaf-lime.png            ライム色 (アクセント)
│   ├── leaf-outline-lime.png    アウトラインのみ (Closing slide 用)
│   └── leaf-outline-mid.png     アウトラインのみ (予備)
└── output/            ← gitignore 対象。ビルド成果物。
    └── AdoptAKale.pptx
```

---

## デザイントークン

`build.js` 冒頭の `C` (color) と `F` (font) を編集すれば全スライドに反映されます。

```js
const C = {
  bg:       "FFFFFF",   // 背景 (白)
  paper:    "FAF7F0",   // 紙色 (Problem カード等)
  cream:    "F8F4EC",   // クリーム (Team カード, テーブル偶数行)
  ink:      "1A1A1A",   // 本文
  muted:    "6B7280",   // キャプション
  hairline: "E5E1D8",   // 罫線

  kale:     "2D5016",   // ★ 主色 — 濃いケール緑
  leaf:     "7BA05B",   // ★ 副色 — 中間ケール緑
  lime:     "C7E66B",   // ★ アクセント — ライム緑
  coral:    "E07856",   // ★ ギフト/温かみ — コーラル
};
const F = { head: "Calibri", body: "Calibri", mono: "Consolas" };
```

サイズ: `LAYOUT_WIDE` (13.3" × 7.5"), 外周マージン `M = 0.7"`。

---

## 13 スライド構成 (v3 — self-grow ナラティブ)

| # | セクション | タイトル | 主要メッセージ |
|---|---|---|---|
| 1 | (Title) | Adopt a Kale. | "Singapore's first AI-managed garden share." / "Your vegetables. Grown by AI. Eaten by you." |
| 2 | 01 PROBLEM | "80% of Singaporeans want to grow their own food. They can't." | NO SPACE / NO ACCESS / NO HELP |
| 3 | 02 WHY NOW | "Four forces converge in 2026." | GARDEN GAP (80%) / WELLNESS / PROVEN MODEL (KKR+DCP) / POLICY (30 by 30) |
| 4 | 03 INSIGHT | "Singapore's garden gap. Nobody fills it." | Allotment / Click & Grow / Sustenir / HDB corridor の限界 → "All four, in one plot" |
| 5 | 04 SOLUTION | "Meet Sarah. Her HDB. Her kale. Her dinner." | Sarah が自分で食べるストーリー (ギフトはおまけ) |
| 6 | 05 PRODUCT | "Six AI layers. Invisible. Every meal, perfect." | 6 層 AI × 各週コース概念 × Value for Sarah |
| 7 | 06 BUSINESS MODEL | "Three tiers. One brand." | Cloud (S$10) / Joint (S$80) / Real (S$200) / Corporate (S$5K+) |
| 8 | 07 UNIT ECONOMICS | "Premium prices. Software margins." | LTV S$1.2K · CAC S$50 · <2mo payback · >65% margin · 24:1 LTV:CAC |
| 9 | 08 GO-TO-MARKET | "Wedge: Crowdfunding. Then SG. Then ASEAN." | 3 フェーズ (0-6mo / 6-18mo / 18+mo) |
| 10 | 09 DEMO | "Sarah's app. Running today." | 電話風 UI モックアップ + 5 production stat |
| 11 | 10 MOAT | "Four ways we hold this." | Brand / AI Quality (vs IFFI/Apollo) / Data Flywheel / Network Effect |
| 12 | 11 TEAM | "Three founders. One brand." | Q (Brand & GTM) · T (Product & AI) · D (Ops & Finance) |
| 13 | (Closing) | Adopt a Kale. | クロージング、葉のアウトライン |

---

## チーム

```
Q  Queenie         · Brand & GTM      · Customer segmentation · Brand voice
T  Takahide KAWABE · Product & AI     · PPO RL · MILP · RAG-LLM
D  Dingyao CHU     · Ops & Finance    · Multi-objective optimisation · Unit econ
```

---

## 検証済みファクト (web search 確認済み — ハルシネーション禁止)

ピッチで使用している全ての具体的な数字・固有名詞は出典あり。書き換える際は必ず再検証してください。

### Singapore market
- **80% HDB 居住** — PropertyGuru / Public Libraries SG
- **NParks ~2,400 allotment plots** (28 parks), **抽選 (ballot) 配分**, 3-year lease — gardeningsg.nparks.gov.sg
- **NParks "Gardening with Edibles" 無料種子配布** — 公式
- **1,900+ コミュニティ・ガーデン**, HDB エステートの 80% が食用作物栽培
- **30 by 30 policy** (2030 年に 30% 国産化目標, 現状 <10%) — Bloomberg / Japan Times 2024
- **S$309M research fund** for 30 by 30 — 同
- **DBS 銀行 150 名社内園芸クラブ** — DBS Live More 公式

### SG vertical farm failures
- **IFFI ceased operations 2024年5月** — therunway.ventures (S$39.4M SFA grant 受領後失敗)
- **Apollo Aquaculture** (Temasek backed) **2024 judicial management 入り** — Bloomberg
- **Sustenir** profitable "in next 6 months" but only after years of losses — Bloomberg/Japan Times 2024
- **Sustenir grows kale, curly kale, spinach, arugula in SG** — TOMRA case study

### Adopt a Cow (China analog)
- **2.566B CNY 2021 revenue**
- **B-round: KKR + DCP Capital + Meituan** (Dec 2021)
- **Yili & Mengniu duopoly 85.7% → cracked**
- **IPO 2024 年 2 月撤回** (申請は 2022 年 7 月)

### Adopt a Kale production stats
- **48ms** MILP solve time (OR-Tools)
- **434 unit tests** + **38 adversarial tests**
- **5 deployment gates**
- **<250ms** power-outage recovery
- **<500ms** RAG-LLM response
- **PPO RL 500K training steps**

---

## 開発の流れ

### スライド本文を編集する

`build.js` の各スライドブロック (`// SLIDE N — ...` コメント) を修正 → `npm run all`。

例: Slide 7 の Joint tier の価格を変える:

```js
{ tag: "JOINT",  price: "S$80",  unit: "/ month", body: "...", ... }
                          ↑ ここを変更
```

### 葉の色や形を変える

`leaves.js` の SVG パスや色を編集 → `npm run leaves` → `npm run all`。

色だけ変えるなら `leaves.js` の最後の `(async () => {...})()` ブロック内のヘックスを変更。

### スライド構成を変える (追加/削除/並び替え)

各スライドは `build.js` 内の `{ const s = pres.addSlide(); ... }` ブロックで独立しています。スライドを丸ごとコピー&ペーストして編集、削除、上下移動が可能。

### スライド番号 (header の "01", "02"...) は自動でない

`pageFrame(s, "01", "THE PROBLEM")` のように手書きで指定しています。スライドを並び替えたら手動で更新を。

---

## pptxgenjs の罠 (要注意)

過去に踏んで時間を溶かしたもの:

1. **色は `"#"` なし**: `color: "FF0000"` ✅ / `color: "#FF0000"` ❌ (ファイル破損)
2. **8文字hex色NG**: 透明度を `"00000020"` のように埋め込まない。`color` と `transparency` を分けて指定。
3. **箇条書きは `bullet: true`**: Unicode `•` を使うと二重バレットになる。
4. **画像は重複格納される**: 同じ PNG を `addImage()` で複数回呼ぶと、バイト列がそのつど複製されてファイルが肥大化。`slim.js` で post-process 必須。Claude.ai プレビューが落ちる原因。
5. **ROUNDED_RECTANGLE のオーバーレイ**: 角丸の上に矩形のアクセントバーを重ねると角からはみ出す。RECTANGLE 推奨。
6. **オプションオブジェクトの再利用 NG**: pptxgenjs はオブジェクトをミューテートする。同じ shadow オブジェクトを 2 回渡すと 2 回目が壊れる。

---

## レポジトリ配置の選択肢

このパッケージは 3 つの場所に置けます:

### A. 単独レポ (推奨)

```bash
cd ~/Documents/GitHub
mv path/to/adopt-a-kale-pitch ./
cd adopt-a-kale-pitch
git init
git add . && git commit -m "Initial pitch deck v3 (self-grow narrative)"
```

ピッチデッキは Adopt a Kale 本体とは独立した成果物。プレゼン用ファイルは Capstone 終了後もポートフォリオとして残せる。

### B. Adopt a Kale (adoptakale) リポ内のサブフォルダ

```bash
mv adopt-a-kale-pitch ~/Documents/GitHub/Greenloop-F2C/pitch
```

メインのコードベースと一緒に管理。

### C. ローカル限定 (Git なし)

そもそも commit せずに `~/Documents/adopt-a-kale-pitch/` などに置いて作業。シンプル。

---

## 次のタスク候補

ピッチ提出 (May 14) までにやれそうな改善:

1. Pitch script v8 を新ナラティブで作成 (口頭プレゼンの台本)
2. Q&A backlog を更新 — PE rep からの想定質問への新しい回答
3. ユニット計算の透明化 (S$80/月 → 顧客が受け取る kg → kgあたり単価) で Slide 8 を補強
4. "なぜ私たちは IFFI にならないか" の補強スライド追加
5. Sarah's app モックアップを multi-crop 表示に強化 (Slide 10)
6. スピーカーノート埋め込み (`slide.addNotes("...")`) — 印刷用 PDF 生成時に活躍
