from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from datetime import datetime

migrate = Migrate()
db = SQLAlchemy()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), default='user')  # 修复：去掉 unique=True
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系命名建议使用复数，因为一个用户可以借多本书
    borrows = db.relationship('Borrow', back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    book_pages = db.Column(db.Integer)
    book_state = db.Column(db.String(20))
    book_price = db.Column(db.Float)
    book_language = db.Column(db.String(20))
    book_intro = db.Column(db.Text)
    publisher = db.Column(db.String(100))
    published_date = db.Column(db.Date)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    location = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 修复：添加默认值
    image = db.Column(db.String(255))
    recommend = db.Column(db.Boolean, default=False)

    category = db.relationship('Category', back_populates="books")
    borrows = db.relationship('Borrow', back_populates="book", cascade="all, delete-orphan")


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)  # 分类描述
    code = db.Column(db.String(20), unique=True)  # 分类代码，如 "LIT", "SCI"
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))  # 支持多级分类
    is_active = db.Column(db.Boolean, default=True)  # 是否激活
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    books = db.relationship('Book', back_populates="category", cascade="all, delete-orphan")

    # 自引用关系，用于多级分类
    parent = db.relationship('Category', remote_side=[id], backref='subcategories')

    def __repr__(self):
        return f'<Category {self.name}>'


class Borrow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='borrowed')  # borrowed, returned, overdue

    user = db.relationship('User', back_populates="borrows")
    book = db.relationship('Book', back_populates="borrows")