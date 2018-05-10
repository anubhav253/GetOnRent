from flask import Flask, render_template, flash, request, redirect, url_for, session, logging, json, jsonify
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt

app = Flask(__name__)

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
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
