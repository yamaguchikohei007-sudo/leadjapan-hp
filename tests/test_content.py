import unittest

from sitegen import content as c
from sitegen.news import CATEGORIES


class ContentTest(unittest.TestCase):
    def test_company_name(self):
        self.assertEqual(c.SITE["name"], "Lead Japan 合同会社")

    def test_four_businesses_in_order(self):
        self.assertEqual([b.title for b in c.BUSINESSES],
                         ["AIソリューションの展開", "コンサルティング", "システム開発", "出版"])

    def test_system_dev_details(self):
        d = c.BUSINESSES[2].details
        self.assertIn("プロジェクトマネジメント関連", " ".join(d))
        self.assertIn("スタートアップ向け業務システムの開発", " ".join(d))

    def test_book_title_in_publishing(self):
        # NEWS is owner-edited content and must never block publishing; check static copy only.
        self.assertIn("外資系PM1年目の教科書", " ".join(c.BUSINESSES[3].details) + c.BUSINESSES[3].summary)

    def test_news_sorted_newest_first(self):
        dates = [n.date for n in c.NEWS]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_news_categories(self):
        self.assertTrue({n.category for n in c.NEWS} <= set(CATEGORIES))

    def test_no_revenue_claims(self):
        # static company copy only: NEWS is owner-written and may legitimately mention amounts.
        blob = repr({k: v for k, v in c.__dict__.items() if k != "NEWS"})
        for word in ("売上高", "億円", "万円"):
            self.assertNotIn(word, blob)

    def test_nav_targets(self):
        self.assertEqual([f for f, _ in c.NAV],
                         ["company.html", "business.html", "message.html", "pm-book.html", "news.html",
                          "contact.html"])


if __name__ == "__main__":
    unittest.main()
