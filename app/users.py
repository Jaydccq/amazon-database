from flask import render_template, redirect, url_for, flash, request, session
from urllib.parse import urlsplit as url_parse
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, NumberRange
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, NumberRange
from decimal import Decimal, InvalidOperation

from .models.user import User
from flask import Blueprint, current_app as app
bp = Blueprint('users', __name__)


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
    # Use DecimalField if available and preferred, otherwise FloatField is fine with Decimal conversion
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Top Up')

# Add the new WithdrawForm
class WithdrawForm(FlaskForm):
    # Use DecimalField if available and preferred, otherwise FloatField is fine with Decimal conversion
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Withdraw')


@bp.route('/topup', methods=['GET', 'POST'])
@login_required
def topup():
    form = TopUpForm()
    if form.validate_on_submit():
        try:
            # Convert float to Decimal for precision
            amount_decimal = Decimal(str(form.amount.data))
            # Ensure current balance is also Decimal
            current_balance_decimal = Decimal(str(current_user.current_balance))
            new_balance = current_balance_decimal + amount_decimal

            app.db.execute("""
                UPDATE Accounts
                SET current_balance = :balance
                WHERE user_id = :uid
            """, balance=new_balance, uid=current_user.id) # Use current_user.id

            # Update the user object in the session
            current_user.current_balance = new_balance
            flash(f'Successfully topped up ${amount_decimal:.2f}!', 'success')
            return redirect(url_for('users.profile'))
        except InvalidOperation:
             flash('Invalid amount entered.', 'danger')
        except Exception as e:
             app.logger.error(f"Topup failed for user {current_user.id}: {e}", exc_info=True)
             flash('An error occurred during top up. Please try again.', 'danger')

    # Pass balance for display, formatted
    current_balance_decimal = Decimal(str(current_user.current_balance))
    return render_template('topup.html', form=form, current_balance=f"{current_balance_decimal:.2f}")

# Add the new withdraw route
@bp.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    form = WithdrawForm()
    # Ensure balance is treated as Decimal
    try:
        current_balance_decimal = Decimal(str(current_user.current_balance))
    except InvalidOperation:
        app.logger.error(f"Could not convert current balance '{current_user.current_balance}' to Decimal for user {current_user.id}")
        flash('There was an error retrieving your balance. Please contact support.', 'danger')
        return redirect(url_for('users.profile'))

    if form.validate_on_submit():
        try:
            amount_decimal = Decimal(str(form.amount.data))

            if amount_decimal <= 0:
                 flash('Withdrawal amount must be positive.', 'warning')
            elif amount_decimal > current_balance_decimal:
                flash('Insufficient balance for this withdrawal.', 'danger')
            else:
                # Perform withdrawal
                new_balance = current_balance_decimal - amount_decimal
                app.db.execute("""
                    UPDATE Accounts
                    SET current_balance = :balance
                    WHERE user_id = :uid
                """, balance=new_balance, uid=current_user.id) # Use current_user.id

                current_user.current_balance = new_balance
                flash(f'Successfully withdrew ${amount_decimal:.2f}!', 'success')
                return redirect(url_for('users.profile'))
        except InvalidOperation:
             flash('Invalid amount entered.', 'danger')
        except Exception as e:
             app.logger.error(f"Withdrawal failed for user {current_user.id}: {e}", exc_info=True)
             flash('An error occurred during withdrawal. Please try again.', 'danger')
             # return redirect(url_for('users.profile'))

    # Pass balance for display, formatted
    return render_template('withdraw.html', form=form, current_balance=f"{current_balance_decimal:.2f}")


@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@bp.route('/become-seller', methods=['GET', 'POST']) # Allow POST if using a form, GET if just a link
@login_required
def become_seller():
    """Route to handle a user becoming a seller."""
    if current_user.is_seller:
        flash('You are already a seller!')
        return redirect(url_for('users.profile'))


    # Update database
    if User.make_seller(current_user.id):
        # Update the current_user object in the session
        current_user.is_seller = True
        session['is_seller'] = True

        flash('Congratulations! You are now registered as a seller.', 'success')
    else:
        flash('An error occurred while updating your account. Please try again.', 'danger')

    return redirect(url_for('users.profile'))

@bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    email = request.form.get('email')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    address = request.form.get('address') # Make sure address field exists in form

    # Basic validation
    if not email or not first_name or not last_name or not address:
         flash('All profile fields are required.', 'warning')
         return redirect(url_for('users.profile'))

    existing_user = User.get_by_email(email)
    if existing_user and existing_user.id != current_user.id:
        flash('Email address is already in use by another account.', 'danger')
        return redirect(url_for('users.profile'))

    if User.update_profile(current_user.id, email, first_name, last_name, address):
        flash('Your profile has been updated successfully!', 'success')
    else:
        flash('An error occurred while updating your profile. Please try again.', 'danger')

    return redirect(url_for('users.profile'))


# Route to handle password change submission
@bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not current_password or not new_password or not confirm_password:
        flash('Please fill in all password fields.', 'warning')
        return redirect(url_for('users.profile'))

    # Verify current password
    # Assuming current_user is fetched correctly by Flask-Login and has check_password
    if not current_user.check_password(current_password):
        flash('Incorrect current password.', 'danger')
        return redirect(url_for('users.profile'))

    # Check if new password and confirmation match
    if new_password != confirm_password:
        flash('New password and confirmation do not match.', 'warning')
        return redirect(url_for('users.profile'))

    # Check password complexity (optional but recommended)
    if len(new_password) < 8: # Example minimum length
        flash('New password must be at least 8 characters long.', 'warning')
        return redirect(url_for('users.profile'))

    # Update the password
    if User.update_password(current_user.id, new_password):
        flash('Your password has been updated successfully!', 'success')
    else:
        flash('An error occurred while changing your password. Please try again.', 'danger')

    return redirect(url_for('users.profile'))