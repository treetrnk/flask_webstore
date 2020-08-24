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
from app.auth.forms import LoginForm, EditUserForm, EditGroupForm, DeleteUserForm, DeleteGroupForm
from app.auth.authenticators import group_required
"""
from app.auth.forms import (
        LoginForm, AddUserForm, EditUserForm, AddGroupForm, EditPermissionForm,
        DeleteGroupForm, DeletePermissionForm, EditContactForm, 
        DeleteContactForm, DeleteUserForm
    )
"""
from app.auth.emojis import emojis
from app.functions import log_change, log_new
from app.main.generic_views import ListView

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
        if session.get('order_id'):
            order = Order.query.filter_by(id=session.get('order_id')).first()
            if order:
                order.user_id = current_user.id
            else:
                order = Order.query.filter_by(user_id=user.id).order_by(Order.created.desc()).first()
                session['order_id'] = order.id
                session['cart_item_count'] = order.total_items()
            db.session.commit()
        return redirect(url_for('admin.index'))
    form.remember_me.data = True
    return render_template('auth/login.html', title='Login', form=form, user='')

@bp.route("/logout")
def logout():
    current_app.logger.info(f'{current_user.email} logged out.\n')
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route("/users")
@bp.route("/users/inactive", defaults={'inactive': True}, endpoint="inactive_users")
@login_required
def users(inactive=False):
    current_app.logger.info(f'inactive: {inactive}')
    users = User.query.filter_by(active=not inactive).order_by('last_name','first_name','username').all()
    return render_template('auth/users.html', users=users, title='Users', inactive=inactive)

#class UserView(ListView):
#    def __init__(self, inactive=None):
#        self.inactive = True if inactive == 'inactive' else False
#        self.template_name = 'auth/users.html'
#        if self.inactive:
#            query_set = User.query.filter_by(active=False).order_by('last_name','first_name','username').all()
#        else:
#            query_set = User.query.filter_by(active=True).order_by('last_name','first_name','username').all()
#        self.context = {'inactive': self.inactive, 'title': 'Users'}
#
#users_view = group_required('admin')(UserView.as_view('users'))
#bp.add_url_rule("/users", view_func=users_view)
#bp.add_url_rule("/users/<string:inactive>", view_func=users_view)
#
#@bp.route("/user/add", methods=['GET','POST'])
#@group_required('admin')
#def add_user():
#    user = User()
#    form = EditUserForm(obj=user())
#    form.avatar.choices = emojis()
#    if form.validate_on_submit():
#        form.populate_obj(user)
#        db.session.add(user)
#        db.session.commit()
#        log_new(user, 'added a user')
#        flash('User added.', 'success')
#        return redirect(url_for('auth.users'))
#    form.active.data = True
#    return render_template('auth/user-edit.html', 
#            form=form,
#            title='Users',
#            action="Add",
#        )

@bp.route("/user/edit/<string:username>", methods=['GET','POST'])
@group_required('admin')
def edit_user(username):
    user = User.query.filter_by(username=username).first()
    form = EditUserForm(obj=user)
    delete_form = DeleteUserForm()
    form.avatar.choices = emojis()
    if form.validate_on_submit():
        log_orig = log_change(user)
        user.groups = form.groups.data
        log_change(log_orig, user, 'edited a user')
        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('auth.users'))
    delete_form.user_id.data = user.id
    return render_template('auth/user-edit.html', 
            user=user, 
            form=form, 
            title='Users',
            action="Edit",
            delete_form=delete_form,
        )

@bp.route("/user/delete", methods=['POST'])
@group_required('admin')
def delete_user():
    form = DeleteUserForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=form.user_id.data).first()
        log_new(user, f"deleted a user")
        db.session.delete(user)
        db.session.commit()
        flash(f'The user has been deleted.', 'success') 
    else:
        log_new(user, f"FAILED to delete user")
        flash('Failed to delete user!', 'danger') 
        return redirect(url_for('auth.edit_user', username=username))
    return redirect(url_for('auth.users'))

@bp.route("/groups")
@group_required('admin')
def groups():
    groups = Group.query.all()
    return render_template('auth/groups.html', groups=groups, title='Groups')

#class GroupView(ListView):
#    def __init__(self, inactive=None):
#        self.template_name = 'auth/groups.html'
#        self.context = {'title': 'Groups'}
#
#    def get_objects(self):
#        return Group.query.order_by('name').all()
#
#groups_view = group_required('admin')(GroupView.as_view('groups'))
#bp.add_url_rule("/groups", view_func=groups_view)

@bp.route("/group/add", methods=['GET','POST'])
@group_required('webdev')
def add_group():
    form = EditGroupForm()
    form.style.choices = Group.STYLE_CHOICES
    if form.validate_on_submit():
        group = Group(
                name = form.name.data,
                description = form.description.data,
                style = form.style.data,
            )
        db.session.add(group)
        db.session.commit()
        log_new(group, 'added a group')
        flash('Group added.', 'success')
        return redirect(url_for('auth.groups'))
    return render_template('auth/group-edit.html',
            title='Add Group',
            form=form,
            action='Add',
        )

@bp.route("/group/edit/<int:group_id>", methods=['GET','POST'])
@group_required('webdev')
def edit_group(group_id):
    form = EditGroupForm()
    delete_form = DeleteGroupForm()
    form.style.choices = Group.STYLE_CHOICES
    group = Group.query.filter_by(id=group_id).first()
    if form.validate_on_submit():
        log_orig = log_change(group)
        group.name = form.name.data
        group.description = form.description.data
        group.style = form.style.data
        log_change(log_orig, group, 'updated a group')
        db.session.commit()
        flash('Group updated.', 'success')
        return redirect(url_for('auth.groups'))
    form.name.data = group.name
    form.description.data = group.description
    form.style.data = group.style
    delete_form.group_id.data = group.id
    return render_template('auth/group-edit.html',
            title='Edit Group',
            form=form,
            action='Edit',
            group=group,
            delete_form=delete_form,
        )

@bp.route("/group/delete", methods=['POST'])
@group_required('webdev')
def delete_group():
    form = DeleteGroupForm()
    if form.validate_on_submit():
        group = Group.query.filter_by(id=form.group_id.data).first()
        log_new(group, f"deleted a group")
        db.session.delete(group)
        db.session.commit()
        flash(f'The group has been deleted.', 'success') 
    else:
        flash('Failed to delete group!', 'danger') 
        return redirect(url_for('auth.edit_group', group_id=form.group_id.data))
    return redirect(url_for('auth.groups'))
