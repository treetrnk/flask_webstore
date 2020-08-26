from flask_wtf import FlaskForm
from flask_wtf import Form
from wtforms import (
        StringField, PasswordField, BooleanField, SubmitField, IntegerField, 
        HiddenField, DecimalField, DateField, TextAreaField, SelectField
    )
from wtforms.ext.appengine.db import model_form
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.validators import DataRequired, ValidationError, EqualTo, Email, Optional, NumberRange, Regexp, Length
from app.models import User, Group
from flask_login import current_user

required = ' *'

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(),Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class SignUpForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(),Email()])
    new_password = PasswordField('Password', validators=[DataRequired(), Length(min=7,max=20)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('new_password')])
    subscribed = BooleanField('Subscribe to our Newsletter?')
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter(User.email.ilike(self.email.data)).first()
        if user:
            raise ValidationError(f'An account already exists for {self.email.data}.')

    def validate_new_password(self, new_password):
        if self.new_password.data:
            password = self.new_password.data
            success = True
            specials = ['~','!','@','#','$','%','^','&','*','(',')','-','_','=','+']
            if not any(char.isupper() for char in password):
                success = False
            if not any(char.islower() for char in password):
                success = False
            if not any(char.isdigit() for char in password):
                success = False
            if not success:
                raise ValidationError('Passwords must include at least one uppercase character, one lowercase character, and a number.')

def all_groups():
    return Group.query.order_by('name').all()

def all_users():
    return User.query.order_by('username').all()

class UserEditForm(FlaskForm):
    first_name = StringField(f'First Name{required}', validators=[DataRequired(), Length(max=100)])
    last_name = StringField(f'Last Name{required}', validators=[DataRequired(), Length(max=100)])
    email = StringField(f'Email{required}', validators=[Email(), DataRequired(), Length(max=100)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=16, min=7)])
    company = StringField('Company', validators=[Length(max=100)], description="<br /><br />")
    current_password = PasswordField(f'Current Password', validators=[Optional(), Length(min=7, max=20)])
    new_password = PasswordField('New Password')
    confirm_password = PasswordField(
            f'Confirm Password', 
            validators=[EqualTo('new_password')])

    def validate_email(self, email):
        user = User.query.filter_by(email=self.email.data).first()
        if user is not None:
            if not user.id == current_user.id:
                raise ValidationError('This email address is already in use.', 'danger')

    def validate_current_password(self, current_password):
        user = User.query.filter_by(id=current_user.id).first()
        if not user.check_password(self.current_password.data):
            raise ValidationError('Your current password was incorrect.', 'danger')

    def validate_new_password(self, new_password):
        if self.new_password.data and self.confirm_password.data:
            if self.new_password.data != self.confirm_password.data:
                raise ValidationError('Your new passwords don\'t match.', 'danger')
        if self.new_password.data:
            password = self.new_password.data
            success = True
            specials = ['~','!','@','#','$','%','^','&','*','(',')','-','_','=','+']
            if not any(char.isupper() for char in password):
                success = False
            if not any(char.islower() for char in password):
                success = False
            if not any(char.isdigit() for char in password):
                success = False
            if not success:
                raise ValidationError('Passwords must include at least one uppercase character, one lowercase character, and a number.')
        return True


class EditGroupForm(FlaskForm):
    name = StringField(f'Group Name{required}', validators=[DataRequired()])
    description = TextAreaField('Description')
    style = SelectField('Style', coerce=str) 
    restricted = BooleanField('Restricted?') 
    submit = SubmitField('Save Group')

class DeleteUserForm(FlaskForm):
    user_id = HiddenField('User id')

class DeleteGroupForm(FlaskForm):
    group_id = HiddenField('Group id')
