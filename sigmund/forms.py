from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, InputRequired, NumberRange
from wtforms.widgets import NumberInput

from . import config


class LoginForm(FlaskForm):
    username = StringField('Username (from forum.cogsci.nl)',
                           validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class ExtendSubscriptionForm(FlaskForm):
    """Admin form (see routes/admin.py) to manually extend a user's
    subscription by a fixed number of days, starting from now, like a
    Stripe renewal.
    """
    days = IntegerField(
        'Days', default=config.subscription_length,
        widget=NumberInput(min=1, max=3650),
        validators=[InputRequired(), NumberRange(min=1, max=3650)])
    submit = SubmitField('Extend subscription')


class AddCreditsForm(FlaskForm):
    """Admin form (see routes/admin.py) to manually add extra credits to a
    user's buffer, in units of CREDITS_PER_UNIT tokens (see routes/store.py).
    """
    units = IntegerField(
        'Units', default=1,
        widget=NumberInput(min=1, max=100),
        validators=[InputRequired(), NumberRange(min=1, max=100)])
    submit = SubmitField('Add extra credits')
