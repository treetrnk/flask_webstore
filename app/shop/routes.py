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
from app.main.forms import DeleteObjForm
from app.auth.authenticators import group_required
from app.shop.forms import AddToCartForm, CartUpdateForm, ShippingForm, ConfirmForm
from app.models import (
        Product, Category, Order, Item, Option, Information
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
        order = Order.query.filter_by(id=session.get('order_id'), status="Incomplete").first()
        if not order and current_user.is_authenticated:
            order = Order.query.filter_by(user_id=current_user.id, status='Incomplete').order_by(Order.created.desc()).first()
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
    current_app.logger.debug(session)
    form = CartUpdateForm()
    delete_form = DeleteObjForm()
    order = Order.query.filter_by(id=session.get('order_id'), status='Incomplete').first()
    if order: 
        session['cart_item_count'] = order.total_items()
    else:
        session['cart_item_count'] = 0
    current_app.logger.debug(order)
    if form.validate_on_submit():
        item = Item.query.filter_by(id=form.item_id.data,order_id=session.get('order_id')).first()
        if item:
            item.amount = form.amount.data
            db.session.commit()
            session['cart_item_count'] = item.order.total_items()
            flash('Your cart has been updated.', 'success')
            return redirect(url_for('shop.cart'))
    return render_template('shop/cart.html',
            order = order,
            form = form,
            delete_form = delete_form,
        )

class DeleteItem(DeleteObjView):
    model = Item
    log_msg = 'deleted a item'
    success_msg = 'Item deleted.'
    redirect = {'endpoint': 'shop.cart'}

    def pre_post(self):
        """ 
        # DELETE CART WHEN DELETING LAST ITEM
        if self.obj.order.total_items(unique=True) < 2:
            log_new(self.obj.order, 'Order deleted')
            db.session.delete(self.obj.order)
        """
        if self.obj.order_id != session.get('order_id'):
            flash('Unable to delete item.', 'warning')
            return redirect(url_for('shop.cart'))

        session['cart_item_count'] = self.obj.order.total_items() - self.obj.amount

bp.add_url_rule("/cart/item/delete", 
        view_func = DeleteItem.as_view('delete_item'))

@bp.route('/cart/shipping', methods=['GET','POST'])
def shipping():
    order = Order.query.filter_by(id=session.get('order_id'), status="Incomplete").first()
    if not order:
        return redirect(url_for('shop.cart'))
    shipping = order.shipping if order.shipping else Information()
    form = ShippingForm(obj=shipping)
    form.state.choices = Information.STATE_CHOICES
    if form.validate_on_submit():
        form.populate_obj(shipping)
        shipping.type = 'shipping'
        if current_user.is_authenticated:
            shipping.user_id = current_user.id
        if not shipping.id:
            db.session.add(shipping)
        db.session.commit()
        order.shipping_id = shipping.id
        db.session.commit()
        return redirect(url_for('shop.confirm'))
    form.state.data='Pennsylvania'
    if current_user.is_authenticated:
        if current_user.first_name and current_user.last_name:
            form.full_name.data = f'{current_user.first_name} {current_user.last_name}'
        if current_user.email:
            form.email.data = current_user.email
        if current_user.phone:
            form.phone.data = current_user.phone
    return render_template('shop/shipping.html',
            form=form,
            order=order,
        )

class EditShipping(SaveObjView):
    title = "Edit Shipping"
    model = Information
    form = ShippingForm
    action = 'Edit'
    log_msg = 'updated shipping information'
    success_msg = 'Shipping information updated.'
    delete_endpoint = 'shop.shipping'
    template = 'shop/shipping.html'
    redirect = {'endpoint': 'shop.confirm'}

    def extra(self):
        order = Order.query.filter_by(id=session.get('order_id'), status="Incomplete").first()
        self.obj_id = order.shipping_id
        self.obj = Information.query.filter_by(id=self.obj_id).first()
        current_app.logger.debug(self.obj)
        if not self.obj:
            flash("It looks like your shipping information doesn't exist. Please try again.", 'warning')
            return redirect(url_for('shop.shipping'))
        self.form = ShippingForm(obj=self.obj)
        self.form.state.choices = Information.STATE_CHOICES
        self.context.update({'form': self.form})

bp.add_url_rule("/cart/shipping/edit", 
        view_func=EditShipping.as_view('edit_shipping'))

@bp.route('/cart/confirm', methods=['GET','POST'])
def confirm():
    order = Order.query.filter_by(id=session.get('order_id')).first()
    if order.status != 'Incomplete':
        return redirect(url_for('shop.index'))
    form = ConfirmForm(obj=order)
    if not order.shipping:
        return redirect(url_for('shop.shipping'))
    if form.validate_on_submit():
        order.status = 'Confirmed'
        for item in order.items:
            item.option.available -= item.amount
        db.session.commit()
        msg = "Thank you for your order! We will begin working on it shortly."
        if current_user.is_authenticated:
            msg += " Go to your <a href='" + url_for('auth.account') + "'>account page</a> to check on its status."
        flash(msg, 'success')
        session['order_id'] = 0
        session['cart_item_count'] = 0
        order.notify_confirmed()
        return redirect(url_for('shop.index'))
    return render_template('shop/confirm.html',
            form=form,
            order=order,
        )
