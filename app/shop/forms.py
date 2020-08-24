from flask_wtf import FlaskForm
from wtforms import (
        HiddenField, IntegerField, StringField, SelectField
    )
from wtforms.validators import DataRequired, NumberRange, Length, Email, Optional

required = " *"

class AddToCartForm(FlaskForm):
    product_id = HiddenField('product id', validators=[DataRequired()])
    option_id = HiddenField('option_id', validators=[DataRequired()])
    amount = IntegerField('Amount', validators=[DataRequired(), NumberRange(min=1)])

class CartUpdateForm(FlaskForm):
    item_id = HiddenField('item id', validators=[DataRequired()])
    amount = IntegerField('Amount', validators=[DataRequired(), NumberRange(min=1)], render_kw={'type': 'number'})

class RemoveItemForm(FlaskForm):
    option_id = HiddenField('option id', validators=[DataRequired()])

class ShippingForm(FlaskForm):
    full_name = StringField(f'Full Name{required}', validators=[DataRequired(), Length(max=150)])
    email = StringField(f'Email{required}', validators=[DataRequired(), Length(max=150), Email()])
    phone = StringField('Phone', validators=[Length(min=10, max=12), Optional()])
    address_1 = StringField(f'Address 1{required}', validators=[DataRequired(), Length(max=100)])
    address = StringField('Address 2', validators=[Length(max=100)])
    city = StringField(f'City{required}', validators=[DataRequired(), Length(max=100)])
    state = SelectField(f'State{required}', validators=[DataRequired(), Length(max=100)])
    zipcode = StringField(f'Zip Code{required}', validators=[DataRequired(), Length(min=5, max=5)])

class ConfirmForm(FlaskForm):
    status = HiddenField('status')
