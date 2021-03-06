from flask import Flask, render_template, flash, request, redirect, url_for, session, logging, json, jsonify
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, TextField, SubmitField
from passlib.hash import sha256_crypt
from functools import wraps
from flask_session import Session
import os
import paypalrestsdk
import smtplib

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.urandom(24)
Session(app)

dataCon = json.load(open('config.json'))
dbCred = dataCon["dbCred"]
paypal = dataCon["paypal"]
feConfig = dataCon["feConfig"]

senderEmail = dataCon["gmailCred"]["email"]
senderPassword = dataCon["gmailCred"]["passWord"]
supportEmail = dataCon["gmailCred"]["supportEmail"]

emailClient = smtplib.SMTP('smtp.gmail.com', 587)
emailClient.starttls()


paypalrestsdk.configure({
  "mode": "sandbox", # sandbox or live
  "client_id": paypal["client_id"],
  "client_secret": paypal["client_secret"] })


app.config['MYSQL_HOST'] = dbCred["host"]
app.config['MYSQL_USER'] = dbCred["user"]
app.config['MYSQL_PASSWORD'] = dbCred["passwd"]
app.config['MYSQL_DB'] = dbCred["db"]
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('home.html', feConfig=feConfig)

@app.route('/about')
def about():
    return render_template('about.html', feConfig=feConfig)

@app.route('/bikes')
def bikes():

    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM bikes")
    bikes = cur.fetchall()

    if result > 0:
        return render_template('bikes.html', bikes=bikes, feConfig=feConfig)
    else:
        msg = 'No Products found.'
        return render_template('bikes.html', msg=msg, feConfig=feConfig)
    
    cur.close()

@app.route('/bike/<string:id>/')
def bike(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM bikes where id = %s", [id])
    bike = cur.fetchone()
    return render_template('bike.html', bike=bike, feConfig=feConfig)

@app.route('/cars')
def cars():

    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM cars")
    cars = cur.fetchall()

    if result > 0:
        return render_template('cars.html', cars=cars, feConfig=feConfig)
    else:
        msg = 'No Products found.'
        return render_template('cars.html', msg=msg, feConfig=feConfig)
    
    cur.close()

@app.route('/car/<string:id>/')
def car(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM cars where id = %s", [id])
    car = cur.fetchone()
    return render_template('car.html', car=car, feConfig=feConfig)

@app.route('/furnitures')
def furnitures():

    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM furnitures")
    furnitures = cur.fetchall()

    if result > 0:
        return render_template('furnitures.html', furnitures=furnitures, feConfig=feConfig)
    else:
        msg = 'No Products found.'
        return render_template('furnitures.html', msg=msg, feConfig=feConfig)
    
    cur.close()

@app.route('/furniture/<string:id>/')
def furniture(id):
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM furnitures where id = %s", [id])
    furniture = cur.fetchone()
    return render_template('furniture.html', furniture=furniture, feConfig=feConfig)

def sendEmail(Email, message):
    try:
        emailClient.login(senderEmail, senderPassword)
        print("Sending Message to " + Email)
        emailClient.sendmail(senderEmail, Email, message)
        print("Message sent")
        emailClient.quit()
    except Exception as e:
        print("Something went wrong in sending email")
        print(e)

class ContactForm(Form):
    name = TextField("Name")
    email = TextField("Email")
    subject = TextField("Subject")
    message = TextAreaField("Message")
    submit = SubmitField("Send")

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        subject = form.subject.data
        message = form.message.data

        msg = "An Application has been submitted by\n"
        msg = msg + "Name = " + name + "\n"
        msg = msg + "Email =" + email + "\n"
        msg = msg + "Subject" + subject + "\n"
        msg = msg + "Message" + message 

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO contactus(name, email, subject, message) VALUES(%s, %s, %s, %s)", (name, email, subject, message))
        mysql.connection.commit()
        cur.close()

        flash('Your message has been delivered.', 'success')
        sendEmail(supportEmail, msg)
        return redirect(url_for('index'))
    return render_template('contact.html', form=form, feConfig=feConfig)

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
        return redirect(url_for('index'))
    return render_template('register.html', form=form, feConfig=feConfig)

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
            role = data['role']

            if (sha256_crypt.verify(password_candidate, password)) and (role == 1):
                session['logged_in'] = True
                session['username'] = username
                session["admin"] = True

                flash('You are now logged in.', 'success')
                return redirect(url_for('profile'))

            elif sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in.', 'success')
                return redirect(url_for('profile'))
            else:
                error = 'Invalid user'
                return render_template('login.html', error=error, feConfig=feConfig)
            
            cur.close()

        else:
            error = 'Username not found'
            return render_template('login.html', error=error, feConfig=feConfig)

    return render_template('login.html', feConfig=feConfig)  

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

def is_admin(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin' in session:
            return f(*args, **kwargs)
        elif 'logged_in' in session:
            flash('Unauthorized, Please login with correct username', 'danger')
            return redirect(url_for('login'))
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
    return render_template('profile.html', feConfig=feConfig)


@app.route('/admin')
@is_admin
def admin():
    return render_template('admin.html', feConfig=feConfig)

@app.route('/buy')
@is_logged_in
def buy():
    return render_template('buy.html', feConfig=feConfig)

@app.route('/payment', methods=['POST'])
def payment():
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "http://localhost:3000/payment/execute",
            "cancel_url": "http://localhost:3000/"},
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": "testitem",
                    "sku": "12345",
                    "price": "50.00",
                    "currency": "USD",
                    "quantity": 1}]},
            "amount": {
                "total": "50.00",
                "currency": "USD"},
            "description": "This is the payment transaction description."}]})

    if payment.create():
        print("Payment Successful")
    else:
        print(payment.error)

    return jsonify({'paymentID':payment.id}, feConfig=feConfig)

@app.route('/execute', methods=['POST'])
def execute():
    success = False

    payment = paypalrestsdk.Payment.find(request.form['paymentID'])
    if payment.execute({'payer_id' : request.form['payerID']}):
        print('Execute success')
        success = True
    else:
        print(payment.error)
    return jsonify({'success' : success}, feConfig=feConfig)


class AddProduct(Form):
    comapany = StringField('Comapany', [validators.Length(min=1, max=100)])
    model = StringField('Body', [validators.Length(min=5, max=100)])
    year = StringField('Year', [validators.Length(max=4)])
    kmdrive = StringField('Km Driven', [validators.Length(max=6)])
    price = StringField('Price', [validators.Length(max=6)])
    description = TextAreaField('Description', [validators.Length(max=500)])
    deposit = StringField('Deposit', [validators.Length(max=6)])
    address = StringField('Address', [validators.Length(max=150)])
    city = StringField('City', [validators.Length(max=30)])
    aliasName = StringField('Alias Name', [validators.Length(max=50)])
    details = TextAreaField('Details', [validators.Length(max=500)])

# Add Product
@app.route('/add_product', methods=['GET', 'POST'])
@is_admin
def add_product():
    form = AddProduct(request.form)
    if request.method == 'POST' and form.validate():
        comapany = form.comapany.data
        model = form.model.data
        year = form.year.data
        kmdrive = form.kmdrive.data
        price = form.price.data
        description = form.description.data
        deposit = form.deposit.data
        address = form.address.data
        city = form.city.data
        aliasName = form.aliasName.data
        details = form.details.data


        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO bikes(comapany, model, year, kmdrive, price, description, deposit, address, city, aliasName, details) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",(comapany, model, year, kmdrive, price, description, deposit, address, city, aliasName, details))
        mysql.connection.commit()
        cur.close()

        flash('Product added', 'success')

        return redirect(url_for('bikes'))

    return render_template('add_product.html', form=form, feConfig=feConfig)

if __name__ == '__main__':
    app.run(debug=True)
