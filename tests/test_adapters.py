import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from zimbra.adapters.reddit import RedditAdapter

class TestRedditAdapter(unittest.TestCase):
    @patch('requests.Session.get')
    def test_fetch_arctic_shift_success(self, mock_get):
        # Setup mock response for Arctic Shift API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "as1",
                    "title": "Arctic Shift Title",
                    "selftext": "Arctic Shift body text",
                    "author": "as_user",
                    "created_utc": 1700000000,
                    "ups": 15.0,
                    "num_comments": 8.0,
                    "permalink": "/r/wallstreetbets/comments/as1/test/"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        adapter = RedditAdapter()
        posts = adapter.fetch(target="wallstreetbets", limit=5)
        
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].source, "reddit")
        self.assertEqual(posts[0].post_id, "reddit_as1")
        self.assertEqual(posts[0].author, "as_user")
        self.assertEqual(posts[0].thread_title, "Arctic Shift Title")
        self.assertEqual(posts[0].likes, 15.0)
        self.assertEqual(posts[0].replies, 8.0)
        
    @patch('requests.Session.get')
    def test_fetch_requests_fallback(self, mock_get):
        # Setup mock responses: First call (Arctic Shift) fails, second call (Reddit JSON) succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = Exception("Arctic Shift Server Error")
        
        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.json.return_value = {
            "data": {
                "children": [
                    {
                        "data": {
                            "id": "t1",
                            "title": "Test Title",
                            "selftext": "Test body text",
                            "author": "user_abc",
                            "created_utc": 1700000000,
                            "ups": 42.0,
                            "num_comments": 12.0,
                            "permalink": "/r/wallstreetbets/comments/t1/test/"
                        }
                    }
                ]
            }
        }
        
        mock_get.side_effect = [mock_response_fail, mock_response_ok]
        
        adapter = RedditAdapter()
        posts = adapter.fetch(target="wallstreetbets", limit=5)
        
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0].source, "reddit")
        self.assertEqual(posts[0].post_id, "reddit_t1")
        self.assertEqual(posts[0].author, "user_abc")
        self.assertEqual(posts[0].thread_title, "Test Title")
        self.assertEqual(posts[0].likes, 42.0)
        self.assertEqual(posts[0].replies, 12.0)

    @patch('requests.Session.get')
    def test_fetch_historical_params(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "t1",
                    "title": "Historical Title",
                    "selftext": "Historical body",
                    "author": "hist_user",
                    "created_utc": 1700000000,
                    "ups": 10.0,
                    "num_comments": 5.0,
                    "permalink": "/r/wallstreetbets/comments/t1/test/"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        adapter = RedditAdapter()
        adapter.fetch(target="wallstreetbets", limit=5, query="BTC", after=1700000000, before=1700100000)
        
        called_url = mock_get.call_args[0][0]
        self.assertIn("subreddit=wallstreetbets", called_url)
        self.assertIn("query=BTC", called_url)
        self.assertIn("after=1700000000", called_url)
        self.assertIn("before=1700100000", called_url)

    def test_live_reddit_fetch(self):
        from zimbra.adapters.reddit import RedditAdapter
        adapter = RedditAdapter()
        try:
            posts = adapter.fetch(target="wallstreetbets", limit=5)
            print(f"\nLIVE_FETCH_REDDIT_COUNT: {len(posts)}")
            if posts:
                print("First post title:", posts[0].thread_title)
                print("First post text:", posts[0].text[:100])
        except Exception as e:
            print(f"\nLIVE_FETCH_REDDIT_ERROR: {e}")
