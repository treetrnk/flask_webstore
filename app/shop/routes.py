import os
import re
import stripe
import json
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
from app.shop.forms import AddToCartForm, CartUpdateForm, ShippingForm, ConfirmForm, PickUpForm
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

@bp.route('/cart/shipping')
def shipping():
    order = Order.query.filter_by(id=session.get('order_id'), status="Incomplete").first()
    if order and order.shipping_type == 'pickup':
        return redirect(url_for('shop.pickup'))
    if request.args.get('type') and request.args.get('type').lower() == 'pickup':
        return redirect(url_for('shop.pickup'))
    return redirect(url_for('shop.delivery'))

@bp.route('/cart/shipping/delivery', methods=['GET','POST'])
def delivery():
    order = Order.query.filter_by(id=session.get('order_id'), status="Incomplete").first()
    if not order:
        return redirect(url_for('shop.cart'))
    shipping = order.shipping if order.shipping else Information()
    form = ShippingForm(obj=shipping)
    form.state.choices = Information.STATE_CHOICES
    if form.validate_on_submit():
        form.populate_obj(shipping)
        order.email = form.email.data
        order.phone = form.phone.data
        order.shipping_type = 'delivery'
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
    form.email.data=order.email
    form.phone.data=order.phone
    return render_template('shop/shipping.html',
            form=form,
            order=order,
            shipping_type='delivery',
        )

@bp.route('/cart/shipping/pickup', methods=['GET','POST'])
def pickup():
    order = Order.query.filter_by(id=session.get('order_id'), status="Incomplete").first()
    current_app.logger.debug(order.shipping_type)
    current_app.logger.debug(order.shipping_time)
    current_app.logger.debug(order.shipping)
    if not order:
        return redirect(url_for('shop.cart'))
    shipping = order.shipping if order.shipping else Information()
    form = PickUpForm(obj=order)
    form.sdate.choices = order.pickup_dates()
    current_app.logger.debug(form.sdate.choices)
    current_app.logger.debug(form.sdate.data)
    form.stime.choices = order.pickup_times()
    if form.validate_on_submit():
        form.populate_obj(order)
        order.shipping_type = 'pickup'
        order.set_shipping_time(form.sdate.data, form.stime.data)
        db.session.commit()
        return redirect(url_for('shop.confirm'))
    return render_template('shop/shipping.html',
            form=form,
            order=order,
            shipping_type='pickup',
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

@bp.route('/cart/create-payment', methods=['POST'])
# @group_required('admin') # DISABLE UNTIL NEEDED
def create_payment():
    order = Order.query.filter_by(id=session.get('order_id'), status="Incomplete").first()
    stripe.api_key = current_app.config.get('STRIPE_SECRET')
    if order and order.total_cost() > 0:
        try:
            current_app.logger.debug(request.data)
            data = json.loads(request.data)
            intent = stripe.PaymentIntent.create(
                    amount=int(order.total_cost() * 100),
                    currency='usd'
                )
            return jsonify({
                'clientSecret': intent['client_secret']
            })
        except Exception as e:
            return jsonify(error=str(e)), 403
    flash('Unable to create payment. There are no items in your cart.')
    return redirect(url_for('shop.cart'))

@bp.route('/cart/confirm', methods=['GET','POST'])
def confirm():
    order = Order.query.filter_by(id=session.get('order_id'), status="Incomplete").first()
    if not order and current_user.is_authenticated:
        order = Order.query.filter_by(user_id=current_user.id, status="Incomplete").first()
    if not order or order.status != 'Incomplete':
        return redirect(url_for('shop.index'))
    form = ConfirmForm(obj=order)
    if not order.has_shipping():
        return redirect(url_for('shop.shipping'))
    if form.validate_on_submit():
        order.status = 'Confirmed'
        if form.payment_id.data:
            order.payment_id = form.payment_id.data
            order.payment_type = 'Credit Card'
            order.paid = True
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
            js='stripe-client.js'
        )

@bp.route('/cart/select-order/<int:obj_id>')
@login_required
def select_order(obj_id):
    order = Order.query.filter_by(id=obj_id, status='Incomplete')
    if not current_user.in_group('admin'):
        order = order.filter_by(user_id=current_user.id)
    order = order.first()
    if not order:
        flash('Failed to select the requested cart.', 'warning')
        return redirect('auth.account')
    session['order_id'] = obj_id
    session['cart_item_count'] = order.total_items()
    return redirect(url_for('auth.account'))

class DeleteOrder(DeleteObjView):
    model = Order
    log_msg = 'deleted an order'
    success_msg = 'Order deleted.'
    redirect = {'endpoint': 'auth.account'}

    def pre_post(self):
        """ 
        # DELETE CART WHEN DELETING LAST ITEM
        if self.obj.order.total_items(unique=True) < 2:
            log_new(self.obj.order, 'Order deleted')
            db.session.delete(self.obj.order)
        """
        if self.obj.user_id != current_user.id or self.obj.status != 'Incomplete':
            flash('Unable to delete order.', 'warning')
            return redirect(url_for('auth.account'))
        if session.get('order_id') == self.obj.id:
            session['order_id'] = 0
            session['cart_item_count'] = 0

bp.add_url_rule("/cart/order/delete", 
        view_func = login_required(DeleteOrder.as_view('delete_order')))

