from flask import Flask, render_template, flash, request, redirect, url_for, session, logging, json, jsonify
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
from flask_session import Session
import os

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.urandom(24)
Session(app)

dataCon = json.load(open('config.json'))
dbCred = dataCon["dbCred"]

app.config['MYSQL_HOST'] = dbCred["host"]
app.config['MYSQL_USER'] = dbCred["user"]
app.config['MYSQL_PASSWORD'] = dbCred["passwd"]
app.config['MYSQL_DB'] = dbCred["db"]
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    phone = StringField('Mobile Number', [validators.Length(min=10, max=10)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/products')
def products():

    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM bikes")
    products = cur.fetchall()

    if result > 0:
        return render_template('products.html', products=products)
    else:
        msg = 'No Articles found.'
        return render_template('products.html', msg=msg)
    
    cur.close()

@app.route('/product/<string:id>/')
def product(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM bikes where id = %s", [id])
    product = cur.fetchone()
    return render_template('product.html', product=product)

# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        phone = form.phone.data

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(name, email, username, password, phone) VALUES(%s, %s, %s, %s, %s)", (name, email, username, password, phone))
        mysql.connection.commit()
        cur.close()

        flash('You are now registered and can log in', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']

        cur = mysql.connection.cursor()

        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
        
        if result > 0:
            data = cur.fetchone()
            password = data['password']

            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in.', 'success')
                return redirect(url_for('profile'))
            else:
                error = 'Invalid user'
                return render_template('login.html', error=error)
            
            cur.close()

        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')  

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

@app.route('/profile')
@is_logged_in
def profile():
    return render_template('profile.html')


if __name__ == '__main__':
    app.run(debug=True)
