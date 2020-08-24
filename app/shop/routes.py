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
    products = Product.query.filter_by(active=True)
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
    product = Product.query.filter_by(id=obj_id).first()
    if not product.active:
        if not current_user.is_authenticated or not current_user.in_group('admin'):
            flash('The product you are looking for is either inactive or no longer available.', 'warning')
            return redirect(url_for('shop.index'))
        else:
            flash('This listing is inactive. You can only see this because you are an administrator.', 'info')
    current_app.logger.debug(session)
    form = AddToCartForm()
    if form.validate_on_submit():
        # Validate Option/Product pairing
        option = Option.query.filter_by(id=form.option_id.data).first()
        if option.product_id != product.id:
            flash('Unable to add item to cart. Please try again. If the problem persists, please contact us at <a href=""></a>.', 'danger')
            return redirect(url_for('shop.product', obj_id=form.product_id.data))
        order = Order.query.filter_by(id=session.get('order_id')).first()
        if not order and current_user.is_authenticated:
            order = Order.query.filter_by(user_id=current_user.id, status='incomplete').order_by(Order.created.desc()).first()
        if not order:
            order = Order()
            if current_user.is_authenticated:
                order.user_id = current_user.id
            db.session.add(order)
            db.session.commit()
            session['order_id'] = order.id

        option = Option.query.filter_by(id=form.option_id.data).first()

        # Validate option availability
        if order.in_cart(option.id):
            item = order.get_item(option.id)
            if item.amount == option.available:
                flash(f'Unable to add more of the <b>{product.name} - {option.name}</b> to your cart. Your cart already has all availble stock for the selected option.', 'info')
                return redirect(url_for('shop.product', obj_id=form.product_id.data))
            if item.amount + form.amount.data > option.available:
                added_amount = option.available - item.amount
                item.amount = option.available

                flash(f'We only added {added_amount} of the <b>{product.name} - {option.name}</b> to your cart, since it is all we have available at the moment.', 'info')
            else:
                item.amount += form.amount.data
        else:
            item = Item(
                    order_id = order.id,
                    product_id = form.product_id.data,
                    option_id = form.option_id.data,
                    amount = form.amount.data,
                )
            db.session.add(item)
        db.session.commit()
        flash(f'<b>{product.name} - {option.name} (x{form.amount.data})</b> has been added to your cart.', 'success')
        session['cart_item_count'] = order.total_items()
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
