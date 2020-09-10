from flask_wtf import FlaskForm
from wtforms import (
        HiddenField, IntegerField, StringField, SelectField, DateField, TimeField,
    )
from wtforms.validators import DataRequired, NumberRange, Length, Email, Optional, ValidationError

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
    parent_id = HiddenField('order id')
    full_name = StringField(f'Full Name{required}', validators=[DataRequired(), Length(max=150)])
    email = StringField(f'Email{required}', validators=[DataRequired(), Length(max=150), Email()])
    phone = StringField('Phone', validators=[Length(min=10, max=12), Optional()])
    address_1 = StringField(f'Address 1{required}', validators=[DataRequired(), Length(max=100)])
    address = StringField('Address 2', validators=[Length(max=100)])
    city = StringField(f'City{required}', validators=[DataRequired(), Length(max=100)])
    state = SelectField(f'State{required}', validators=[DataRequired(), Length(max=100)])
    zipcode = StringField(f'Zip Code{required}', validators=[DataRequired(), Length(min=5, max=5)])

    def validate_state(self, state):
        if self.state.data.lower() != 'pennsylvania':
            raise ValidationError('We are currently only delivering locations in Lancaster, Pennsylvania.')

    def validate_zipcode(self, zipcode):
        accepted_zipcodes = [
                '17601', # North Lancaster
                '17602', # East Lancaster
                '17603', # West Lancaster
                '17554', # Mountville
                '17520', # East Petersburg
                '17576', # Smoketown
                #'17584', # Willow Street
                #'17551', # Millersville
            ]
        if self.zipcode.data not in accepted_zipcodes:
            raise ValidationError('We are currently only delivering to the following zipcodes: ' + ', '.join(accepted_zipcodes))

class PickUpForm(FlaskForm):
    sdate = SelectField(f'Pickup Date{required}', validators=[DataRequired()])
    stime = SelectField(f'Pickup Time{required}', validators=[DataRequired()])

class ConfirmForm(FlaskForm):
    status = HiddenField('status')
    payment_id = HiddenField('payment id')
