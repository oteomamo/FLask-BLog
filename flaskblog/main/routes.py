"""
This module contains route definitions for the main functionality of the Flask application.
"""

#import logging
#from datetime import datetime
from os import environ as env
#from urllib.parse import urlencode

from flask import Blueprint, render_template, request, jsonify
from flask import json, session, redirect, url_for, flash, current_app
from sqlalchemy import func, case, select, union_all, literal_column

from flaskblog import db, oauth
from flaskblog.models import NewsItem, Post, User, UserInteraction

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    """
    Home route
    """
    news_select = select(
        NewsItem.id,
        NewsItem.title,
        NewsItem.text,
        NewsItem.time.label('datetime'),
        literal_column("'news'").label('type'),
        literal_column("0").label('likes'),
        literal_column("0").label('dislikes')
    )

    post_select = select(
        Post.id,
        Post.title,
        Post.content.label('text'),
        Post.date_posted.label('datetime'),
        literal_column("'post'").label('type'),
        func.count(case((UserInteraction.interaction == 'like', 1))).label('likes'), # pylint: disable=not-callable
        func.count(case((UserInteraction.interaction == 'dislike', 1))).label('dislikes') # pylint: disable=not-callable
    ).outerjoin(UserInteraction, Post.id == UserInteraction.post_id).group_by(Post.id)

    combined_query = (
        union_all(news_select, post_select)
        .order_by(literal_column('datetime desc'))
        .limit(30)
    )
    combined_results = db.session.execute(combined_query).fetchall()

    return render_template('home.html', news=combined_results)

@main.route("/about")
def about():
    """
    About route
    """
    return render_template('about.html', title='About')

@main.route("/newsfeed")
def newsfeed():
    """
    Newsfeed
    """
    try:
        # Create a subquery for NewsItem
        news_subquery = db.session.query(
            NewsItem.id.label('id'),
            NewsItem.by.label('by'),
            NewsItem.descendants.label('descendants'),
            NewsItem.kids.label('kids'),
            NewsItem.score.label('score'),
            NewsItem.time.label('time'),
            NewsItem.title.label('title'),
            NewsItem.type.label('type'),
            NewsItem.url.label('url'),
            NewsItem.text.label('text'),
            NewsItem.time.label('datetime')
        ).subquery()

        # Create a subquery for Post
        post_subquery = db.session.query(
            Post.id.label('id'),
            Post.user_email.label('by'),
            literal_column("NULL").label('descendants'),
            literal_column("NULL").label('kids'),
            literal_column("NULL").label('score'),
            literal_column("NULL").label('time'),
            Post.title.label('title'),
            literal_column("'post'").label('type'),
            literal_column("NULL").label('url'),
            Post.content.label('text'),
            func.strftime('%s', Post.date_posted).label('datetime')
        ).subquery()

        union_query = union_all(news_subquery.select(),post_subquery.select()).alias('union_query')
        ordered_union_query = (
            db.session.query(union_query)
            .order_by(union_query.c.datetime.desc())
            .limit(30)
        )
        results = ordered_union_query.all()
        news_list = [
            {
                "id": item.id,
                "by": item.by,
                "descendants": item.descendants if item.descendants else "N/A",
                "kids": item.kids if item.kids else "N/A",
                "score": item.score if item.score else "N/A",
                "time": item.time if item.time else "N/A",
                "title": item.title,
                "type": item.type,
                "url": item.url if item.url else "N/A",
                "text": item.text if item.text else "N/A",
                "datetime": item.datetime
            }
            for item in results
        ]

        return current_app.response_class(
            response=json.dumps(news_list, indent=4),
            status=200,
            mimetype='application/json'
        )
    except Exception as e: # pylint: disable=broad-except
        return jsonify({"error": str(e)}), 500

@main.route("/callback", methods=["GET", "POST"])
def callback():
    """
    Callback route for Auth0
    """
    oauth.auth0.authorize_access_token() # Authorize without assigning to token
    userinfo_endpoint = f'https://{env.get("AUTH0_DOMAIN")}/userinfo'
    resp = oauth.auth0.get(userinfo_endpoint)
    userinfo = resp.json()
    email = userinfo.get('email')
    name = userinfo.get('name')
    nickname = userinfo.get('nickname')
    picture = userinfo.get('picture')

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, name=name, nickname=nickname, picture=picture, role='User')
        db.session.add(user)
        db.session.commit()
    else:
        user.name = name
        user.nickname = nickname
        user.picture = picture
        db.session.commit()

    session["user"] = {
        'name': name,
        'nickname': nickname,
        'email': email,
        'picture': picture,
        'id': user.id
    }

    return redirect(url_for('main.home'))


@main.route('/update_interaction', methods=['POST'])
def update_interaction():
    """
    Update Interactions
    """
    data = request.get_json()

    user_session = session.get('user')
    if not user_session or 'id' not in user_session:
        return jsonify({'error': 'User not authenticated'}), 401
    user_id = user_session['id']

    post_id = data['id']
    action = data['action']

    # Find an existing interaction
    interaction = UserInteraction.query.filter_by(user_id=user_id, post_id=post_id).first()

    if interaction:
        if interaction.interaction != action:
            interaction.interaction = action
        else:
            db.session.delete(interaction)
    else:
        # Add new interaction
        interaction = UserInteraction(user_id=user_id, post_id=post_id, interaction=action)
        db.session.add(interaction)

    db.session.commit()

    like_count = UserInteraction.query.filter_by(post_id=post_id, interaction='like').count()
    dislike_count = UserInteraction.query.filter_by(post_id=post_id, interaction='dislike').count()

    return jsonify(new_like_count=like_count, new_dislike_count=dislike_count)

@main.route('/update_user', methods=['POST'])
def update_user():
    """
    Update User
    """
    user_data = request.json
    email = user_data['email']

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, role='User')
        db.session.add(user)

    user.name = user_data.get('name')
    user.nickname = user_data.get('nickname')
    user.picture = user_data.get('picture')

    if 'role' in user_data:
        user.role = user_data['role']
    if 'name' in user_data:
        user.name = user_data['name']
    db.session.commit()

    return jsonify({'status': 'success'}), 200


@main.route("/update_nickname", methods=["POST"])
def update_nickname():
    """
    Update Nickname
    """
    if not session.get('user'):
        flash('You need to login first.', 'danger')
        return redirect(url_for('main.login'))

    user_email = session.get('user')['email']
    user = User.query.filter_by(email=user_email).first()

    if user:
        new_nickname = request.form.get('nickname')
        user.nickname = new_nickname
        db.session.commit()
        flash('Nickname updated successfully.', 'success')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('main.settings'))


@main.route("/update_name", methods=["POST"])
def update_name():
    """
    Update Name
    """
    if not session.get('user'):
        flash('You need to login first.', 'danger')
        return redirect(url_for('main.login'))

    user_email = session.get('user')['email']
    user = User.query.filter_by(email=user_email).first()

    if user:
        new_name = request.form.get('name')
        user.name = new_name
        db.session.commit()
        flash('Name updated successfully.', 'success')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('main.settings'))

@main.route("/update_profile", methods=["POST"])
def update_profile():
    """
    Update The Users Profile
    """
    if not session.get('user'):
        flash('You need to login first.', 'danger')
        return redirect(url_for('main.login'))

    user_email = session.get('user')['email']
    user = User.query.filter_by(email=user_email).first()

    if user:
        user.name = request.form.get('name')
        user.nickname = request.form.get('nickname')
        db.session.commit()
        flash('Profile updated successfully.', 'success')
    else:
        flash('User not found.', 'danger')

    return redirect(url_for('main.settings'))



@main.route("/settings")
def settings():
    """
    Settings Page
    """
    if not session.get('user'):
        flash('You need to login first.', 'danger')
        return redirect(url_for('main.login'))

    user_email = session.get('user')['email']
    user = User.query.filter_by(email=user_email).first()

    if user is None:
        flash('User not found.', 'danger')
        return redirect(url_for('main.home'))

    my_posts = (
        db.session.query(
            Post.id,
            Post.user_email.label('by'),
            Post.title,
            Post.date_posted.label('time'),
            func.count(case((UserInteraction.interaction == 'like', 1))).label('likes'), # pylint: disable=not-callable
            func.count(case((UserInteraction.interaction == 'dislike', 1))).label('dislikes') # pylint: disable=not-callable
        )
        .outerjoin(UserInteraction, Post.id == UserInteraction.post_id)
        .filter(Post.user_email == user_email)
        .group_by(Post.id, Post.user_email, Post.title, Post.date_posted)
        .all()
    )

    user_id = user.id

    post_interactions = db.session.query(
        UserInteraction.post_id,
        Post.title,
        UserInteraction.interaction
    ).join(Post, Post.id == UserInteraction.post_id)\
      .filter(UserInteraction.user_id == user_id).all()

    news_interactions = db.session.query(
        UserInteraction.post_id,
        NewsItem.title,
        UserInteraction.interaction
    ).join(NewsItem, NewsItem.id == UserInteraction.post_id)\
      .filter(UserInteraction.user_id == user_id).all()

    combined_interactions = post_interactions + news_interactions

    all_posts = []
    if user.role == 'Admin':
        news_query = select(
            NewsItem.id,
            NewsItem.by,
            NewsItem.title,
            NewsItem.time.label('datetime'),
            literal_column("'0'").label('likes'),
            literal_column("'0'").label('dislikes'),
            literal_column("'news'").label('type')
        )

        post_query = select(
            Post.id,
            Post.user_email.label('by'),
            Post.title,
            Post.date_posted.label('datetime'),
            func.count(case((UserInteraction.interaction == 'like', 1))).label('likes'), # pylint: disable=not-callable
            func.count(case((UserInteraction.interaction == 'dislike', 1))).label('dislikes'), # pylint: disable=not-callable
            literal_column("'post'").label('type')
        ).outerjoin(UserInteraction, Post.id == UserInteraction.post_id).group_by(Post.id)

        combined_query = union_all(news_query, post_query).order_by(literal_column('datetime desc'))

        all_posts = db.session.execute(combined_query).fetchall()

    return render_template(
        'settings.html',
        user=user,
        all_posts=all_posts,
        my_posts=my_posts,
        user_interactions=combined_interactions
    )
@main.route("/delete_post", methods=["POST"])
def delete_post():
    """
    Delete Posts
    """
    try:
        data = request.get_json()
        post_id = data.get('id')
        post_type = data.get('type')
        UserInteraction.query.filter_by(post_id=post_id).delete()
        if post_type == 'post':
            Post.query.filter_by(id=post_id).delete()
        elif post_type == 'news':
            NewsItem.query.filter_by(id=post_id).delete()
        else:
            return jsonify({'status': 'error', 'message': 'Invalid post type'}), 400

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Post deleted successfully'})
    except Exception as e: # pylint: disable=broad-except
        print(e)
        return jsonify({'status': 'error', 'message': 'An error occurred during deletion'})

# Login route
@main.route("/login")
def login():
    """
    Login using Auth0
    """
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("main.callback", _external=True)
    )

@main.route("/create_post", methods=["GET", "POST"])
def create_post():
    """
    Creat a new post function
    """
    if not session.get('user'):
        flash('You need to login first.', 'danger')
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        user_email = session.get('user')['email']
        post = Post(title=title, content=content, user_email=user_email)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('main.home'))
    return render_template('create_post.html')


# Logout route
@main.route("/logout")
def logout():
    """
    Logout from Auth0
    """
    session.clear()
    domain = env.get("AUTH0_DOMAIN")
    client_id = env.get("AUTH0_CLIENT_ID")
    return_to = url_for('main.home', _external=True)
    logout_url = f'https://{domain}/v2/logout?client_id={client_id}&returnTo={return_to}'
    print("Logout URL:", logout_url)
    return redirect(logout_url)

def safe_str(value):
    """
    Value
    """
    return str(value) if value else ''
