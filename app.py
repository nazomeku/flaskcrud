from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from passlib.hash import sha256_crypt
from data import Articles

app = Flask(__name__)
Articles = Articles()

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
    return render_template('articles.html', articles=Articles)

# Single article
@app.route('/article/<string:id_number>/')
def article(id_number):
    return render_template('article.html', id=id_number)

# Register form
class RegisterForm(Form):
    name = StringField('Name', validators=[DataRequired("Please enter your name."), Length(min=1, max=50)])
    username = StringField('Username', validators=[DataRequired("Please enter your username."), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired("Please enter your email address."), Email("Please enter a valid email address.")])
    password = PasswordField('Password', validators=[DataRequired("Please enter your password."), Length(min=6, message="Passwords must be at least 6 characters long."), EqualTo('confirm', message='Password do not match.')])
    confirm = PasswordField('Confirm password.', validators=[DataRequired("Please re-enter your password.")])

# Register user
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
        return redirect(url_for('index'))
    return render_template('register.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
