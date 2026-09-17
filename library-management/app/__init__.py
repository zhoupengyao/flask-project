from datetime import datetime

from flask import Flask, send_from_directory, request, session, url_for
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

mail = Mail()

def create_app():
    # 创建Flask应用
    app = Flask(__name__)

    # 加载配置
    app.config.from_object(Config)

    # 配置会话在服务器重启后失效
    app.config.update(
        SESSION_PERMANENT=False,  # 会话不是永久的
        PERMANENT_SESSION_LIFETIME=3600,  # 会话生命周期1小时
    )

    from .models import db, migrate, User  # 导入 User 模型
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # 初始化 Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.sign_in'  # 设置登录页面
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'warning'

    # 设置会话保护模式
    login_manager.session_protection = "strong"  # 或 "basic"

    # 用户加载回调
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 注册蓝图
    from .routes.books import bp as bp_books
    from .routes.auth import bp as bp_auth
    from .routes.borrow import bp as bp_borrow
    app.register_blueprint(bp_books)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_borrow)

    @app.route('/uploads/<filename>')
    def uploads(filename):
        print('-----------------------')
        print(app.config['UPLOAD_FOLDER'])
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # ========== 添加导航历史跟踪 ==========
    @app.before_request
    def track_navigation_history():
        """在每个请求前执行，记录页面访问历史"""
        # 排除静态文件和不重要的端点
        excluded_endpoints = ['static', 'auth.login', 'auth.logout']

        if (request.endpoint and
                request.endpoint not in excluded_endpoints and
                request.method == 'GET'):

            # 初始化历史记录
            if 'nav_history' not in session:
                session['nav_history'] = []

            current_page = {
                'endpoint': request.endpoint,
                'url': request.url,
                'timestamp': datetime.now().isoformat(),
                'args': dict(request.args)
            }

            # 避免重复记录相同的页面（比如刷新）
            nav_history = session['nav_history']
            if (not nav_history or
                    nav_history[-1]['endpoint'] != current_page['endpoint'] or
                    nav_history[-1]['url'] != current_page['url']):

                # 保持历史记录长度（保留最近10个页面）
                if len(nav_history) >= 10:
                    nav_history.pop(0)

                nav_history.append(current_page)
                session['nav_history'] = nav_history
                session.modified = True

    # ========== 添加上下文处理器 ==========
    @app.context_processor
    def utility_processor():
        """向模板注入辅助函数"""

        def get_previous_url(default_endpoint='books.index'):
            """获取上一个页面的URL"""
            nav_history = session.get('nav_history', [])

            if len(nav_history) >= 2:
                previous_page = nav_history[-2]
                try:
                    return url_for(previous_page['endpoint'], **previous_page['args'])
                except:
                    return url_for(default_endpoint)
            else:
                return url_for(default_endpoint)

        return {'get_previous_url': get_previous_url}

    return app