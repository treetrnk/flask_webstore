from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (
        DateField, HiddenField,StringField, TextAreaField, SelectField, 
        IntegerField, SelectMultipleField, FieldList, FormField, FloatField,
        BooleanField
    )
from wtforms.validators import DataRequired, Length, Optional, InputRequired

required = " <span class='text-danger'>*</span>"

class UserEditForm(FlaskForm):
    pass

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
    description = TextAreaField(f'Description{required}', validators=[DataRequired(), Length(max=1000)])
    priority = IntegerField(f'Priority')

class PageEditForm(FlaskForm):
    pass

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
