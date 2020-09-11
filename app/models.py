import os
import re
import pytz
from flask import current_app, url_for, render_template, session
from datetime import datetime, timedelta, date, time
from dateutil import tz
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user
from sqlalchemy import desc, or_
from sqlalchemy.orm import backref
from app import db, login
from app.functions import round_half_up, log_change, log_new
from slugify import slugify
from markdown import markdown
from app.email import send_email

groups = db.Table('groups',
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
)

##########
## USER ########################################################################
##########
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(20), unique=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(100))
    company = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    avatar = db.Column(db.String(200), default='')
    password = db.Column(db.String(1000), default='webstore')
    groups = db.relationship('Group', secondary=groups, lazy='subquery',
            backref=db.backref('users', lazy=True))
    subscribed = db.Column(db.Boolean, nullable=False, default=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def full_name(self):
        inactive = " (Inactive)" if not self.active else ""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}{inactive}"
        return self.username + inactive

    def short_name(self):
        inactive = " (Inactive)" if not self.active else ""
        if self.first_name:
            return f"{self.first_name} {self.last_name[0]}.{inactive}" if self.last_name else self.first_name + inactive
        return self.email + inactive

    def display_name(self):
        return self.short_name()

    def in_group(self, group_names):
        group_names = group_names.split(',')
        if group_names != ['webdev']:
            group_names += ['admin']
        my_group_names = [g.name for g in self.groups]
        if 'webdev' in my_group_names:
            return True
        for group_name in group_names:
            if group_name in my_group_names:
                return True
        return False

    def __repr__(self):
        return f'User({self.id}, {self.username}, {self.first_name}, {self.last_name})'

    def __str__(self):
        return self.display_name()

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


###########
## GROUP #######################################################################
###########
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(75), unique=True)
    description = db.Column(db.String(300), nullable=True)
    style = db.Column(db.String(75), default='info')
    #restricted = db.Column(db.Boolean(), default=False)
    updater_id = db.Column(db.Integer, db.ForeignKey('user.id'))#, onupdate=current_user.id, default=current_user.id)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow, default=datetime.utcnow)

    STYLE_CHOICES = [
            ('info', 'Info (Gray-blue)'),
            ('primary', 'Primary (Bright blue)'),
            ('secondary', 'Secondary (Gray)'),
            ('success', 'Success (Green)'),
            ('warning', 'Warning (Orange)'),
            ('danger', 'Danger (Red)'),
            ('light', 'Light (White)'),
            ('dark', 'Dark (Black)'),
            ('RED', 'Red'),
            ('ORG', 'Orange'),
            ('YLW', 'Yellow'),
            ('GRN', 'Green'),
            ('BLU', 'Blue'),
            ('PUR', 'Purple'),
            ('PNK', 'Pink'),
            ('GRY', 'Gray'),
            ('WHT', 'White'),
            ('BLK', 'Black'),
        ]

    def all_permissions(self):
        return [p for p in self.permissions]

    def __repr__(self):
        return f'Group({self.id}, {self.name})'

    def __str__(self):
        return self.name


#############
## COMMENT #####################################################################
#############
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='comments', lazy=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    product = db.relationship('Product', backref=backref('comments', order_by='Comment.created.desc()'), lazy=True)
    text = db.Column(db.String(5000), nullable=False, default=' ')
    pinned = db.Column(db.Boolean, default=False)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow, default=datetime.utcnow)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    hidden = db.Column(db.Boolean, default=False)

    def html_text(self):
        return markdown(self.text)

    def created_local(self):
        utc_created = pytz.utc.localize(self.created)
        return utc_created.astimezone(tz.tzlocal())

    def notify(self, edited_user, subject="New Comment", url='/', item=''):
        if edited_user.id == self.user.id:
            recipients = [m.email for m in edited_user.get_managers()]        
        else:
            recipients = [edited_user.email]
            for manager in edited_user.get_managers():
                if self.user.id != manager.id:
                    recipients += [manager.email]
        recipients = [e for e in recipients if e]
        if len(recipients) == 0:
            print("Could not send email(s). No recipients!")
            return False
        base_url = current_app.config['BASE_URL']
        subject = subject + f' by {self.user.display_name_short()}' if self.user else subject
        text_body = f"EBS Portal Notification\n\nA new comment by {self.user.display_name_short()} was made on {item}.\n\nView it here: {base_url+url}"
        send_email(
                sender=current_app.config['MAIL_DEFAULT_SENDER'],
                subject=subject,
                recipients=recipients,
                text_body=text_body,
                html_body=render_template('email/comment.html',
                        url=base_url + url,
                        user=self.user,
                        comment=self,
                        item=item,
                        debug=current_app.config.get("DEBUG"),
                    )
            )
        return recipients

    def __repr__(self):
        if self.product_id:
            return f"Product Comment({self.id}, '{self.user}', '{self.product_id}', '{self.text}')"
        if self.label_id:
            return f"Label Comment({self.id}, '{self.user}', '{self.label_id}', '{self.text}')"
        if self.item_id:
            return f"Item Comment({self.id}, '{self.user}', '{self.item_id}', '{self.text}')"


#############
## CATEGORY #####################################################################
#############
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    image_path = db.Column(db.String(1000))
    description = db.Column(db.String(1000))
    priority = db.Column(db.Integer)

    def image_filename(self):
        if self.image_path:
            return self.image_path.split('/')[-1]
        return ''

    def html_description(self):
        if self.description:
            return markdown(self.description)
        return ''

    def active_products(self):
        return Product.query.filter_by(category_id=self.id, active=True).order_by('name').all()

    def head_data(self):
        return {
                'title': f'{self.name} Shop',
                'description': self.description,
                'image': url_for('main.uploads', filename=self.image_filename()),
            }

    def __repr__(self):
        return f'Category({self.id}, {self.name})'

    def __str__(self):
        return f'{self.name}'


#############
## PRODUCT #####################################################################
#############
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    image_path = db.Column(db.String(1000))
    description = db.Column(db.String(5000))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', backref=backref('products', order_by='Product.name'), lazy=True)
    active = db.Column(db.Boolean, default=True)
    updater_id = db.Column(db.Integer, db.ForeignKey('user.id'))#, onupdate=current_user.id, default=current_user.id)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow, default=datetime.utcnow)

    def slugify(self):
        return slugify(self.name, max_length=200)

    def log_filename(self):
        return slugify(self.name) + '_' + str(self.id) + datetime.now().strftime('_%Y-w%W.txt')
    
    def logs_link(self):
        return url_for('main.view_log', folder='product', log_name=self.log_filename())

    def image_filename(self):
        if self.image_path:
            return self.image_path.split('/')[-1]
        return ''

    def head_data(self):
        return {
                'title': f'{self.name}',
                'description': self.description,
                'image': url_for('main.uploads', filename=self.image_filename()),
            }

    def option_count(self):
        return len(self.options)

    def total_available(self):
        total = 0
        for option in self.options:
            total += option.available
        return total

    def html_description(self):
        if self.description:
            return markdown(self.description)
        return ''

    def is_sold_out(self):
        for option in self.options:
            if option.available > 0:
                return False
        return True 

    def starting_price(self):
        price = None
        for option in self.options:
            if price == None:
                price = option.price
            elif option.price < price:
                price = option.price
        return price

    def sold_out(self):
        if self.is_sold_out():
            return '<p class="text-center"><small class="border border-dark px-2">OUT OF STOCK</small></p>'
        return ''

    def export_inventory(active_only=True):
        data = [[
                'ID',
                'Name',
                'Barcode',
                'Available',
                'Capacity',
                'Shelf Start',
                'Shelf End',
                'Model',
                'Manufacturer',
                'Price',
                'Adapter',
                'Packaging',
                'Notes',
                'Comment',
                'Inventory Note',
                'Active',
            ]]
        products = Product.query
        if active_only:
            products = products.filter_by(active=True)
        products = products.order_by('name').all()

        for product in products:
            data += [[
                    product.id,
                    product.name,
                    product.barcode,
                    product.available,
                    product.capacity,
                    product.shelf_start,
                    product.shelf_end,
                    remove_commas(product.model),
                    remove_commas(product.manufacturer),
                    product.price,
                    remove_commas(product.adapter),
                    remove_commas(product.packaging),
                    remove_commas(product.notes),
                    remove_commas(product.comment),
                    remove_commas(product.inventory_note),
                    product.active,
                ]]

        return data

    def top_comment(self):
        comment = Comment.query.filter_by(product_id=self.id).order_by(desc('pinned'),desc('created')).first()
        return comment

    def __repr__(self):
        return f'Product({self.id}, {self.name})'

    def __str__(self):
        return f'{self.name}'

#############
## OPTION #####################################################################
#############
class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey(f'product.id'), nullable=False)
    product = db.relationship('Product', backref=backref('options', order_by='Option.price,Option.name'), lazy=True)
    barcode = db.Column(db.String(100), unique=True)
    image_path = db.Column(db.String(1000))
    description = db.Column(db.String(5000))
    tooltip = db.Column(db.String(100))
    available = db.Column(db.Integer, default=0)
    capacity = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Float)
    on_sale = db.Column(db.Boolean, default=False)
    sale_price = db.Column(db.Float)
    packaging = db.Column(db.String(50))
    notes = db.Column(db.String(50))
    comment = db.Column(db.String(50))
    location = db.Column(db.String(200))
    priority = db.Column(db.Integer)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow, default=datetime.utcnow)
    updater_id = db.Column(db.Integer, db.ForeignKey('user.id'))#, onupdate=current_user.id, default=current_user.id)

    def html_description(self):
        if self.description:
            return markdown(self.description)
        return ''

    def image_filename(self):
        if self.image_path:
            return self.image_path.split('/')[-1]
        return ''

    def __repr__(self):
        return f'Option({self.id}, {self.name})'

    def __str__(self):
        return f'{self.name} ({self.barcode})'

#############
## ORDER #####################################################################
#############
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(100), default='Incomplete')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=backref('orders', order_by='Order.created.desc()'), lazy=True)
    email = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    shipping_type = db.Column(db.String(100))
    shipping_time = db.Column(db.DateTime)
    shipping_id = db.Column(db.Integer, db.ForeignKey('information.id'))
    shipping = db.relationship('Information', foreign_keys=shipping_id, 
            backref='shipping_orders', lazy=True)
    billing_id = db.Column(db.Integer, db.ForeignKey('information.id'))
    billing = db.relationship('Information', foreign_keys=billing_id, 
            backref='billing_orders', lazy=True)
    payment_id = db.Column(db.String(200))
    payment_type = db.Column(db.String(100))
    paid = db.Column(db.Boolean)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow, default=datetime.utcnow)

    STATUS_CHOICES = [
            ['Incomplete', 'Incomplete - Unconfirmed order'],
            ['Confirmed', 'Confirmed - Customer has stated intent to buy or has already paid'],
            ['Packaged', 'Packaged - Ready for delivery'],
            ['Complete', 'Complete - Order has been delivered or picked up'],
        ]

    PAYMENT_TYPE_CHOICES = [
            ['Credit Card', 'Credit Card'],
            ['Cash', 'Cash'],
            ['Check', 'Check'],
        ]

    def has_shipping(self):
        if self.shipping_type == 'delivery' and self.shipping:
            return True
        if self.shipping_type == 'pickup' and self.shipping_time:
            return True
        return False

    def total_items(self, unique=False):
        if unique:
            return len(self.items)
        total = 0 
        for item in self.items:
            total += item.amount
        return total

    def status_class(self):
        if self.status == 'Incomplete':
            return 'warning'
        elif self.status == 'Complete':
            return 'success'
        return 'primary'

    def total_cost(self):
        total = 0.0
        for item in self.items:
            total += item.option.price * item.amount
        return round_half_up(total, 2)

    def in_cart(self, option_id):
        for item in self.items:
            if item.option_id == option_id:
                return True
        return False

    def get_item(self, option_id):
        for item in self.items:
            if item.option_id == option_id:
                return item
        return False

    def pickup_dates(self):
        now = datetime.now()
        first_day = now + timedelta(days=2)
        days = 0
        output = []
        while days < 7:
            new_date = first_day + timedelta(days=days)
            output += [[str(new_date.date()), new_date.strftime('%a. %b %-d, %Y')]]
            days += 1
        return output

    def pickup_times(self):
        times = [
                '8 AM','9 AM','10 AM','11 AM',
                '12 PM','1 PM','2 PM','3 PM',
                '4 PM','5 PM','6 PM','7 PM','8 PM'
            ]
        output = []
        for time in times:
            output += [[time, time]]
        return output
    
    def set_shipping_time(self, sdate, stime):
        shipping_time = datetime.strptime(f'{sdate} {stime}', '%Y-%m-%d %I %p')
        self.shipping_time = shipping_time

    def notify_confirmed(self):
        sender = current_app.config['MAIL_DEFAULT_SENDER']
        subject=f"Order Confirmation #{self.id} - {current_app.config.get('COMPANY_NAME')}"
        body=f"Your order has been confirmed. We will begin working on it shortly. We currently do deliveries every Thursday evening. If you have any questions please email us at {current_app.config.get('MAIL_USERNAME')}. \r\n\r\nYour order:\r\n"
        for item in self.items:
            body += f"{item.option.product.name} - {item.option.name} (x{item.amount}) ${item.total_cost()}"
        body += f"Order Total: ${self.total_cost}"
        send_email(
                subject,
                sender,
                [self.email, current_app.config.get('MAIL_USERNAME')],
                body,
                render_template('email/order-confirmation.html', order=self),
            )

    def __repr__(self):
        return f'Order({self.id}, {self.status})'

    def __str__(self):
        return f'Order #{self.id} ({self.status})'

#############
## ITEM #####################################################################
#############
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey(f'order.id'), nullable=True)
    order = db.relationship('Order', backref=backref('items', order_by='Item.created'), lazy=True)
    product_id = db.Column(db.Integer, db.ForeignKey(f'product.id'), nullable=True)
    product = db.relationship('Product', backref=backref('items', order_by='Item.created.desc()'), lazy=True)
    option_id = db.Column(db.Integer, db.ForeignKey(f'option.id'), nullable=True)
    option = db.relationship('Option', backref=backref('items', order_by='Item.created.desc()'), lazy=True)
    amount = db.Column(db.Integer, default=1, nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow, default=datetime.utcnow)

    def total_cost(self):
        return self.amount * self.option.price
    
    def __repr__(self):
        return f'Item({self.id}, (order #{self.order_id})'

    def __str__(self):
        return f'Item #{self.id}'

#################
## INFORMATION #####################################################################
#################
class Information(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    full_name = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=backref('informations', order_by='Information.default.desc(),Information.name'), lazy=True)
    type = db.Column(db.String(50), default="shipping")
    address_1 = db.Column(db.String(200), nullable=False)
    address_2 = db.Column(db.String(200))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    zipcode = db.Column(db.String(20), nullable=False)
    card = db.Column(db.String(200))
    expiration = db.Column(db.String(10))
    cvc = db.Column(db.String(10))
    default = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow, default=datetime.utcnow)

    TYPE_CHOICES = (
            ['shipping', 'Shipping'],
            ['billing', 'Billing'],
        )

    STATE_CHOICES = (
            ['Alabama','Alabama'],
            ['Alaska','Alaska'],
            ['Arizona','Arizona'],
            ['Arkansas','Arkansas'],
            ['California','California'],
            ['Colorado','Colorado'],
            ['Connecticut','Connecticut'],
            ['Delaware','Delaware'],
            ['Florida','Florida'],
            ['Georgia','Georgia'],
            ['Hawaii','Hawaii'],
            ['Idaho','Idaho'],
            ['Illinois','Illinois'],
            ['Indiana','Indiana'],
            ['Iowa','Iowa'],
            ['Kansas','Kansas'],
            ['Kentucky','Kentucky'],
            ['Louisiana','Louisiana'],
            ['Maine','Maine'],
            ['Maryland','Maryland'],
            ['Massachusetts','Massachusetts'],
            ['Michigan','Michigan'],
            ['Minnesota','Minnesota'],
            ['Mississippi','Mississippi'],
            ['Missouri','Missouri'],
            ['Montana','Montana'],
            ['Nebraska','Nebraska'],
            ['Nevada','Nevada'],
            ['New Hampshire','New Hampshire'],
            ['New Jersey','New Jersey'],
            ['New Mexico','New Mexico'],
            ['New York','New York'],
            ['North Carolina','North Carolina'],
            ['North Dakota','North Dakota'],
            ['Ohio','Ohio'],
            ['Oklahoma','Oklahoma'],
            ['Oregon','Oregon'],
            ['Pennsylvania','Pennsylvania'],
            ['Rhode Island','Rhode Island'],
            ['South Carolina','South Carolina'],
            ['South Dakota','South Dakota'],
            ['Tennessee','Tennessee'],
            ['Texas','Texas'],
            ['Utah','Utah'],
            ['Vermont','Vermont'],
            ['Virginia','Virginia'],
            ['Washington','Washington'],
            ['West Virginia','West Virginia'],
            ['Wisconsin','Wisconsin'],
            ['Wyoming','Wyoming'],
        )

    def __repr__(self):
        return f'Information({self.id} ({self.type})'

    def __str__(self):
        return f'Information #{self.id}'

#############
## PAGE #####################################################################
#############
class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), unique=True, nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    body = db.Column(db.String(5000))
    top_nav = db.Column(db.Boolean)
    priority = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=True)

    def html_body(self):
        if self.body:
            return markdown(self.body)
        return ''

    def head_data(self):
        return {
                'title': f'{self.title}',
                'description': self.body,
            }

    def __repr__(self):
        return f'Page({self.id}, {self.title})'

    def __str__(self):
        return f'{self.title}'

#############
## SETTING #####################################################################
#############
class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(5000))

    def __repr__(self):
        return f'Setting({self.id}, {self.name})'

    def __str__(self):
        return f'{self.name}'

