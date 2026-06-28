from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import db, Product, Service, ProductOrder, ServiceOrder, OrderItem, Wishlist, User, OrderReview, ReturnRequest
import cloudinary.uploader

orders = Blueprint('orders', __name__)

@orders.route('/dashboard')
@login_required
def dashboard():
    product_orders = ProductOrder.query.filter_by(user_id=current_user.id)\
                        .order_by(ProductOrder.created_at.desc()).all()
    service_orders = ServiceOrder.query.filter_by(user_id=current_user.id)\
                        .order_by(ServiceOrder.created_at.desc()).all()
    return render_template('orders/dashboard.html',
        product_orders=product_orders,
        service_orders=service_orders
    )

@orders.route('/order/product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def place_product_order(product_id):
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        quantity = int(request.form.get('quantity', 1))
        address = request.form.get('delivery_address')
        total = product.price * quantity
        order = ProductOrder(
            user_id=current_user.id,
            total_price=total,
            delivery_address=address,
            status='Placed'
        )
        db.session.add(order)
        db.session.flush()
        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=quantity,
            price=product.price
        )
        db.session.add(item)
        db.session.commit()
        flash('Order placed successfully!', 'success')
        return redirect(url_for('orders.dashboard'))
    return render_template('orders/place_product_order.html', product=product)

@orders.route('/order/service/<int:service_id>', methods=['POST'])
@login_required
def place_service_order(service_id):
    service = Service.query.get_or_404(service_id)
    design_type = request.form.get('design_type')
    design_details = request.form.get('design_details')
    quantity = int(request.form.get('quantity', 1))
    design_file_url = None
    if 'design_file' in request.files and request.files['design_file'].filename != '':
        file = request.files['design_file']
        result = cloudinary.uploader.upload(file, resource_type='auto')
        design_file_url = result['secure_url']
    order = ServiceOrder(
        user_id=current_user.id,
        service_id=service.id,
        design_type=design_type,
        design_details=design_details,
        design_file_url=design_file_url,
        quantity=quantity,
        status='Placed'
    )
    db.session.add(order)
    db.session.commit()
    flash('Service order placed successfully!', 'success')
    return redirect(url_for('orders.dashboard'))

@orders.route('/wishlist')
@login_required
def wishlist():
    items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('orders/wishlist.html', items=items)

@orders.route('/wishlist/add/<int:product_id>')
@login_required
def add_to_wishlist(product_id):
    existing = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if not existing:
        item = Wishlist(user_id=current_user.id, product_id=product_id)
        db.session.add(item)
        db.session.commit()
        flash('Added to wishlist!', 'success')
    else:
        flash('Already in wishlist!', 'info')
    return redirect(url_for('products.detail', id=product_id))

@orders.route('/wishlist/remove/<int:product_id>')
@login_required
def remove_from_wishlist(product_id):
    item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Removed from wishlist!', 'success')
    return redirect(url_for('orders.wishlist'))

@orders.route('/profile')
@login_required
def profile():
    return render_template('orders/profile.html', user=current_user)

@orders.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.phone = request.form.get('phone')
        current_user.address = request.form.get('address')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('orders.profile'))
    return render_template('orders/edit_profile.html', user=current_user)


@orders.route('/review/<string:order_type>/<int:order_id>', methods=['GET', 'POST'])
@login_required
def review_order(order_type, order_id):
    existing = OrderReview.query.filter_by(
        user_id=current_user.id,
        order_type=order_type,
        order_id=order_id
    ).first()
    if existing:
        flash('You have already reviewed this order!', 'info')
        return redirect(url_for('orders.dashboard'))
    if request.method == 'POST':
        image_url = None
        has_issue = request.form.get('has_issue') == 'on'
        if has_issue and 'issue_image' in request.files and request.files['issue_image'].filename != '':
            file = request.files['issue_image']
            result = cloudinary.uploader.upload(file)
            image_url = result['secure_url']
        review = OrderReview(
            user_id=current_user.id,
            order_type=order_type,
            order_id=order_id,
            rating=int(request.form.get('rating', 5)),
            review=request.form.get('review'),
            has_issue=has_issue,
            issue_description=request.form.get('issue_description') if has_issue else None,
            issue_image_url=image_url,
            status='Pending'
        )
        db.session.add(review)
        db.session.commit()
        flash('Thank you for your feedback! 🙏', 'success')
        return redirect(url_for('orders.dashboard'))
    return render_template('orders/review.html', order_type=order_type, order_id=order_id)


@orders.route('/return/<string:order_type>/<int:order_id>', methods=['GET', 'POST'])
@login_required
def return_request(order_type, order_id):
    # Check if already requested
    existing = ReturnRequest.query.filter_by(
        user_id=current_user.id,
        order_type=order_type,
        order_id=order_id
    ).first()
    if existing:
        flash('You have already submitted a return request for this order!', 'info')
        return redirect(url_for('orders.dashboard'))

    # Check 3 day limit
    from datetime import datetime, timedelta
    if order_type == 'product':
        order = ProductOrder.query.get_or_404(order_id)
    else:
        order = ServiceOrder.query.get_or_404(order_id)

    days_since = (datetime.utcnow() - order.created_at).days
    if days_since > 3:
        flash('Return window has expired. Returns are only accepted within 3 days of delivery.', 'danger')
        return redirect(url_for('orders.dashboard'))

    if request.method == 'POST':
        image_url = None
        if 'image' in request.files and request.files['image'].filename != '':
            file = request.files['image']
            result = cloudinary.uploader.upload(file)
            image_url = result['secure_url']
        return_req = ReturnRequest(
            user_id=current_user.id,
            order_type=order_type,
            order_id=order_id,
            reason=request.form.get('reason'),
            resolution=request.form.get('resolution'),
            image_url=image_url,
            status='Pending'
        )
        db.session.add(return_req)
        db.session.commit()
        flash('Return request submitted! We will review and get back to you within 24 hours.', 'success')
        return redirect(url_for('orders.dashboard'))
    return render_template('orders/return_request.html', order_type=order_type, order_id=order_id, days_since=days_since)
