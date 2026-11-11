from datetime import datetime, timezone
import unittest
from unittest.mock import MagicMock, patch

from blog_template import source_notice
from news_selection import collect_candidates, recent_lessons, statistics_entries
from content_quality import source_text
from source_catalog import FEEDS, STAT_UPDATES, history_key


class OfficialSourceTests(unittest.TestCase):
    def test_statistics_dates_and_navigation_are_not_guessed(self):
        page = b'''<article><h1>What's New</h1>December 30<ul>
        <li><a href="/english/data/cpi/results.html">Consumer Price Index</a></li>
        <li><a href="/english/info/news.html">News bulletin</a></li></ul>
        January 2<ul><li><a href="/english/data/jobs.html">Jobs</a></li></ul>
        Unknown<ul><li><a href="/english/data/other.html">Other</a></li></ul></article>'''
        entries = statistics_entries(page, datetime(2027, 1, 3, tzinfo=timezone.utc))
        self.assertEqual(2, len(entries))
        self.assertTrue(entries[0]['published'].startswith('2026-12-30'))
        self.assertTrue(entries[1]['published'].startswith('2027-01-02'))

    def test_mutable_result_page_skips_only_published_release(self):
        url = 'https://www.stat.go.jp/english/data/cpi/results.html'
        page = b'''<article><h1>What's New</h1>November 10<ul>
        <li><a href="/english/data/cpi/results.html">CPI</a></li></ul></article>'''
        with patch('news_selection.requests.get', return_value=MagicMock(content=page)):
            args = dict(feeds=[STAT_UPDATES], emit=MagicMock(),
                        now=datetime(2026, 11, 11, tzinfo=timezone.utc))
            self.assertEqual(1, len(collect_candidates(**args, recent_urls={history_key(url, '2026-10-10')})))
            self.assertEqual([], collect_candidates(**args, recent_urls={history_key(url, '2026-11-10')}))

    def test_source_attribution_round_trips_history_and_escapes(self):
        url = 'https://www.stat.go.jp/english/data/cpi/results.html'
        content = source_notice(url, '2026-11-10T00:00:00Z')
        response = MagicMock()
        response.json.return_value = [{'title':{'rendered':'CPI'}, 'content':{'rendered':content}}]
        with patch('news_selection.requests.get', return_value=response):
            urls, _ = recent_lessons(MagicMock())
        self.assertIn(history_key(url, '2026-11-10'), urls)
        self.assertIn('編集・翻訳', content)
        self.assertNotIn('<script>', source_notice('https://www.bea.gov/news?x=<script>'))

    def test_active_sources_exclude_personal_only_news_feeds(self):
        self.assertTrue(all(not any(host in feed for host in ('nikkei', 'cnbc', 'channelnewsasia')) for feed in FEEDS))

    def test_ranking_pool_contains_only_fetched_sources_and_excerpts(self):
        entries = [{'title':'Trade', 'link':'https://www.bea.gov/news/trade'},
                   {'title':'Unavailable', 'link':'https://www.bea.gov/news/blocked'}]
        from types import SimpleNamespace
        with patch('news_selection.requests.get', return_value=MagicMock(content=b'feed')), \
                patch('news_selection.feedparser.parse', return_value=SimpleNamespace(entries=entries)), \
                patch('news_selection.source_text', side_effect=['fact ' * 1500, '']):
            candidates = collect_candidates(['feed'], MagicMock(), with_sources=True)
        self.assertEqual(1, len(candidates))
        self.assertEqual(4000, len(candidates[0]['source_excerpt']))
        self.assertEqual('fact ' * 1500, candidates[0]['source_evidence'])

    def test_official_numeric_tables_are_kept(self):
        response = MagicMock(status_code=200, headers={'Content-Type':'text/html'})
        response.__enter__.return_value = response
        response.iter_content.return_value = [b'<table>numeric findings</table>']
        with patch('content_quality.requests.get', return_value=response), \
                patch('content_quality.trafilatura.extract', return_value='fact ' * 150) as extract:
            self.assertTrue(source_text('https://www.stat.go.jp/english/data/cpi/results.html', ''))
        self.assertTrue(extract.call_args.kwargs['include_tables'])


if __name__ == '__main__':
    unittest.main()
