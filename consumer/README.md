# Adopt a Kale — Consumer App

Sarah's app の Web 実装。Next.js 16 (Turbopack) + Tailwind v4 + Framer Motion で構築。

ピッチ Slide 10 に出てくる Sarah's app をそのまま動かせるレベルまでスキャフォールド済み。モックデータ (`lib/mock-data.ts`) で全 UI が動作する状態。後から FastAPI 経由で実 AI に接続するだけ。

---

## クイックスタート

```bash
npm install
npm run dev
# → http://localhost:3000
```

ブラウザで開けば、ランディング → オンボーディング → My Plot → Chat → Schedule の全フローが動きます。

```bash
npm run build       # 本番ビルド (静的化)
npm run start       # 本番サーバー起動
```

---

## ルート構成

| パス | 内容 | ピッチ Slide |
|---|---|---|
| `/` | ランディング (hero + 3 tier プラン) | Slide 1, 7 |
| `/onboarding` | tier 選択 → 作物選択 → 確認 (4 ステップ) | Slide 7 |
| `/plot` | **Sarah's app センターピース** (成熟度リング + crops + deliveries + activity) | **Slide 10** |
| `/chat` | "Ask your kale" RAG-style Q&A | Slide 10, 6 |
| `/schedule` | 配送カレンダー + 作物タイムライン | Slide 6 |
| `/account` | サブスクリプション + 設定 | Slide 7 |

---

## ディレクトリ構成

```
consumer/
├── app/
│   ├── layout.tsx          ← root layout
│   ├── globals.css         ← Tailwind + ケールブランドトークン
│   ├── page.tsx            ← ランディング
│   ├── onboarding/page.tsx ← 4ステップフロー
│   ├── plot/page.tsx       ← Sarah's app 中核
│   ├── chat/page.tsx       ← RAG チャット
│   ├── schedule/page.tsx   ← カレンダー
│   └── account/page.tsx    ← アカウント
├── components/
│   ├── brand/
│   │   ├── leaf-mark.tsx   ← ロゴ (curly kale + ワードマーク)
│   │   └── app-nav.tsx     ← グローバルナビ
│   ├── plot/
│   │   └── maturity-ring.tsx ← SVG プログレスリング (Slide 10 中央)
│   └── ui/
│       ├── button.tsx      ← cva ベース、5 variant
│       ├── card.tsx        ← 角丸 + ヘアライン
│       └── badge.tsx       ← 4 variant
├── lib/
│   ├── utils.ts            ← cn (tailwind-merge + clsx)
│   └── mock-data.ts        ← Sarah / crops / chat / 配送 (差し替え地点)
├── public/assets/          ← ピッチから移植したケール葉 PNG
└── package.json
```

---

## デザイントークン

`app/globals.css` の CSS 変数で全色を一元管理:

```css
--kale:  #2D5016   /* 主色 — ロゴ・ヘッドライン */
--leaf:  #7BA05B   /* 副色 — プログレス・アイコン */
--lime:  #C7E66B   /* アクセント (on dark) */
--coral: #E07856   /* ギフト・温かみ・CTA */
--paper: #FAF7F0   /* カード背景 */
--cream: #F8F4EC   /* 軽いセクション背景 */
--ink:   #1A1A1A   /* 本文 */
--muted: #6B7280   /* キャプション */
```

Tailwind では `bg-kale`, `text-coral`, `border-hairline` のように使用可能。
ピッチデッキの `build.js` と完全に同じパレット。視覚的継続性あり。

---

## モック → 実 API への切り替え

現在 `lib/mock-data.ts` に Sarah の状態・作物・チャット応答をハードコード。実 AI 接続の選択肢:

### Pattern 1: Next.js Route Handlers (シンプル)

```ts
// app/api/plot/route.ts
export async function GET() {
  const data = await fetch("http://localhost:8000/plot/042");
  return Response.json(await data.json());
}
```

`useSWR("/api/plot")` 等でフェッチに置換。

### Pattern 2: 別 FastAPI サービス (推奨)

```python
# api/main.py
from fastapi import FastAPI
from src.greenloop.ai import ppo_agent, milp_solver, rag_chat  # 既存コード再利用

app = FastAPI()

@app.get("/plot/{plot_id}")
def get_plot(plot_id: str):
    return {
        "plotId": plot_id,
        "maturity": ppo_agent.get_status(plot_id),
        "nextHarvest": milp_solver.next_harvest(plot_id),
    }

@app.post("/chat/{plot_id}")
def chat(plot_id: str, question: str):
    return rag_chat.answer(plot_id, question)
```

```bash
uvicorn api.main:app --reload --port 8000
```

### 接続優先度 (May 14 デモ用)

1. **Chat (RAG-LLM)** — Sarah's app デモで一番効くポイント。実接続必須レベル。
2. **Plot status (PPO RL)** — "74% mature" の数字が実データなだけでもデモ強度UP。
3. その他 (delivery / schedule) — モックで十分。

---

## ビジュアル設計の意図

### `/plot` (中核)
- **巨大な maturity ring** が画面の主役 → ピッチ Slide 10 と一致
- ケール葉 PNG を中央に配置 → ブランド一貫性
- 周辺に作物・配送・アクティビティ → "ある程度動いている" 感
- 下部の lifetime stats → 継続性 (LTV) を視覚化
- グラデーションは控えめ (cream → white) で premium 感

### `/chat`
- ケール葉アイコン付きアバター → AI が話している感
- citations (Sources) を必ず表示 → "RAG-grounded" 訴求 (ピッチと一致)
- thinking 中の bouncing dots → レスポンス感
- Suggested questions → 最初の入力を helping

### `/onboarding`
- 4 ステップ + プログレスバー → "3 minutes" の約束を視覚化
- "Most popular" バッジ → Joint への誘導
- ケール葉 + チェックマーク → 完了の喜び

---

## 残タスク (May 14 まで)

優先度順:

| # | タスク | 工数 | デモ価値 |
|---|---|---|---|
| 1 | **Chat を実 RAG に接続** | 4-6h | ★★★★★ |
| 2 | Plot status を実 PPO/MILP に接続 | 4-8h | ★★★★ |
| 3 | カメラ風プレースホルダ動画/画像を `/plot` に | 1-2h | ★★★ |
| 4 | `/schedule` の VRP 実接続 | 2-4h | ★★ |
| 5 | モバイル動作確認 (Sarah はスマホで使う想定) | 1h | ★★★★ |
| 6 | デプロイ (Vercel + Render) | 1-2h | ★★★ |

最低でも 1 番だけは抑えたい。残りは時間次第。

---

## Adopt a Kale リポジトリへの取り込み

```bash
# 1. リポジトリへ
cd ~/Documents/GitHub/Greenloop-F2C
git checkout -b feat/consumer-app

# 2. zip 展開
unzip ~/Downloads/adopt-a-kale-consumer.zip -d .

# 3. 動作確認
cd consumer
npm install
npm run dev
# → http://localhost:3000

# 4. 既存 Adopt a Kale (旧 Adopt a Kale) と同時起動 (デモ時の構成)
# Terminal 1 (Operator dashboard):
#   cd ~/Documents/GitHub/Greenloop-F2C
#   uv run streamlit run src/greenloop/dashboard/app.py
#   → localhost:8501
# Terminal 2 (Consumer app):
#   cd ~/Documents/GitHub/Greenloop-F2C/consumer
#   npm run dev
#   → localhost:3000

# 5. コミット
cd ~/Documents/GitHub/Greenloop-F2C
git add consumer
git commit -m "feat(consumer): scaffold Adopt a Kale consumer app

Next.js 16 + Tailwind v4 + Framer Motion.
6 routes: landing, onboarding, plot, chat, schedule, account.
Mock data layer for AI components — wire to FastAPI later."

git checkout main
git merge feat/consumer-app
git push origin main
```

---

## 技術スタック

| 領域 | バージョン | 役割 |
|---|---|---|
| Next.js | 16.2.6 | App Router + Turbopack |
| React | 19.2 | server + client components |
| TypeScript | 5.x | 型 |
| Tailwind | v4 | スタイル (CSS 変数主導) |
| Framer Motion | 最新 | アニメーション |
| Lucide React | 最新 | アイコン |

shadcn/ui は採用せず — Tailwind v4 との互換性がまだ新しい段階だったので、必要な primitive (Button / Card / Badge) を自前で書いた方が制御しやすい判断。

---

## トラブルシュート

**画像が表示されない**: `public/assets/leaf-*.png` が存在するか確認。
**Tailwind クラスが効かない**: `globals.css` の `@theme inline` ブロックで CSS 変数を Tailwind カラーに mapping 済み。新色を足す場合はここに `--color-X: var(--X)` を追加。
**Google Fonts ビルドエラー (オフライン環境)**: 現状は system font 使用。ローカルなら `app/layout.tsx` で `next/font/google` から Geist 等を import 可能。
