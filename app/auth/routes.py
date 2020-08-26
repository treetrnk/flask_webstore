import functools
from flask import (
    flash, g, redirect, render_template, request, session, url_for, jsonify,
    current_app
)
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.auth import bp
from datetime import datetime
from app.models import User, Group, Order 
from app.auth.forms import LoginForm, UserEditForm, SignUpForm
from app.auth.authenticators import group_required
from app.functions import log_change, log_new
from app.main.generic_views import SaveObjView, DeleteObjView, ListView

@bp.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            flash(f'User with email <b>{form.email.data}</b> does not exist!', 'danger')
            current_app.logger.warning(f'Permissions Warning: Failed login attempt non-existant user {form.email.data}.\n')
            return redirect(url_for('auth.login'))
        if not user.active:
            flash('Cannot login. Your account has been deactivated. Please speak with your supervisor to gain login privileges.', 'danger')
            current_app.logger.warning(f'Permissions Warning: Failed login for inactive user {form.email.data}.\n')
            return redirect(url_for('auth.login'))
        if not user.check_password(form.password.data):
            flash('Invalid email or password!', 'danger')
            current_app.logger.warning(f'Permissions Warning: Failed login attempt for user {form.email.data}.\n')
            return redirect(url_for('auth.login'))
        current_app.logger.info(f'{user.email} logged in.\n')
        current_app.logger.info(f'Remember {user.email} login? ' + str(form.remember_me.data) + '.\n')
        login_user(user, remember=form.remember_me.data)
        flash('Login successful!', 'success')
        current_app.logger.debug(session)
        order = Order.query.filter_by(id=session.get('order_id'), status='Incomplete').first()
        current_app.logger.debug(order)
        if order:
            order.user_id = current_user.id
            db.session.commit()
        else:
            order = Order.query.filter_by(user_id=user.id, status='Incomplete').order_by(Order.created.desc()).first()
            current_app.logger.debug(order)
        if order:
            session['order_id'] = order.id
            session['cart_item_count'] = order.total_items()
        else:
            session['cart_item_count'] = 0
        if user.in_group('admin'):
            return redirect(url_for('admin.index'))
        else:
            return redirect(url_for('auth.account'))
    #form.remember_me.data = True
    return render_template('auth/login.html', title='Login', form=form, user='')

@bp.route("/logout")
def logout():
    current_app.logger.info(f'{current_user.email} logged out.\n')
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/sign-up', methods=['GET','POST'])
def sign_up():
    form = SignUpForm()
    if form.validate_on_submit():
        user = User()
        form.populate_obj(obj=user)
        user.set_password(form.new_password.data)
        customer = Group.query.filter_by(name='customer').first()
        if customer:
            user.groups = [customer]
        log_new(user, f'User added for email: {form.email.data}')
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=False)
        flash('Thanks for creating an account!', 'success')
        return redirect(url_for('shop.index'))
    form.subscribed.data = True
    return render_template('auth/login.html', title='Sign Up', form=form, user='')

@bp.route('/account')
@login_required
def account():
    user = User.query.filter_by(id=current_user.id).first()
    orders = Order.query.filter_by(user_id=user.id).all()
    current_app.logger.debug(session)
    return render_template('auth/index.html',
            user=user,
            orders=orders,
        )

class EditUser(SaveObjView):
    title = "Edit Account"
    model = User
    form = UserEditForm
    action = 'Edit'
    log_msg = 'updated their account'
    success_msg = 'Account updated.'
    delete_endpoint = 'auth.delete_user'
    template = 'object-edit.html'
    redirect = {'endpoint': 'auth.account'}

    def extra(self):
        self.obj_id = current_user.id
        self.obj = User.query.filter_by(id=self.obj_id).first()
        current_app.logger.debug(self.obj)
        if not self.obj:
            flash('It looks like your account no longer exists. Please create a new one.', 'warning')
            return redirect(url_for('auth.sign_up'))
        self.form = UserEditForm(obj=self.obj)
        self.context.update({'form': self.form})
        self.delete_form.obj_id.data = self.obj.id
        self.context.update({'delete_form': self.delete_form})

    def pre_post(self):
        if self.form.current_password.data and self.form.new_password.data and self.form.current_password.data:
            current_user.set_password(self.form.new_password.data)

bp.add_url_rule("/account/edit", 
        view_func=login_required(EditUser.as_view('edit_user')))

class DeleteUser(DeleteObjView):
    model = User
    log_msg = 'deleted their account'
    success_msg = 'Account deleted.'
    redirect = {'endpoint': 'main.index'}

    def extra(self):
        self.obj_id = current_user.id
        self.obj = User.query.filter_by(id=self.obj_id).first_or_404()

    def post_post(self):
        current_app.logger.info(f'{current_user.email} logged out.\n')
        logout_user()

bp.add_url_rule("/account/delete", 
        view_func = login_required(DeleteUser.as_view('delete_user')))

