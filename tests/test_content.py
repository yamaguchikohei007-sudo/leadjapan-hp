import unittest

from sitegen import content as c
from sitegen.news import CATEGORIES


class ContentTest(unittest.TestCase):
    def test_company_name(self):
        self.assertEqual(c.SITE["name"], "Lead Japan 合同会社")

    def test_one_package_of_four_services(self):
        self.assertEqual([sv.title for sv in c.SERVICES],
                         ["業務オペレーション分析", "情報共有と業務の標準化", "AI・システム開発",
                          "運用設計と定着支援"])
        # not only AI: standardisation, handover and shared information are part of the package (v1.7)
        blob = " ".join(d for sv in c.SERVICES for d in sv.details)
        for word in ("引き継げる", "更新責任", "不要な業務の廃止", "確認・承認"):
            self.assertIn(word, blob)
        self.assertEqual(len({sv.slug for sv in c.SERVICES}), 4)

    def test_three_stages_with_published_terms(self):
        self.assertEqual([st.label for st in c.STAGES], ["Stage 1", "Stage 2", "Stage 3"])
        self.assertIn("30万円（税別）", c.STAGES[0].terms)
        self.assertIn("見積もり制", c.STAGES[1].terms)
        self.assertIn("月額50万円（税別）", c.STAGES[2].terms)

    def test_terms_left_out_until_decided(self):
        # v1.7: no unlimited-scope wording, no "about half a year", and no fee credit until its start date is decided
        static = repr({k: v for k, v in c.__dict__.items() if k != "NEWS"})
        for phrase in ("一律", "対象範囲によらず", "雇うような", "約半年", "実質0円", "全額差し引", "1ヶ月以内", "省人化"):
            self.assertNotIn(phrase, static)
        for text in (c.PROCESS_NOTE, c.CONTACT_PROCESS, dict(c.FAQ)["期間はどのくらいかかりますか。"]):
            self.assertIn("4〜6ヶ月", text)
            self.assertIn("7〜9ヶ月", text)

    def test_no_headcount_promise(self):
        static = repr({k: v for k, v in c.__dict__.items() if k != "NEWS"})
        for phrase in ("半分", "半減", "採用不要", "採用が不要"):
            self.assertNotIn(phrase, static)
        self.assertNotIn("人員を半分にできますか。", dict(c.FAQ))

    def test_saas_fee_not_priced_yet(self):
        blob = " ".join([*c.STAGES[2].notes, *(a for _, a in c.FAQ), *c.PRODUCT_TEXT])
        self.assertIn("提供開始時にご案内", blob)
        self.assertNotRegex(" ".join(c.PRODUCT_TEXT), r"\d+円")

    def test_result_is_the_founders_own(self):
        # 30%→5% is the founder's result at a foreign-affiliated company, not a Lead Japan case study
        self.assertIn("代表個人", c.RESULT_NOTE)
        self.assertIn("Lead Japan としての支援実績ではありません", c.RESULT_NOTE)
        self.assertIn("保証するものではなく", c.RESULT_NOTE)
        for text in (c.RESULT_SHORT, c.RESULT_TEXT[0], " ".join(c.MESSAGE)):
            self.assertIn("外資系日本法人での業務", text)
            self.assertNotIn("前職", text)

    def test_book_title_matches_book_page(self):
        self.assertIn(f"『{c.BOOK_TITLE}』", " ".join(c.MESSAGE))
        static = repr({k: v for k, v in c.__dict__.items() if k != "NEWS"})
        self.assertNotIn("外資系PM1年目の教科書", static)

    def test_news_sorted_newest_first(self):
        dates = [n.date for n in c.NEWS]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_news_categories(self):
        self.assertTrue({n.category for n in c.NEWS} <= set(CATEGORIES))

    def test_no_revenue_claims(self):
        # static company copy only: NEWS is owner-written and may legitimately mention amounts.
        blob = repr({k: v for k, v in c.__dict__.items() if k != "NEWS"})
        for word in ("売上高", "億円"):
            self.assertNotIn(word, blob)

    def test_amounts_only_in_published_prices(self):
        # 万円 appears only in the stage prices (STAGES, FAQ, contact page note), never as a claim elsewhere
        priced = {"NEWS", "STAGES", "FAQ", "CONTACT_PROCESS"}
        blob = repr({k: v for k, v in c.__dict__.items() if k not in priced})
        self.assertNotIn("万円", blob)

    def test_nav_targets(self):
        self.assertEqual([f for f, _ in c.NAV],
                         ["company.html", "business.html", "message.html", "pm-book.html", "news.html",
                          "contact.html"])


if __name__ == "__main__":
    unittest.main()
