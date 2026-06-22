import os
import tempfile
from datetime import datetime, timezone
from zimbra.models import PostRecord
from zimbra.database import init_db, save_posts, load_posts

def test_database_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_market.db")
        
        init_db(db_path)
        assert os.path.exists(db_path)
        
        post = PostRecord(
            source="reddit",
            platform_entity="wallstreetbets",
            post_id="reddit_test123",
            author="test_user",
            created_utc=datetime.now(timezone.utc),
            text="This is a test post.",
            thread_id="thread_test123",
            thread_title="Test Thread Title",
            likes=10.0,
            replies=2.0
        )
        
        save_posts([post], db_path)
        
        df = load_posts(db_path)
        assert not df.empty
        assert len(df) == 1
        assert df.iloc[0]["post_id"] == "reddit_test123"
        assert df.iloc[0]["author"] == "test_user"
        assert df.iloc[0]["text"] == "This is a test post."
