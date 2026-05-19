# Adopt a Kale — Consumer App (Streamlit)

Sarah's app の Streamlit 実装。既存 Adopt a Kale (旧 Adopt a Kale F2C) と同じ Python / Streamlit スタックで構築。
ピッチ Slide 10 をそのまま動かせるレベルまでスキャフォールド済み。モックデータ (`lib/mock_data.py`) で全ページ動作。後から既存 Adopt a Kale の AI コンポーネントを呼ぶように接続するだけ。

---

## クイックスタート

```bash
# 1. 依存インストール (uv 推奨, 既存 Adopt a Kale 同様)
uv pip install -r requirements.txt
# または
pip install -r requirements.txt

# 2. 起動
streamlit run Home.py
# → http://localhost:8501 が自動で開く
```

`uv` を既存 Adopt a Kale で使っているなら、同じ環境内で動くはずです。

---

## ページ構成 (sidebar から切り替え)

| ファイル | URL | 内容 | ピッチ Slide |
|---|---|---|---|
| `Home.py` | `/` | ランディング (hero + 3 tier プラン) | 1, 7 |
| `pages/1_🚀_Start.py` | `/Start` | オンボーディング (4 ステップ) | 7 |
| `pages/2_🌿_My_Plot.py` | `/My_Plot` | **Sarah's app センターピース** | **10** |
| `pages/3_💬_Chat.py` | `/Chat` | Ask your kale (RAG モック) | 10, 6 |
| `pages/4_📅_Schedule.py` | `/Schedule` | 配送カレンダー | 6 |
| `pages/5_👤_Account.py` | `/Account` | サブスク + 設定 | 7 |

ファイル名先頭の数字でサイドバーの順番が決まります。

---

## ディレクトリ構成

```
consumer_app/
├── Home.py                  ← エントリーポイント (ランディング)
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml          ← ケールテーマ (primaryColor 等)
├── pages/
│   ├── 1_🚀_Start.py        ← オンボーディング 4 ステップ
│   ├── 2_🌿_My_Plot.py      ← Sarah's app 中核
│   ├── 3_💬_Chat.py         ← RAG-style チャット
│   ├── 4_📅_Schedule.py     ← 配送カレンダー
│   └── 5_👤_Account.py      ← アカウント
├── lib/
│   ├── styles.py            ← 共通 CSS + ヘルパー関数 (pill, hero, maturity_ring 等)
│   └── mock_data.py         ← Sarah, crops, chat レスポンス (差し替え地点)
└── assets/
    └── leaf-*.png           ← ピッチから移植したケール葉 PNG (5 枚)
```

---

## デザインの仕組み

### テーマ (基本色)
`.streamlit/config.toml` で primaryColor / backgroundColor 等を指定。Streamlit がボタン色等に自動適用。

```toml
primaryColor = "#2D5016"      # ケール緑 — ボタン
backgroundColor = "#FFFFFF"   # 白基調
secondaryBackgroundColor = "#F8F4EC"  # クリーム — サイドバー
```

### カスタムCSS (細部)
`lib/styles.py` の `GLOBAL_CSS` で:
- Streamlit のメニュー/footer を非表示
- ボタンを丸角ピル形状に
- カスタム class (`.kale-card`, `.kale-pill`, `.kale-hero` 等) を提供

各ページの先頭で `inject_css()` を呼ぶだけで全体に適用される。

### ヘルパー関数
`lib/styles.py` から import して使う:
- `brand_header()` — ロゴ + ワードマーク
- `pill(text, variant)` — バッジ
- `eyebrow(text)` — セクション上の小見出し
- `hero(headline, subhead, description)` — ランディング用
- `maturity_ring_html(percent, size)` — SVG 進捗リング (Slide 10 中央)
- `progress_card(label, value, total, emoji, variety)` — 作物進捗カード

---

## モック → 実 API への切り替え

現在 `lib/mock_data.py` に Sarah / crops / chat レスポンスをハードコード。
実 AI に接続する場合:

### Chat (最優先 — デモで一番効く)

`lib/mock_data.py` の `mock_response()` 関数を、既存 Adopt a Kale の RAG-LLM 呼び出しに置き換え:

```python
# Before (mock)
def mock_response(question: str) -> dict:
    if "ready" in question.lower():
        return {"text": "...", "citations": [...]}

# After (real RAG)
from src.greenloop.ai.rag import answer_question  # 既存コード

def mock_response(question: str) -> dict:
    result = answer_question(plot_id="042", question=question)
    return {"text": result.answer, "citations": result.sources}
```

`pages/3_💬_Chat.py` は変更不要。関数の振る舞いだけ切り替え。

### Plot status (2 番目に効く)

`lib/mock_data.py` の `STATUS` 辞書 (74% maturity 等) を実 PPO/MILP 出力に:

```python
# Before
STATUS = {"maturity": 74, ...}

# After
from src.greenloop.ai.ppo_agent import get_plot_status

def get_status():
    return get_plot_status("042")  # returns dict with maturity, etc.
```

`pages/2_🌿_My_Plot.py` で `from lib.mock_data import STATUS` を `from lib.mock_data import get_status` に変えて関数呼び出しに。

### 接続優先度 (May 14 デモ用)

| # | 接続先 | 効果 | 工数 |
|---|---|---|---|
| 1 | **Chat (RAG-LLM)** | デモの "wow" ポイント | 2-4h |
| 2 | Plot status (PPO RL) | "74% mature" が実データ | 2-4h |
| 3 | Schedule (MILP/VRP) | 配送日が実計算 | 2-4h |

最低でも 1 番は接続したい。残りはモックのままでもデモは成立。

---

## ピッチデッキとの整合

- **カラーパレット**: pitch/build.js と完全一致 (kale `#2D5016` / leaf `#7BA05B` / lime `#C7E66B` / coral `#E07856`)
- **ケール葉アイコン**: pitch/assets/ から `assets/` に移植 (5 枚)
- **コピー**: ピッチの一字一句に揃えた (Sarah, "Singapore's first AI-managed garden share" 等)
- **検証済み数値**: 48ms MILP, 434 unit tests, <500ms RAG, <250ms recovery, PPO 500K steps — 全て保持

ピッチデッキ → Streamlit アプリを連続でデモすると、ビジュアル的にシームレスな世界観になります。

---

## Adopt a Kale リポジトリへの取り込み

既存 Adopt a Kale と並列で運用できる構成。同じ uv 環境を共有。

```bash
# 1. リポジトリへ
cd ~/Documents/GitHub/Greenloop-F2C
git checkout -b feat/consumer-app

# 2. zip 展開
unzip ~/Downloads/adopt-a-kale-consumer-streamlit.zip -d .
# → consumer_app/ ディレクトリが作られる

# 3. 動作確認
cd consumer_app
streamlit run Home.py
# → http://localhost:8501

# 4. 既存 Adopt a Kale と同時起動 (デモ構成)
# Terminal 1 — Operator dashboard (既存)
#   cd ~/Documents/GitHub/Greenloop-F2C
#   uv run streamlit run src/greenloop/dashboard/app.py --server.port 8501
# Terminal 2 — Consumer app (今回追加)
#   cd ~/Documents/GitHub/Greenloop-F2C/consumer_app
#   streamlit run Home.py --server.port 8502

# 5. コミット
cd ~/Documents/GitHub/Greenloop-F2C
git add consumer_app
git commit -m "feat(consumer): scaffold Adopt a Kale consumer Streamlit app

Sarah's app implementation (Slide 10).
6 pages: landing, onboarding, plot, chat, schedule, account.
Mock data layer in lib/mock_data.py — wire to real RAG/PPO/MILP later."

git checkout main
git merge feat/consumer-app
git push origin main
```

---

## デモ時の構成 (推奨)

ブラウザのタブを 2 つ並べて切り替えながら見せる:

| タブ | 内容 | URL |
|---|---|---|
| 1 | **Operator dashboard** (既存 Adopt a Kale) — AI の中身、運営側ビュー | `localhost:8501` |
| 2 | **Consumer app** (Adopt a Kale) — Sarah が見ている消費者ビュー | `localhost:8502` |

「同じ AI で 2 つのオーディエンス」のストーリーが立つので、PE rep / Hong 教授に対するデモ強度が大きく上がります。

---

## 既知の Streamlit 限界

- **アニメーション**: Framer Motion のような滑らかなトランジションは無理。プログレスバーは動くが、ページ遷移は瞬間切替。
- **モバイル**: Streamlit はモバイル動作するが、レスポンシブ最適化はされていない。デモは laptop 想定。
- **チャットの入力位置**: `st.chat_input` は常にページ最下部固定。

致命的でない範囲のトレードオフ。実 AI 接続後の機能性 > 見た目のスムーズさ。

---

## トラブルシュート

**ポート衝突**: 既存 Adopt a Kale が 8501 を使っている場合、`--server.port 8502` で起動。

**画像が表示されない**: `assets/leaf-*.png` が存在するか確認。`ls assets/` で 5 ファイルあれば OK。

**CSS が効かない**: 各ページの先頭で `inject_css()` を呼んでいるか確認。Streamlit の再実行 (R キー) で解決することも。

**サイドバーの順番がおかしい**: ページファイル名の先頭の数字 (`1_`, `2_`, ...) で決まる。リネームすれば変わる。

---

## 次のステップ (May 14 まで)

優先度順:

1. **Chat の RAG 接続** (★★★★★) — `mock_response()` を実 RAG に置換
2. **Plot status の実 PPO 接続** (★★★★) — `STATUS` を実データに
3. **デモシナリオのリハーサル** (★★★★★) — 5 分プレゼン台本に合わせて画面遷移を練習
4. カメラ風プレースホルダ画像/動画追加 (★★★) — Slide 10 の "live camera" 強化
5. モバイルでも見せられるか確認 (★★★) — Sarah はスマホで使う想定

何から進めるか、ご相談ください。
