import os
import re
from flask import Blueprint, render_template, url_for, redirect, flash, current_app, send_from_directory, request, session, jsonify
from app.shop import bp
from app import db
from flask_login import login_required, current_user
#from app.auth.authenticators import permission_required, user_permission_required
from werkzeug.utils import secure_filename
from datetime import datetime
from app.functions import log_new, log_change
from app.main.generic_views import SaveObjView, DeleteObjView
from app.auth.authenticators import group_required
from app.shop.forms import AddToCartForm
from app.models import (
        Product, Category, Order, Item, Option
    )

@bp.route('/shop')
@bp.route('/shop/<string:category>')
def index(category='all'):
    active = None
    categories = Category.query.order_by('priority','name').all()
    products = Product.query
    if category != 'all':
        active = Category.query.filter(Category.name.ilike(category)).first()
        products = products.filter(Product.category.has(Category.name == category))
    products = products.order_by('name').all()

    return render_template('shop/index.html',
            active=active,
            categories=categories,
            products=products,
            head_data=active.head_data() if active else None,
        )

@bp.route('/shop/<int:obj_id>', methods=['GET','POST'])
@bp.route('/shop/<int:obj_id>/<string:slug>', methods=['GET','POST'])
def product(obj_id, slug=''):
    product = Product.query.filter_by(id=obj_id,active=True).first()
    form = AddToCartForm()
    if form.validate_on_submit():
        order = None
        if session.get('order_id'):
            order = Order.query.filter_by(id=session.get('order_id')).first()
        if not order:
            order = Order()
            db.session.add(order)
            db.session.commit()
            session['order_id'] = order.id

        option = Option.query.filter_by(id=form.option_id.data).first()

        item = Item(
                order_id = order.id,
                product_id = form.product_id.data,
                option_id = form.option_id.data,
                amount = form.amount.data,
            )
        db.session.add(item)
        db.session.commit()
        flash(f'<b>{product.name} - {option.name} (x{form.amount.data})</b> has been added to your cart.', 'success')
        return redirect(url_for('shop.cart'))
    form.product_id.data = product.id
    form.option_id.data = product.options[0].id if product.options else None
    return render_template('shop/product.html',
            product=product,
            form=form,
            head_data=product.head_data(),
        )

@bp.route('/cart', methods=['GET','POST'])
def cart():
    order = Order.query.filter_by(id=session.get('order_id')).first()
    return render_template('shop/cart.html',
            order = order,
        )
