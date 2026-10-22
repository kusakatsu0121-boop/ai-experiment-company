import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from publish_bluesky import validate_text, rkey_for, publish, COMPANY_HANDLE


class PublisherTests(unittest.TestCase):
    def test_real_draft_valid(self):
        text = pathlib.Path(__file__).resolve().parents[1].joinpath('content/first_post.txt').read_text(encoding='utf-8')
        self.assertLessEqual(len(validate_text(text)), 300)

    def test_invalid_drafts(self):
        for text in ('', ' ', 'x' * 301):
            with self.assertRaises(ValueError):
                validate_text(text)

    def test_deterministic_key(self):
        self.assertEqual(rkey_for('a'), rkey_for('a'))
        self.assertNotEqual(rkey_for('a'), rkey_for('b'))

    def test_missing_secret_no_network(self):
        with self.assertRaises(ValueError):
            publish('hello', '', poster=lambda *a: self.fail('network call'), reader=lambda *a: self.fail('network call'))

    def test_approved_api_and_readback(self):
        calls = []
        posted = {}
        def poster(endpoint, payload, bearer=None):
            calls.append((endpoint, payload, bearer))
            if endpoint.endswith('createSession'):
                return {'did': 'did:plc:company', 'accessJwt': 'test-token'}
            posted['text'] = payload['record']['text']
            posted['rkey'] = payload['rkey']
            return {'uri': 'at://did:plc:company/app.bsky.feed.post/' + payload['rkey'], 'cid': 'test-cid'}
        def reader(rkey):
            if not posted:
                return None
            return {'uri': 'at://did:plc:company/app.bsky.feed.post/' + rkey, 'value': {'text': posted['text']}}
        result = publish('hello', 'test-password', poster=poster, reader=reader)
        self.assertEqual(result['status'], 'PUBLICATION_VERIFIED')
        self.assertEqual(calls[0][1]['identifier'], COMPANY_HANDLE)
        self.assertEqual(calls[1][2], 'test-token')
        self.assertIn('/post/aie-', result['url'])

    def test_duplicate_never_reposts(self):
        text = 'hello'
        result = publish(text, 'dummy', poster=lambda *a: self.fail('posted twice'), reader=lambda rkey: {'uri': 'existing', 'value': {'text': text}})
        self.assertEqual(result['status'], 'ALREADY_EXISTS')

    def test_readback_mismatch_not_verified(self):
        def poster(endpoint, payload, bearer=None):
            if endpoint.endswith('createSession'):
                return {'did': 'did:plc:company', 'accessJwt': 'token'}
            return {'uri': 'at://did:plc:company/app.bsky.feed.post/rkey', 'cid': 'cid'}
        results = iter([None, {'uri': 'other-uri', 'value': {'text': 'hello'}}])
        result = publish('hello', 'dummy', poster=poster, reader=lambda _: next(results))
        self.assertEqual(result['status'], 'API_ACCEPTED_READBACK_PENDING')


if __name__ == '__main__':
    unittest.main()
