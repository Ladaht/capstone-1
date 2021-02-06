from flask import Flask, render_template, redirect, session, flash, Markup
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Post
from forms import UserForm, PostForm
from sqlalchemy.exc import IntegrityError
import requests 
from flask import url_for
import urllib

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgres:///bucketlist_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False


connect_db(app)

toolbar = DebugToolbarExtension(app)

# ---------- this route show a list of destination in Alphabetical order ----------
@app.route('/index')
def home():
    all_posts = Post.query.all()
    value = Markup('<p><strong><a href="/countries">Discover a Destination!</a></strong></p>')
    return render_template('dashboard.html', countries=value, posts=all_posts)

@app.route('/countries')
def sidebar():
    country_name = []
    
    alphabetList= ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
     'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

    results = requests.get('https://travelbriefing.org/countries.json')
    
    countries = results.json()

   # ---------- gets only counrty names from object in API response ------------------
    for obj in countries:
        single_country = obj['name']
        country_name.append(single_country)
    all_posts = Post.query.all()
    return render_template('dashboard.html',  country_name=country_name, alphabetList=alphabetList, tweets=all_posts)

@app.route('/country_view/<name_arg>', methods=['GET', 'POST'])
def country_view(name_arg):

    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/login')

    #---------------Unequal format specifiers and values for URL
    key = name_arg
    url = "https://travelbriefing.org/%s?format=json" % (key)
   
    results = requests.get(url)
    country_infos = results.json()
    #---------------Countent that is not availble will throw exceptions, need to be handled
    name1 = country_infos['names']['name']
    name2 = country_infos['names']['full']
    maps1 = country_infos['maps']['lat']
    maps2 = country_infos['maps']['long']
    lang = country_infos['language'][0]['language']
    cur_name = country_infos['currency']['name']
    cur_symbol = country_infos['currency']['symbol'] 
    advise = country_infos['advise']['UA']['advise']
    country_code = country_infos['names']['iso2']
    form = PostForm()
    all_posts = Post.query.all()
    if form.validate_on_submit():
        text = form.text.data
        new_post = Post(text=text, user_id=session['user_id'])
        db.session.add(new_post)
        db.session.commit()
        flash('Post Created!', 'success')
        #return redirect('/posts')

    return render_template('country_view.html', name1=name1, name2=name2,
 maps1=maps1, maps2=maps2,lang=lang, cur_name=cur_name, cur_symbol=cur_symbol, advise=advise, form=form, posts=all_posts, code=country_code.lower() )

# -------------- this route show locations for a particaular counrty, coming soon ... ---------
@app.route('/locations')
def locations():
    locations = [{}]
    return render_template('locations.html', locations=locations)

# -------------- show all user posts ----------------------------------------------------------

@app.route('/posts', methods=['GET', 'POST'])
def show_posts():
    if "user_id" not in session:
        flash("Please login first!", "danger")
        return redirect('/')
    form = PostForm()
    all_posts = Post.query.all()
    if form.validate_on_submit():
        text = form.text.data
        new_post = Post(text=text, user_id=session['user_id'])
        db.session.add(new_post)
        db.session.commit()
        flash('Post Created!', 'success')
        return redirect('/posts')

    return render_template("posts.html", form=form, posts=all_posts)

# --------- this route will delete a post, or ask to login  ----------

@app.route('/posts/<int:id>', methods=["POST"])
def delete_post(id):
    """Delete Post"""
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect('/login')
    post = Post.query.get_or_404(id)
    if post.user_id == session['user_id']:
        db.session.delete(post)
        db.session.commit()
        flash("Post deleted!", "info")
        return redirect('/posts')
    flash("Action Not Alowed", "danger")
    return redirect('/posts')

# ------------ user register route ---------------

@app.route('/register', methods=['GET', 'POST'])
def register_user():
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        new_user = User.register(username, password)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username Not Available!')
            return render_template('register.html', form=form)
        session['user_id'] = new_user.id
        flash('Welcome! Successfully Created Your Account!', "success")
        return redirect('/index')

    return render_template('register.html', form=form)


@app.route('/', methods=['GET', 'POST'])
def login_user():
    form = UserForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            flash(f"Welcome Back, {user.username}!", "primary")
            session['user_id'] = user.id
            return redirect('/index') #conditions needed to show certain pages"""
        else:
            form.username.errors = ['Invalid username/password.']

    return render_template('login.html', form=form)

# ------------ user logout  ---------------
@app.route('/logout')
def logout_user():
    session.pop('user_id')
    flash("Goodbye!", "info")
    return redirect('/')
