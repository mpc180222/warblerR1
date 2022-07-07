"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from app import app
from datetime import datetime

from sqlalchemy.exc import IntegrityError

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


class MessageModelTestCase(TestCase):
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

    def test_message_model(self):
        with app.test_client() as client:
            """Does basic model work?"""
            user1 = User.query.filter(User.username =='user1').one()
            m = Message(
                text="test message model",
                timestamp =datetime.utcnow(),
                user_id= user1.id
            )

            db.session.add(m)
            db.session.commit()
            self.assertEqual(m.user.username,'user1')
            
    def test_invalid_message_model(self):
        """testing user_id left blank"""
        with self.assertRaises(IntegrityError):
            m = Message(
                    text="test message model",
                    timestamp =datetime.utcnow()
                
                )
            db.session.add(m)
            db.session.commit()

           
