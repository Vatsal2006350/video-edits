"""Offline safety tests. Never contacts Instagram or launches the publisher."""
import datetime as dt
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('birthday_loop', Path(__file__).with_name('birthday-trial-loop.py'))
loop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loop)


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.queue = self.root / 'publishing/queue/test'
        self.queue.mkdir(parents=True)
        self.metadata = {'account': loop.ACCOUNT, 'format': 'trial_reel', 'graduation_strategy': 'MANUAL'}
        (self.queue / 'publish.json').write_text(json.dumps(self.metadata))
        (self.queue / 'caption.txt').write_text('birthday test')
        (self.queue / 'reel.mp4').write_bytes(b'fake test video')
        for name, value in [('ROOT', self.root), ('STATE', self.root / 'state')]:
            patcher = patch.object(loop, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.run = patch.object(loop.subprocess, 'run').start()
        self.api = patch.object(loop, 'api', return_value={'username': loop.ACCOUNT}).start()
        self.recent = patch.object(loop, 'recent', return_value=[]).start()
        self.addCleanup(patch.stopall)

    def test_refuses_auto_graduation_before_network(self):
        self.metadata['graduation_strategy'] = 'SS_PERFORMANCE'
        (self.queue / 'publish.json').write_text(json.dumps(self.metadata))
        with self.assertRaisesRegex(RuntimeError, 'Refusing'):
            loop.publish(self.queue)
        self.run.assert_not_called()
        self.api.assert_not_called()

    def test_refuses_wrong_account(self):
        self.api.return_value = {'username': 'another.account'}
        with self.assertRaisesRegex(RuntimeError, 'identity'):
            loop.publish(self.queue)
        self.assertEqual(self.run.call_count, 1)

    def test_refuses_existing_caption(self):
        self.recent.return_value = [{'caption': 'birthday test'}]
        with self.assertRaisesRegex(RuntimeError, 'caption already exists'):
            loop.publish(self.queue)
        self.assertEqual(self.run.call_count, 1)

    def test_refuses_daily_cap(self):
        folder = loop.STATE / 'attempts'
        folder.mkdir(parents=True)
        for n in range(2):
            (folder / f'{n}.json').write_text(json.dumps({'started_at': loop.now(), 'sha256': str(n), 'queue': str(n)}))
        with self.assertRaisesRegex(RuntimeError, 'cap reached'):
            loop.publish(self.queue)
        self.assertEqual(self.run.call_count, 1)

    def test_uncertain_result_blocks_retry(self):
        self.run.return_value.returncode = 1
        self.run.return_value.stdout = 'connection lost'
        self.run.return_value.stderr = ''
        with self.assertRaisesRegex(RuntimeError, 'did not confirm'):
            loop.publish(self.queue)
        with self.assertRaisesRegex(RuntimeError, 'Prior attempt'):
            loop.publish(self.queue)
        with self.assertRaisesRegex(RuntimeError, 'Not a proven'):
            loop.reconcile_pre_ingest(self.queue)

    def test_extra_batch_rejects_unlisted_queue(self):
        with self.assertRaisesRegex(RuntimeError, 'authorization does not cover'):
            loop.publish(self.queue, authorized_extra_batch=True)
        self.assertEqual(self.run.call_count, 1)

    def test_six_batch_rejects_unlisted_queue(self):
        with self.assertRaisesRegex(RuntimeError, 'Six reel authorization'):
            loop.publish(self.queue, authorized_birthday_six=True)
        self.assertEqual(self.run.call_count, 1)

    def test_music_refresh_rejects_unlisted_queue(self):
        with self.assertRaisesRegex(RuntimeError, 'Music refresh authorization'):
            loop.publish(self.queue, authorized_music_refresh=True)
        self.assertEqual(self.run.call_count, 1)


if __name__ == '__main__':
    unittest.main()
