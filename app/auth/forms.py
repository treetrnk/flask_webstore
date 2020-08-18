from flask_wtf import FlaskForm
from flask_wtf import Form
from wtforms import (
        StringField, PasswordField, BooleanField, SubmitField, IntegerField, 
        HiddenField, DecimalField, DateField, TextAreaField, SelectField
    )
from wtforms.ext.appengine.db import model_form
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.validators import DataRequired, ValidationError, EqualTo, Email, Optional, NumberRange, Regexp
from app.models import User, Group
from flask_login import current_user

required = '<span class="text-danger">*</span>'

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(),Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

def all_groups():
    return Group.query.order_by('name').all()

def all_users():
    return User.query.order_by('username').all()

class AddUserForm(FlaskForm):
    username = StringField(f'Username{required}', validators=[DataRequired()])
    password = PasswordField(f'Password{required}', validators=[DataRequired()])
    confirm_password = PasswordField(
            f'Confirm Password{required}', 
            validators=[DataRequired(), EqualTo('password')])
    phone = StringField('Cellphone', validators=[
            Regexp(r'^(?:\d{3}-)?\d{3}-\d{4}$', message="Invalid phone number"), 
            Optional(),
        ])
    extension = IntegerField('Extension', validators=[Optional()])
    email = StringField('Email', validators=[Email(), Optional()])
    allergies = StringField('Allergies')
    first_name = StringField(f'First Name{required}')
    last_name = StringField(f'Last Name{required}')
    avatar = SelectField('Avatar', coerce=str)
    groups = QuerySelectMultipleField('Groups', query_factory=all_groups, allow_blank=True)
    active = BooleanField('Active?')
    submit = SubmitField('Add User')

    def validate_username(self, username):
        user = User.query.filter_by(username=self.username.data).first()
        if user is not None:
            raise ValidationError('Username already in use.')
        return True

class EditUserForm(FlaskForm):
    id = HiddenField()
    username = StringField(f'Username{required}', validators=[DataRequired()])
    #password = PasswordField(f'Current Password', validators=[Optional()])
    #new_password = PasswordField('New Password')
    #confirm_password = PasswordField(
    #        f'Confirm Password', 
    #        validators=[EqualTo('new_password')])
    email = StringField('Email', validators=[Email(), Optional()])
    #allergies = StringField('Allergies')
    first_name = StringField(f'First Name{required}')
    last_name = StringField(f'Last Name{required}')
    avatar = SelectField('Avatar', coerce=str, validators=[Optional()])
    groups = QuerySelectMultipleField('Groups', query_factory=all_groups, allow_blank=True)
    #active = BooleanField('Active?')
    submit = SubmitField('Update User')

    def validate_username(self, username):
        user = User.query.filter_by(username=self.username.data).first()
        if user is not None:
            if not user.id == int(self.id.data):
                raise ValidationError('Username already in use.', 'danger')

    def validate_password(self, password):
        print(current_user.id)
        user = User.query.filter_by(id=current_user.id).first()
        if not user.check_password(self.password.data):
            raise ValidationError('Your current password was incorrect.', 'danger')
        if self.new_password.data != self.confirm_password.data:
            raise ValidationError('Your new passwords don\'t match.', 'danger')
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
