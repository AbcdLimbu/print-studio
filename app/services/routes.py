from flask import Blueprint, render_template
from app.models import Service, PredefinedDesign

services = Blueprint('services', __name__)

@services.route('/services')
def index():
    all_services = Service.query.filter_by(is_active=True).all()
    return render_template('services/index.html', services=all_services)

@services.route('/services/<int:id>')
def detail(id):
    service = Service.query.get_or_404(id)
    designs = PredefinedDesign.query.filter_by(is_active=True).all()
    return render_template('services/detail.html', service=service, designs=designs)
