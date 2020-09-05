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
        PageEditForm, OptionEditForm, OrderEditForm, PaymentEditForm,
    )
from app.shop.forms import ShippingForm
from app.admin.functions import save_file, delete_file
from app.models import (
        User, Group, Category, Product, Setting, Page, Option, Order, Information
    )
from sqlalchemy import or_

@bp.route('/admin')
def index():
    if current_user.is_authenticated:
        if current_user.in_group('admin'):
            return redirect(url_for('admin.orders'))
        return redirect(url_for('main.index'))
    return redirect(url_for('auth.login'))

##########
## USER ################################################################
##########

@bp.route('/admin/users')
@group_required('admin')
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
        view_func=group_required('admin')(AddUser.as_view('add_user')))

class EditUser(SaveObjView):
    title = "Edit User"
    model = User
    form = UserEditForm
    action = 'Edit'
    log_msg = 'updated a user'
    success_msg = 'User updated.'
    delete_endpoint = 'admin.delete_user'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.users'}
    context = {'tab': 'users'}

bp.add_url_rule("/admin/user/edit/<int:obj_id>", 
        view_func=group_required('admin')(EditUser.as_view('edit_user')))

class DeleteUser(DeleteObjView):
    model = User
    log_msg = 'deleted a user'
    success_msg = 'User deleted.'
    redirect = {'endpoint': 'admin.users'}

bp.add_url_rule("/admin/user/delete", 
        view_func = group_required('admin')(DeleteUser.as_view('delete_user')))

###########
## GROUP ################################################################
###########

@bp.route('/admin/groups')
@group_required('admin')
def groups():
    groups = Group.query.order_by('name')
    return render_template('admin/groups.html', 
            tab='users', 
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
    context = {'tab': 'users'}

    def extra(self):
        self.form.style.choices = Group.STYLE_CHOICES

bp.add_url_rule("/admin/group/add", 
        view_func=group_required('admin')(AddGroup.as_view('add_group')))

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
    context = {'tab': 'users'}

    def extra(self):
        self.form.style.choices = Group.STYLE_CHOICES

bp.add_url_rule("/admin/group/edit/<int:obj_id>", 
        view_func=group_required('admin')(EditGroup.as_view('edit_group')))

class DeleteGroup(DeleteObjView):
    model = Group
    log_msg = 'deleted a group'
    success_msg = 'Group deleted.'
    redirect = {'endpoint': 'admin.groups'}

bp.add_url_rule("/admin/group/delete", 
        view_func = group_required('admin')(DeleteGroup.as_view('delete_group')))

##############
## PRODUCT ################################################################
##############

@bp.route('/admin/products')
@group_required('admin')
def products():
    products = Product.query.order_by('name')
    return render_template('admin/products.html', 
            tab='shop', 
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
    context = {'tab': 'shop'}

    def extra(self):
        self.form.category_id.choices = [[0,'']] + [(c.id, c.name) for c in Category.query.order_by('priority','name').all()]
        self.form.active.data = True 

    def post_post(self):
        if self.form.image.data:
            path = save_file(self.form.image.data, self.obj.id, self.obj.name)
            self.obj.image_path = path

bp.add_url_rule("/admin/product/add", 
        view_func=group_required('admin')(AddProduct.as_view('add_product')))

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
    context = {'tab': 'shop'}

    def extra(self):
        self.form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('priority','name').all()]

    def pre_post(self):
        if self.form.image.data:
            delete_file(self.obj.image_path)
            path = save_file(self.form.image.data, self.obj.id, self.obj.name)
            self.obj.image_path = path


bp.add_url_rule("/admin/product/edit/<int:obj_id>", 
        view_func=group_required('admin')(EditProduct.as_view('edit_product')))

class DeleteProduct(DeleteObjView):
    model = Product
    log_msg = 'deleted a product'
    success_msg = 'Product deleted.'
    redirect = {'endpoint': 'admin.products'}

bp.add_url_rule("/admin/product/delete", 
        view_func = group_required('admin')(DeleteProduct.as_view('delete_product')))

##############
## OPTIONS ################################################################
##############

class AddOption(SaveObjView):
    title = "Add Option"
    model = Option
    form = OptionEditForm
    action = 'Add'
    log_msg = 'added a option'
    success_msg = 'Option added.'
    delete_endpoint = 'admin.delete_option'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.products'}
    context = {'tab': 'shop'}

    def extra(self):
        if self.parent_id:
            self.form.product_id.data = self.parent_id

    def post_post(self):
        if self.form.image.data:
            path = save_file(self.form.image.data, self.obj.id, self.obj.name)
            self.obj.image_path = path

bp.add_url_rule("/admin/option/add/<int:parent_id>", 
        view_func=group_required('admin')(AddOption.as_view('add_option')))

class EditOption(SaveObjView):
    title = "Edit Option"
    model = Option
    form = OptionEditForm
    action = 'Edit'
    log_msg = 'updated a option'
    success_msg = 'Option updated.'
    delete_endpoint = 'admin.delete_option'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.products'}
    context = {'tab': 'shop'}

    def pre_post(self):
        if self.form.image.data:
            delete_file(self.obj.image_path)
            path = save_file(self.form.image.data, self.obj.id, self.obj.name)
            self.obj.image_path = path


bp.add_url_rule("/admin/option/edit/<int:obj_id>", 
        view_func=group_required('admin')(EditOption.as_view('edit_option')))

class DeleteOption(DeleteObjView):
    model = Option
    log_msg = 'deleted a option'
    success_msg = 'Option deleted.'
    redirect = {'endpoint': 'admin.products'}

bp.add_url_rule("/admin/option/delete", 
        view_func = group_required('admin')(DeleteOption.as_view('delete_option')))

##############
## CATEGORY ################################################################
##############

@bp.route('/admin/categories')
@group_required('admin')
def categories():
    categories = Category.query.order_by('name')
    return render_template('admin/categories.html', 
            tab='shop', 
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
    context = {'tab': 'shop'}

    def pre_post(self):
        if self.form.image.data:
            path = save_file(self.form.image.data, self.obj.id, self.obj.name)
            self.obj.image_path = path

bp.add_url_rule("/admin/category/add", 
        view_func=group_required('admin')(AddCategory.as_view('add_category')))

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
    context = {'tab': 'shop'}

    def pre_post(self):
        if self.form.image.data:
            delete_file(self.obj.image_path)
            path = save_file(self.form.image.data, self.obj.id, self.obj.name)
            self.obj.image_path = path

bp.add_url_rule("/admin/category/edit/<int:obj_id>", 
        view_func=group_required('admin')(EditCategory.as_view('edit_category')))

class DeleteCategory(DeleteObjView):
    model = Category
    log_msg = 'deleted a category'
    success_msg = 'Category deleted.'
    redirect = {'endpoint': 'admin.categories'}

bp.add_url_rule("/admin/category/delete", 
        view_func = group_required('admin')(DeleteCategory.as_view('delete_category')))

##########
## ORDER ################################################################
##########

@bp.route('/admin/orders')
@bp.route('/admin/orders/<string:status>')
@group_required('admin')
def orders(status='confirmed'):
    if status.lower() == 'all':
        orders = Order.query.all()
    elif status.lower() == 'confirmed':
        orders = Order.query.filter(or_(Order.status.ilike(status),Order.status.ilike('packaged'))).all()
    else:
        orders = Order.query.filter(Order.status.ilike(status)).all()
    return render_template('admin/orders.html', 
            tab='shop', 
            orders=orders, 
            status=status,
        )

@bp.route('/admin/order/<int:obj_id>')
@group_required('admin')
def view_order(obj_id):
    order = Order.query.filter_by(id=obj_id).first()
    form = PaymentEditForm()
    return render_template('admin/view-order.html',
            tab='shop',
            order=order,
            form=form,
        )

class AddOrder(SaveObjView):
    title = "Add Order"
    model = Order
    form = OrderEditForm
    action = 'Add'
    log_msg = 'added a order'
    success_msg = 'Order added.'
    delete_endpoint = 'admin.delete_order'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.orders'}
    context = {'tab': 'shop'}

bp.add_url_rule("/admin/order/add", 
        view_func=group_required('admin')(AddOrder.as_view('add_order')))

class EditOrder(SaveObjView):
    title = "Edit Order"
    model = Order
    form = OrderEditForm
    action = 'Edit'
    log_msg = 'updated a order'
    success_msg = 'Order updated.'
    delete_endpoint = 'admin.delete_order'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.orders'}
    context = {'tab': 'shop'}

    def extra(self):
        self.form.status.choices = Order.STATUS_CHOICES
        self.form.payment_type.choices = [['','']] + Order.PAYMENT_TYPE_CHOICES

bp.add_url_rule("/admin/order/edit/<int:obj_id>", 
        view_func=group_required('admin')(EditOrder.as_view('edit_order')))

class DeleteOrder(DeleteObjView):
    model = Order
    log_msg = 'deleted a order'
    success_msg = 'Order deleted.'
    redirect = {'endpoint': 'admin.orders'}

bp.add_url_rule("/admin/order/delete", 
        view_func = group_required('admin')(DeleteOrder.as_view('delete_order')))

@bp.route('/admin/order/<int:obj_id>/paid', methods=['POST'])
@group_required('admin')
def set_payment(obj_id):
    order = Order.query.filter_by(id=obj_id).first()
    form = PaymentEditForm()
    if not order:
        flash('Failed to find order.', 'warning')
        return redirect(url_for('admin.orders'))
    if form.validate_on_submit():
        for field in form:
            current_app.logger.debug(f'{field.name}: {field.data}')
        form.paid.data = True if form.paid.data == 'y' else False
        form.populate_obj(obj=order)
        db.session.commit()
        flash('Payment updated.','success')
        return redirect(url_for('admin.view_order', obj_id=order.id))
    flash('Failed to update payment.','danger')
    return redirect(url_for('admin.view_order', obj_id=order.id))


#################
## INFORMATION ################################################################
#################

class AddInformation(SaveObjView):
    title = "Add Information"
    model = Information
    form = ShippingForm
    action = 'Add'
    log_msg = 'added information'
    success_msg = 'Information added.'
    delete_endpoint = 'admin.delete_information'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.orders'}
    context = {'tab': 'shop'}

bp.add_url_rule("/admin/information/add", 
        view_func=group_required('admin')(AddInformation.as_view('add_information')))

class EditInformation(SaveObjView):
    title = "Edit Information"
    model = Information
    form = ShippingForm
    action = 'Edit'
    log_msg = 'updated information'
    success_msg = 'Information updated.'
    delete_endpoint = 'admin.delete_information'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.orders'}
    context = {'tab': 'shop'}

    def extra(self):
        self.form.state.choices = Information.STATE_CHOICES
        if self.parent_id:
            self.form.parent_id.data = self.parent_id
        if self.form.parent_id.data:
            self.redirect = {'endpoint': 'admin.view_order', 'obj_id': self.form.parent_id.data}
        self.context.update({'form': self.form, 'redirect': self.redirect})

bp.add_url_rule("/admin/order/<int:parent_id>/information/edit/<int:obj_id>", 
        view_func=group_required('admin')(EditInformation.as_view('edit_order_information')))
bp.add_url_rule("/admin/order/information/edit/<int:obj_id>", 
        view_func=group_required('admin')(EditInformation.as_view('edit_information')))

class DeleteInformation(DeleteObjView):
    model = Information
    log_msg = 'deleted information'
    success_msg = 'Information deleted.'
    redirect = {'endpoint': 'admin.orders'}

bp.add_url_rule("/admin/information/delete", 
        view_func = group_required('admin')(DeleteInformation.as_view('delete_information')))

##########
## PAGE ################################################################
##########

@bp.route('/admin/pages')
@group_required('admin')
def pages():
    pages = Page.query.order_by('title')
    return render_template('admin/pages.html', 
            tab='settings', 
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
    context = {'tab': 'settings'}

bp.add_url_rule("/admin/page/add", 
        view_func=group_required('admin')(AddPage.as_view('add_page')))

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
    context = {'tab': 'settings'}

bp.add_url_rule("/admin/page/edit/<int:obj_id>", 
        view_func=group_required('admin')(EditPage.as_view('edit_page')))

class DeletePage(DeleteObjView):
    model = Page
    log_msg = 'deleted a page'
    success_msg = 'Page deleted.'
    redirect = {'endpoint': 'admin.pages'}

bp.add_url_rule("/admin/page/delete", 
        view_func = group_required('admin')(DeletePage.as_view('delete_page')))

##############
## SETTING ################################################################
##############

@bp.route('/admin/settings')
@group_required('admin')
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
        view_func=group_required('admin')(AddSetting.as_view('add_setting')))

class EditSetting(SaveObjView):
    title = "Edit Setting"
    model = Setting
    form = SettingEditForm
    action = 'Edit'
    log_msg = 'updated a setting'
    success_msg = 'Setting updated.'
    delete_endpoint = 'admin.delete_setting'
    template = 'admin/object-edit.html'
    redirect = {'endpoint': 'admin.settings'}
    context = {'tab': 'settings'}

bp.add_url_rule("/admin/setting/edit/<int:obj_id>", 
        view_func=group_required('admin')(EditSetting.as_view('edit_setting')))

class DeleteSetting(DeleteObjView):
    model = Setting
    log_msg = 'deleted a setting'
    success_msg = 'Setting deleted.'
    redirect = {'endpoint': 'admin.settings'}

bp.add_url_rule("/admin/setting/delete", 
        view_func = group_required('admin')(DeleteSetting.as_view('delete_setting')))

##########
## LOGS ########################################################################
##########
@bp.route("/logs")
@group_required('admin')
def logs():
    main_logs = os.listdir(current_app.config['MAIN_LOG_DIR'])
    product_logs = os.listdir(current_app.config['PRODUCT_LOG_DIR'])
    scan_logs = os.listdir(current_app.config['SCAN_LOG_DIR'])

    files = {
            'main': [],
            'product': [],
            'scan': [],
        }

    def create_log_list(logs, path):
        output = []
        if logs:
            for log in sorted(logs):
                output += [{
                        'filename': log,
                        'dir': os.path.basename(os.path.normpath(path))
                    }]
        return output

    files['main'] = create_log_list(main_logs, current_app.config['MAIN_LOG_DIR'])[::-1]
    files['product'] = create_log_list(product_logs, current_app.config['PRODUCT_LOG_DIR'])
    files['scan'] = create_log_list(scan_logs, current_app.config['SCAN_LOG_DIR'])[::-1]

    current_app.logger.debug(files['scan'])

    return render_template('main/logs.html',
            title = 'Logs',
            files = files,
        )

@bp.route("/logs/errors")
@group_required('admin')
def error_logs():
    return send_from_directory('../textlogs', 'flask_webstore_warnings.log')

