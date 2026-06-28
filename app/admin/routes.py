from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from app.models import db, Product, Service, ProductOrder, ServiceOrder, ProductAttribute, ProductImage, ProductVariant, PredefinedDesign, OrderReview, ReturnRequest
import cloudinary.uploader

admin = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please login as admin.', 'warning')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated

@admin.route('/dashboard')
@admin_required
def dashboard():
    total_products = Product.query.count()
    total_services = Service.query.count()
    total_product_orders = ProductOrder.query.count()
    total_service_orders = ServiceOrder.query.count()
    recent_product_orders = ProductOrder.query.order_by(ProductOrder.created_at.desc()).limit(5).all()
    recent_service_orders = ServiceOrder.query.order_by(ServiceOrder.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
        total_products=total_products,
        total_services=total_services,
        total_product_orders=total_product_orders,
        total_service_orders=total_service_orders,
        recent_product_orders=recent_product_orders,
        recent_service_orders=recent_service_orders
    )

@admin.route('/products')
@admin_required
def products():
    all_products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=all_products)

@admin.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        product = Product(
            name=request.form.get('name'),
            description=request.form.get('description'),
            price=float(request.form.get('price')),
            category=request.form.get('category'),
            stock=int(request.form.get('stock', 0)),
            is_active=True
        )
        db.session.add(product)
        db.session.flush()

        # Handle multiple images
        images = request.files.getlist('images')
        for index, file in enumerate(images):
            if file and file.filename != '':
                result = cloudinary.uploader.upload(file)
                img = ProductImage(
                    product_id=product.id,
                    image_url=result['secure_url'],
                    is_primary=(index == 0),
                    order_index=index
                )
                db.session.add(img)
                if index == 0:
                    product.image_url = result['secure_url']

        # Handle attributes
        attr_names = request.form.getlist('attr_name')
        attr_values = request.form.getlist('attr_value')
        for name, value in zip(attr_names, attr_values):
            if name and value:
                attr = ProductAttribute(product_id=product.id, attribute_name=name, attribute_value=value)
                db.session.add(attr)

        # Handle variants
        variant_types = request.form.getlist('variant_type')
        variant_values = request.form.getlist('variant_value')
        variant_prices = request.form.getlist('variant_price')
        variant_stocks = request.form.getlist('variant_stock')
        for vtype, vvalue, vprice, vstock in zip(variant_types, variant_values, variant_prices, variant_stocks):
            if vtype and vvalue:
                variant = ProductVariant(
                    product_id=product.id,
                    variant_type=vtype,
                    variant_value=vvalue,
                    extra_price=float(vprice or 0),
                    stock=int(vstock or 0)
                )
                db.session.add(variant)

        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/add_product.html')

@admin.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.category = request.form.get('category')
        product.stock = int(request.form.get('stock', 0))
        product.is_active = request.form.get('is_active') == 'on'

        # Handle new images
        images = request.files.getlist('images')
        for index, file in enumerate(images):
            if file and file.filename != '':
                result = cloudinary.uploader.upload(file)
                existing_count = len(product.images)
                img = ProductImage(
                    product_id=product.id,
                    image_url=result['secure_url'],
                    is_primary=(existing_count == 0 and index == 0),
                    order_index=existing_count + index
                )
                db.session.add(img)
                if existing_count == 0 and index == 0:
                    product.image_url = result['secure_url']

        # Delete removed images
        delete_image_ids = request.form.getlist('delete_image')
        for img_id in delete_image_ids:
            img = ProductImage.query.get(int(img_id))
            if img:
                db.session.delete(img)

        # Handle attributes
        ProductAttribute.query.filter_by(product_id=product.id).delete()
        attr_names = request.form.getlist('attr_name')
        attr_values = request.form.getlist('attr_value')
        for name, value in zip(attr_names, attr_values):
            if name and value:
                attr = ProductAttribute(product_id=product.id, attribute_name=name, attribute_value=value)
                db.session.add(attr)

        # Handle variants
        ProductVariant.query.filter_by(product_id=product.id).delete()
        variant_types = request.form.getlist('variant_type')
        variant_values = request.form.getlist('variant_value')
        variant_prices = request.form.getlist('variant_price')
        variant_stocks = request.form.getlist('variant_stock')
        for vtype, vvalue, vprice, vstock in zip(variant_types, variant_values, variant_prices, variant_stocks):
            if vtype and vvalue:
                variant = ProductVariant(
                    product_id=product.id,
                    variant_type=vtype,
                    variant_value=vvalue,
                    extra_price=float(vprice or 0),
                    stock=int(vstock or 0)
                )
                db.session.add(variant)

        # Set primary image
        set_primary_id = request.form.get('set_primary')
        if set_primary_id:
            ProductImage.query.filter_by(product_id=product.id).update({'is_primary': False})
            img = ProductImage.query.get(int(set_primary_id))
            if img:
                img.is_primary = True
                product.image_url = img.image_url

        db.session.commit()
        flash('Product updated!', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/edit_product.html', product=product)

@admin.route('/products/delete/<int:id>')
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    ProductAttribute.query.filter_by(product_id=product.id).delete()
    ProductImage.query.filter_by(product_id=product.id).delete()
    ProductVariant.query.filter_by(product_id=product.id).delete()
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted!', 'success')
    return redirect(url_for('admin.products'))

@admin.route('/services')
@admin_required
def services():
    all_services = Service.query.order_by(Service.id.desc()).all()
    return render_template('admin/services.html', services=all_services)

@admin.route('/services/add', methods=['GET', 'POST'])
@admin_required
def add_service():
    if request.method == 'POST':
        image_url = None
        if 'image' in request.files and request.files['image'].filename != '':
            file = request.files['image']
            result = cloudinary.uploader.upload(file)
            image_url = result['secure_url']
        service = Service(
            name=request.form.get('name'),
            description=request.form.get('description'),
            starting_price=float(request.form.get('starting_price') or 0),
            image_url=image_url,
            is_active=True
        )
        db.session.add(service)
        db.session.commit()
        flash('Service added!', 'success')
        return redirect(url_for('admin.services'))
    return render_template('admin/add_service.html')

@admin.route('/services/delete/<int:id>')
@admin_required
def delete_service(id):
    service = Service.query.get_or_404(id)
    if service.service_orders:
        flash('Cannot delete service with existing orders. Deactivate it instead.', 'danger')
        return redirect(url_for('admin.services'))
    db.session.delete(service)
    db.session.commit()
    flash('Service deleted!', 'success')
    return redirect(url_for('admin.services'))

@admin.route('/services/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_service(id):
    service = Service.query.get_or_404(id)
    if request.method == 'POST':
        service.name = request.form.get('name')
        service.description = request.form.get('description')
        service.starting_price = float(request.form.get('starting_price') or 0)
        service.is_active = request.form.get('is_active') == 'on'
        if 'image' in request.files and request.files['image'].filename != '':
            file = request.files['image']
            result = cloudinary.uploader.upload(file)
            service.image_url = result['secure_url']
        db.session.commit()
        flash('Service updated!', 'success')
        return redirect(url_for('admin.services'))
    return render_template('admin/edit_service.html', service=service)

@admin.route('/orders/products')
@admin_required
def product_orders():
    orders = ProductOrder.query.order_by(ProductOrder.created_at.desc()).all()
    return render_template('admin/product_orders.html', orders=orders)

@admin.route('/orders/products/update/<int:id>', methods=['POST'])
@admin_required
def update_product_order(id):
    order = ProductOrder.query.get_or_404(id)
    order.status = request.form.get('status')
    db.session.commit()
    flash('Order status updated!', 'success')
    return redirect(url_for('admin.product_orders'))

@admin.route('/orders/services')
@admin_required
def service_orders():
    orders = ServiceOrder.query.order_by(ServiceOrder.created_at.desc()).all()
    return render_template('admin/service_orders.html', orders=orders)

@admin.route('/orders/services/update/<int:id>', methods=['POST'])
@admin_required
def update_service_order(id):
    order = ServiceOrder.query.get_or_404(id)
    order.status = request.form.get('status')
    db.session.commit()
    flash('Order status updated!', 'success')
    return redirect(url_for('admin.service_orders'))
@admin.route('/designs')
@admin_required
def designs():
    all_designs = PredefinedDesign.query.order_by(PredefinedDesign.created_at.desc()).all()
    return render_template('admin/designs.html', designs=all_designs)

@admin.route('/designs/add', methods=['GET', 'POST'])
@admin_required
def add_design():
    if request.method == 'POST':
        image_url = None
        if 'image' in request.files and request.files['image'].filename != '':
            file = request.files['image']
            result = cloudinary.uploader.upload(file)
            image_url = result['secure_url']
        design = PredefinedDesign(
            name=request.form.get('name'),
            category=request.form.get('category'),
            image_url=image_url,
            is_active=True
        )
        db.session.add(design)
        db.session.commit()
        flash('Design added!', 'success')
        return redirect(url_for('admin.designs'))
    return render_template('admin/add_design.html')

@admin.route('/designs/delete/<int:id>')
@admin_required
def delete_design(id):
    design = PredefinedDesign.query.get_or_404(id)
    db.session.delete(design)
    db.session.commit()
    flash('Design deleted!', 'success')
    return redirect(url_for('admin.designs'))

@admin.route('/reviews')
@admin_required
def reviews():
    all_reviews = OrderReview.query.order_by(OrderReview.created_at.desc()).all()
    return render_template('admin/reviews.html', reviews=all_reviews)

@admin.route('/reviews/update/<int:id>', methods=['POST'])
@admin_required
def update_review(id):
    review = OrderReview.query.get_or_404(id)
    review.status = request.form.get('status')
    db.session.commit()
    flash('Review status updated!', 'success')
    return redirect(url_for('admin.reviews'))

@admin.route('/returns')
@admin_required
def returns():
    all_returns = ReturnRequest.query.order_by(ReturnRequest.created_at.desc()).all()
    return render_template('admin/returns.html', returns=all_returns)

@admin.route('/returns/update/<int:id>', methods=['POST'])
@admin_required
def update_return(id):
    return_req = ReturnRequest.query.get_or_404(id)
    return_req.status = request.form.get('status')
    db.session.commit()
    flash('Return request updated!', 'success')
    return redirect(url_for('admin.returns'))
