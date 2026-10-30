import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from youtube_upload import CHANNEL, upload, validate_schedule, review_hash, prepare, digest


class UploadTests(unittest.TestCase):
    def test_prepare_rejects_changed_video_and_missing_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            movie, draft = Path(folder) / 'video.mp4', Path(folder) / 'draft.json'
            movie.write_bytes(b'rendered video')
            data = {'sha256': digest(movie), 'podcast_provenance': {
                'review_status': 'manual_preview_review', 'selection': {},
                'script': 'source', 'episode_id': '123'},
                'example_origin': 'podcast_script', 'duration_seconds': 55,
                'title': 'Test', 'description': 'Source and learning material'}
            draft.write_text(json.dumps(data))
            with patch('youtube_upload.validate_provenance', return_value=True):
                with self.assertRaises(ValueError):
                    prepare(movie, draft)
                with patch('youtube_upload.validate_usage_review', return_value=True):
                    self.assertEqual(prepare(movie, draft)['body']['status']['privacyStatus'], 'private')
                    movie.write_bytes(b'changed')
                    with self.assertRaises(ValueError):
                        prepare(movie, draft)

    def api(self):
        api = MagicMock()
        api.channels.return_value.list.return_value.execute.return_value = {'items': [{'id': CHANNEL}]}
        api.videos.return_value.insert.return_value.next_chunk.return_value = (None, {
            'id': 'test-id', 'snippet': {'channelId': CHANNEL}, 'status': {'privacyStatus': 'private'}})
        return api

    def plan(self):
        return {'episode_id': '123', 'video_sha256': 'abc',
                'body': {'snippet': {'title': 'Test'}, 'status': {'privacyStatus': 'private'}}}

    def test_duplicate_episode_and_video_blocked(self):
        with tempfile.TemporaryDirectory() as folder:
            api, plan = self.api(), self.plan()
            ledger = Path(folder) / 'ledger.db'
            self.assertEqual(upload(api, 'video.mp4', plan, ledger, MagicMock()), 'test-id')
            for changed in ({}, {'episode_id': '456'}, {'video_sha256': 'def'}):
                with self.assertRaises(ValueError):
                    upload(api, 'video.mp4', dict(plan, **changed), ledger, MagicMock())
            self.assertEqual(api.videos.return_value.insert.call_count, 1)

    def test_ambiguous_failure_never_reuploads(self):
        with tempfile.TemporaryDirectory() as folder:
            api = self.api()
            api.videos.return_value.insert.return_value.next_chunk.side_effect = TimeoutError()
            ledger = Path(folder) / 'ledger.db'
            with self.assertRaises(TimeoutError):
                upload(api, 'video.mp4', self.plan(), ledger, MagicMock())
            with self.assertRaises(ValueError):
                upload(api, 'video.mp4', self.plan(), ledger, MagicMock())
            self.assertEqual(api.videos.return_value.insert.call_count, 1)

    def test_wrong_channel_stops_before_upload(self):
        api = self.api()
        api.channels.return_value.list.return_value.execute.return_value = {'items': [{'id': 'other'}]}
        with tempfile.TemporaryDirectory() as folder, self.assertRaises(ValueError):
            upload(api, 'video.mp4', self.plan(), Path(folder) / 'db', MagicMock())
        api.videos.assert_not_called()

    def test_future_timezone_required(self):
        now = datetime(2026, 10, 29, tzinfo=timezone.utc)
        for value in ('2026-10-28T19:00:00+09:00', '2026-10-30T19:00:00'):
            with self.assertRaises(ValueError):
                validate_schedule(value, now)
        self.assertEqual(validate_schedule('2026-10-30T19:00:00+09:00', now), '2026-10-30T10:00:00Z')

    def test_review_bound_to_metadata(self):
        plan = self.plan()
        changed = copy.deepcopy(plan)
        changed['body']['snippet']['title'] = 'Different'
        self.assertNotEqual(review_hash(plan), review_hash(changed))


if __name__ == '__main__':
    unittest.main()
