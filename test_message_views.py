"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})
            

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_messages_show(self):
        """Can we see a newly-created test message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            new_msg_resp = c.post("/messages/new", data={"text": "Hello"})
            msg = Message.query.one()

            resp = c.get(f"/messages/{msg.id}")
            html = resp.data.decode("utf-8")

            # import pdb; pdb.set_trace()

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello", html)
    
    def test_messages_destroy(self):
        """Testing that we are redirecting to test user's profile after delete, and
        that querying the message table after delete yields an empty result"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            new_msg_resp = c.post("/messages/new", data={"text": "Hello"})
            msg = Message.query.one()
            resp = c.post(f"/messages/{msg.id}/delete")
            msg_check = Message.query.all()
            

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(msg_check, [])
    
    def test_add_message_when_logged_out(self):
        """Are we rightly prohibited from adding a message when logged out?"""
        with self.client as c:
            # with c.session_transaction() as sess:
            #     sess[CURR_USER_KEY] = self.testuser.id
            #     del sess[CURR_USER_KEY]


            resp = c.post("/messages/new", data={"text": "Shouldn't be posted"}, follow_redirects=True)
            html = resp.data.decode("utf-8")
            msg_check = Message.query.all()
            # import pdb; pdb.set_trace()
            self.assertEqual(msg_check, [])
            self.assertIn("Access unauthorized", html)

    def test_delete_message_when_logged_out(self):
        """Are we rightly prohibited from deleting a message when logged out?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            create_msg_resp = c.post("/messages/new", data={"text": "Will try to delete"})
            with c.session_transaction() as sess:
                del sess[CURR_USER_KEY]
            msg = Message.query.one()
            attempt_del_resp = c.post(f"/messages/{msg.id}/delete", follow_redirects=True)
            html = attempt_del_resp.data.decode("utf-8")
            msg_check = Message.query.all()
            self.assertNotEqual(msg_check, [])
            self.assertIn("Access unauthorized", html)

    def test_like_message(self):
        """Tests of the like_unlike view function."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            create_msg_resp = c.post("/messages/new", data={"text": "Like this!"})
            msg = Message.query.one()
            like_resp = c.post(f"/users/add_like/{msg.id}", data={"user_id": self.testuser.id, "message_id": msg.id }, follow_redirects=True)
            likes = Likes.query.one()
            html = like_resp.data.decode("utf-8")
            # import pdb; pdb.set_trace()
            self.assertIn('liked', html)
            self.assertEqual(likes.message_id, msg.id)
            """Unliking the same post"""
            unlike_resp = c.post(f"/users/add_like/{msg.id}", data={"user_id": self.testuser.id, "message_id": msg.id }, follow_redirects=True)
            all_likes = Likes.query.all()
            unlike_html = unlike_resp.data.decode("utf-8")
            self.assertIn('unliked', unlike_html)
            self.assertEqual(all_likes, [])
    
    def test_like_message_logged_out(self):
        """Tests of the like_unlike view function while logged out - it should not allow us to like."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            create_msg_resp = c.post("/messages/new", data={"text": "Like this!"})
            msg = Message.query.one()
            with c.session_transaction() as sess:
                del sess[CURR_USER_KEY]
            like_resp = c.post(f"/users/add_like/{msg.id}", data={"user_id": self.testuser.id, "message_id": msg.id }, follow_redirects=True)
            likes = Likes.query.all()
            html = like_resp.data.decode("utf-8")
            self.assertIn("Liking not allowed!!", html)
            self.assertEqual(likes, [])






    



            
        



            

        

