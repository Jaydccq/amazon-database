from flask import render_template, redirect, url_for, flash, request
from urllib.parse import urlsplit as url_parse
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo

from .models.user import User
from flask import Blueprint, current_app as app

bp = Blueprint('users', __name__)

# psql -h localhost -p 15432 -U miniamazon -d miniamazon
#ssh -L 15432:localhost:5432 zs181@vcm-45418.vm.duke.edu
# psql -h localhost -p 15432 -U miniamazon -d miniamazon -f load_app_data.sql
# icecream@tastes.good  test123
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_auth(form.email.data, form.password.data)
        if user is None:
            flash('Invalid email or password')
            return redirect(url_for('users.login'))
        login_user(user)

        from flask import session
        session['full_name'] = user.first_name + ' ' + user.last_name
        session['is_seller'] = user.is_seller
        session['user_id'] = user.user_id

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index.index')

        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)



class RegistrationForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    address = StringField('Address', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(),
                                    EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        if User.email_exists(email.data):
            raise ValidationError('Already a user with this email.')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.register(form.email.data,
                        form.password.data,
                        form.firstname.data,
                        form.lastname.data,
                        form.address.data
                        ):
            flash('Congratulations, you are now a registered user!')
            return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)



@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index.index'))



class TopUpForm(FlaskForm):
    amount = FloatField('Amount', validators=[DataRequired()])
    submit = SubmitField('Top Up')


@bp.route('/topup', methods=['GET', 'POST'])
@login_required
def topup():
    form = TopUpForm()
    if form.validate_on_submit():
        # Convert float to Decimal to avoid type mismatch
        from decimal import Decimal
        amount_decimal = Decimal(str(form.amount.data))  # Convert via string to avoid precision issues
        new_balance = current_user.current_balance + amount_decimal

        app.db.execute("""
            UPDATE Accounts
            SET current_balance = :balance
            WHERE user_id = :uid
        """, balance=new_balance, uid=current_user.user_id)

        current_user.current_balance = new_balance
        flash(f'Successfully topped up ${amount_decimal:.2f}!')
        return redirect(url_for('users.profile'))

    return render_template('topup.html', form=form)



@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

