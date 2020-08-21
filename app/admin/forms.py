from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (
        DateField, HiddenField,StringField, TextAreaField, SelectField, 
        IntegerField, SelectMultipleField, FieldList, FormField, FloatField,
        BooleanField
    )
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.validators import DataRequired, Length, Optional, InputRequired, Email
from app.models import Group

required = " <span class='text-danger'>*</span>"

def all_groups():
    return Group.query.order_by('name').all()

class UserEditForm(FlaskForm):
    email = StringField(f'Email{required}', validators=[DataRequired(), Email(), Length(max=120)])
    username = StringField('Username', validators=[Length(max=20)])
    first_name = StringField('First Name', validators=[Length(max=50)])
    last_name = StringField('Last Name', validators=[Length(max=50)])
    groups = QuerySelectMultipleField('Groups', query_factory=all_groups, allow_blank=True, 
            render_kw={'data-type': 'select2'})
    company = StringField('Company', validators=[Length(max=100)])
    phone = StringField('Phone Number', validators=[Length(max=12)])
    subscribed = BooleanField('Subscribed?')


class GroupEditForm(FlaskForm):
    name = StringField(f'Name{required}', validators=[DataRequired(), Length(max=75)])
    description = TextAreaField('Description', validators=[Length(max=300)])
    style = SelectField(f'Style{required}', validators=[Length(max=75)])

class SettingEditForm(FlaskForm):
    name = StringField(f'Name{required}', validators=[DataRequired(), Length(max=100)])
    value = TextAreaField(f'value{required}', validators=[DataRequired(), Length(max=5000)])

class ProductEditForm(FlaskForm):
    name = StringField(f'Name{required}', 
                validators=[DataRequired(), Length(max=200)])
    barcode = StringField(f'Barcode', validators=[Length(max=50)])
    image = FileField('Image')#, validators=[FileAllowed('image', 'File must be an image.')]) 
    description = TextAreaField('Description', validators=[Length(max=5000)])
    category_id = SelectField('Category', coerce=int, render_kw={'data_type': 'select2'})
    price = FloatField(f'Price', validators=[DataRequired()], 
            render_kw={'type': 'number', 'step': '.01'})
    on_sale = BooleanField('On Sale?', description="")
    sale_price = FloatField(f'Sale Price', validators=[Optional()], 
            render_kw={'type': 'number', 'step': '.01'})
    packaging = StringField('Packaging', validators=[Length(max=50)])
    notes = StringField('Notes', validators=[Length(max=50)])
    comment = StringField('Comment', validators=[Length(max=50)])
    available = IntegerField('Available', validators=[Optional()], render_kw={'type': 'number'})
    capacity = IntegerField(f'Capacity{required}', validators=[InputRequired()], render_kw={'type': 'number'})
    active = BooleanField('Active?', 
            description="<small class='text-muted ml-4'>Deactivate if the product should no longer be used.</small>",
            render_kw={'data_type': 'switch'})

class CategoryEditForm(FlaskForm):
    name = StringField(f'Name{required}', validators=[DataRequired(), Length(max=100)])
    image = FileField('Image')#, validators=[FileAllowed('image', 'File must be an image.')]) 
    description = TextAreaField(f'Description', validators=[Length(max=1000)])
    priority = IntegerField(f'Priority')

class PageEditForm(FlaskForm):
    title = StringField(f'Title{required}', validators=[DataRequired(), Length(max=200)])
    slug = StringField(f'Slug{required}', validators=[DataRequired(), Length(max=200)])
    body = TextAreaField(f'Body{required}', validators=[DataRequired(), Length(max=5000)])
    priority = IntegerField('Priority', validators=[Optional()])
    top_nav = BooleanField('In Navigation?')
    active = BooleanField('Active?')

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
