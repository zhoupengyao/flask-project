from datetime import datetime, timedelta

from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from ..models import User, Book, Borrow, Category, db

bp = Blueprint('borrow', __name__)

@bp.route('/borrow/<int:book_id>', methods=['GET','POST'])
@login_required
def borrow_book(book_id):
    active = Borrow.query.filter_by(user_id=current_user.id, book_id=book_id).filter(
        Borrow.status.in_(['borrowed', 'overdue'])
    ).first()
    if active:
        flash('您已借阅此书', 'error')
        return redirect(url_for('books.book_detail', book_id=book_id))
    book = Book.query.get(book_id)
    if book.available_copies <= 0:
        flash('此书已无库存', 'error')
        return redirect(url_for('books.book_detail', book_id=book_id))
    borrow = Borrow(
        user_id=current_user.id,
        book_id=book_id,
        due_date=datetime.now() + timedelta(days=7),
        status='borrowed'
    )
    db.session.add(borrow)
    book.available_copies -= 1
    db.session.commit()
    flash('借阅成功', 'success')
    return redirect(url_for('books.book_detail', book_id=book_id))

@bp.route('/borrow/return/<int:borrow_id>', methods=['POST'])
@login_required
def return_book(borrow_id):
    """归还图书（仅管理员）"""
    if current_user.role != 'admin':
        flash('您没有权限执行此操作', 'error')
        return redirect(url_for('books.index'))
    borrow = Borrow.query.get_or_404(borrow_id)
    if borrow.status != 'borrowed' and borrow.status != 'overdue':
        flash('此借阅记录已归还', 'warning')
        return redirect(url_for('borrow.admin_borrow'))
    borrow.status = 'returned'
    borrow.return_date = datetime.now()
    borrow.book.available_copies += 1
    db.session.commit()
    flash(f'《{borrow.book.title}》归还成功', 'success')
    return redirect(url_for('borrow.admin_borrow'))

@bp.route('/borrow/delete/<int:borrow_id>', methods=['POST'])
@login_required
def delete_borrow(borrow_id):
    """删除借阅记录（仅本人）"""
    borrow = Borrow.query.get_or_404(borrow_id)
    if borrow.user_id != current_user.id:
        flash('无权操作此记录', 'error')
        return redirect(url_for('auth.user_home'))
    if borrow.status == 'borrowed' or borrow.status == 'overdue':
        borrow.book.available_copies += 1
    db.session.delete(borrow)
    db.session.commit()
    flash('借阅记录已删除', 'success')
    return redirect(url_for('auth.user_home'))

@bp.route('/borrow/manage')
@login_required
def admin_borrow():
    """管理员借阅管理"""
    if not current_user.role == 'admin':
        flash('您没有权限访问此页面', 'error')
        return redirect(url_for('books.index'))

    # 逾期检测
    now = datetime.now()
    overdue_borrows = Borrow.query.filter(
        Borrow.status == 'borrowed',
        Borrow.due_date < now
    ).all()
    for b in overdue_borrows:
        b.status = 'overdue'
    if overdue_borrows:
        db.session.commit()

    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = Borrow.query.options(
        db.joinedload(Borrow.user),
        db.joinedload(Borrow.book)
    ).order_by(Borrow.borrow_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    borrows = pagination.items

    def page_url(p):
        args = dict(request.args)
        args['page'] = str(p)
        return '&'.join(f'{k}={v}' for k, v in args.items())

    return render_template('auth/borrow_manage.html', borrows=borrows, pagination=pagination, page_url=page_url)