TutorBizz 



TutorBizz is an all-in-one educational platform designed to connect students with expert tutors, provide SAT preparation tools, and streamline the learning process. With secure logins, email-based password recovery, and Stripe-powered checkout, TutorBizz ensures that students and tutors can focus on learning without worrying about logistics.

Whether you're preparing for standardized tests or seeking academic support, TutorBizz offers a simple, user-friendly interface that empowers students and tutors alike to:

Manage tutoring sessions

Track progress

Prepare for the SAT

Build knowledge with ease

Getting Started
  Installation & Setup

Clone this repository:

git clone https://github.com/yourusername/tutorbizz.git
cd tutorbizz


Create a virtual environment and install dependencies:

python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux  
.venv\Scripts\activate     # Windows  
pip install -r requirements.txt


Set up environment variables in a .env file:

FLASK_APP=app.py
FLASK_ENV=development
MYSQL_USER=youruser
MYSQL_PASSWORD=yourpassword
MYSQL_DB=tutorbizz
STRIPE_SECRET_KEY=yourstripekey
MAIL_USERNAME=youremail@example.com
MAIL_PASSWORD=yourpassword


Run the app:

flask run

Trying It Out

Register as a student or tutor.

Explore the SAT prep tools.

Simulate a checkout with Stripe’s test mode.

Reset your password via email recovery.


Technologies Used

Backend: Python, Flask

Database: MySQL

Authentication: Flask-Login, Flask-Mail

Payments: Stripe API

Frontend: HTML, CSS, Bootstrap (extendable to React if needed)

