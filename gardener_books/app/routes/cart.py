from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import db, Book, CartItem, Order, OrderItem

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')


@cart_bp.route('/add', methods=['POST'])
@login_required
def add():
    book_id = request.form.get('book_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)

    book = Book.query.get_or_404(book_id)
    if not book.is_active:
        flash('该图书已下架', 'danger')
        return redirect(url_for('books.book_detail', book_id=book_id))

    if quantity < 1:
        quantity = 1

    existing = CartItem.query.filter_by(user_id=current_user.id,
                                        book_id=book_id).first()
    if existing:
        existing.quantity += quantity
    else:
        item = CartItem(user_id=current_user.id, book_id=book_id,
                        quantity=quantity)
        db.session.add(item)

    db.session.commit()
    flash('已添加到购物车', 'success')
    return redirect(url_for('books.book_detail', book_id=book_id))


@cart_bp.route('')
@login_required
def view_cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.book.price * item.quantity for item in items)
    return render_template('cart/cart.html', items=items, total=total)


@cart_bp.route('/update', methods=['POST'])
@login_required
def update():
    item_id = request.form.get('item_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)

    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('无权操作', 'danger')
        return redirect(url_for('cart.view_cart'))

    if quantity < 1:
        db.session.delete(item)
    else:
        item.quantity = quantity
    db.session.commit()
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
@login_required
def remove(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('无权操作', 'danger')
        return redirect(url_for('cart.view_cart'))

    db.session.delete(item)
    db.session.commit()
    flash('已从购物车移除', 'info')
    return redirect(url_for('cart.view_cart'))


@cart_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('购物车为空', 'danger')
        return redirect(url_for('cart.view_cart'))

    if request.method == 'GET':
        total = sum(item.book.price * item.quantity for item in items)
        return render_template('cart/checkout.html', items=items, total=total)

    address = request.form.get('address', '').strip()
    phone = request.form.get('phone', '').strip()
    if not address or not phone:
        flash('请填写收货地址和联系电话', 'danger')
        total = sum(item.book.price * item.quantity for item in items)
        return render_template('cart/checkout.html', items=items, total=total)

    total = sum(item.book.price * item.quantity for item in items)
    order = Order(user_id=current_user.id, total_amount=total,
                  address=address, phone=phone)
    db.session.add(order)
    db.session.flush()

    for item in items:
        order_item = OrderItem(order_id=order.id, book_id=item.book_id,
                               price=item.book.price, quantity=item.quantity)
        db.session.add(order_item)
        book = item.book
        if book.stock is not None:
            book.stock -= item.quantity
        db.session.delete(item)

    db.session.commit()
    flash('下单成功！', 'success')
    return redirect(url_for('cart.orders_detail', order_id=order.id))


@cart_bp.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(
        Order.created_at.desc()).all()
    return render_template('orders/orders.html', orders=user_orders)


@cart_bp.route('/orders/<int:order_id>')
@login_required
def orders_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('无权查看此订单', 'danger')
        return redirect(url_for('cart.orders'))
    return render_template('orders/detail.html', order=order)
