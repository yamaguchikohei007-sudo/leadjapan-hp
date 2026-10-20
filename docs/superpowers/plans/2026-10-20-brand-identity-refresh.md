# ブランドアイデンティティ刷新 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新ロゴ（「A」型の2本の斜線＋赤い丸のマーク）とブランドカラー（ディープネイビー `#10366B` / ジャパンレッド `#D71920`）をサイト全体に適用する。

**Architecture:** 色はすべて `static/css/style.css` の `:root` トークン経由に一本化し、旧パレット（ネイビー `#0b1f3a`、東京タワー朱 `#e8380d`、ゴールド `#c8a24a` など）を撤去する。ロゴマークは `sitegen/render.py` にインライン SVG（線は `currentColor`、丸は赤固定）として持ち、ヘッダー（ネイビー）とフッター／モバイルメニュー（白）で同じマークを色だけ変えて使う。favicon は同じ図形のスタンドアロン SVG。

**Tech Stack:** Python 3.13 標準ライブラリ（静的サイト生成）、素の CSS、`unittest`。

**Spec:** ユーザー提供のロゴシート（マーク単体／横組み／アイコン展開例）と、この会話で指定されたブランドカラー:
- ディープネイビー `#10366B` — コーポレートのメインカラー
- ジャパンレッド `#D71920` — 日本を象徴するアクセントカラー

既存要件: `docs/superpowers/specs/2026-10-19-lead-japan-corporate-site-requirements.md`

## Global Constraints

- ブランド色の値は `#10366B` と `#D71920` そのもの。近似色に置き換えない。
- JavaScript を追加しない（`check_no_javascript`）。外部リソースは Google Fonts のみ（`check_only_free_external_hosts`）。
- 文言は `sitegen/content.py` にのみ置く（README のルール）。ロゴの読み上げ名は `SITE["name"]`（`Lead Japan 合同会社`）を使う。
- テキストのコントラストは WCAG AA（通常文字 4.5:1 以上）。ジャパンレッドはネイビー背景上では 2.3:1 しかないため、**ネイビー上の文字には使わない**（線・丸・下線などの装飾のみ）。
- テスト実行: `python3 -m unittest discover -s tests -v` がすべて通ること。

## 決定事項（色トークン）

`:root` を次の値に置き換える（旧名 `--tower` / `--tower-text` / `--gold` は廃止し、参照はすべて付け替える）。

| トークン | 値 | 用途 |
| --- | --- | --- |
| `--navy` | `#10366B` | メイン（見出し、ボタン、フッター、ヘッダー文字） |
| `--navy-dark` | `#0A2447` | ボタン hover、ヒーロー背景、CTA グラデーション終点 |
| `--red` | `#D71920` | アクセント（ヘッダー上線、カード上線、下線、フォーカスリング、白背景上のラベル文字） |
| `--sky` | `#A9C1E3` | ネイビー背景上のラベル文字（旧 `--gold` の置き換え）、事業アイコンの線 |
| `--ink` | `#1A1A1A` | 本文 |
| `--paper` | `#FFFFFF` | 背景 |
| `--mist` | `#F3F6FA` | 交互セクション背景 |

- `rgba(11, 31, 58, …)`（旧ネイビー）は `rgba(16, 54, 107, …)` に、ヒーローのベール `rgba(5, 15, 32, …)` は `rgba(7, 24, 48, …)` に置換（不透明度はそのまま）。
- 置換表: `var(--tower)`→`var(--red)`、`var(--tower-text)`→`var(--red)`、`var(--gold)`→`var(--sky)`、`var(--navy-2)`→`var(--navy-dark)`（リンク色 `a { color }` と日付色は `var(--navy)`）、`#071629`→`var(--navy-dark)`。
- コントラスト（実測値）: 赤/白 5.2:1、白/ネイビー 11.9:1、sky/ネイビー 6.5:1、ネイビー/mist 11.0:1。

## 決定事項（ロゴマーク）

ロゴシートのマーク単体から起こした座標（viewBox `0 0 256 196`）。これを出発点とし、Task 2 の目視比較で微調整してよい（調整後の座標がテストの対象になるのではなく、テストは構造のみを見る）。

```svg
<svg viewBox="0 0 256 196">
  <polygon points="0,179 56,179 179,0 123,0" fill="currentColor"/>      <!-- 左の長い斜線 -->
  <polygon points="150,64 176,52 254,194 205,194" fill="currentColor"/> <!-- 右の短い斜線 -->
  <circle cx="129" cy="165" r="26" fill="#D71920"/>                     <!-- 赤い丸 -->
</svg>
```

ワードマーク（「Lead Japan」の A が横棒なし＋赤丸の特殊字形）は SVG 化せず、**マーク SVG ＋ HTML テキスト（Inter 700 の「Lead Japan」＋小さい「合同会社」）**で横組みを再現する。理由: テキストのまま検索・読み上げ・拡大に強く、字形の手作業トレースによる品質リスクを避ける。正式な SVG/AI データが手に入ったら Task 2 の SVG を差し替えるだけで済む構造にする。

## Review Focus

1. **モバイルメニュー展開時のロゴ** — メニューを開くと背景がネイビーになる。マークの線が `currentColor` で白に切り替わり、赤丸は残ること（`.logo:has(~ .nav-toggle:checked)` で `color: #fff`）。→ Task 2 のテスト `test_logo_mark_uses_current_color` と目視確認。
2. **ネイビー背景上の赤文字** — ページヒーローや CTA のラベルに赤が残ると読めない。→ Task 1 の `test_labels_on_navy_use_sky`。
3. **旧色の取りこぼし** — CSS 以外（skyline SVG、favicon、`rgba()` 表記）に旧色が残ると色ズレが出る。→ Task 1 の `test_no_legacy_colors`（CSS／`static/img/*.svg`／`sitegen/*.py` を走査）。
4. **ロゴの読み上げ重複** — マーク SVG と社名テキストが両方読まれる。マークは `aria-hidden="true"`、リンクの名前はテキストのみ。→ Task 2 の `test_header_logo_markup`。
5. **favicon の小サイズ表示** — 16px で線が潰れる。ネイビー角丸背景＋白マーク（アイコン展開例の右）にする。→ Task 3 のテストと 16px 目視確認。

---

### Task 1: カラートークンの刷新と旧色の撤去

**Files:**
- Modify: `static/css/style.css`（`:root` と全参照）
- Modify: `static/css/motion.css:85`（`var(--tower)`→`var(--red)`）
- Modify: `static/img/tokyo-skyline.svg`（`#e8380d`/`#ff6a3d`/`#ff5a2a`→`#D71920` 系、`#0b1f3a`→`#10366B`）
- Modify: `tests/test_pages.py:53`（`#e8380d` → `#d71920` を期待）
- Create: `tests/test_brand.py`

**Interfaces:**
- Produces: CSS トークン `--navy`, `--navy-dark`, `--red`, `--sky`, `--ink`, `--paper`, `--mist`（Task 2・3 が使用）。テストヘルパー `contrast(hex1: str, hex2: str) -> float`（`tests/test_brand.py` 内、WCAG 相対輝度式）。

- [ ] **Step 1: 失敗するテストを書く** — `tests/test_brand.py` に `BrandColorTests`:
  - `test_root_tokens`: `style.css` に `--navy: #10366B;` と `--red: #D71920;` と `--sky: #A9C1E3;` が含まれる（大文字小文字無視で比較）。
  - `test_no_legacy_colors`: `static/css/*.css`、`static/img/*.svg`、`sitegen/*.py` のどれにも `0b1f3a`, `13315c`, `e8380d`, `c4300a`, `c8a24a`, `071629`, `ff6a3d`, `ff5a2a`, `rgba(11, 31, 58`, `rgba(5, 15, 32`, `--tower`, `--gold` が含まれない（小文字化して検索）。
  - `test_contrast_pairs`: `contrast("#D71920", "#FFFFFF") >= 4.5`、`contrast("#FFFFFF", "#10366B") >= 4.5`、`contrast("#A9C1E3", "#10366B") >= 4.5`、`contrast("#10366B", "#F3F6FA") >= 4.5`、`contrast("#D71920", "#10366B") < 4.5`（最後はネイビー上で赤文字を使わない根拠を固定する）。
  - `test_labels_on_navy_use_sky`: `style.css` の `.page-hero .section-label`、`.cta-band .section-label`、`.hero-kicker` の各ルールに `color: var(--sky)` が含まれる（ルール本文を正規表現で切り出して確認）。
- [ ] **Step 2: 失敗を確認** — `python3 -m unittest tests.test_brand -v` → `test_root_tokens` 等が FAIL。
- [ ] **Step 3: 実装** — 上の「決定事項（色トークン）」の表と置換表どおりに `style.css` / `motion.css` / `tokyo-skyline.svg` を書き換える。skyline の東京タワーのグラデーションは `#E8474D`→`#D71920`、ハロー等の `#ff5a2a` は `#D71920`。`tests/test_pages.py:53` の期待値を `#d71920` に更新。
- [ ] **Step 4: 全テスト通過を確認** — `python3 -m unittest discover -s tests -v` → OK。
- [ ] **Step 5: 目視確認** — `python3 build.py && python3 -m http.server -d site 8000` を起動し、Playwright（Chromium 同梱）で `index.html` / `company.html` / `business.html` / `news.html` を 1280px と 375px でスクリーンショット。ネイビー上に赤文字がないこと、色が落ち着いていることを確認。
- [ ] **Step 6: コミット** — `git commit -m "style: apply brand colors (deep navy #10366B, japan red #D71920)"`

### Task 2: ヘッダー・フッターのロゴマーク

**Files:**
- Modify: `sitegen/render.py`（`LOGO_MARK` 定数とヘッダー／フッターのマークアップ）
- Modify: `static/css/style.css`（`.logo`, `.logo-mark`, `.footer-logo`）
- Test: `tests/test_render.py`

**Interfaces:**
- Consumes: Task 1 の `--navy`, `--red`。
- Produces: `sitegen.render.LOGO_MARK: str` — `<svg class="logo-mark" viewBox="0 0 256 196" aria-hidden="true" focusable="false">…</svg>`（Task 3 が同じ座標を favicon に使う）。

- [ ] **Step 1: 失敗するテストを書く**（`tests/test_render.py`）:
  - `test_logo_mark_uses_current_color`: `LOGO_MARK` に `viewBox="0 0 256 196"`、`fill="currentColor"` が2回、`<circle` と `#D71920` が1回ずつ、`aria-hidden="true"` を含む。
  - `test_header_logo_markup`: `render_layout(...)` の `<a class="logo" href="index.html" aria-label="Lead Japan 合同会社">` の直後に `LOGO_MARK` があり、続いて `<span class="logo-text">Lead Japan <small>合同会社</small></span>` がある（`aria-label` の値は `SITE["name"]`）。
  - `test_footer_logo_markup`: フッターに `class="footer-logo"` の要素があり、その中に `LOGO_MARK` を含む。
- [ ] **Step 2: 失敗を確認** — `python3 -m unittest tests.test_render -v` → ImportError / FAIL。
- [ ] **Step 3: 実装** — `render.py` に `LOGO_MARK` を上記「決定事項（ロゴマーク）」の図形で定義し、ヘッダーのロゴリンクとフッターの `footer-company` 先頭（`<p class="footer-name">` の前に `<div class="footer-logo">{LOGO_MARK}</div>`）に入れる。CSS: `.logo { display: inline-flex; align-items: center; gap: .6em; color: var(--navy); }`、`.logo-mark { width: 44px; height: auto; flex: none; }`（768px 以下は 36px）、`.footer-logo { color: #fff; width: 56px; margin-bottom: 12px; }`。モバイルメニュー展開時の `.logo:has(~ .nav-toggle:checked) { color: #fff; }` は既存のまま効くことを確認。
- [ ] **Step 4: テスト通過を確認** — `python3 -m unittest discover -s tests -v` → OK。
- [ ] **Step 5: 目視確認** — ロゴシートの「マーク単体」とヘッダーのマークを並べたスクリーンショットで比較し、必要なら座標を微調整（テストは構造のみなので座標変更でテストは壊れない）。375px でメニューを開いた状態（`#nav-toggle` を check）も撮り、白い線＋赤丸になっていることを確認。
- [ ] **Step 6: コミット** — `git commit -m "feat: new Lead Japan logo mark in header and footer"`

### Task 3: favicon・theme-color

**Files:**
- Modify: `static/img/favicon.svg`
- Modify: `sitegen/render.py`（`<meta name="theme-color" content="#10366B">` を `<head>` に追加）
- Test: `tests/test_brand.py`

**Interfaces:**
- Consumes: Task 2 の `LOGO_MARK` と同じ多角形・円の座標。

- [ ] **Step 1: 失敗するテストを書く**（`tests/test_brand.py` に `FaviconTests`）:
  - `test_favicon_uses_brand_mark`: `favicon.svg` に `#10366B`（背景の角丸 `rect`）と `#D71920`（`circle`）を含み、`<text` を含まず、`<polygon` が2つ、`<script` なし、1KB 未満。
  - `test_theme_color`: `render_layout(...)` に `<meta name="theme-color" content="#10366B">` を含む。
- [ ] **Step 2: 失敗を確認** — `python3 -m unittest tests.test_brand -v` → 2件 FAIL。
- [ ] **Step 3: 実装** — favicon は viewBox `0 0 64 64`、`<rect width="64" height="64" rx="14" fill="#10366B"/>` の上に、マークを `transform="translate(8 14) scale(.1875)"` 相当で白（`#FFFFFF`）の多角形2つ＋`#D71920` の円で配置（アイコン展開例の右側と同じ構成）。`render.py` の `<meta name="viewport">` の次の行に theme-color を追加。
- [ ] **Step 4: テスト通過を確認** — `python3 -m unittest discover -s tests -v` → OK。
- [ ] **Step 5: 目視確認** — favicon を 16px / 32px / 180px にラスタライズ（Playwright で `<img width=16>` を撮影）し、16px でもマークと赤丸が判別できること。
- [ ] **Step 6: コミット** — `git commit -m "feat: brand favicon and theme-color"`

### Task 4: 仕上げ（README・最終確認）

**Files:**
- Modify: `README.md`（「構成」に `static/img/favicon.svg` とロゴマークの場所、「ブランドカラー」節を追加: 2色の値と用途、ネイビー上に赤文字を使わないルール、正式ロゴデータ入手時の差し替え先 `sitegen/render.py` の `LOGO_MARK` と `static/img/favicon.svg`）

- [ ] **Step 1: README 更新**
- [ ] **Step 2: 全体確認** — `python3 -m unittest discover -s tests -v` → OK、`python3 build.py` が新しい警告を出さない。全ページを 1280px / 375px で撮影し一覧で確認。
- [ ] **Step 3: コミット＆プッシュ** — `git commit -m "docs: brand colors and logo in README"`、`git push -u origin claude/kind-ramanujan-9g3qt8`
