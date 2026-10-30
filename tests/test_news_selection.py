import collections
from contextlib import ExitStack
from datetime import datetime, timezone
import importlib
import io
import json
import os
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from news_selection import collect_candidates, parse_ranking
from content_quality import validate_lesson
from test_quality import lesson, markdown


class SelectionTests(unittest.TestCase):
    def test_all_feeds_dedup_history_and_stale_articles(self):
        now=datetime(2026,10,30,tzinfo=timezone.utc)
        entries=[{'title':'Valid','link':'https://www.cnbc.com/new','published':'Thu, 29 Oct 2026 10:00:00 GMT'},
                 {'title':'Duplicate','link':'https://www.cnbc.com/new'},
                 {'title':'Already published','link':'https://www.cnbc.com/old'},
                 {'title':'Stale','link':'https://www.cnbc.com/stale','published':'Thu, 01 Oct 2026 10:00:00 GMT'},
                 {'title':'Untrusted URL','link':'https://example.com/not-allowed'}]
        response=MagicMock(content=b'feed')
        events=[]
        with patch('news_selection.requests.get',return_value=response) as get, \
                patch('news_selection.feedparser.parse',return_value=SimpleNamespace(entries=entries)):
            candidates=collect_candidates(['feed1','feed2','feed3'],lambda stage,**kw:events.append((stage,kw)),
                     recent_urls={'https://www.cnbc.com/old'},now=now)
        self.assertEqual(3,get.call_count)
        self.assertEqual(['https://www.cnbc.com/new'],[c['url'] for c in candidates])
        self.assertTrue(any(e[1].get('reason')=='SOURCE_DATE_OUT_OF_RANGE' for e in events))

    def test_rank_compares_learning_fit_and_requires_complete_typed_results(self):
        candidates=[{'id':'business','url':'https://www.cnbc.com/business','published_at':None},
                    {'id':'politics','url':'https://www.cnbc.com/politics','published_at':None}]
        rows=[dict(id=cid,eligible=True,economic_relevance=e,learning_value=3,
                   comprehensibility=3,novelty=2,reason='編集判断') for cid,e in [('business',3),('politics',1)]]
        ranked=parse_ranking(json.dumps({'candidates':rows}),candidates,MagicMock())
        self.assertEqual(['business'],[c['id'] for c in ranked])
        for invalid in (rows[:1], [rows[0],rows[0]], [dict(rows[0],learning_value=True),rows[1]]):
            with self.assertRaises(ValueError):
                parse_ranking(json.dumps({'candidates':invalid}),candidates,MagicMock())

    def test_actual_present_perfect_mislabel_is_rejected(self):
        data=lesson()
        data['Grammar Point']=data['Grammar Point'].replace('might + verb','Present Perfect Tense')
        self.assertIn('present perfect label does not match quoted sentence',validate_lesson(data))


class RecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        keys=('OPENAI_API_KEY','S3_BUCKET_NAME','WP_URL','WP_USER','WP_APP_PASS',
              'SPREAKER_SHOW_ID','SPREAKER_OAUTH_TOKEN','SPREAKER_REFRESH_TOKEN',
              'SPREAKER_CLIENT_ID','SPREAKER_CLIENT_SECRET')
        with patch.dict(os.environ,{key:'test-placeholder' for key in keys}),patch('boto3.client'):
            cls.main=importlib.import_module('main')

    def setUp(self):
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.candidates=[{'id':str(n),'title':f'Business {n}','summary':'Facts',
                          'url':f'https://www.cnbc.com/{n}','selection_reason':'学習価値あり'} for n in (1,2)]
        for name,value in (('recent_lessons',(set(),[])),('collect_candidates',self.candidates),
                           ('rank_candidates',self.candidates),('source_text','source '*150),
                           ('gpt',markdown(lesson())),('review_lesson',True),('repair_lesson','SKIP: cannot repair')):
            self.stack.enter_context(patch.object(self.main,name,return_value=value))
        self.writers=[]
        for name in ('synthesize_speech','upload_to_s3','upload_episode_to_spreaker',
                     'post_to_wordpress','save_rss','update_episode_description'):
            self.writers.append(self.stack.enter_context(patch.object(self.main,name)))

    def assert_no_writes(self):
        for writer in self.writers: writer.assert_not_called()

    def test_dry_run_executes_gates_but_never_publishes(self):
        result=self.main.handler({'dry_run':True})
        self.assertEqual(200,result['statusCode'])
        self.assert_no_writes()

    def test_insufficient_source_then_next_candidate(self):
        self.main.source_text.side_effect=['','source '*150]
        result=self.main.handler({'dry_run':True})
        self.assertEqual('2',result['candidate_id'])
        self.assertEqual(1,self.main.gpt.call_count)
        self.assert_no_writes()

    def test_generation_skip_then_next_candidate_reason_logged(self):
        self.main.gpt.side_effect=['SKIP: LOW_LEARNING_VALUE 専門的すぎる',markdown(lesson())]
        out=io.StringIO()
        with patch('sys.stdout',out): result=self.main.handler({'dry_run':True})
        self.assertEqual('2',result['candidate_id'])
        events=[json.loads(line) for line in out.getvalue().splitlines() if line.startswith('{')]
        self.assertTrue(any(e.get('decision_stage')=='generation' and 'LOW_LEARNING_VALUE' in e['reason'] for e in events))
        self.assertEqual(1,len({e['run_id'] for e in events}))
        self.assert_no_writes()

    def test_invalid_grammar_repaired_once_then_full_review(self):
        bad=lesson();bad['Grammar Quote']='A sentence absent from the source script.'
        self.main.gpt.return_value=markdown(bad)
        self.main.repair_lesson.return_value=markdown(lesson())
        result=self.main.handler({'dry_run':True})
        self.assertEqual('1',result['candidate_id'])
        self.assertEqual(1,self.main.repair_lesson.call_count)
        self.assertEqual(1,self.main.review_lesson.call_count)
        self.assert_no_writes()

    def test_bad_repair_moves_on_without_publishing(self):
        self.main.gpt.return_value='### Script\nInvalid'
        self.main.repair_lesson.return_value='### Script\nStill invalid'
        self.assertEqual(204,self.main.handler({'dry_run':True})['statusCode'])
        self.assertEqual(2,self.main.repair_lesson.call_count)  # once per candidate
        self.assert_no_writes()

    def test_reviewer_rejection_is_repaired_and_rechecked(self):
        self.main.review_lesson.side_effect=[False,True]
        self.main.repair_lesson.return_value=markdown(lesson())
        self.assertEqual(200,self.main.handler({'dry_run':True})['statusCode'])
        self.assertEqual(2,self.main.review_lesson.call_count)
        self.assert_no_writes()

    def test_time_budget_and_missing_history_stop_before_generation(self):
        context=SimpleNamespace(aws_request_id='test-run',get_remaining_time_in_millis=lambda:10000)
        self.assertEqual(204,self.main.handler({'dry_run':True},context)['statusCode'])
        self.main.gpt.assert_not_called()
        self.main.recent_lessons.return_value=(None,None)
        self.assertEqual(204,self.main.handler({'dry_run':True})['statusCode'])
        self.assert_no_writes()


if __name__=='__main__': unittest.main()
