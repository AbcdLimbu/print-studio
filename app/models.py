from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(300), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    stock = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(300), nullable=True)
    starting_price = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

class ProductAttribute(db.Model):
    __tablename__ = 'product_attributes'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    attribute_name = db.Column(db.String(100), nullable=False)  # e.g. "Size", "Color"
    attribute_value = db.Column(db.String(200), nullable=False) # e.g. "30cm", "Red/Blue"

    product = db.relationship('Product', backref='attributes')

class ProductImage(db.Model):
    __tablename__ = 'product_images'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    image_url = db.Column(db.String(300), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)

    product = db.relationship('Product', backref='images')

class ProductVariant(db.Model):
    __tablename__ = 'product_variants'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    variant_type = db.Column(db.String(50), nullable=False)   # e.g. "Color", "Size"
    variant_value = db.Column(db.String(100), nullable=False)  # e.g. "Red", "A4"
    extra_price = db.Column(db.Float, default=0.0)
    stock = db.Column(db.Integer, default=0)

    product = db.relationship('Product', backref='variants')
    
class ProductOrder(db.Model):
    __tablename__ = 'product_orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Placed')
    delivery_address = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(50), default='cod')
    user = db.relationship('User', backref='product_orders')
    items = db.relationship('OrderItem', backref='order')

class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('product_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    product = db.relationship('Product', backref='order_items')

class ServiceOrder(db.Model):
    __tablename__ = 'service_orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    design_type = db.Column(db.String(50), nullable=False)  # 'predefined' or 'custom'
    design_details = db.Column(db.Text, nullable=True)
    design_file_url = db.Column(db.String(300), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Placed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='service_orders')
    service = db.relationship('Service', backref='service_orders')

class Wishlist(db.Model):
    __tablename__ = 'wishlists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='wishlist')
    product = db.relationship('Product', backref='wishlisted_by')

class PredefinedDesign(db.Model):
    __tablename__ = 'predefined_designs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    image_url = db.Column(db.String(300), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class OrderReview(db.Model):
    __tablename__ = 'order_reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_type = db.Column(db.String(20), nullable=False)
    order_id = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text, nullable=True)
    has_issue = db.Column(db.Boolean, default=False)
    issue_description = db.Column(db.Text, nullable=True)
    issue_image_url = db.Column(db.String(300), nullable=True)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='reviews')

class ReturnRequest(db.Model):
    __tablename__ = 'return_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_type = db.Column(db.String(20), nullable=False)
    order_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    resolution = db.Column(db.String(20), nullable=False)  # 'replacement' or 'refund'
    image_url = db.Column(db.String(300), nullable=True)
    status = db.Column(db.String(50), default='Pending')  # Pending, Accepted, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='returns')
