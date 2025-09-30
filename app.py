import os
import re
import random
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
import MySQLdb.cursors
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
import stripe

load_dotenv()

stripe.api_key = os.environ['STRIPE_API_KEY']
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
YOUR_DOMAIN = os.environ.get('APP_BASE_URL', 'http://localhost:5000')

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_secret_key')


app.config['MYSQL_HOST'] = os.environ['MYSQL_HOST']
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = os.environ['MYSQL_PASSWORD']
app.config['MYSQL_DB'] = os.environ['DB_NAME']
app.config['MYSQL_PORT'] = 28682

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'h8642639@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)
mysql = MySQL(app)
executor = ThreadPoolExecutor(max_workers=4)


@app.route('/')
def home():
    return redirect(url_for('homepage'))

@app.route('/home')
def homepage():
    return render_template('home.html')

@app.route('/lhome', methods=['GET', 'POST'])
def loggedhome():
    return render_template('lhome.html')

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
            session['payment'] = account.get('payment', 'empty')
            return render_template('lhome.html', msg=username)
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
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s)', (username, password, email, "empty"))
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
    return render_template('checkout.html', publishable_key=STRIPE_PUBLISHABLE_KEY)

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
    session_id = request.args.get('session_id')
    session_obj = stripe.checkout.Session.retrieve(session_id)
    try:
        paid = False
        if getattr(session_obj, 'payment_status', None) == 'paid' or getattr(session_obj, 'status', None) == 'complete':
            paid = True
        if paid and session.get('loggedin'):
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE accounts SET payment = %s WHERE id = %s', ('SAT', session['id']))
            mysql.connection.commit()
            session['payment'] = 'SAT'
    except Exception:
        pass

    customer_email = None
    if getattr(session_obj, 'customer_details', None):
        customer_email = session_obj.customer_details.email

    return jsonify(
        status=getattr(session_obj, 'status', None),
        payment_status=getattr(session_obj, 'payment_status', None),
        customer_email=customer_email
    )

@app.route('/return.html')
def return_html():
    return render_template('return.html')

@app.route('/sat-bank')
def sat_bank():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT payment FROM accounts WHERE id = %s', (session['id'],))
    account = cursor.fetchone()
    if account and account['payment'] == 'SAT':
        return render_template('practice.html')
    return redirect(url_for('checkout'))

@app.route("/practice")
def practice():
    if not session.get('loggedin'):
        return redirect(url_for('login'))
    return render_template("practice.html")


async def _generate_sat_question_async():
    prompt = """
    Create an SAT-style question with a clear question, four options, and a single correct answer.
    The question should be in one of the SAT subjects: Reading, Writing and Language, or Math.
    """

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "q": {"type": "STRING"},
                    "options": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "minItems": 4,
                        "maxItems": 4
                    },
                    "answer": {"type": "STRING"}
                }
            }
        }
    }

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"error": "API key is missing"}

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"

    import aiohttp
    async with aiohttp.ClientSession() as session_http:
        for i in range(5):
            try:
                async with session_http.post(api_url, json=payload, headers={'Content-Type': 'application/json'}) as response:
                    response.raise_for_status()
                    result = await response.json()

                    if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
                        json_string = result["candidates"][0]["content"]["parts"][0]["text"]
                        return json.loads(json_string)
                    else:
                        raise ValueError("Unexpected API response format")

            except (aiohttp.client_exceptions.ClientError, ValueError):
                await asyncio.sleep(2 ** i)
        return {"error": "Failed to generate question after multiple retries"}

def generate_sat_question():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(_generate_sat_question_async())

@app.route("/get_question")
def get_question():
    if not session.get('loggedin'):
        return jsonify({"error": "Not logged in"}), 401
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT payment FROM accounts WHERE id = %s', (session['id'],))
    account = cursor.fetchone()
    if not account or account['payment'] != 'SAT':
        return jsonify({"error": "Payment required"}), 403
    question = generate_sat_question()
    return jsonify(question)

if __name__ == '__main__':
    app.run(debug=True)
