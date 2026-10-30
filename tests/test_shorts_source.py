import copy
import importlib
import json
import os
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch

from shorts_source import candidate_from_sections, draft_bundle, validate_provenance, validate_usage_review
from test_quality import lesson, markdown


def selected_lesson():
    data = lesson()
    data['Shorts Candidate'] = json.dumps({
        'expression': 'invest in', 'meaning_ja': '〜に投資する',
        'sentence': data['Script'],
        'sentence_ja': 'その会社は新しい配送システムに投資するかもしれません。',
    }, ensure_ascii=False)
    return data


class SourceQuoteTests(unittest.TestCase):
    def test_generated_output_cannot_self_certify_external_usage(self):
        data = selected_lesson(); value = json.loads(data['Shorts Candidate'])
        value['usage_review'] = {'status':'verified'}
        data['Shorts Candidate'] = json.dumps(value)
        self.assertNotIn('usage_review',candidate_from_sections(data))

    def test_usage_record_is_bound_to_expression_and_requires_transfer(self):
        item = candidate_from_sections(selected_lesson())
        record = {
            'status':'verified','method':'primary_source_editorial_check',
            'expression':'invest in','script_sha256':item['script_sha256'],
            'transfer_note_ja':'投資対象が変わっても使える。',
            'reuse_contexts_ja':['設備への投資','教育への投資'],
            'references':[{'kind':'dictionary','publisher':'Test fixture','title':'Test fixture',
                           'url':'https://example.org/entry','excerpt':'invest in','checked_on':'2026-10-29'}],
        }
        self.assertTrue(validate_usage_review(item,record))
        self.assertFalse(validate_usage_review(item,{**record,'reuse_contexts_ja':[]}))
        self.assertFalse(validate_usage_review(item,{**record,'expression':'investment'}))
        self.assertFalse(validate_usage_review(item,{**record,'script_sha256':'changed'}))
        bad = copy.deepcopy(record);bad['references'][0]['excerpt']='investment'
        self.assertFalse(validate_usage_review(item,bad))
        self.assertFalse(validate_usage_review(item,None))

    def test_exact_sentence_and_offsets_not_vocabulary_practice(self):
        data = selected_lesson()
        item = candidate_from_sections(data)
        self.assertTrue(validate_provenance(item, data['Script']))
        self.assertEqual('invest in', data['Script'][item['expression_start']:item['expression_end']])
        bad = json.loads(data['Shorts Candidate'])
        bad['sentence'] = 'The company will invest in new delivery systems.'
        data['Vocabulary'] += '\nExample: '+bad['sentence']
        data['Shorts Candidate'] = json.dumps(bad)
        self.assertIsNone(candidate_from_sections(data))

    def test_changed_script_or_quote_is_rejected(self):
        data = selected_lesson(); item = candidate_from_sections(data)
        self.assertFalse(validate_provenance(item, data['Script'].replace('might', 'will')))
        tampered = {**item, 'sentence': item['sentence'].replace('might', 'will')}
        self.assertFalse(validate_provenance(tampered, data['Script']))

    def test_cut_clause_and_changed_expression_are_rejected(self):
        data = selected_lesson(); item = json.loads(data['Shorts Candidate'])
        for change in ({'sentence': 'invest in new delivery systems.'}, {'expression': 'investment'}):
            with self.subTest(change=change):
                data['Shorts Candidate'] = json.dumps({**item, **change})
                self.assertIsNone(candidate_from_sections(data))

    def test_missing_or_bad_optional_selection_skips_without_core_failure(self):
        data = lesson()
        for value in ('', 'null', 'invalid JSON', '[]', '{"expression":12}'):
            data['Shorts Candidate'] = value
            self.assertIsNone(candidate_from_sections(data))

    def test_single_basic_word_is_not_a_short_expression(self):
        data = selected_lesson()
        item = json.loads(data['Shorts Candidate'])
        item['expression'] = 'company'
        item['meaning_ja'] = '会社'
        data['Shorts Candidate'] = json.dumps(item)
        self.assertIsNone(candidate_from_sections(data))

    def test_bundle_keeps_original_script_and_publication_identity(self):
        data = selected_lesson(); item = candidate_from_sections(data)
        result = draft_bundle(item, data['Script'], episode_id=123,
                              lesson_url='https://econenglish.jp/?p=1',
                              source_url='https://www.cnbc.com/story', title='過去の教材',
                              published_at='2026-10-02', review_status='independent_review_passed')
        self.assertEqual(data['Script'], result['script'])
        self.assertEqual('123', result['episode_id'])
        self.assertFalse(result['youtube_upload_performed'])


class ShortsExportBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        keys = ('OPENAI_API_KEY', 'S3_BUCKET_NAME', 'WP_URL', 'WP_USER', 'WP_APP_PASS',
                'SPREAKER_SHOW_ID', 'SPREAKER_OAUTH_TOKEN', 'SPREAKER_REFRESH_TOKEN')
        with patch.dict(os.environ, {key:'test-placeholder' for key in keys}), patch('boto3.client'):
            cls.main = importlib.import_module('main')

    def run_handler(self, *, approved, enabled=True, wp_link='https://econenglish.jp/?p=1', fail_export=False):
        main = self.main; data = selected_lesson()
        article = SimpleNamespace(title='News', summary='Facts', link='https://www.cnbc.com/story')
        def review(source, sections, shorts_verdict=None, review_details=None):
            shorts_verdict['approved'] = approved
            return True
        def upload(path, bucket, folder):
            if folder == 'shorts/drafts' and fail_export:
                raise TimeoutError()
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {'SHORTS_DRAFT_EXPORT':'1' if enabled else '0'}))
            for name, value in (
                ('recent_lessons',(set(), [])),
                ('collect_candidates',[{'id':'test','title':'News','summary':'Facts','url':article.link}]),
                ('rank_candidates',[{'id':'test','title':'News','summary':'Facts','url':article.link,'selection_reason':'教材に適合'}]),
                ('fetch_article', article), ('source_text', 'source '*150),
                ('is_significant', (True,'yes')), ('gpt', markdown(data)),
                ('synthesize_speech','/tmp/test.mp3'),
                ('upload_episode_to_spreaker', {'episode_id':123,'stream_url':'https://example.com/audio.mp3'}),
                ('post_to_wordpress',wp_link), ('update_episode_description',None), ('save_rss',None),
            ):
                stack.enter_context(patch.object(main,name,return_value=value))
            stack.enter_context(patch.object(main,'review_lesson',side_effect=review))
            s3 = stack.enter_context(patch.object(main,'upload_to_s3',side_effect=upload))
            result = main.handler()
            folders = [c.args[2] for c in s3.call_args_list]
        return result,folders

    def test_only_enabled_reviewed_published_sources_are_exported(self):
        for approved, enabled, link, expected in (
            (True,True,'https://econenglish.jp/?p=1',True),
            (False,True,'https://econenglish.jp/?p=1',False),
            (True,False,'https://econenglish.jp/?p=1',False),
            (True,True,None,False),
        ):
            with self.subTest(approved=approved, enabled=enabled, link=link):
                result,folders = self.run_handler(approved=approved,enabled=enabled,wp_link=link)
                self.assertEqual(200,result['statusCode'])
                self.assertEqual(expected,'shorts/drafts' in folders)

    def test_export_failure_does_not_fail_or_repeat_podcast_publication(self):
        result,folders = self.run_handler(approved=True,fail_export=True)
        self.assertEqual(200,result['statusCode'])
        self.assertEqual(['audio','rss','shorts/drafts'],folders)

    def test_short_review_is_separate_and_requires_boolean_true(self):
        for shorts_flag, approved in ((True,True),(False,False),('true',False)):
            content = {k:True for k in ('source_sufficient','facts_supported','grammar_correct','answers_correct','metadata_accurate')}
            content['shorts_accurate'] = shorts_flag
            response = SimpleNamespace(choices=[SimpleNamespace(finish_reason='stop',message=SimpleNamespace(content=json.dumps(content)))])
            with patch.object(self.main.client.chat.completions,'create',return_value=response):
                verdict = {}
                self.assertTrue(self.main.review_lesson('source',selected_lesson(),verdict))
                self.assertEqual(approved,verdict['approved'])


if __name__ == '__main__':
    unittest.main()
