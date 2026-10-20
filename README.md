# Lead Japan 合同会社 コーポレートサイト

Python 標準ライブラリだけで生成する静的サイトです。外部サービス・有料サービスは使用しません（フォントのみ Google Fonts を利用）。

## 構成

- `build.py` — ビルドスクリプト。`site/` に HTML、`sitemap.xml`、`robots.txt` と `static/` を出力します。
- `sitegen/seo.py` — 検索エンジン・SNS 向けの情報（正規 URL、OGP、構造化データ、サイトマップ）。
- `sitegen/content.py` — サイトの文言とデータ（会社情報、事業、ニュース、プライバシーポリシーなど）。
- `sitegen/pages.py` — 各ページの構成。
- `sitegen/render.py` — 共通レイアウト（ヘッダー、フッター、ナビゲーション）。
- `static/css/style.css`, `static/css/motion.css` — スタイルとスクロール演出。
- `static/img/tokyo-skyline.svg` — 東京の街並みのイラスト。
- `static/img/favicon.svg` — ファビコン（ネイビーの角丸にロゴマーク）。
- ロゴマーク（ヘッダー・フッター）は `sitegen/render.py` の `LOGO_MARK` にあります。
- `tests/` — テスト。
- `.github/workflows/ci.yml` — push / プルリクエスト時のテスト実行（公開は Cloudflare Pages が行います）。

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
| `sitegen/content.py` の会社情報 `"representative"` | 代表者名 | 代表者名を入力 |
| `sitegen/content.py` の会社情報 `"founded"` | 設立日（「2026年」の後ろ） | 例: `1月15日` のように入力 |
| `sitegen/content.py` の会社情報 `"address"` | 住所の詳細（「東京都」の後ろ） | 番地などを入力 |
| `sitegen/content.py` の会社情報 `"email"` | お問い合わせ用メールアドレス | メールアドレスを入力 |
| `sitegen/content.py` の `MESSAGE`（代表挨拶本文） | 草案の文面 | 代表者本人が内容を確認し、必要に応じて修正 |
| `sitegen/content.py` の `CONTACT_HOURS`（受付時間） | 仮の受付時間 | 実際の受付時間に修正 |
| `sitegen/content.py` の `NEWS`（ニュース） 2件 | 日付が推定値のニュース 2件（`# 【要入力】` コメント付き） | 実際の日付に置き換え |

ニュースの日付は次の2件が推定値です。

- 『外資系PM1年目の教科書』の刊行予定に関するお知らせ（2026-06-01）
- Lead Japan 合同会社の設立に関するお知らせ（2026-04-01）

サイト公開のお知らせ（2026-10-19）も、公開当日の日付に更新してください。

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

### 独自ドメインを使う場合

1. ドメインを取得します（ドメイン費用のみ有料）。
2. Cloudflare の Pages プロジェクト → **Custom domains** → **Set up a custom domain** でドメイン（例: `www.example.co.jp`）を追加します。
3. 画面の案内に従って DNS を設定します（ドメインを Cloudflare で管理している場合は自動、他社 DNS の場合は表示された CNAME レコードを追加）。
4. 有効になったら `sitegen/content.py` の `SITE_URL` を独自ドメインの URL に変更し、push します。

内部リンク・CSS・画像は `/` から始まるルート基準のパスです（`sitegen/render.py` の `url()`）。どの階層の存在しない URL（例: `/a/b/c`）でも、404 ページが正しい見た目で表示されます。その代わり、サイトはドメインの一番上（`https://example.co.jp/`）に置く前提で、サブフォルダ（`https://example.com/leadjapan/`）への設置や、HTML ファイルをダブルクリックして直接開く確認には対応しません。確認は「プレビュー」の手順で行ってください。

### 検索エンジン・SNS 向けの情報

`SITE_URL` をもとに、ビルド時に次のものを自動で作ります（`sitegen/seo.py`）。`SITE_URL` を独自ドメインに変えれば、すべて追従します。

- 各ページの正規 URL（`canonical`）と SNS 共有用の情報（OGP）。共有時の画像は、記事に画像があればその画像、なければトップページの写真です。
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

**スラッグの注意:** 公開後にスラッグを変えると記事の URL が変わり、以前の URL は表示できなくなります。公開前に決めてください。

### プレビュー

記事の編集画面にあるプレビューのリンクから、実際のサイトと同じレイアウトで表示を確認できます（下書きも確認できます）。

### 公開する（「サイトに反映」）

1. 公開したい記事の「状態」を「公開」にして保存します。下書きのままの記事や、公開から「下書き」に戻した記事はサイトに出ません。
2. 記事一覧の「サイトに反映」ボタンを押し、確認画面で実行します。
3. `content/news.json` と `static/img/news/` を書き出し、テスト実行・コミット・GitHub への push を行います。

**必ず `main` ブランチで行い、この Mac で GitHub にログイン済みである必要があります**（`gh auth login` を済ませるか、git の認証情報を設定してください）。

結果のメッセージ:

| メッセージ | 意味 |
| --- | --- |
| 数分でサイトに反映されます | 成功。push 後、数分で公開サイトが更新されます |
| 変更はありません | 前回の反映から変更がなく、送信待ちのコミットもありません |
| テストが失敗したため反映を中止しました | サイトのテストが失敗。表示された出力を確認してください。ファイルは元に戻され、コミットされません |
| GitHub への送信に失敗しました | オフラインや認証切れなど。コミットは保存済みで、ログインし直して再度「サイトに反映」を押すと送信されます |
| GitHub 側に新しい変更があるため送信できませんでした | GitHub 上に自分の知らない更新があります。コミットは保存済みです。サイトの管理者に連絡してください |
| 別の反映処理が実行中です | 「サイトに反映」が二重に押されました。しばらく待ってからやり直してください |
| main ブランチで実行してください | `main` 以外のブランチにいます。`git switch main` してください |
| 予期しないエラーが発生しました | 想定外の問題です。ファイルは元に戻されます。メッセージを管理者に伝えてください |
| その他のエラー（書き出し・コミットの失敗） | メッセージに原因が出ます。ファイルは元に戻されます |

公開先は Cloudflare Pages（https://leadjapan-hp.pages.dev/ ）です。`main` への push 後、Cloudflare 側のビルドが終わると数分で反映されます。

### バックアップ

- 管理画面のデータベース（`cms/db.sqlite3`）と画像（`cms/media/`）は OneDrive 内にあり、Git 管理対象外です。OneDrive が履歴を保持します。
- サイトの元データは Git で管理される `content/news.json`（と `static/img/news/`）です。データベースを失っても、`import_news` で記事の文章を復元できます（画像は復元されないため、`cms/media/` のバックアップも残してください）。ただし、公開（「公開」状態で反映）済みの記事のみが対象です。下書きはデータベースにしか存在しません。

### 管理画面のテスト

```
~/.venvs/leadjapan-cms/bin/python cms/manage.py test press
```

## お問い合わせ

お問い合わせはメールアドレスでの受付です。有料のフォームサービスは使用していません。無料の Google フォームを追加する場合は、`sitegen/pages.py` の `body_contact` にあるコメント箇所に埋め込みを追加してください。

## 注意事項

- プライバシーポリシーの文面は草案です。公開前に内容を確認してください。
- スクロール演出は Chrome / Edge / Safari 26 以降で動作します。それ以外のブラウザでは、演出なしでコンテンツが静的に表示されます。
- 独自ドメインを後で使う場合は、ドメイン取得費用のみ有料です（任意）。手順は「Cloudflare Pages での公開」の「独自ドメインを使う場合」を参照してください。

## 画像のクレジット

- トップページの写真: Louie Martinez / Unsplash（[Unsplash ライセンス](https://unsplash.com/license)、商用利用可・クレジット表記は任意）。元画像: https://unsplash.com/photos/IocJwyqRv3M
- 写真を差し替えるときは `static/img/hero-tokyo.jpg` を同じ名前で置き換えます（横長・1920px 程度・800KB 未満）。
