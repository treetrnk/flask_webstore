import os
import re
from flask import Blueprint, render_template, url_for, redirect, flash, current_app, send_from_directory, request, session, jsonify
from app.profile import bp
from app import db
from flask_login import login_required, current_user
#from app.auth.authenticators import permission_required, user_permission_required
from werkzeug.utils import secure_filename
from datetime import datetime
from app.functions import log_new, log_change
from app.main.generic_views import SaveObjView, DeleteObjView
from app.main.forms import DeleteObjForm
from app.auth.authenticators import group_required
from app.shop.forms import AddToCartForm, CartUpdateForm
from app.models import (
        User, Order,
    )

@bp.route('/profile')
@login_required
def index():
    user = User.query.filter_by(id=current_user.id).first()
    orders = Order.query.filter_by(user_id=user.id).all()
    return render_template('profile/index.html',
            user=user,
            orders=orders,
        )
