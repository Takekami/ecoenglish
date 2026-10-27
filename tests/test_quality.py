import importlib
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from content_quality import source_text, validate_lesson, parse_lesson, SECTIONS


def lesson():
    data = {name: "教材の解説" for name in SECTIONS}
    sentence = "The company might invest in new delivery systems."
    data.update({
        "Script": sentence,
        "Grammar Quote": sentence,
        "Grammar Point": f"might + verb – “{sentence}”（可能性を示す）",
        "Vocabulary": "\n".join(f"- word{i} : definition" for i in range(5)),
        "Listening Questions": "1. True/False: The plan is certain.\n2. MCQ: What?\n a) A\n b) B\n c) C\n d) D\n3. MCQ: Why?\n a) A\n b) B\n c) C\n d) D",
        "Reading Questions": "1. What?\n2. Why?\n3. Meaning?",
        "Answers": "1. False\n2. a) A\n3. b) B\n4. Investment.\n5. Demand.\n6. Possibility.",
        "Japanese Title": "配送会社への投資を英語で学ぶ｜中級者向け教材",
        "Meta Description": "配送会社への投資を題材に、ビジネス英語を学ぶ中級者向け教材です。音声と英文スクリプト、重要単語、日本語解説とクイズで学習できます。",
        "Introduction": "配送会社への投資を題材に、ビジネス英語を学びます。中級者向けの音声を聞いてから英文を読み、重要単語と文法を確認してクイズに答えてみましょう。",
    })
    return data


def markdown(data):
    return "\n\n".join(f"### {key}\n{value}" for key, value in data.items())


class QualityTests(unittest.TestCase):
    def test_valid_and_markdown_parse(self):
        self.assertEqual([], validate_lesson(parse_lesson(markdown(lesson()))))

    def test_mismatched_grammar_and_missing_answers(self):
        data = lesson()
        data["Grammar Quote"] = "A fabricated sentence is absent from the script."
        data["Answers"] = "1. True"
        errors = validate_lesson(data)
        self.assertIn("grammar quote not in script", errors)
        self.assertIn("invalid numbered items in Answers", errors)

    def test_missing_sections_and_malformed_mcq(self):
        data = lesson()
        del data["Introduction"]
        self.assertIn("missing Introduction", validate_lesson(data))
        data = lesson()
        data["Listening Questions"] = data["Listening Questions"].replace(" d) D", "")
        self.assertIn("MCQ requires a-d options", validate_lesson(data))

    @patch("content_quality.requests.get")
    def test_no_headline_fallback_or_untrusted_hosts(self, get):
        get.side_effect = __import__("requests").Timeout()
        self.assertEqual("", source_text("https://www.cnbc.com/story", "A short headline"))
        self.assertEqual("", source_text("http://127.0.0.1/story", "word " * 150))
        self.assertEqual(1, get.call_count)

    @patch("content_quality.requests.get")
    def test_substantive_rss_fallback(self, get):
        get.side_effect = __import__("requests").Timeout()
        self.assertTrue(source_text("https://www.cnbc.com/story", "<p>" + "word " * 150 + "</p>"))

    def test_duplicate_sections_rejected(self):
        with self.assertRaises(ValueError):
            parse_lesson("### Script\nOne\n### Script\nTwo")


class PublishBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        keys = ("OPENAI_API_KEY", "S3_BUCKET_NAME", "WP_URL", "WP_USER", "WP_APP_PASS",
                "SPREAKER_SHOW_ID", "SPREAKER_OAUTH_TOKEN", "SPREAKER_REFRESH_TOKEN",
                "SPREAKER_CLIENT_ID", "SPREAKER_CLIENT_SECRET")
        with patch.dict(os.environ, {key: "test-placeholder" for key in keys}), \
                patch("boto3.client"):
            cls.main = importlib.import_module("main")

    def test_invalid_or_rejected_lessons_have_no_publish_side_effects(self):
        main = self.main
        article = SimpleNamespace(title="News", summary="Facts", link="https://www.cnbc.com/story")
        for md, verdict in (("### Script\nOnly a script", True), (markdown(lesson()), False)):
            with self.subTest(verdict=verdict), \
                    patch.object(main, "fetch_article", return_value=article), \
                    patch.object(main, "source_text", return_value="verified source " * 150), \
                    patch.object(main, "is_significant", return_value=(True, "yes")), \
                    patch.object(main, "gpt", return_value=md), \
                    patch.object(main, "review_lesson", return_value=verdict), \
                    patch.object(main, "synthesize_speech") as tts, \
                    patch.object(main, "upload_to_s3") as s3, \
                    patch.object(main, "upload_episode_to_spreaker") as podcast, \
                    patch.object(main, "post_to_wordpress") as wp:
                self.assertEqual(204, main.handler()["statusCode"])
                for writer in (tts, s3, podcast, wp):
                    writer.assert_not_called()

    def test_reviewer_requires_actual_booleans_and_complete_json(self):
        main = self.main
        for result in ('{}', '{"facts_supported":"true"}', 'not JSON'):
            response = SimpleNamespace(choices=[SimpleNamespace(
                finish_reason="stop", message=SimpleNamespace(content=result))])
            with patch.object(main.client.chat.completions, "create", return_value=response):
                self.assertFalse(main.review_lesson("source", lesson()))

    def test_valid_lesson_publishes_japanese_metadata(self):
        main = self.main
        data = lesson()
        article = SimpleNamespace(title="News", summary="Facts", link="https://www.cnbc.com/story")
        with patch.object(main, "fetch_article", return_value=article), \
                patch.object(main, "source_text", return_value="source " * 150), \
                patch.object(main, "is_significant", return_value=(True, "yes")), \
                patch.object(main, "gpt", return_value=markdown(data)), \
                patch.object(main, "review_lesson", return_value=True), \
                patch.object(main, "synthesize_speech", return_value="/tmp/test.mp3"), \
                patch.object(main, "upload_to_s3"), \
                patch.object(main, "upload_episode_to_spreaker", return_value={"stream_url": "https://example.com/audio.mp3"}), \
                patch.object(main, "save_rss"), \
                patch.object(main, "post_to_wordpress", return_value="https://example.com/lesson") as wp:
            self.assertEqual(200, main.handler()["statusCode"])
            self.assertEqual(data["Japanese Title"], wp.call_args.args[0])
            self.assertEqual(data["Meta Description"], wp.call_args.kwargs["excerpt"])
            self.assertIn(data["Introduction"], wp.call_args.args[1])

    def test_insufficient_source_never_calls_generation(self):
        main = self.main
        article = SimpleNamespace(title="News", summary="Headline only", link="https://www.cnbc.com/story")
        with patch.object(main, "fetch_article", return_value=article), \
                patch.object(main, "source_text", return_value=""), \
                patch.object(main, "gpt") as generate, \
                patch.object(main, "post_to_wordpress") as publish:
            self.assertEqual(204, main.handler()["statusCode"])
            generate.assert_not_called()
            publish.assert_not_called()

    def test_wordpress_metadata_and_escaped_intro(self):
        import wp_poster
        from blog_template import build_blog_post_html
        response = MagicMock(status_code=201)
        response.json.return_value = {"link": "https://example.com/lesson"}
        with patch.object(wp_poster.requests, "post", return_value=response) as post:
            wp_poster.post_to_wordpress("日本語のタイトル", "<p>教材</p>", excerpt="日本語の説明")
            self.assertEqual("日本語の説明", post.call_args.kwargs["json"]["excerpt"])
        result = build_blog_post_html(*([""] * 13), introduction="学習 <script>unsafe</script>")
        self.assertIn("&lt;script&gt;", result)


if __name__ == "__main__":
    unittest.main()
