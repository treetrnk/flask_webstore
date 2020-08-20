import os
import re
from flask import Blueprint, render_template, url_for, redirect, flash, current_app, send_from_directory, request, session, jsonify
from app.admin import bp
from app import db
from flask_login import login_required, current_user
#from app.auth.authenticators import permission_required, user_permission_required
from werkzeug.utils import secure_filename
from datetime import datetime
from app.functions import log_new, log_change
from app.main.generic_views import SaveObjView, DeleteObjView
from app.auth.authenticators import group_required
from app.admin.forms import (
        UserEditForm, SettingEditForm, GroupEditForm, ProductEditForm, CategoryEditForm,
        PageEditForm,
    )
from app.admin.functions import save_file, delete_file
from app.models import (
        User, Group, Category, Product, Setting, Page,
    )

@bp.route('/admin')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('admin.products'))
    return redirect(url_for('auth.login'))

##########
## USER ################################################################
##########

@bp.route('/admin/users')
@login_required
def users():
    users = User.query.order_by('email')
    return render_template('admin/users.html', 
            tab='users', 
            users=users, 
        )

class AddUser(SaveObjView):
    title = "Add User"
    model = User
    form = UserEditForm
    action = 'Add'
    log_msg = 'added a user'
    success_msg = 'User added.'
    delete_endpoint = 'admin.delete_user'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.users'}
    context = {'tab': 'users'}

bp.add_url_rule("/admin/user/add", 
        view_func=login_required(AddUser.as_view('add_user')))

class EditUser(SaveObjView):
    title = "Edit User"
    model = User
    form = SettingEditForm
    action = 'Edit'
    log_msg = 'updated a user'
    success_msg = 'User updated.'
    delete_endpoint = 'admin.delete_user'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.users'}
    context = {'tab': 'users'}

bp.add_url_rule("/admin/user/edit/<int:obj_id>", 
        view_func=login_required(EditUser.as_view('edit_user')))

class DeleteUser(DeleteObjView):
    model = User
    log_msg = 'deleted a user'
    success_msg = 'User deleted.'
    redirect = {'endpoint': 'admin.users'}

bp.add_url_rule("/admin/user/delete", 
        view_func = login_required(DeleteUser.as_view('delete_user')))

###########
## GROUP ################################################################
###########

@bp.route('/admin/groups')
@login_required
def groups():
    groups = Group.query.order_by('name')
    return render_template('admin/groups.html', 
            tab='groups', 
            groups=groups, 
        )

class AddGroup(SaveObjView):
    title = "Add Group"
    model = Group
    form = GroupEditForm
    action = 'Add'
    log_msg = 'added a group'
    success_msg = 'Group added.'
    delete_endpoint = 'admin.delete_group'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.groups'}
    context = {'tab': 'groups'}

    def extra(self):
        self.form.style.choices = Group.STYLE_CHOICES

bp.add_url_rule("/admin/group/add", 
        view_func=login_required(AddGroup.as_view('add_group')))

class EditGroup(SaveObjView):
    title = "Edit Group"
    model = Group
    form = GroupEditForm
    action = 'Edit'
    log_msg = 'updated a group'
    success_msg = 'Group updated.'
    delete_endpoint = 'admin.delete_group'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.groups'}
    context = {'tab': 'groups'}

    def extra(self):
        self.form.style.choices = Group.STYLE_CHOICES

bp.add_url_rule("/admin/group/edit/<int:obj_id>", 
        view_func=login_required(EditGroup.as_view('edit_group')))

class DeleteGroup(DeleteObjView):
    model = Group
    log_msg = 'deleted a group'
    success_msg = 'Group deleted.'
    redirect = {'endpoint': 'admin.groups'}

bp.add_url_rule("/admin/group/delete", 
        view_func = login_required(DeleteGroup.as_view('delete_group')))

##############
## PRODUCT ################################################################
##############

@bp.route('/admin/products')
@login_required
def products():
    products = Product.query.order_by('name')
    return render_template('admin/products.html', 
            tab='products', 
            products=products, 
        )

class AddProduct(SaveObjView):
    title = "Add Product"
    model = Product
    form = ProductEditForm
    action = 'Add'
    log_msg = 'added a product'
    success_msg = 'Product added.'
    delete_endpoint = 'admin.delete_product'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.products'}
    context = {'tab': 'products'}

    def extra(self):
        self.form.category_id.choices = [[0,'']] + [(c.id, c.name) for c in Category.query.order_by('priority','name').all()]
        self.form.active.data = True 

    def post_post(self):
        if self.form.image.data:
            path = save_file(self.form.image.data, self.obj.id, self.obj.name)
            self.obj.image_path = path

bp.add_url_rule("/admin/product/add", 
        view_func=login_required(AddProduct.as_view('add_product')))

class EditProduct(SaveObjView):
    title = "Edit Product"
    model = Product
    form = ProductEditForm
    action = 'Edit'
    log_msg = 'updated a product'
    success_msg = 'Product updated.'
    delete_endpoint = 'admin.delete_product'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.products'}
    context = {'tab': 'products'}

    def extra(self):
        self.form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('priority','name').all()]

    def pre_post(self):
        if self.form.image.data:
            delete_file(self.obj.image_path)
            path = save_file(self.form.image.data, self.obj.id, self.obj.name)
            self.obj.image_path = path


bp.add_url_rule("/admin/product/edit/<int:obj_id>", 
        view_func=login_required(EditProduct.as_view('edit_product')))

class DeleteProduct(DeleteObjView):
    model = Product
    log_msg = 'deleted a product'
    success_msg = 'Product deleted.'
    redirect = {'endpoint': 'admin.products'}

bp.add_url_rule("/admin/product/delete", 
        view_func = login_required(DeleteProduct.as_view('delete_product')))

##############
## CATEGORY ################################################################
##############

@bp.route('/admin/categories')
@login_required
def categories():
    categories = Category.query.order_by('name')
    return render_template('admin/categories.html', 
            tab='categories', 
            categories=categories, 
        )

class AddCategory(SaveObjView):
    title = "Add Category"
    model = Category
    form = CategoryEditForm
    action = 'Add'
    log_msg = 'added a category'
    success_msg = 'Category added.'
    delete_endpoint = 'admin.delete_category'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.categories'}
    context = {'tab': 'categories'}

    def pre_post(self):
        if self.form.image.data:
            path = save_file(self.form.image.data, self.obj.id, self.obj.name)
            self.obj.image_path = path

bp.add_url_rule("/admin/category/add", 
        view_func=login_required(AddCategory.as_view('add_category')))

class EditCategory(SaveObjView):
    title = "Edit Category"
    model = Category
    form = CategoryEditForm
    action = 'Edit'
    log_msg = 'updated a category'
    success_msg = 'Category updated.'
    delete_endpoint = 'admin.delete_category'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.categories'}
    context = {'tab': 'categories'}

    def pre_post(self):
        if self.form.image.data:
            delete_file(self.obj.image_path)
            path = save_file(self.form.image.data, self.obj.id, self.obj.name)
            self.obj.image_path = path

bp.add_url_rule("/admin/category/edit/<int:obj_id>", 
        view_func=login_required(EditCategory.as_view('edit_category')))

class DeleteCategory(DeleteObjView):
    model = Category
    log_msg = 'deleted a category'
    success_msg = 'Category deleted.'
    redirect = {'endpoint': 'admin.categories'}

bp.add_url_rule("/admin/category/delete", 
        view_func = login_required(DeleteCategory.as_view('delete_category')))

##########
## PAGE ################################################################
##########

@bp.route('/admin/pages')
@login_required
def pages():
    pages = Page.query.order_by('title')
    return render_template('admin/pages.html', 
            tab='pages', 
            pages=pages, 
        )

class AddPage(SaveObjView):
    title = "Add Page"
    model = Page
    form = PageEditForm
    action = 'Add'
    log_msg = 'added a page'
    success_msg = 'Page added.'
    delete_endpoint = 'admin.delete_page'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.pages'}
    context = {'tab': 'pages'}

bp.add_url_rule("/admin/page/add", 
        view_func=login_required(AddPage.as_view('add_page')))

class EditPage(SaveObjView):
    title = "Edit Page"
    model = Page
    form = PageEditForm
    action = 'Edit'
    log_msg = 'updated a page'
    success_msg = 'Page updated.'
    delete_endpoint = 'admin.delete_page'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.pages'}
    context = {'tab': 'pages'}

bp.add_url_rule("/admin/page/edit/<int:obj_id>", 
        view_func=login_required(EditPage.as_view('edit_page')))

class DeletePage(DeleteObjView):
    model = Page
    log_msg = 'deleted a page'
    success_msg = 'Page deleted.'
    redirect = {'endpoint': 'admin.pages'}

bp.add_url_rule("/admin/page/delete", 
        view_func = login_required(DeletePage.as_view('delete_page')))

##############
## SETTING ################################################################
##############

@bp.route('/admin/settings')
@login_required
def settings():
    settings = Setting.query.order_by('name')
    return render_template('admin/settings.html', 
            tab='settings', 
            settings=settings, 
        )

class AddSetting(SaveObjView):
    title = "Add Setting"
    model = Setting
    form = SettingEditForm
    action = 'Add'
    log_msg = 'added a setting'
    success_msg = 'Setting added.'
    delete_endpoint = 'admin.delete_setting'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.settings'}
    context = {'tab': 'settings'}

bp.add_url_rule("/admin/setting/add", 
        view_func=login_required(AddSetting.as_view('add_setting')))

class EditSetting(SaveObjView):
    title = "Edit Setting"
    model = Setting
    form = SettingEditForm
    action = 'Edit'
    log_msg = 'updated a setting'
    success_msg = 'Setting updated.'
    delete_endpoint = 'admin.delete_setting'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.setting'}
    context = {'tab': 'settings'}

bp.add_url_rule("/admin/setting/edit/<int:obj_id>", 
        view_func=login_required(EditSetting.as_view('edit_setting')))

class DeleteSetting(DeleteObjView):
    model = Setting
    log_msg = 'deleted a setting'
    success_msg = 'Setting deleted.'
    redirect = {'endpoint': 'admin.settings'}

bp.add_url_rule("/admin/setting/delete", 
        view_func = login_required(DeleteSetting.as_view('delete_setting')))

