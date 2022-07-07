"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from app import app

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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        user1 = User.signup(email = 'user1@gmail.com', username = 'user1', image_url = '/static/images/default-pic.png', password = 'user1password')
        user2 = User.signup(email = 'user2@gmail.com', username = 'user2', image_url = '/static/images/default-pic.png', password = 'user2password')
        db.session.commit()
        self.client = app.test_client()

    def tearDown(self):

        db.session.rollback()

    def test_user_model(self):
        with app.test_client() as client:
            """Does basic model work?"""

            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            db.session.add(u)
            db.session.commit()

            # User should have no messages & no followers
            self.assertEqual(len(u.messages), 0)
            self.assertEqual(len(u.followers), 0)
        def test_repr_method(self):
            """testing _repr_ method"""
            user1 = User.query.filter(User.username =='user1').one()
            result = repr(user1)

            self.assertIn('user1@gmail.com', result)
    
    def test_is_following(self):
        with app.test_client() as client:
            user1 = User.query.filter(User.username =='user1').one()
            user2 = User.query.filter(User.username =='user2').one()
            
            result1 = user1.is_following(user2)
            user1_follows_user2 = Follows(user_being_followed_id = user2.id, user_following_id = user1.id)
            db.session.add(user1_follows_user2)
            db.session.commit()
            result2 = user1.is_following(user2)
            
            
            result3 = user1.is_followed_by(user2)
            user2_follows_user1 = Follows(user_being_followed_id =user1.id, user_following_id =user2.id)
            db.session.add(user2_follows_user1)
            db.session.commit()
            result4 = user1.is_followed_by(user2)

            self.assertEqual(result1, False)
            self.assertEqual(result2, True)
            self.assertEqual(result3, False)
            self.assertEqual(result4, True)    

    def test_create_user(self):
        with app.test_client() as client:
            valid_user = User.signup(email='validuser@gmail.com', username = 'validuser', password = 'password123', image_url = "/static/images/default-pic.png")
            
            db.session.commit()
            # no_pwd_user = User.signup(email='nearlyvaliduser@gmail.com', username = 'validuser')
            # duplicate_username_user = User.signup(email='anotheruser@gmail.com', username = 'validuser', password = 'password123')
            # db.session.commit()

            query = User.query.filter(User.username =='validuser').one()
            self.assertEqual(query.username, 'validuser')

    def test_create_nopwd_user(self):
        with self.assertRaises(TypeError):
            no_pwd_user = User.signup(email='nearlyvaliduser@gmail.com', username = 'validuser', image_url = "/static/images/default-pic.png")

    def test_create_duplicate_username(self):
        with self.assertRaises(TypeError):
            duplicate_username_user = User.signup(email='anotheruser@gmail.com', username = 'user1', password = 'password123')
    
    def test_valid_user_authenticate(self):
        with app.test_client() as client:
            user1 = User.query.filter(User.username =='user1').one()
            user1_auth = user1.authenticate(username = 'user1', password = 'user1password')
            self.assertNotEqual(user1_auth,False)

    def test_invalid_password_authenticate(self):
        with app.test_client() as client:
            user1 = User.query.filter(User.username =='user1').one()
            user1_auth = user1.authenticate(username = 'user1', password = 'user1passwors')
            self.assertEqual(user1_auth,False)
    
    def test_invalid_username_authenticate(self):
        with app.test_client() as client:
            user1 = User.query.filter(User.username =='user1').one()
            user1_auth = user1.authenticate(username = 'userx', password = 'user1password')
            self.assertEqual(user1_auth,False)



        








