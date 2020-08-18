from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (
        DateField, HiddenField,StringField, TextAreaField, SelectField, 
        IntegerField, SelectMultipleField, FieldList, FormField, FloatField
    )
from wtforms.validators import DataRequired, Length, Optional, Email

required = " <span class='text-danger'>*</span>"

class SubscribeForm(FlaskForm):
    email = StringField('Email Address', validators=[Email()], render_kw={'placeholder': 'Email Address'})

    class Meta:
        csrf = False

class CommentForm(FlaskForm):
    user_id = HiddenField('User')
    punch_id = HiddenField('punch id')
    event_id = HiddenField('event id')
    ticket_id = HiddenField('ticket id')
    comment = TextAreaField('Comment')

class DeleteCommentForm(FlaskForm):
    comment_id = HiddenField('Comment ID', validators=[DataRequired()])
    redirect = HiddenField('Redirect')
    
class DeleteObjForm(FlaskForm):
    obj_id = HiddenField('Object id', validators=[DataRequired()])
    redirect = HiddenField('Redirect URL')
