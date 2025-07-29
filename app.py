import re
import random
import MySQLdb.cursors
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
import stripe

stripe.api_key = 'sk_test_51RofqsRxn8ni2a1RF4Bqle3Ejj2smfnxZr9nMbAiIhwiwpLztqTB0UcQsSSRXKA5EnMTQPIwF8gckEMpqV7fQKoa00HwWuoqVR'
YOUR_DOMAIN = 'http://localhost:5000'

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'tutorbizz'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'h8642639@gmail.com'
app.config['MAIL_PASSWORD'] = 'bjrw wcmz iorv uuqk'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
mysql = MySQL(app)

@app.route('/')
def home():
    return redirect(url_for('homepage'))
@app.route('/home')
def homepage():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return render_template('index.html', msg='Logged in successfully!')
        else:
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def mail_send(email_address):
    random_code = random.randrange(10 ** 9, 10 ** 10)
    session['reset_code'] = str(random_code)
    msg = Message('Password Reset Code', sender='h8642639@gmail.com', recipients=[email_address])
    msg.body = f"Your verification code is: {random_code}"
    mail.send(msg)
    return 'Sent'

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only letters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    return render_template('register.html', msg=msg)

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    msg = ''
    if request.method == 'POST' and 'email' in request.form:
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            session['reset_email'] = email
            mail_send(email)
            return render_template('forgot2.html', msg='Verification code sent to your email.')
        else:
            msg = 'Email does not exist!'
    return render_template('forgot.html', msg=msg)

@app.route('/forgot2', methods=['GET', 'POST'])
def forgot2():
    msg = ''
    if request.method == 'POST' and 'vercode' in request.form:
        vercode = request.form['vercode'].strip()
        if vercode == session.get('reset_code'):
            return render_template('forgot3.html')
        else:
            msg = 'Code doesn\'t match!'
    return render_template('forgot2.html', msg=msg)

@app.route('/forgot3', methods=['GET', 'POST'])
def forgot3():
    msg = ''
    if request.method == 'POST' and 'newpassword' in request.form:
        newpassword = request.form['newpassword']
        email = session.get('reset_email')
        if not newpassword:
            msg = 'Password is required!'
        elif email:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE accounts SET password = %s WHERE email = %s', (newpassword, email))
            mysql.connection.commit()
            session.pop('reset_email', None)
            session.pop('reset_code', None)
            return render_template('login.html', msg='Password reset successful. You may now log in.')
        else:
            msg = 'Session expired. Please try again.'
    return render_template('forgot3.html', msg=msg)

@app.route('/checkout')
def checkout():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    return render_template('checkout.html')

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        session_obj = stripe.checkout.Session.create(
            ui_mode='embedded',
            line_items=[{
                'price': 'price_1Rog4ERxn8ni2a1RKEYKgApk',
                'quantity': 1,
            }],
            mode='payment',
            return_url=YOUR_DOMAIN + '/return.html?session_id={CHECKOUT_SESSION_ID}'
        )
        return jsonify(clientSecret=session_obj.client_secret)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/session-status', methods=['GET'])
def session_status():
    session_obj = stripe.checkout.Session.retrieve(request.args.get('session_id'))
    return jsonify(status=session_obj.status, customer_email=session_obj.customer_details.email)

if __name__ == '__main__':
    app.run(debug=True)
