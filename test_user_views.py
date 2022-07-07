"""User views tests."""


import os
from unittest import TestCase
from app import app, CURR_USER_KEY
from flask import url_for
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///warbler-test"
app.config['SQLALCHEMY_ECHO'] = False


# Now we can import app



# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        self.client = app.test_client()
        self.testuser = User.signup(email = 'user1@gmail.com', username = 'user1', image_url = '/static/images/default-pic.png', password = 'user1password')
        db.session.commit()
        user2 = User.signup(email = 'user2@gmail.com', username = 'user2', image_url = '/static/images/default-pic.png', password = 'user2password')
        db.session.commit()
        

    # def tearDown(self):

    #     db.session.rollback()
    
    def test_user_edit(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post(f"/users/{self.testuser.id}/edit", data={"email" : "user1@gmail.com",
            "username": "user1",
            "image_url": "/static/images/default-pic.png",
            "password": "user1password",
            "bio": "successfully edited"})
            html = resp.data.decode("utf-8")
            # import pdb; pdb.set_trace()
            self.assertEqual(resp.status_code, 200)
            self.assertIn("successfully edited", html)

    def test_user_edit_logged_out(self):
        with self.client as c:
            resp = c.post(f"/users/{self.testuser.id}/edit", data={"email" : "user1@gmail.com",
            "username": "user1",
            "image_url": "/static/images/default-pic.png",
            "password": "user1password",
            "bio": "successfully edited"}, follow_redirects = True)
            html = resp.data.decode("utf-8")
            # import pdb; pdb.set_trace()
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_list_users(self):
        with self.client as c:
            resp = c.get('/users')
            html = resp.data.decode("utf-8")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("user1", html)

    def test_user_show(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f"/users/{self.testuser.id}")
            html = resp.data.decode("utf-8")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@user1", html)

    def test_add_follow_and_show_following_and_show_followers(self):
        """Have our test user follow user2, and be redirected to our test user's following page."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            user2 =  User.query.filter(User.username =='user2').one()
            resp = c.post(f'/users/follow/{user2.id}', follow_redirects = True)
            html = resp.data.decode("utf-8")
            total_follows = Follows.query.all()
            """Show user2 followers while our test user is logged in."""
            user2 =  User.query.filter(User.username =='user2').one()
            show_followers_resp = c.get(f'/users/{user2.id}/followers')
            show_followers_resp_html = show_followers_resp.data.decode("utf-8")
            """logout and demonstrate unable to visit following or followers pages"""
            with c.session_transaction() as sess:
                del sess[CURR_USER_KEY] 
            user2 =  User.query.filter(User.username =='user2').one()
            logged_out_show_followers_resp = c.get(f'/users/{user2.id}/followers', follow_redirects = True)
            logged_out_show_followers_resp_html = logged_out_show_followers_resp.data.decode("utf-8")
            logged_out_show_following_resp = c.get(f'/users/{user2.id}/followers', follow_redirects = True)
            logged_out_show_following_resp_html = logged_out_show_following_resp.data.decode("utf-8")


            self.assertIn("user2", html)
            self.assertEqual(len(total_follows), 1)
            self.assertIn("user1", show_followers_resp_html)
            self.assertIn("Access unauthorized.", logged_out_show_followers_resp_html)
            self.assertIn("Access unauthorized.", logged_out_show_following_resp_html)

    def test_stop_following(self):
        """begin by making our test user follow user2."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            user2 =  User.query.filter(User.username =='user2').one()
            follow_resp = c.post(f'/users/follow/{user2.id}', follow_redirects = True)
            """make our post request for testuser to unfollow user2"""
            user2 =  User.query.filter(User.username =='user2').one()
            unfollow_resp = c.post(f'/users/stop-following/{user2.id}', follow_redirects = True)
            html = unfollow_resp.data.decode("utf-8")
            total_follows = Follows.query.all()
            
            self.assertEqual(unfollow_resp.status_code, 200)
            self.assertEqual(len(total_follows), 0)
    
    def test_delete_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post('/users/delete', follow_redirects = True)
            html = resp.data.decode("utf-8")
            total_users = User.query.all()
            """the test will look that there is only one user in the database - user2, our test user has been deleted.
            Also that we are redirecting to the signup page."""
            self.assertIn('Join Warbler today.', html)
            self.assertEqual(len(total_users), 1)
    
    def test_delete_user_logged_out(self):
        with self.client as c:
            resp = c.post('/users/delete', follow_redirects = True)
            html = resp.data.decode("utf-8")
            total_users = User.query.all()
            """Both users should still be in database, and we should get a danger redirect."""
            self.assertIn('Access unauthorized.', html)
            self.assertEqual(len(total_users), 2)


        





            
                



            


    


        
    
   


        


    


            