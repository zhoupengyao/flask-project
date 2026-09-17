import os
from datetime import datetime

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename

from ..models import Book, db, Borrow, Category

# 创建蓝图
bp = Blueprint('books', __name__)

@bp.route('/')
def index():
    """首页"""
    books = Book.query.all()
    return render_template('index.html', books=books)

@bp.route('/books')
def books():
    """图书列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    pagination = Book.query.paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items

    def page_url(p):
        args = dict(request.args)
        args['page'] = str(p)
        return '&'.join(f'{k}={v}' for k, v in args.items())

    return render_template('books/search.html', books=books, keyword='', pagination=pagination, page_url=page_url)


@bp.route('/books/<int:book_id>')
def book_detail(book_id):
    """图书详情"""
    book = Book.query.get(book_id)
    related_books = Book.query.filter(
        Book.category_id == book.category_id,
        Book.id != book.id
    ).limit(4).all()
    return render_template('books/book_detail.html', book=book, related_books=related_books)

@bp.route('/books/manage')
@login_required
def admin_index():
    """管理员首页（含搜索、筛选、分页）"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    keyword = request.args.get('keyword', '')
    author = request.args.get('author', '')
    isbn = request.args.get('isbn', '')
    publisher = request.args.get('publisher', '')
    category_id = request.args.get('category_id', type=int)
    location = request.args.get('location', '')
    year_from = request.args.get('year_from', type=int)
    year_to = request.args.get('year_to', type=int)
    sort = request.args.get('sort', 'title')
    display = request.args.get('display', 'all')

    query = Book.query.options(db.joinedload(Book.category))

    if keyword:
        query = query.filter(Book.title.like(f'%{keyword}%'))
    if author:
        query = query.filter(Book.author.like(f'%{author}%'))
    if isbn:
        query = query.filter(Book.isbn.like(f'%{isbn}%'))
    if publisher:
        query = query.filter(Book.publisher.like(f'%{publisher}%'))
    if category_id:
        query = query.filter(Book.category_id == category_id)
    if location:
        query = query.filter(Book.location == location)
    if year_from:
        query = query.filter(db.extract('year', Book.published_date) >= year_from)
    if year_to:
        query = query.filter(db.extract('year', Book.published_date) <= year_to)
    if display == 'available':
        query = query.filter(Book.available_copies > 0)
    elif display == 'borrowed':
        query = query.filter(Book.available_copies < Book.total_copies)

    sort_map = {
        'title': Book.title,
        'author': Book.author,
        'year': Book.published_date,
        'location': Book.location,
        'add_time': Book.created_at,
    }
    order = sort_map.get(sort, Book.title)
    query = query.order_by(order)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items

    # 构建分页URL参数函数
    def page_url(p):
        args = dict(request.args)
        args['page'] = str(p)
        return '&'.join(f'{k}={v}' for k, v in args.items())

    return render_template('auth/admin_manage.html', books=books, pagination=pagination, page_url=page_url)


@bp.route('/books/addbook', methods=['GET', 'POST'])
@login_required
def admin_addbook():
    """管理员添加图书"""
    if request.method == 'POST':
        # 处理表单提交
        return handle_book_submission()

    # GET 请求：显示空表单
    return render_template('auth/add_book.html')

@bp.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
def admin_editbook(book_id):
    """管理员编辑图书"""
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        return handle_book_edit(book)
    return render_template('auth/add_book.html', book=book)

def handle_book_edit(book):
    """处理图书编辑提交"""
    try:
        book.isbn = request.form.get('bookIsbn')
        book.title = request.form.get('bookTitle')
        book.author = request.form.get('author')
        book.book_pages = request.form.get('book_pages')
        book.book_price = request.form.get('book_price')
        book.book_state = request.form.get('book_state')
        book.book_language = request.form.get('book_language')
        book.book_intro = request.form.get('book_intro')
        book.publisher = request.form.get('publisher')
        book.published_date = request.form.get('published_date')
        book.category_id = request.form.get('category_id')
        book.location = request.form.get('location')
        book.recommend = request.form.get('recommend')

        # 处理图片上传
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename != '':
                book.image = save_uploaded_image(image_file)

        db.session.commit()
        flash('图书更新成功！', 'success')
        return redirect(url_for('books.admin_index'))
    except Exception as e:
        db.session.rollback()
        flash(f'更新失败：{str(e)}', 'error')
        return render_template('auth/add_book.html', book=book)

def handle_book_submission():
    """处理图书提交逻辑"""
    try:
        # 获取文本数据
        isbn = request.form.get('bookIsbn')
        title = request.form.get('bookTitle')
        author = request.form.get('author')
        book_pages = request.form.get('book_pages')
        book_price = request.form.get('book_price')
        book_state = request.form.get('book_state')
        book_language = request.form.get('book_language')
        book_intro = request.form.get('book_intro')
        publisher = request.form.get('publisher')
        published_date = request.form.get('published_date')
        category_id = request.form.get('category_id')
        total_copies = request.form.get('total_copies')
        available_copies = total_copies
        location = request.form.get('location')
        recommend = request.form.get('recommend')

        # 处理图片上传
        image_path = None
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename != '':
                image_path = save_uploaded_image(image_file)

        # 创建图书对象
        book = Book(
            isbn=isbn, title=title, author=author,
            book_pages=book_pages, book_price=book_price,
            book_state=book_state, book_language=book_language,
            book_intro=book_intro, publisher=publisher,
            published_date=published_date, category_id=category_id,
            total_copies=total_copies, available_copies=available_copies,
            location=location, image=image_path, recommend=recommend
        )

        # 保存到数据库
        db.session.add(book)
        db.session.commit()

        flash('图书添加成功！', 'success')
        return redirect(url_for('books.admin_index'))  # 重定向到图书列表

    except Exception as e:
        db.session.rollback()
        flash(f'添加失败：{str(e)}', 'error')
        return render_template('auth/add_book.html')

def save_uploaded_image(image_file):
    """保存上传的图片文件"""
    # 确保上传目录存在
    app_root = current_app.root_path
    upload_folder = os.path.join(app_root, 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # 生成安全的文件名
    filename = secure_filename(image_file.filename)
    # 添加时间戳避免重名
    name, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{name}_{timestamp}{ext}"

    # 保存文件
    file_path = os.path.join(upload_folder, filename)
    image_file.save(file_path)

    return filename  # 返回文件名用于存储在数据库


@bp.route('/books/search')
def search():
    """图书搜索"""
    keyword = request.args.get('keyword', '')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    query = Book.query.filter(Book.title.like(f'%{keyword}%') | Book.author.like(f'%{keyword}%'))
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items

    def page_url(p):
        args = dict(request.args)
        args['page'] = str(p)
        return '&'.join(f'{k}={v}' for k, v in args.items())

    return render_template('books/search.html', books=books, keyword=keyword, pagination=pagination, page_url=page_url)


@bp.route('/book/delete/<int:book_id>')
@login_required
def delete_book(book_id):
    """删除图书"""
    book = Book.query.get(book_id)
    if book:
        db.session.delete(book)
        db.session.commit()
        flash('图书删除成功！', 'success')
    else:
        flash('图书不存在！', 'error')
    return redirect(url_for('books.admin_index'))