# Lead Japan 合同会社 コーポレートサイト

Python 標準ライブラリだけで生成する静的サイトです。外部サービス・有料サービスは使用しません（フォントのみ Google Fonts を利用）。

## 構成

- `build.py` — ビルドスクリプト。`site/` に HTML、`sitemap.xml`、`robots.txt` と `static/` を出力します。
- `sitegen/seo.py` — 検索エンジン・SNS 向けの情報（正規 URL、OGP、構造化データ、サイトマップ）。
- `sitegen/headers.py`, `functions/_middleware.js` — セキュリティヘッダー（下の「セキュリティヘッダー」）。
- `sitegen/content.py` — サイトの文言とデータ（会社情報、事業、ニュース、プライバシーポリシーなど）。
- `sitegen/pages.py` — 各ページの構成。
- `sitegen/render.py` — 共通レイアウト（ヘッダー、フッター、ナビゲーション）。
- `static/css/style.css`, `static/css/motion.css` — スタイルとスクロール演出。
- `static/img/tokyo-skyline.svg` — 東京の街並みのイラスト（代表挨拶ページ）。
- `static/img/japan-map.svg` — トップページの日本地図（`tools/japan_map.py` で作成。下の「トップページの地図と赤い点」を参照）。
- `sitegen/geo.py` — 地図の範囲と都道府県の位置。
- `functions/pm-book-bonus/download.js`, `bonus/` — 書籍の読者特典のダウンロード（下の「書籍ページと読者特典」）。
- `functions/index.js` — トップページの赤い点を閲覧者の都道府県に動かす Cloudflare Pages Functions（サーバー側だけで動き、ブラウザには JavaScript を送りません）。
- `static/img/favicon.svg` — ファビコン（ネイビーの角丸にロゴマーク）。
- ロゴマーク（ヘッダー・フッター）は `sitegen/render.py` の `LOGO_MARK` にあります。
- `tests/` — テスト。
- `.github/workflows/ci.yml` — push / プルリクエスト時のテスト実行（公開は Cloudflare Pages が行います）。

## 書籍ページと読者特典

- `pm-book.html`（`/pm-book`）— 書籍『外資系プロジェクトマネージャー1年目の教科書』の紹介ページ。グローバルナビの「書籍」と、出版のページ（`/publishing`）から入れます。文章と設定は `sitegen/content.py` の `BOOK_*`（原稿は pm-book リポジトリの `06_HP紹介/HP書籍紹介_実装仕様.md`）。画像は `static/img/book/`。
- 書籍ページは書籍専用のヘッダー・フッター（ページ内リンクと発行元だけ）で表示します（`sitegen/render.py` の `layout="book"`）。特典ページも同じです。
- 後から入れる値は `sitegen/content.py` の `BOOK` にまとめています。`None` の項目は表示されません。
  - 発売のお知らせの窓口：`x_url`（X）、`line_url`（LINE公式の友だち追加 URL）、`newsletter_url`（メール登録フォームの URL）。入れたものだけボタンが出ます。全部 `None` のあいだは「発売日が決まりしだいお知らせします」と表示します。
  - 購入ボタン：`kindle_url`・`paperback_url`（Amazon の商品ページ。予約ページでも可）。入れた版のボタンが出ます。価格は `kindle_price`・`paperback_price`、ISBN は `isbn`。
  - 発売したら `"status": "on_sale"` にします（「好評発売中」になり、お知らせ欄の代わりに購入ボタンを大きく出します）。
- 表紙横の帯（`BOOK_BADGES`）には事実だけを書きます。ランキングや推薦は、実際にあったときに足してください。
- 特典セクションの画面写真（`static/img/book/bonus-screen-*.webp`）は、特典ツールにサンプルデータを入れて撮ったものです。ツールの見た目を変えたら撮り直します。
- `pm-book-bonus.html`（`/pm-book-bonus`）— 読者特典のパスワード入力ページ（検索エンジンには載せません）。フォームは `functions/pm-book-bonus/download.js`（Cloudflare Pages Functions）に送られ、パスワードが正しければ特典のHTMLファイルがダウンロードされます。間違っていれば `pm-book-bonus-error.html` に戻ります。
- 特典ファイルの原本は `bonus/pm-book-gantt-tool.html` です。`static/` には置かないので、公開サイトから直接は取得できません。差し替えたら `python3 tools/bonus_module.py` を実行して `bonus/pm-book-gantt-tool.js`（関数に組み込まれる形）を作り直します。
- 読者パスワードは、サイトにもリポジトリにも書きません（本の中だけで案内）。`bonus/download.js` にはハッシュ値だけを置いています。全角・前後の空白・大文字小文字の違いは許容します。パスワードを変えるときは、`bonus/download.js` の冒頭にあるコマンドで新しいハッシュ値を作り、`PASSWORD_SHA256` を置き換えます。

## ブランドカラーとロゴ

| 名前 | 値 | 用途 |
| --- | --- | --- |
| ディープネイビー | `#10366B` | コーポレートのメインカラー（CSS の `--navy`） |
| ジャパンレッド | `#D71920` | 日本を象徴するアクセントカラー（CSS の `--red`） |

色はすべて `static/css/style.css` の `:root` で定義しています。補助色として `--navy-dark`（濃いネイビー）、`--sky`（ネイビー背景上の小見出し用の淡い青）、`--mist`（薄い背景）があります。

- ネイビー背景の上の文字にジャパンレッドは使いません（コントラストが不足し読みにくいため）。赤は線・下線・丸などの装飾と、白背景上の文字に使います。
- ネイビー背景の上では、フォーカス枠と現在ページの下線も白にしています（赤では見えにくいため）。
- 「Lead Japan」の文字ロゴは画像ではなく文字（Inter）で表示しています。
- 正式なロゴデータ（SVG など）を入手したら、`sitegen/render.py` の `LOGO_MARK` と `static/img/favicon.svg` の図形を差し替えてください。

## 文言の編集

表示される文言（社名の由来、お問い合わせ文面、404 の文言、各ページのタイトル・説明文、制定日、著作権表記を含む）はすべて `sitegen/content.py` にあります。文言の編集は `sitegen/content.py` のみで行ってください。HTML を直接編集する必要はありません。

## 【要入力】 の一覧と埋め方

まだ確定していない情報は `【要入力】` と表示されています。ビルド時に残数と該当ファイルが警告として表示されます（ニュースの日付は `【要入力】` の文字ではなく仮の日付値として入っているため、警告の件数には含まれません）。

| 場所 | 内容 | 埋め方 |
| --- | --- | --- |
| `sitegen/content.py` の会社情報 `"email"` | お問い合わせ用メールアドレス（お問い合わせページとプライバシーポリシーに表示） | メールアドレスを入力 |

代表者名・設立日（2026年10月19日）・所在地（東京都中野区）は入力済みです。

次の項目は `【要入力】` ではありませんが、公開前に内容の確認が必要です（ビルド時に `要確認:` として表示されます）。

| 場所 | 内容 | 確認すること |
| --- | --- | --- |
| `sitegen/content.py` の `MESSAGE`（代表挨拶本文） | 草案の文面 | 代表者本人が内容を確認し、必要に応じて修正 |
| `sitegen/content.py` の `CONTACT_HOURS`（受付時間） | 仮の受付時間 | 実際の受付時間に修正 |
| `sitegen/content.py` の `COMPANY_NAME_ORIGIN`（社名の由来） | 草案の文面 | 内容を確認 |
| `sitegen/content.py` の `PRIVACY`（プライバシーポリシー） | 草案の文面 | 専門家による確認を推奨 |
| `sitegen/content.py` の `BUSINESSES`（3事業） | トップの帯とカード、事業・サービス（`/business`）のカード3枚。カードから事業ごとのページ（`/solution`・`/product`・`/publishing`）へ進む | 事業を増減したら、そのページの関数と `PAGE_META`、`ICONS`（`sitegen/pages.py`）も合わせる |
| `sitegen/content.py` の `RESULT_*`（管理業務 30%→5%） | 代表個人の実績。AI駆動ソリューション（`/solution`）と代表挨拶に表示 | 外資系日本法人の数字を公開してよいか（社内ルール）。必ず `RESULT_NOTE` の注記を添える |
| `sitegen/content.py` の `STAGES`・`FAQ`（料金） | Stage 1 30万円、Stage 2 見積もり制、Stage 3 月額50万円（すべて税別）。期間の目安は Stage 2 まで4〜6ヶ月、Stage 3 を加えて7〜9ヶ月 | 料金・期間を変えたら `STAGES`・`PROCESS_NOTE`・`FAQ`・`CONTACT_PROCESS` をそろえて直す。診断料の充当は起算日が決まるまで載せない |
| `sitegen/content.py` の `PRODUCT_*` | 開発中のプロジェクト管理SaaS（短い紹介のみ） | 名前・機能・提供開始時期が決まったら追記。先行案内の登録窓口ができたらボタンを足す |
| ニュース（管理画面） | 『外資系PM1年目の教科書』の刊行予定のお知らせの日付（推定値 2026-06-01）、サイト公開のお知らせの日付（2026-10-19） | 実際の日付に直し、管理画面から「サイトに反映」 |

ニュースは管理画面で編集します（`content/news.json` は手で書き換えません。下の「プレスリリース管理画面」を参照）。

ビルド時には、公開前に確認が必要な項目も `要確認: ` として1行ずつ表示されます（`sitegen/content.py` の `UNCONFIRMED`。サイトには表示されません）。確認が済んだ項目は `UNCONFIRMED` から削除してください。

埋めたら `python3 build.py` を実行し、警告が消えたことを確認してください。

## ビルド

```
python3 build.py
```

`site/` ディレクトリが作成されます（Git 管理対象外）。

## プレビュー

```
python3 -m http.server -d site 8000
```

ブラウザで http://localhost:8000 を開きます。

## テスト

```
python3 -m unittest discover -s tests -v
```

## Cloudflare Pages での公開

Cloudflare Pages（無料プラン・商用利用可）で公開します。`main` に push されるたびに Cloudflare 側でテストと `python build.py` が実行され、テストが通った場合だけ自動で公開されます（テストが失敗するとビルドが止まり、公開中のサイトはそのまま残ります）。

### 初回設定

1. Cloudflare のアカウントを作成します（https://dash.cloudflare.com/sign-up 。無料プランで足ります）。
2. ダッシュボードで **Workers & Pages** → **Create** → **Pages** タブ → **Connect to Git** を選びます。
3. GitHub と連携し、リポジトリ **`yamaguchikohei007-sudo/leadjapan-hp`** を選びます（Cloudflare の GitHub アプリにこのリポジトリへのアクセスを許可します）。
4. ビルド設定を次のとおり入力します。

   | 項目 | 値 |
   | --- | --- |
   | Production branch | `main` |
   | Framework preset | `None` |
   | Build command | `python -m unittest discover -s tests && python build.py` |
   | Build output directory | `site` |
   | 環境変数（Environment variables） | `PYTHON_VERSION` = `3.13` |

5. **Save and Deploy** を押します。最初のデプロイが終わると `https://<プロジェクト名>.pages.dev` の URL が表示されます。この URL をメモします。
6. `sitegen/content.py` の `SITE_URL` にその URL を設定します（現在は `SITE_URL = "https://leadjapan-hp.pages.dev"`）。記事ページの `og:url` / `og:image` に使われます。

7. **Settings** → **Runtime** → **Fail open / closed** を **Fail open** にします。トップページの赤い点（下記）は無料枠（1日10万回）で動いており、使い切ったときに Fail open ならエラーではなく通常のページ（赤い点は東京）が表示されます。

### トップページの地図と赤い点

トップページの日本地図には、閲覧者のおおよその場所（都道府県単位）を赤い点で目立たないように表示します。ラベルなどは出しません。

- 場所は Cloudflare が IP アドレスから推定した都道府県で、点はその県庁所在地に置きます。海外からの閲覧・場所が分からないとき・エラーのときは東京に表示します。
- 処理は `functions/index.js`（Cloudflare Pages Functions）で、トップページ（`/`）を返すときにだけ動きます（`build.py` が書き出す `site/_routes.json` で限定。ほかのページや画像は無料・無制限の静的配信のままです）。位置は保存・記録しません。
- ページは閲覧者ごとに違うので、`Cache-Control: private, no-store` を付けて、他の人にキャッシュされたページが届かないようにしています。
- 手元のプレビュー（`python3 -m http.server`）では Functions は動かないため、赤い点は常に東京です。
- 推定は外れることがあります（スマホ回線は東京・大阪の設備を経由しやすく、VPN では別の場所になります）。
- 公開サイトに JavaScript を使わない方針の例外です。`functions/index.js` は Cloudflare のサーバー上でだけ動き、ブラウザには送られません。テストは `node --test tests/js/visitor_pin.test.mjs`（Node.js がある環境では `python -m unittest` からも実行されます）。
- 地図の範囲や都道府県の位置（`sitegen/geo.py`）を変えたときは、地図データ（[ne_10m_admin_0_countries_jpn.geojson](https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_0_countries_jpn.geojson)）をダウンロードして `python3 tools/japan_map.py <ダウンロードしたファイル>` を実行し、`static/img/japan-map.svg` と `functions/index.js` の位置表を作り直します。

### セキュリティヘッダー

すべての応答に、CSP（Content-Security-Policy）・HSTS などのセキュリティヘッダーを付けています。

- 値は `sitegen/headers.py` にあります。`build.py` がそれを `site/_headers` に書き出し、Cloudflare Pages が静的ページに付けます。
- Cloudflare Pages は `_headers` を Functions の応答（トップページ `/` と `/pm-book-bonus/download`）には付けないため、`functions/_middleware.js` が同じ値を付けます。値を変えるときは両方を直します（`tests/test_headers.py` が一致を確認します）。
- CSP は例外なしの厳しい設定です。読み込めるのは自サイトの CSS・画像と Google Fonts だけで、JavaScript、HTML 内の `style="..."`・`<style>` は使えません（ブラウザが無視します）。スクロール演出の遅延は `style="--d: 1"` ではなく、クラス `reveal--d1`〜`reveal--d3`（`static/css/motion.css`）で付けます。外部の画像・埋め込み（YouTube など）やフォントを足すときは、CSP も合わせて直します。テストが埋め込みスタイルと外部の読み込みを検出します。
- HSTS（`Strict-Transport-Security: max-age=31536000`）は独自ドメインに移ってもそのまま効きます。同じドメインのほかのサブドメインに影響しないよう、`includeSubDomains`・`preload` は付けていません。
- 手元のプレビュー（`python3 -m http.server`）ではヘッダーは付きません。

### 独自ドメインを使う場合

1. ドメインを取得します（ドメイン費用のみ有料）。
2. Cloudflare の Pages プロジェクト → **Custom domains** → **Set up a custom domain** でドメイン（例: `www.example.co.jp`）を追加します。
3. 画面の案内に従って DNS を設定します（ドメインを Cloudflare で管理している場合は自動、他社 DNS の場合は表示された CNAME レコードを追加）。
4. 有効になったら `sitegen/content.py` の `SITE_URL` を独自ドメインの URL に変更し、push します。

内部リンク・CSS・画像は `/` から始まるルート基準のパスです（`sitegen/render.py` の `url()`）。どの階層の存在しない URL（例: `/a/b/c`）でも、404 ページが正しい見た目で表示されます。その代わり、サイトはドメインの一番上（`https://example.co.jp/`）に置く前提で、サブフォルダ（`https://example.com/leadjapan/`）への設置や、HTML ファイルをダブルクリックして直接開く確認には対応しません。確認は「プレビュー」の手順で行ってください。

### 検索エンジン・SNS 向けの情報

`SITE_URL` をもとに、ビルド時に次のものを自動で作ります（`sitegen/seo.py`）。`SITE_URL` を独自ドメインに変えれば、すべて追従します。

- 各ページの正規 URL（`canonical`）と SNS 共有用の情報（OGP）。共有時の画像は、記事に画像があればその画像、なければ東京の写真（`static/img/hero-tokyo.jpg`）です。
- `sitemap.xml`（404 ページを除く全ページ）と `robots.txt`。
- トップページの会社情報（構造化データ。社名・所在地など。メールアドレスは確定後に自動で追加されます）。
- 404 ページは検索結果に出ないよう `noindex` にしています。

正規 URL は Cloudflare Pages の表示に合わせて `.html` を除いた形（例: `/company`）です。

## プレスリリース管理画面

ニュース（プレスリリース）を、ブラウザの管理画面から書いて公開するための仕組みです。この Mac だけで動き（`127.0.0.1` 限定）、外部には公開されません。サイト本体（`build.py` など）は従来どおり標準ライブラリだけで動き、管理画面に必要な Django 等は `requirements-admin.txt` に分けてあります。

### 初回セットアップ

以降 `VPY` は `~/.venvs/leadjapan-cms/bin/python` のことです。仮想環境は OneDrive の外に作ります。

```
python3 -m venv ~/.venvs/leadjapan-cms
~/.venvs/leadjapan-cms/bin/pip install -r requirements-admin.txt
~/.venvs/leadjapan-cms/bin/python cms/manage.py migrate
~/.venvs/leadjapan-cms/bin/python cms/manage.py createsuperuser
~/.venvs/leadjapan-cms/bin/python cms/manage.py import_news
```

- `createsuperuser` で管理画面のログイン用ユーザー名とパスワードを決めます（この Mac のみで使います）。
- `import_news` は、既存の `content/news.json` の記事を管理画面のデータベースに取り込みます（初回のみ。`--path` でファイルを指定できます）。

### 起動

```
~/.venvs/leadjapan-cms/bin/python cms/manage.py runserver 127.0.0.1:8001
```

ブラウザで http://127.0.0.1:8001/admin/ を開き、ログインします。終了はターミナルで Ctrl+C です。

### 管理画面の権限

- 管理者（スーパーユーザー）はすべての操作ができます。
- スタッフに下書きプレビュー・画像の閲覧を許可する場合は、記事の「閲覧」権限を付与します。画像は `/media/` とプレビューの両方で認証・権限を確認します。
- 「サイトに反映」には記事の「変更」権限が必要です。この権限はGitへのコミット・pushも許可するため、公開を担当する人だけに付与してください。
- 下書きプレビューと画像の応答はブラウザ・共有キャッシュに保存させません。
- 管理画面は引き続き `127.0.0.1` 限定で使用してください。インターネット公開用の構成ではありません。

### 記事を書く

管理画面の「記事」から「記事を追加」を選び、次の項目を入力します。

| 項目 | 内容 |
| --- | --- |
| タイトル | 記事のタイトル（他の記事と重複不可） |
| スラッグ | URL になる半角英小文字・数字・ハイフンのみ（例: `new-book`）。ページは `news-<スラッグ>.html` になります |
| 公開日 | 記事に表示される日付 |
| カテゴリ | プレスリリース / お知らせ / 出版 / 事業 |
| 概要 | 一覧や検索結果に出る短い説明（200字まで） |
| 本文 | Markdown で書きます（下記） |
| 画像・代替テキスト | 任意。画像を付ける場合は代替テキストが必須（5MB以下） |
| 状態 | 下書き / 公開 |

Markdown の書き方:

| 表現 | 書き方 |
| --- | --- |
| 見出し | `## 見出し` |
| 太字 | `**太字**` |
| 箇条書き | 行頭に `- ` |
| リンク | `[表示する文字](https://example.com/)` |

リンクは `http://`、`https://`、`mailto:` または相対パスのみ使えます。HTML タグは書いても文字として表示されます。

本文には画像を入れられません（メイン画像欄を使ってください）。

メイン画像は「サイトに反映」のときに自動で整えられます。横幅 1600px を超える画像は縮小・再圧縮され、写真の撮影情報（撮影場所の位置情報を含む EXIF）は削除されます。スマホの写真をそのまま使っても大丈夫です。管理画面に保存された元の画像はそのまま残ります。

**スラッグの注意:** 公開後にスラッグを変えると記事の URL が変わり、以前の URL は表示できなくなります。公開前に決めてください。

### プレビュー

記事の編集画面にあるプレビューのリンクから、実際のサイトと同じレイアウトで表示を確認できます（下書きも確認できます）。

### 公開する（「サイトに反映」）

1. 公開したい記事の「状態」を「公開」にして保存します。下書きのままの記事や、公開から「下書き」に戻した記事はサイトに出ません。
2. 記事一覧の「サイトに反映」ボタンを押し、確認画面で実行します。
3. GitHub 上の最新の `main` から一時的な作業用コピーを作り、そこに `content/news.json` と `static/img/news/` を書き出してサイトのテストを実行します。テストが通れば、`news/publish` ブランチに送信して PR（変更の提案）を作ります。
4. 完了メッセージの PR へのリンクを開き、GitHub で内容を確認して **マージ** します。マージすると Cloudflare Pages が数分で公開サイトを更新します（https://leadjapan-hp.pages.dev/ ）。

- 作業用コピーは終わると消えます。この Mac のフォルダ（今いるブランチや、作業中のファイル）は変更されません。
- 反映待ちの PR は常に 1 つです。マージする前にもう一度「サイトに反映」を押すと、新しい PR は作らず、今の PR を最新の内容に置き換えます。
- **この Mac で GitHub にログイン済みであること**と、**GitHub CLI（`gh`）が使えること**が必要です（`brew install gh` のあと `gh auth login`）。`gh` が使えない場合も送信まではでき、PR を作るためのリンクが表示されます。

結果のメッセージ:

| メッセージ | 意味 |
| --- | --- |
| PR を作成しました | 成功。リンク先の PR を GitHub でマージするとサイトに反映されます |
| 反映待ちの PR を最新の内容に更新しました | まだマージしていない PR があったので、その中身を置き換えました。リンク先でマージしてください |
| 反映待ちの PR はすでに最新です | 前回の「サイトに反映」から変更がありません。リンク先の PR をマージしてください |
| 変更はありません | 公開中のサイトと同じ内容です |
| 反映待ちの PR を閉じました | マージ前の PR があったが、記事を下書きに戻すなどして公開中のサイトと同じ内容に戻ったため、その PR を自動で閉じました（間違えてマージされないように） |
| テストが失敗したため反映を中止しました | サイトのテストが失敗しました。表示された出力を確認してください。何も送信されません |
| GitHub への送信に失敗しました | オフラインやログイン切れなど。ログインし直して、もう一度「サイトに反映」を押してください |
| 反映待ちの PR が別の場所で更新されていた | 誰かが GitHub 上で PR を直接変更しました。上書きしないよう止めています。もう一度押すと、その時点の状態から作り直します |
| PR を作成できませんでした | 送信は済んでいます。表示されたリンクから GitHub で PR を作成してください（`gh` が未インストール・未ログインのとき） |
| GitHub から最新の状態を取得できません | オフラインやログイン切れなど。何も送信されません |
| 別の反映処理が実行中です | 「サイトに反映」が二重に押されました。しばらく待ってからやり直してください |
| 予期しないエラーが発生しました | 想定外の問題です。何も送信されません。メッセージを管理者に伝えてください |
| その他のエラー（書き出し・コミットの失敗） | メッセージに原因が出ます。何も送信されません |

### バックアップ

- 管理画面のデータベース（`cms/db.sqlite3`）と画像（`cms/media/`）は OneDrive 内にあり、Git 管理対象外です。OneDrive が履歴を保持します。
- サイトの元データは Git で管理される `content/news.json`（と `static/img/news/`）です。データベースを失っても、`import_news` で記事の文章を復元できます（画像は復元されないため、`cms/media/` のバックアップも残してください）。ただし、公開（「公開」状態で反映）済みの記事のみが対象です。下書きはデータベースにしか存在しません。

### 管理画面のテスト

```
~/.venvs/leadjapan-cms/bin/python cms/manage.py test press
```

GitHub の CI でも、push と PR のたびにサイトのテストと管理画面のテストの両方が実行されます。管理画面のテストには、`content/news.json` の表示用 HTML（`body_html`）が Markdown の本文（`body_md`）から正しく作られたものかの確認が含まれます。`news.json` は手で書き換えず、必ず管理画面から反映してください。

## お問い合わせ

お問い合わせはメールアドレスでの受付です。有料のフォームサービスは使用していません。無料の Google フォームを追加する場合は、`sitegen/pages.py` の `body_contact` にあるコメント箇所に埋め込みを追加してください。

## 注意事項

- プライバシーポリシーの文面は草案です。公開前に内容を確認してください。
- スクロール演出は Chrome / Edge / Safari 26 以降で動作します。それ以外のブラウザでは、演出なしでコンテンツが静的に表示されます。
- スマホのメニューは、JavaScript を使わずブラウザ標準の「ポップオーバー」で開閉します（Esc キーや「閉じる」ボタンで閉じ、開閉の状態は読み上げソフトにも伝わります）。ポップオーバーに対応していない古いブラウザでは、メニューボタンの代わりにフッターのリンク一覧へ移動する「メニュー」リンクが表示されます。
- 独自ドメインを後で使う場合は、ドメイン取得費用のみ有料です（任意）。手順は「Cloudflare Pages での公開」の「独自ドメインを使う場合」を参照してください。

## 画像のクレジット

- SNS 共有用の画像（`static/img/hero-tokyo.jpg`、トップページには表示しません）: Louie Martinez / Unsplash（[Unsplash ライセンス](https://unsplash.com/license)、商用利用可・クレジット表記は任意）。元画像: https://unsplash.com/photos/IocJwyqRv3M
- 地図データ: [Natural Earth](https://www.naturalearthdata.com/)（パブリックドメイン）。国境は日本の見解に沿った版（`ne_10m_admin_0_countries_jpn`）を使っています。
