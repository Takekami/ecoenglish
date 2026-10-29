import datetime
import importlib
import os
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch, Mock
from urllib.parse import parse_qs, urlsplit

import requests
from podcast_links import tracked_lesson_url, episode_description
from rss_generator import generate_rss


class PodcastLinksTests(unittest.TestCase):
    def test_tracking_preserves_permalink_query_and_replaces_old_utm(self):
        link = tracked_lesson_url('https://econenglish.jp/?p=1469&utm_source=old#part', 123)
        params = parse_qs(urlsplit(link).query)
        self.assertEqual(['1469'], params['p'])
        self.assertEqual(['spreaker'], params['utm_source'])
        self.assertEqual(['123'], params['utm_content'])
        self.assertFalse(urlsplit(link).fragment)
        with self.assertRaises(ValueError):
            tracked_lesson_url('javascript:alert(1)', 123)

    def test_rss_is_valid_xml_with_utm_ampersands_and_special_characters(self):
        notes = episode_description('金利 & 物価 <教材>', 'https://econenglish.jp/lesson/', 123, 'podcast_rss')
        xml = generate_rss('Feed & title', 'https://econenglish.jp/', 'A & B', 'Description', [{
            'title': 'News & <more>', 'description': notes,
            'mp3_url': 'https://example.org/audio.mp3?x=1&y=2',
            'pub_date': datetime.datetime(2026, 10, 29, tzinfo=datetime.timezone.utc),
        }])
        root = ET.fromstring(xml)
        self.assertEqual(notes, root.findtext('./channel/item/description'))
        self.assertEqual('https://example.org/audio.mp3?x=1&y=2', root.find('./channel/item/enclosure').get('url'))

    def test_episode_update_refreshes_once_on_401_without_reuploading_audio(self):
        keys = ('SPREAKER_SHOW_ID', 'SPREAKER_CLIENT_ID', 'SPREAKER_CLIENT_SECRET', 'SPREAKER_REFRESH_TOKEN')
        with patch.dict(os.environ, {key: 'test' for key in keys}):
            module = importlib.import_module('spreaker_uploader')
        first = Mock(status_code=401)
        second = Mock(status_code=200)
        with patch.object(module, '_get_auth_header', return_value={'Authorization': 'Bearer old'}), \
                patch.object(module, '_refresh_access_token', return_value='new'), \
                patch.object(module.requests, 'post', side_effect=[first, second]) as post:
            module.update_episode_description(123, '教材リンク')
            self.assertEqual(2, post.call_count)
            self.assertTrue(all(call.args[0].endswith('/episodes/123') for call in post.call_args_list))
            self.assertEqual({'description': '教材リンク'}, post.call_args.kwargs['data'])
            second.raise_for_status.assert_called_once()
        with self.assertRaises(ValueError):
            module.update_episode_description('../shows/1', 'invalid')
