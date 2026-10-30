"""Regression checks for the prior noun-introduction/verb-example mismatch."""
import json
from pathlib import Path
import unittest

from render_vocabulary import scenes_for
from from_podcast import video_from_bundle
from shorts_source import candidate_from_sections, draft_bundle


class VocabularyContractTests(unittest.TestCase):
    def setUp(self):
        data = json.loads(Path(__file__).with_name('vocabulary-pilots.json').read_text())
        self.rate_cut = next(v for v in data['videos'] if v['id'] == '02-rate-cut')

    def test_prior_rate_cut_mismatch_is_rejected(self):
        old = {**self.rate_cut, 'english_example': 'The central bank cut interest rates.'}
        with self.assertRaises(ValueError):
            scenes_for(old)

    def test_same_phrase_is_used_for_example_and_replay(self):
        scenes = scenes_for(self.rate_cut)
        English = {kind: text for kind, text, lang, *_ in scenes if lang == 'en'}
        self.assertEqual(English, {
            'term': 'a rate cut.',
            'example': 'The central bank announced a rate cut.',
            'extension': 'cut interest rates.',
            'replay': 'The central bank announced a rate cut.',
        })

    def test_extension_is_after_consistent_example_and_explicitly_introduced(self):
        scenes = scenes_for(self.rate_cut)
        kinds = [s[0] for s in scenes]
        self.assertLess(kinds.index('translation'), kinds.index('extension_intro'))
        self.assertLess(kinds.index('extension_intro'), kinds.index('extension'))
        self.assertIn('動詞', next(s[1] for s in scenes if s[0] == 'extension_intro'))

    def test_partial_word_does_not_count_as_same_expression(self):
        changed = {**self.rate_cut, 'english_example': 'The central bank announced a rate cutting plan.'}
        with self.assertRaises(ValueError):
            scenes_for(changed)

    def test_source_backed_quote_and_article_cannot_silently_change(self):
        script = self.rate_cut['english_example']
        selection = candidate_from_sections({'Script':script,'Shorts Candidate':json.dumps({
            'expression':'a rate cut','meaning_ja':'利下げ','sentence':script,
            'sentence_ja':'中央銀行が利下げを発表した。',
        })})
        bundle = draft_bundle(selection,script,episode_id=123,
                              lesson_url='https://econenglish.jp/?p=1',
                              source_url='https://example.org/news',title='Test',
                              published_at='2026-10-02',review_status='manual_preview_review')
        with self.assertRaises(ValueError):
            video_from_bundle(bundle)
        bundle['usage_review'] = {
            'status':'verified','method':'primary_source_editorial_check',
            'expression':selection['expression'],'script_sha256':selection['script_sha256'],
            'transfer_note_ja':'複数の経済・企業ニュースで使える。',
            'reuse_contexts_ja':['中央銀行の政策発表','企業の資金調達の説明'],
            'references':[{'kind':'dictionary','publisher':'Test fixture','title':'Test dictionary fixture',
                           'url':'https://example.org/dictionary','excerpt':'a rate cut','checked_on':'2026-10-29'}],
        }
        video = video_from_bundle(bundle)
        scenes_for(video)
        for changes in ({'english_example':'The central bank cut interest rates.'},
                        {'english_term':'rate cut'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                scenes_for({**video,**changes})


if __name__ == '__main__':
    unittest.main()
