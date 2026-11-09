import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

# Never connect tests to the configured application database.
os.environ['DATABASE_URL'] = 'sqlite://'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
import main


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        self.db_patch = patch.object(main, 'engine', self.engine)
        self.db_patch.start()
        with self.engine.begin() as conn:
            conn.execute(text('CREATE TABLE tool (id INTEGER PRIMARY KEY, name TEXT, price TEXT, tags TEXT, url TEXT, short_description TEXT, description TEXT, advantages TEXT, disadvantages TEXT)'))
            conn.execute(text('CREATE TABLE review (id INTEGER PRIMARY KEY, tool_id INTEGER, rating INTEGER, title TEXT, date DATE, description TEXT)'))
            conn.execute(text("INSERT INTO tool (id, name, price, tags) VALUES (1, 'Alpha', 'Free; USD 10/month', '[\"research\"]'), (2, 'Beta', 'Contact sales', '[]')"))
        self.client = TestClient(main.app)

    def tearDown(self):
        self.client.close()
        self.db_patch.stop()
        self.engine.dispose()

    def test_pagination_and_detail(self):
        first = self.client.get('/tools?amount=1').json()
        self.assertEqual(first['tools'][0]['id'], 1)
        self.assertTrue(first['hasMore'])
        self.assertEqual(self.client.get('/tools?amount=1&offset=1').json()['tools'][0]['id'], 2)
        self.assertFalse(self.client.get('/tools?amount=1&offset=2').json()['hasMore'])
        self.assertEqual(self.client.get('/tool/1').json()['id'], 1)
        self.assertEqual(self.client.get('/tool/999').status_code, 404)
        self.assertEqual(self.client.get('/tools?amount=101').status_code, 422)

    def test_review_write_read_and_rating(self):
        for rating in (3, 5):
            response = self.client.post('/add-review', json={'tool_id': 1, 'rating': rating, 'title': ' Useful ', 'description': 'Worked for my task.'})
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json()['title'], 'Useful')
        self.assertEqual(len(self.client.get('/get-reviews/1').json()), 2)
        detail = self.client.get('/tool/1').json()
        self.assertEqual(detail['id'], 1)
        self.assertEqual(sorted(r['rating'] for r in self.client.get('/get-reviews/1').json()), [3, 5])
        for changes, status in [({'rating': 6}, 422), ({'title': '   '}, 422), ({'tool_id': 999}, 404)]:
            self.assertEqual(self.client.post('/add-review', json={'tool_id': 1, 'rating': 5, 'title': 'Title', 'description': 'Text', **changes}).status_code, status)

    def mock_response(self, content, status='completed'):
        return SimpleNamespace(status=status, error=None, output=[SimpleNamespace(type='message', content=[SimpleNamespace(type='output_text', text=content)])])

    def test_prompt_uses_history_and_catalog_ids(self):
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-only'}), patch.object(main, 'OpenRouter') as sdk:
            send = sdk.return_value.__enter__.return_value.responses.send
            send.return_value = self.mock_response(json.dumps({'text': 'Try Alpha.', 'tool_ids': [1, 1]}))
            response = self.client.post('/prompt', json={'messages': [{'role': 'user', 'content': 'Research'}, {'role': 'assistant', 'content': 'What budget?'}, {'role': 'user', 'content': 'Free'}]})
            self.assertEqual(response.status_code, 200)
            self.assertEqual([t['id'] for t in response.json()['tools']], [1])
            payload = send.call_args.kwargs
            self.assertEqual(json.loads(payload['input'])['messages'][-1]['content'], 'Free')
            self.assertIn('Alpha', payload['instructions'])

    def test_prompt_configuration_and_bad_upstream(self):
        body = {'messages': [{'role': 'user', 'content': 'Research'}]}
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': ''}):
            self.assertEqual(self.client.post('/prompt', json=body).status_code, 500)
        for content in ('not json', json.dumps({'text': 'Made up', 'tool_ids': [999]})):
            with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-only'}), patch.object(main, 'OpenRouter') as sdk:
                sdk.return_value.__enter__.return_value.responses.send.return_value = self.mock_response(content)
                self.assertEqual(self.client.post('/prompt', json=body).status_code, 502)
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test-only'}), patch.object(main, 'OpenRouter') as sdk:
            sdk.return_value.__enter__.return_value.responses.send.return_value = self.mock_response('', status='failed')
            with self.assertRaises(RuntimeError):
                self.client.post('/prompt', json=body)
        self.assertEqual(self.client.post('/prompt', json=[]).status_code, 422)

if __name__ == '__main__':
    unittest.main()
