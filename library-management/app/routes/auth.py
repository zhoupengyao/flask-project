import random
from flask import render_template, Blueprint, request, flash, redirect, url_for, session, send_file
from flask_login import login_user, logout_user, login_required, current_user

from ..form import RegisterForm, LoginForm, RetrievePasswordForm
from ..models import User, Book, Borrow, Category, db
from ..captcha import generate_captcha
from .. import mail
from flask_mail import Message


bp = Blueprint('auth', __name__)

@bp.route('/captcha')
def captcha():
    chars, buf = generate_captcha()
    session['captcha'] = chars
    return send_file(buf, mimetype='image/png')

@bp.route('/send_code', methods=['POST'])
def send_code():
    email = request.form.get('email', '')
    captcha_input = request.form.get('captcha', '')
    if not email:
        return {'ok': False, 'msg': '请输入邮箱'}
    if captcha_input.upper() != session.pop('captcha', ''):
        return {'ok': False, 'msg': '图形验证码错误'}
    user = User.query.filter_by(email=email).first()
    if not user:
        return {'ok': False, 'msg': '该邮箱未注册'}
    code = ''.join(random.choices('0123456789', k=6))
    session['reset_code'] = code
    session['reset_email'] = email
    try:
        msg = Message('图书馆 - 密码重置验证码', recipients=[email])
        msg.body = f'您的验证码是：{code}\n\n验证码有效期为10分钟，请勿泄露给他人。\n如果这不是您的操作，请忽略此邮件。'
        mail.send(msg)
        return {'ok': True, 'msg': '验证码已发送，请查收邮箱'}
    except Exception as e:
        return {'ok': True, 'msg': f'验证码发送失败（演示模式：{code}）'}

@bp.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    op = request.args.get('operate', 'login')

    if op == 'register':
        form = RegisterForm()
    elif op == 'login':
        form = LoginForm()
    else:
        form = RetrievePasswordForm()

    if request.method == 'POST':
        if op == 'register':
            if form.validate_on_submit():
                return handle_register(form)
        elif op == 'login':
            if form.validate_on_submit():
                return handle_login(form)
        else:
            if form.validate_on_submit():
                return handle_reset_password(form)

    return render_template('auth/sign_in.html', operate=op, form=form)

def handle_register(form):
    """处理注册逻辑"""
    existing_user = User.query.filter_by(username=form.username.data).first()
    if existing_user:
        flash('用户名已存在')
        return render_template('auth/sign_in.html', operate='register', form=form)
    new_user = User(
        username=form.username.data,
        email=form.email.data,
        role='user'
    )
    new_user.set_password(form.password.data)

    try:
        db.session.add(new_user)
        db.session.commit()
        flash('注册成功！请登录', 'success')
        return redirect(url_for('auth.sign_in', operate='login'))
    except Exception as e:
        db.session.rollback()
        flash('注册失败，请重试', 'error')
        return render_template('auth/sign_in.html', operate='register', form=form)

def handle_login(form):
    """处理登录逻辑"""
    user = User.query.filter_by(username=form.username.data).first()

    if user and user.check_password(form.password.data):
        login_user(user, remember=True)
        # 这里应该设置登录状态，例如使用 flask-login
        if user.role == 'admin':
            flash('欢迎回来，管理员！', 'success')
            return redirect(url_for('books.admin_index'))
        flash(f'欢迎回来，{user.username}!', 'success')
        return redirect(url_for('books.index'))  # 登录成功后跳转到首页
    else:
        flash('用户名或密码错误', 'error')
        return render_template('auth/sign_in.html', operate='login', form=form)

def handle_reset_password(form):
    """重置密码"""
    if not form.verification_code.data or len(form.verification_code.data) != 6:
        flash('请输入6位邮箱验证码', 'error')
        return render_template('auth/sign_in.html', operate='forget', form=form)
    if not form.password.data or len(form.password.data) < 8:
        flash('密码长度不能少于8位', 'error')
        return render_template('auth/sign_in.html', operate='forget', form=form)
    if form.password.data != form.password2.data:
        flash('两次输入的密码不一致', 'error')
        return render_template('auth/sign_in.html', operate='forget', form=form)
    code = session.get('reset_code')
    email = session.get('reset_email')
    if not code or not email:
        flash('请先获取验证码', 'error')
        return render_template('auth/sign_in.html', operate='forget', form=form)
    if form.email.data != email:
        flash('邮箱与获取验证码的邮箱不一致', 'error')
        return render_template('auth/sign_in.html', operate='forget', form=form)
    if form.verification_code.data != code:
        flash('验证码错误', 'error')
        return render_template('auth/sign_in.html', operate='forget', form=form)
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('用户不存在', 'error')
        return render_template('auth/sign_in.html', operate='forget', form=form)
    user.set_password(form.password.data)
    db.session.commit()
    session.pop('reset_code', None)
    session.pop('reset_email', None)
    flash('密码重置成功，请重新登录', 'success')
    return redirect(url_for('auth.sign_in', operate='login'))

@bp.route('/logout')
def logout():
    """处理登出逻辑"""
    # 这里应该设置登出状态，例如使用 flask-login
    logout_user()
    flash('您已登出', 'success')
    return redirect(url_for('books.index'))

@bp.route('/user/home')
@login_required
def user_home():
    """用户主页"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = Borrow.query.filter_by(user_id=current_user.id).options(
        db.joinedload(Borrow.book).joinedload(Book.category)
    ).order_by(Borrow.borrow_date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    borrows = pagination.items

    def page_url(p):
        args = dict(request.args)
        args['page'] = str(p)
        return '&'.join(f'{k}={v}' for k, v in args.items())

    return render_template('auth/user_manage.html', borrows=borrows, pagination=pagination, page_url=page_url)

