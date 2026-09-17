from flask import Blueprint, render_template, request, current_app
from app.models import Book, Category

books_bp = Blueprint('books', __name__)


@books_bp.route('/')
def index():
    new_books = Book.query.filter_by(is_active=True).order_by(
        Book.created_at.desc()).limit(8).all()
    categories = Category.query.all()
    return render_template('index.html', new_books=new_books,
                           categories=categories)


@books_bp.route('/books')
def book_list():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    keyword = request.args.get('keyword', '').strip()
    per_page = current_app.config.get('BOOKS_PER_PAGE', 12)

    query = Book.query.filter_by(is_active=True)

    if category_id:
        query = query.filter_by(category_id=category_id)

    if keyword:
        like = f'%{keyword}%'
        query = query.filter(
            Book.title.ilike(like) | Book.author.ilike(like)
        )

    pagination = query.order_by(Book.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    categories = Category.query.all()
    return render_template('books/list.html', pagination=pagination,
                           categories=categories, category_id=category_id,
                           keyword=keyword)


@books_bp.route('/books/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('books/detail.html', book=book)
