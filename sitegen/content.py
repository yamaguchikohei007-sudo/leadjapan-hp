"""Site content for Lead Japan 合同会社. Unknown facts use PLACEHOLDER."""
from __future__ import annotations

from dataclasses import dataclass

from sitegen.news import NewsItem, load_news

PLACEHOLDER = "【要入力】"

SITE: dict[str, str] = {
    "name": "Lead Japan 合同会社",
    "name_en": "Lead Japan LLC",
    "tagline": "日本を導き、世界へ。",
    "philosophy": (
        "Lead Japan 合同会社は、日本を導き、世界の中で日本の立ち位置を発展させていく。"
        "その思いを込めて名付けました。日本の成長に寄与するか――それが私たちの価値基準です。"
    ),
    "location": "東京都",
    "address": "東京都中野区",
    "founded": "2026年10月19日",
    "representative": "山口康平",
    "email": PLACEHOLDER,  # TBC
    "status": "2026年設立。現在、各事業の立ち上げを進めています。",
}


@dataclass(frozen=True)
class Business:
    slug: str
    number: str
    title: str
    title_en: str
    summary: str
    details: tuple[str, ...]


BUSINESSES: tuple[Business, ...] = (
    Business(
        slug="ai",
        number="01",
        title="AIソリューションの展開",
        title_en="AI Solutions",
        summary="生成AIをはじめとするAI技術を、日本の企業の現場で実際に使える形にして届けます。",
        details=(
            "業務の中でAIを活用できる領域の整理と、導入方針のご提案",
            "生成AIを活用した業務効率化ソリューションの企画・展開",
            "AI活用を社内に定着させるための運用設計と支援",
        ),
    ),
    Business(
        slug="consulting",
        number="02",
        title="コンサルティング",
        title_en="Consulting",
        summary="事業とプロジェクトの課題に向き合い、成果につながる実行まで伴走します。",
        details=(
            "プロジェクトの立ち上げから推進までを支えるマネジメント支援",
            "事業課題の整理と、実行可能な改善計画の策定",
            "グローバルな視点を取り入れた組織・業務プロセスの見直し",
        ),
    ),
    Business(
        slug="system",
        number="03",
        title="システム開発",
        title_en="System Development",
        summary="現場の業務に寄り添い、使いやすく成長に合わせて拡張できるシステムを開発します。",
        details=(
            "プロジェクトマネジメント関連システムの開発",
            "スタートアップ向け業務システムの開発",
            "既存業務の見直しを伴うシステム化のご相談",
        ),
    ),
    Business(
        slug="publishing",
        number="04",
        title="出版",
        title_en="Publishing",
        summary="実務で培った知見を書籍にまとめ、多くの方に届けます。",
        details=(
            "『外資系PM1年目の教科書』（2026年刊行予定）の企画・出版",
            "プロジェクトマネジメントやキャリアに関する実践的な知見の発信",
        ),
    ),
)


SITE_URL = "https://leadjapan-hp.pages.dev"

NEWS: tuple[NewsItem, ...] = load_news()

MESSAGE_TITLE = "日本を導き、世界へ。"

MESSAGE: tuple[str, ...] = (
    "この度は Lead Japan 合同会社のウェブサイトをご覧いただき、誠にありがとうございます。",
    "当社の社名には、日本を導き、世界の中で日本の立ち位置を発展させていきたいという思いを込めています。日本の成長に寄与するかどうか。それを、私たちはすべての判断の拠り所としています。",
    "事業の柱は、AIソリューションの展開、コンサルティング、システム開発、出版の四つです。AIという新しい力を現場で使える形にし、プロジェクトマネジメントの知見を通じて、日本企業が世界で力を発揮するための土台づくりをお手伝いします。",
    "出版では、私自身の経験をもとに『外資系PM1年目の教科書』を2026年に刊行する予定です。働き方や仕事の進め方を言葉にして共有することも、日本の成長につながると考えています。",
    "まだ歩み始めたばかりの会社ですが、一つひとつの取り組みを誠実に積み重ねてまいります。今後とも、ご指導ご鞭撻を賜りますようお願い申し上げます。",
)

PRIVACY: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "基本方針",
        (
            "Lead Japan 合同会社（以下「当社」）は、個人情報の重要性を認識し、個人情報の保護に関する法令を遵守するとともに、適切に取り扱うことに努めます。",
        ),
    ),
    (
        "取得する個人情報",
        (
            "当社は、お問い合わせの際にお客様からご提供いただく氏名、メールアドレス、お問い合わせ内容などの個人情報を取得することがあります。",
            "個人情報は、適法かつ公正な手段により取得いたします。",
        ),
    ),
    (
        "利用目的",
        (
            "取得した個人情報は、お問い合わせへの回答、ご連絡、およびサービスのご案内のために利用します。",
            "上記の目的以外には利用いたしません。",
        ),
    ),
    (
        "閲覧地域の表示",
        (
            "本サイトのトップページでは、閲覧者の IP アドレスから当社のサイト配信事業者（Cloudflare, Inc.）が推定した大まかな地域（都道府県単位）を、地図上の表示のためだけに利用します。",
            "この情報は表示の際に一時的に用いるのみで、当社が保存・記録することはありません。",
        ),
    ),
    (
        "第三者提供",
        (
            "当社は、法令に基づく場合を除き、ご本人の同意なく個人情報を第三者に提供することはありません。",
        ),
    ),
    (
        "安全管理",
        (
            "当社は、個人情報の漏えい、滅失、毀損を防止するため、必要かつ適切な安全管理措置を講じます。",
        ),
    ),
    (
        "開示・訂正・削除の請求",
        (
            "ご本人から個人情報の開示、訂正、削除などのご請求があった場合は、ご本人であることを確認のうえ、法令に基づき速やかに対応いたします。",
            "ご請求は、下記のお問い合わせ窓口までご連絡ください。",
        ),
    ),
    (
        "お問い合わせ窓口",
        (
            f"事業者名：{SITE['name']}",
            f"所在地：{SITE['address']}",
            f"代表者：{SITE['representative']}",
            f"個人情報の取り扱いに関するお問い合わせは、次のメールアドレス、またはお問い合わせページからお寄せください。メールアドレス：{SITE['email']}",
        ),
    ),
    (
        "改定",
        (
            "当社は、法令の変更や運用の見直しに応じて、本方針を改定することがあります。改定後の内容は、本サイトに掲載した時点から効力を生じます。",
        ),
    ),
)

NAV: tuple[tuple[str, str], ...] = (
    ("company.html", "会社紹介"),
    ("business.html", "事業概要"),
    ("message.html", "代表挨拶"),
    ("news.html", "ニュースルーム"),
    ("contact.html", "お問い合わせ"),
)

HERO_SUB = "Lead Japan — Tokyo, Japan"
HERO_LEAD = (
    "AIソリューション、コンサルティング、システム開発、出版。"
    "4つの事業を通じて、日本の企業が世界で力を発揮するための土台をつくります。"
)

# トップページの各セクション: 英字の大見出し（飾り）と導入文
SECTION_DISPLAY: dict[str, str] = {
    "about": "Who we are",
    "business": "What we do",
    "message": "Our promise",
    "news": "Newsroom",
    "contact": "Let’s talk.",
}
ABOUT_LEAD = "日本の成長に寄与するか――それが、私たちの価値基準です。"
ABOUT_TEXT = "Lead Japan 合同会社は、日本を導き、世界の中で日本の立ち位置を発展させていく。その思いを込めて名付けました。"
# 代表挨拶（MESSAGE）からの抜粋。本文を直したらここも合わせる
MESSAGE_EXCERPT = "日本の成長に寄与するかどうか。それを、私たちはすべての判断の拠り所としています。"
CTA_LEAD = "AI導入・システム開発・出版に関するご相談、お見積もりなど、まずはお気軽にお問い合わせください。"
FOOTER_DESCRIPTION = (
    "日本を導き、世界へ。AIソリューション、コンサルティング、システム開発、出版を通じて、日本の成長に寄与します。"
)
FOOTER_CONTACT = "ご相談・お問い合わせはこちらから。"
COPYRIGHT = "© 2026 Lead Japan LLC"
PRIVACY_ENACTED = "2026年10月19日"

COMPANY_NAME_ORIGIN: tuple[str, ...] = (
    "社名の「Lead」には、人や物事を導き、先頭に立って進むという意味を込めています。",
    "「Japan」には、日本の成長に寄与し、世界の中での日本の立ち位置を高めていきたいという願いを託しました。",
    "この二つの言葉を合わせた名前が、私たちの目指す姿そのものです。",
)

CONTACT_INTRO = (
    "事業に関するご相談、取材・出版に関するお問い合わせは、下記のメールアドレスまでご連絡ください。"
    "内容を確認のうえ、担当者よりご連絡いたします。"
)
CONTACT_HOURS = "平日 10:00〜18:00（土日祝・年末年始を除く）"
CONTACT_CATEGORIES: tuple[str, ...] = ("AIソリューション", "コンサルティング", "システム開発", "出版・取材")

NOT_FOUND_TEXT = (
    "お探しのページは移動または削除された可能性があります。"
    "URLをご確認のうえ、トップページからあらためてお探しください。"
)

# filename -> (title, meta description)
PAGE_META: dict[str, tuple[str, str]] = {
    "index.html": (
        "Lead Japan 合同会社 | 日本を導き、世界へ。",
        "Lead Japan 合同会社（東京都）の公式サイト。AIソリューションの展開、"
        "コンサルティング、システム開発、出版を通じて、日本の成長に寄与します。",
    ),
    "company.html": (
        "会社紹介 | Lead Japan 合同会社",
        "Lead Japan 合同会社の企業理念、社名の由来、会社概要をご紹介します。",
    ),
    "business.html": (
        "事業概要 | Lead Japan 合同会社",
        "AIソリューションの展開、コンサルティング、システム開発、出版。Lead Japan 合同会社の事業をご紹介します。",
    ),
    "message.html": (
        "代表挨拶 | Lead Japan 合同会社",
        "Lead Japan 合同会社 代表からのご挨拶。",
    ),
    "news.html": (
        "ニュースルーム | Lead Japan 合同会社",
        "Lead Japan 合同会社からのお知らせ・ニュースをご案内します。",
    ),
    "privacy.html": (
        "プライバシーポリシー | Lead Japan 合同会社",
        "Lead Japan 合同会社の個人情報の取り扱いについて定めたプライバシーポリシーです。",
    ),
    "contact.html": (
        "お問い合わせ | Lead Japan 合同会社",
        "Lead Japan 合同会社へのお問い合わせ方法のご案内です。",
    ),
    "404.html": (
        "ページが見つかりません | Lead Japan 合同会社",
        "お探しのページが見つかりませんでした。トップページからお探しください。",
    ),
}

# 公開前にオーナーが確認すべき項目（サイトには表示されない。ビルド時に「要確認」として表示）
UNCONFIRMED: tuple[str, ...] = (
    "NEWS: 書籍刊行のお知らせの日付（推定値 2026-06-01）",
    "NEWS: サイト公開日の日付（2026-10-19。公開当日の日付に更新）",
    "代表挨拶の本文（代表者本人による確認）",
    "受付時間（CONTACT_HOURS）",
    "社名の由来の文章（COMPANY_NAME_ORIGIN）",
    "プライバシーポリシー（専門家による確認を推奨）",
)
