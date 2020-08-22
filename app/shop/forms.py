from flask_wtf import FlaskForm
from wtforms import (
        HiddenField, IntegerField, 
    )
from wtforms.validators import DataRequired, NumberRange

required = " <span class='text-danger'>*</span>"

class AddToCartForm(FlaskForm):
    product_id = HiddenField('product id', validators=[DataRequired()])
    amount = IntegerField('Amount', validators=[DataRequired(), NumberRange(min=1)])
