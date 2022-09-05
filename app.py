from flask import Flask, render_template, flash, redirect, url_for, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime


# Create a Flask instance.
app = Flask(__name__)
# Add a secret key.
app.config["SECRET_KEY"] = "MY super secret key"
# Connect to a database.
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///database.db'
# Get rid of SQLALCHEMY_TRACK_MODIFICATIONS warning.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Create db Instance.
db = SQLAlchemy(app)


# Create the login manager.
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Create a Users class.
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    full_name = db.Column(db.String(200))
    age = db.Column(db.Integer())
    location = db.Column(db.String())
    username = db.Column(db.String(15), unique=True)
    password = db.Column(db.String(80))
    email = db.Column(db.String(), unique=True)
    date_added = db.Column(db.String())


# Create Login Form.
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log In")


# Create Registration Form.
class RegistrationForm(FlaskForm):
    full_name = StringField("Full Name", validators=[InputRequired()])
    age = StringField("Your age", validators=[InputRequired()])
    location = StringField("Country", validators=[InputRequired()])
    username = StringField("Username(Nickname) - You will need this to log in", validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=8, max=80)])
    email = StringField("Email", validators=[InputRequired(), Email(message="Invalid E-mail!")])
    date_added = str(datetime.now()).split(".")[0]
    signup = SubmitField("Register")


# Create a UserUpdate form.
class UserUpdate(FlaskForm):
    full_name = StringField("Full Name", validators=[InputRequired()])
    age = StringField("Your age", validators=[InputRequired()])
    location = StringField("Country", validators=[InputRequired()])
    username = StringField("Username(Nickname) - You will need this to log in",
                           validators=[InputRequired(), Length(min=4, max=15)])
    email = StringField("Email", validators=[InputRequired(), Email(message="Invalid E-mail!")])
    submit = SubmitField("Update Profile")


# Create index route.
@app.route("/")
def index():
    return render_template("index.html")

# Create admin route.
@app.route("/admin")
@login_required
def admin():
    all_users = Users.query.order_by(Users.date_added)
    id = current_user.id
    if id == 1:
        return render_template("admin.html",
                               all_users=all_users)
    else:
        flash("Sorry only admins can access admin page.")
        return redirect((url_for("dashboard")))

# Create login route.
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                flash("Logged in successfully!")
                return redirect(url_for('dashboard'))
        else:
            flash(f"Invalid username or password.")
    return render_template("login.html",
                           form=form)

# Create a sign up route.
@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        mail = Users.query.filter_by(email=form.email.data).first()
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        if user:
            flash(f"Username '{form.username.data}' already exists.")
        if mail:
            flash(f"E-mail address '{form.email.data}' is already asociated to another user.")
        else:
            new_user = Users(full_name=form.full_name.data,
                             age=form.age.data,
                             location=form.location.data,
                             username=form.username.data,
                             email=form.email.data,
                             password=hashed_password,
                             date_added=form.date_added)

            db.session.add(new_user)
            db.session.commit()
            flash(f"User '{form.username.data}' has been successfully created. Got to login page.")
    return render_template("signup.html",
                           form=form)

# Create a login manager function
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Create a dashboard route.
@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    form = UserUpdate()
    id = current_user.id
    to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        to_update.full_name = request.form["full_name"]
        to_update.age = request.form["age"]
        to_update.location = request.form["location"]
        to_update.username = request.form["username"]
        to_update.email = request.form["email"]
        try:
            db.session.commit()
            flash("User details updated successfully!")
            return render_template("dashboard.html",
                                   current_user=current_user,
                                   to_update=to_update,
                                   form=form)
        except:
            flash("Oops! Seems there was an error! Try again!")
            return render_template("dashboard.html",
                                   current_user=current_user,
                                   to_update=to_update,
                                   form=form)
    return render_template("dashboard.html",
                           current_user=current_user,
                           to_update=to_update,
                           form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))





if __name__ == "__main__":
    app.run(debug=True)