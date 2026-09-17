import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.models import db, User, Book, Category, Order, OrderItem

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('需要管理员权限', 'danger')
            return redirect(url_for('books.index'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('')
@login_required
@admin_required
def dashboard():
    stats = {
        'user_count': User.query.count(),
        'book_count': Book.query.count(),
        'order_count': Order.query.count(),
        'pending_orders': Order.query.filter_by(status='待付款').count(),
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_orders=recent_orders)


@admin_bp.route('/books')
@login_required
@admin_required
def books():
    page = request.args.get('page', 1, type=int)
    pagination = Book.query.order_by(Book.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/books.html', pagination=pagination)


@admin_bp.route('/books/add', methods=['GET', 'POST'])
@login_required
@admin_required
def book_add():
    categories = Category.query.all()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        if not title or not author:
            flash('书名和作者不能为空', 'danger')
            return render_template('admin/book_form.html', book=None,
                                   categories=categories)

        cover_url = ''
        file = request.files.get('cover_image')
        if file and file.filename:
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if ext in {'jpg', 'jpeg', 'png', 'gif', 'webp'}:
                saved_name = f'{os.urandom(8).hex()}.{ext}'
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], saved_name))
                cover_url = saved_name

        book = Book(
            title=title,
            author=author,
            publisher=request.form.get('publisher', '').strip(),
            isbn=request.form.get('isbn', '').strip(),
            description=request.form.get('description', '').strip(),
            price=request.form.get('price', type=float) or 0,
            original_price=request.form.get('original_price', type=float),
            condition=request.form.get('condition', '八成新'),
            category_id=request.form.get('category_id', type=int),
            stock=request.form.get('stock', 1, type=int),
            cover_url=cover_url,
        )
        db.session.add(book)
        db.session.commit()
        flash('图书添加成功', 'success')
        return redirect(url_for('admin.books'))

    return render_template('admin/book_form.html', book=None,
                           categories=categories)


@admin_bp.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def book_edit(book_id):
    book = Book.query.get_or_404(book_id)
    categories = Category.query.all()
    if request.method == 'POST':
        book.title = request.form.get('title', '').strip()
        book.author = request.form.get('author', '').strip()
        book.publisher = request.form.get('publisher', '').strip()
        book.isbn = request.form.get('isbn', '').strip()
        book.description = request.form.get('description', '').strip()
        book.price = request.form.get('price', type=float) or 0
        book.original_price = request.form.get('original_price', type=float)
        book.condition = request.form.get('condition', '八成新')
        book.category_id = request.form.get('category_id', type=int)
        book.stock = request.form.get('stock', 1, type=int)
        file = request.files.get('cover_image')
        if file and file.filename:
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
            if ext in {'jpg', 'jpeg', 'png', 'gif', 'webp'}:
                saved_name = f'{os.urandom(8).hex()}.{ext}'
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], saved_name))
                book.cover_url = saved_name

        if not book.title or not book.author:
            flash('书名和作者不能为空', 'danger')
            return render_template('admin/book_form.html', book=book,
                                   categories=categories)

        db.session.commit()
        flash('图书更新成功', 'success')
        return redirect(url_for('admin.books'))

    return render_template('admin/book_form.html', book=book,
                           categories=categories)


@admin_bp.route('/books/<int:book_id>/toggle', methods=['POST'])
@login_required
@admin_required
def book_toggle(book_id):
    book = Book.query.get_or_404(book_id)
    book.is_active = not book.is_active
    db.session.commit()
    flash('状态已更新', 'success')
    return redirect(url_for('admin.books'))


@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    status_filter = request.args.get('status', '')
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    orders_list = query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders_list,
                           current_status=status_filter)


@admin_bp.route('/orders/<int:order_id>/update', methods=['POST'])
@login_required
@admin_required
def order_update(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status', '')
    valid_statuses = ['待付款', '已付款', '已发货', '已完成', '已取消']
    if new_status in valid_statuses:
        order.status = new_status
        db.session.commit()
        flash('订单状态已更新', 'success')
    else:
        flash('无效的状态', 'danger')
    return redirect(url_for('admin.orders'))


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)
