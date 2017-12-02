from functools import wraps
from flask import Flask, render_template, flash, redirect, url_for, session, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from passlib.hash import sha256_crypt

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'user'
app.config['MYSQL_PASSWORD'] = 'pass'
app.config['MYSQL_DB'] = 'db'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.secret_key = "devkey"

# Init MySQL
mysql = MySQL(app)

# Index
@app.route('/')
def index():
    return render_template('home.html')

# About
@app.route('/about')
def about():
    return render_template('about.html')

# Articles
@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()
    # Get articles
    result = cur.execute("SELECT * FROM articles")
    all_articles = cur.fetchall()
    if result > 0:
        return render_template('articles.html', articles=all_articles)
    # Close connection
    cur.close()
    # Message for user
    msg = 'No articles found.'
    return render_template('articles.html', msg=msg)

# Single article
@app.route('/article/<string:id_number>/')
def article(id_number):
    # Create cursor
    cur = mysql.connection.cursor()
    # Get article
    cur.execute("SELECT * FROM articles WHERE id = %s", [id_number])
    one_article = cur.fetchone()
    return render_template('article.html', article=one_article)

# User register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        # Create cursor
        cur = mysql.connection.cursor()
        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
        # Commit to DB
        mysql.connection.commit()
        # Close connection
        cur.close()
        # Message for user
        flash('You are now registered.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form fields
        username = request.form['username']
        password_candidate = request.form['password']
        # Create cursor
        cur = mysql.connection.cursor()
        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']
            # Compare passwords
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                # Message for user
                flash('You are now logged in.', 'success')
                return redirect(url_for('dashboard'))
            # Close connection
            cur.close()
            # Message for user
            error = 'Wrong password.'
            return render_template('login.html', error=error)
        # Message for user
        error = 'Username not found.'
        return render_template('login.html', error=error)
    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        # Message for user
        flash('Unauthorized access, please login first.', 'danger')
        return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    # Message for user
    flash('You are now logged out.', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()
    # Get articles
    result = cur.execute("SELECT * FROM articles")
    all_articles = cur.fetchall()
    if result > 0:
        return render_template('dashboard.html', articles=all_articles)
    # Close connection
    cur.close()
    # Message for user
    msg = 'No articles found.'
    return render_template('dashboard.html', msg=msg)

# Add article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        # Create cursor
        cur = mysql.connection.cursor()
        # Execute query
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))
        # Commit to DB
        mysql.connection.commit()
        # Close connection
        cur.close()
        # Message for user
        flash('Article created.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)

# Edit article
@app.route('/edit_article/<string:id_number>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id_number):
    # Create cursor
    cur = mysql.connection.cursor()
    # Get article by id
    cur.execute("SELECT * FROM articles WHERE id=%s", [id_number])
    one_article = cur.fetchone()
    # Get form
    form = ArticleForm(request.form)
    # Populate article form fields
    form.title.data = one_article['title']
    form.body.data = one_article['body']
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
        # Create cursor
        cur = mysql.connection.cursor()
        # Execute query
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id_number))
        # Commit to DB
        mysql.connection.commit()
        # Close connection
        cur.close()
        # Message for user
        flash('Article updated.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)

# Delete article
@app.route('/delete_article/<string:id_number>', methods=['POST'])
@is_logged_in
def delete_article(id_number):
    # Create cursor
    cur = mysql.connection.cursor()
    # Execute query
    cur.execute("DELETE FROM articles WHERE id=%s", [id_number])
    # Commit to DB
    mysql.connection.commit()
    # Close connection
    cur.close()
    # Message for user
    flash('Article deleted.', 'success')
    return redirect(url_for('dashboard'))

# Register form class
class RegisterForm(Form):
    name = StringField('Name', validators=[DataRequired("Please enter your name."), Length(min=1, max=50)])
    username = StringField('Username', validators=[DataRequired("Please enter your username."), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired("Please enter your email address."), Email("Please enter a valid email address.")])
    password = PasswordField('Password', validators=[DataRequired("Please enter your password."), Length(min=6, message="Passwords must be at least 6 characters long."), EqualTo('confirm', message='Password do not match.')])
    confirm = PasswordField('Confirm password.', validators=[DataRequired("Please re-enter your password.")])

# Article form class
class ArticleForm(Form):
    title = StringField('Title', validators=[DataRequired("Please enter article title."), Length(min=1, max=200)])
    body = TextAreaField('Article', validators=[DataRequired("Please enter content for article."), Length(min=30)])

if __name__ == '__main__':
    app.run(debug=True)
