from flask import Blueprint, render_template, request
from app.models import Product

products = Blueprint('products', __name__)

@products.route('/products')
def index():
    category = request.args.get('category', '')
    search = request.args.get('search', '')

    query = Product.query.filter_by(is_active=True)

    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))

    all_products = query.order_by(Product.created_at.desc()).all()
    
    # Sort images so primary comes first for each product
    for product in all_products:
        product.images.sort(key=lambda x: (not x.is_primary, x.order_index))
    
    categories = ['Trophies', 'Awards', 'Bags', 'Fashion','Decor', 'Utility', 'Events', 'Gift Items', 'Other']

    return render_template('products/index.html',
        products=all_products,
        categories=categories,
        selected_category=category,
        search=search
    )

@products.route('/products/<int:id>')
def detail(id):
    product = Product.query.get_or_404(id)
    
    # Sort images so primary comes first
    product.images.sort(key=lambda x: (not x.is_primary, x.order_index))
    
    related = Product.query.filter_by(category=product.category, is_active=True)\
                .filter(Product.id != id).limit(4).all()
    from app.models import OrderReview, OrderItem
    reviews = OrderReview.query.filter_by(order_type='product').all()
    product_reviews = []
    for review in reviews:
        item = OrderItem.query.filter_by(product_id=product.id, order_id=review.order_id).first()
        if item:
            product_reviews.append(review)
    avg_rating = round(sum(r.rating for r in product_reviews) / len(product_reviews), 1) if product_reviews else 0
    return render_template('products/detail.html',
        product=product,
        related=related,
        reviews=product_reviews,
        avg_rating=avg_rating
    )
