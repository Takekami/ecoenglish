from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from shorts_source import candidate_from_sections, draft_bundle
from daily_worker import process_bundle, verify_lesson
from usage_check import allowed, cited_urls, fetch_attestation


def fixture():
    script='The companies plan to enter merger discussions next month.'
    raw={'expression':'enter merger discussions','meaning_ja':'合併協議に入る',
         'sentence':script,'sentence_ja':'両社は来月、合併協議に入る計画です。'}
    item=candidate_from_sections({'Script':script,'Shorts Candidate':json.dumps(raw)})
    return draft_bundle(item,script,episode_id='987654',lesson_url='https://econenglish.jp/?p=55',
                        source_url='https://www.cnbc.com/source',title='合併協議',
                        published_at='2026-10-30T06:00:00+10:00',review_status='independent_review_passed')


def review(bundle,*args):
    return {'status':'verified','method':'primary_source_automated_check','context_review_passed':True,
            'expression':bundle['selection']['expression'],'script_sha256':bundle['selection']['script_sha256'],
            'transfer_note_ja':'他の企業にも使える','reuse_contexts_ja':['製造業の合併','銀行の合併'],
            'references':[{'kind':'company_announcement','publisher':'Issuer','title':'Merger',
                           'url':'https://view.news.eu.nasdaq.com/view','excerpt':'enter merger discussions',
                           'checked_on':'2026-10-30','page_sha256':'a'*64}]}


class WorkerTests(unittest.TestCase):
    def test_full_chain_uses_source_then_usage_then_render_then_private_upload(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);config={'upload_ledger':str(root/'upload.db'),'token':'unused'}
            order=[]
            def renderer(v,work,cache):
                order.append('render');target=work/v['id'];target.mkdir()
                movie=target/(v['id']+'.mp4');movie.write_bytes(b'fixture')
                (target/'upload-draft.json').write_text(json.dumps({'sha256':hashlib.sha256(b'fixture').hexdigest(),
                    'podcast_provenance':v['podcast_provenance'],'example_origin':'podcast_script',
                    'duration_seconds':50,'title':v['title'],'description':v['lesson_url']}))
                return target
            def usage(bundle,*args):order.append('usage');return review(bundle)
            def lesson(bundle):order.append('lesson');return '#eel-script'
            with patch('daily_worker.upload',return_value='private-id') as upload:
                result=process_bundle(fixture(),config,root,lesson_check=lesson,usage_check=usage,
                                      renderer=renderer,client=MagicMock(),youtube=MagicMock(),media_factory=MagicMock())
                self.assertEqual('uploaded_private',result['state'])
                self.assertEqual(['lesson','usage','render'],order)
                plan=upload.call_args.args[2]
                self.assertEqual('private',plan['body']['status']['privacyStatus'])
                self.assertIn('#eel-script',plan['body']['snippet']['description'])
                self.assertNotIn('publishAt',plan['body']['status'])
                process_bundle(fixture(),config,root,lesson_check=lesson,client=MagicMock())
                upload.assert_called_once()

    def test_no_attestation_stops_before_paid_render_or_upload(self):
        with tempfile.TemporaryDirectory() as folder,patch('daily_worker.upload') as upload:
            render=MagicMock()
            def no_evidence(*args):raise ValueError('NO_LIVE_PRIMARY_SOURCE_ATTESTATION')
            result=process_bundle(fixture(),{'upload_ledger':str(Path(folder)/'db')},Path(folder),
                   lesson_check=lambda b:'#eel-script',usage_check=no_evidence,renderer=render,client=MagicMock())
            self.assertEqual('held',result['state']);render.assert_not_called();upload.assert_not_called()

    def test_changed_published_script_stops(self):
        response=MagicMock()
        response.json.return_value={'status':'publish','date_gmt':'2026-10-29T20:00:00',
            'content':{'rendered':'<h2>Script</h2><p>Changed script.</p><h2>Vocabulary</h2>'}}
        with patch('requests.get',return_value=response),self.assertRaisesRegex(ValueError,'PUBLISHED_SCRIPT_MISMATCH'):
            verify_lesson(fixture())

    def test_reference_urls_are_not_model_guesses_or_untrusted_hosts(self):
        self.assertFalse(allowed('http://127.0.0.1'))
        self.assertFalse(allowed('https://dictionary.cambridge.org.evil.test/a'))
        self.assertTrue(allowed('https://dictionary.cambridge.org/dictionary/english/talks'))
        response={'output':[{'type':'web_search_call','action':{'sources':[
            {'url':'https://merriam-webster.com/dictionary/merger'}, {'url':'https://evil.test/'}]}}]}
        self.assertEqual(['https://merriam-webster.com/dictionary/merger'],cited_urls(response))
        self.assertEqual([],cited_urls({'output':[{'type':'web_search_call','action':{'sources':None},'content':None}]}))

    def test_live_page_must_actually_contain_exact_expression(self):
        response=MagicMock(status_code=200,headers={'Content-Type':'text/html'})
        response.__enter__.return_value=response
        response.iter_content.return_value=[b'<html>different words</html>']
        with patch('usage_check.requests.get',return_value=response),patch('usage_check.trafilatura.extract',return_value='different words'):
            self.assertIsNone(fetch_attestation('https://view.news.eu.nasdaq.com/view','enter merger discussions'))


if __name__=='__main__':unittest.main()
