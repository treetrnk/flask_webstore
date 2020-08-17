from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (
        DateField, HiddenField,StringField, TextAreaField, SelectField, 
        IntegerField, SelectMultipleField, FieldList, FormField, FloatField
    )
from wtforms.validators import DataRequired, Length, Optional

required = " <span class='text-danger'>*</span>"

class CommentForm(FlaskForm):
    user_id = HiddenField('User')
    punch_id = HiddenField('punch id')
    event_id = HiddenField('event id')
    ticket_id = HiddenField('ticket id')
    comment = TextAreaField('Comment')

class BoxlistChangeForm(FlaskForm):
    boxlist = SelectField(f'Box List{required}', coerce=int)

class MarketplaceEditForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=150)])
    profit_multiplier = FloatField('Default Profit Multiplier', validators=[Optional()],
            description='<small class="text-muted">Will be used to automatically fill fields when creating a label for this marketplace</small>'
        )
    marketplace_fee = FloatField('Default Marketplace Fee', validators=[Optional()],
            description='<small class="text-muted">Will be used to automatically fill fields when creating a label for this marketplace</small>'
        )

class DestinationEditForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=150)])
    percent = IntegerField('Percent', validators=[DataRequired()], render_kw={'type': 'number'})

class BoxlistEditForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=150)])
    boxnames = SelectMultipleField('Box Names', validators=[DataRequired()], render_kw={'data_type': 'select2-tags'})

class ThemeEditForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=150)])
    text_color = StringField('Text Color', validators=[DataRequired(), Length(max=7)], render_kw={'type': 'color'})
    background_color = StringField('Background Color', validators=[DataRequired(), Length(max=7)], render_kw={'type': 'color'})

class SetBoxlistForm(FlaskForm):
    boxlist_id = IntegerField('boxlist_id', validators=[DataRequired()])

class DeleteCommentForm(FlaskForm):
    comment_id = HiddenField('Comment ID', validators=[DataRequired()])
    redirect = HiddenField('Redirect')
    
class DeleteObjForm(FlaskForm):
    obj_id = HiddenField('Object id', validators=[DataRequired()])
    redirect = HiddenField('Redirect URL')
