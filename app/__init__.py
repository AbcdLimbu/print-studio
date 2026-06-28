from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import cloudinary
import os

from app.models import db, User

load_dotenv()

login_manager = LoginManager()

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    # Configs
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///npprinters.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Cloudinary config
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.auth.routes import auth
    from app.main.routes import main
    from app.products.routes import products
    from app.services.routes import services
    from app.orders.routes import orders
    from app.admin.routes import admin

    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(products)
    app.register_blueprint(services)
    app.register_blueprint(orders)
    app.register_blueprint(admin)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('main/404.html'), 404

    @app.context_processor
    def admin_notifications():
        if session.get('admin_logged_in'):
            from app.models import ProductOrder, ServiceOrder, ReturnRequest
            new_product_orders = ProductOrder.query.filter_by(status='Placed').count()
            new_service_orders = ServiceOrder.query.filter_by(status='Placed').count()
            new_returns = ReturnRequest.query.filter_by(status='Pending').count()
            return dict(
                new_product_orders=new_product_orders,
                new_service_orders=new_service_orders,
                new_returns=new_returns
            )
        return dict(new_product_orders=0, new_service_orders=0, new_returns=0)

    return app
