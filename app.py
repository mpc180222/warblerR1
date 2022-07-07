import os

from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from sqlalchemy.exc import IntegrityError

from forms import UserAddForm, LoginForm, MessageForm, UserEditForm
from models import db, connect_db, User, Message, Follows, Likes

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///warbler'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = 'abc12345'


connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
        


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)
        

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""
    do_logout()
    flash('you have logged out')
    return redirect('/login')


##############################################################################
# General user routes:

@app.route('/users/<int:user_id>/edit', methods = ["GET", "POST"])
def user_edit(user_id):

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    original_user = User.query.get_or_404(user_id)
    form = UserEditForm()
    if form.validate_on_submit():
        entered_password = form.password.data
        user = User.authenticate(original_user.username, entered_password)
        if user:
            user.username = form.username.data
            user.email = form.email.data
            user.image_url = form.image_url.data
            user.header_image_url = form.header_image_url.data
            user.bio = form.bio.data
            db.session.commit()
            return redirect(url_for('users_show', user_id = user.id))
        else:
                flash("Access unauthorized.", "danger")
                return redirect("/")
    return render_template("/users/edit.html", form=form)

@app.route('/users/<int:user_id>/likes')
def show_user_likes(user_id):
    user = User.query.get_or_404(user_id)
    liked_warbles = user.likes

    return render_template('/users/likes.html', liked_warbles = liked_warbles)


    


@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())
    return render_template('users/show.html', user=user, messages=messages)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/following.html', user=user)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['GET','POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    to_follow_user = User.query.get_or_404(follow_id)
    # below single line was the old way, appending to a list
    # g.user.following.append(followed_user)
    new_follow = Follows(user_being_followed_id = to_follow_user.id, user_following_id = g.user.id)
    db.session.add(new_follow)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/stop-following/<int:follow_id>', methods=['GET','POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get(follow_id)
    # below single line was the old way, appending to a list
    # g.user.following.remove(followed_user)
    follow_to_remove = Follows.query.get((followed_user.id, g.user.id))
    
    db.session.delete(follow_to_remove)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")

# This should be covered in user_edit
# @app.route('/users/profile', methods=["GET", "POST"])
# def profile():
#     """Update profile for current user."""

#     # IMPLEMENT THIS


@app.route('/users/delete', methods=["GET","POST"])
def delete_user():
    """Delete user. Need to delete all their likes, likes on their messages,
    all follows, and all messages"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get(g.user.id)
    

    do_logout()

    db.session.delete(user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Messages routes:


@app.route('/users/add_like/<int:message_id>', methods = ["GET","POST"])
def like_unlike_message(message_id):
    if not g.user:
        flash("Liking not allowed!!", "danger")
        return redirect("/")
    user_likes = User.query.get(g.user.id).likes
    message = Message.query.get_or_404(message_id)
    if message not in user_likes:
        like = Likes(user_id = g.user.id, message_id = message_id)
        db.session.add(like)
        db.session.commit()
        flash('liked')
        return redirect('/')
    else:
        
        delete_like = Likes.query.filter(Likes.message_id == message_id, Likes.user_id == g.user.id).first()
        db.session.delete(delete_like)
        db.session.commit()
        flash('unliked')
        return redirect('/')


@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET"])
def messages_show(message_id):
    """Show a message."""

    msg = Message.query.get(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    msg = Message.query.get(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(f"/users/{g.user.id}")


##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followed_users
    """

    if g.user:
        # old subquery
        subquery = db.session.query(Follows.user_being_followed_id).filter(Follows.user_following_id == g.user.id).subquery()
        # subquery = db.execute(select(Follows.user_being_followed_id).where(Follows.user_following_id == g.user.id))

        liked_messages = Likes.query.filter(Likes.user_id == g.user.id)
        liked_message_ids = [liked_message.message_id for liked_message in liked_messages]
        
        messages = (Message
                    .query
                    .filter(Message.user_id.in_(subquery))
                    .order_by(Message.timestamp.desc())
                    .limit(100)
                    .all())

        return render_template('home.html', messages=messages, liked_message_ids = liked_message_ids)

    else:
        return render_template('home-anon.html')


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
