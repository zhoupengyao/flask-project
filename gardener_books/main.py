from app import create_app, db
from app.models import User, Category

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Category': User}


@app.cli.command('init-db')
def init_db():
    """Initialize database and create default admin & categories."""
    db.create_all()

    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', phone='13800000000', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)

    default_categories = ['文学', '科技', '历史', '艺术', '教育', '生活', '经济', '哲学']
    for name in default_categories:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))

    db.session.commit()
    print('Database initialized: admin/admin123, 8 default categories.')


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', phone='13800000000', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            for name in ['文学', '科技', '历史', '艺术', '教育', '生活', '经济', '哲学']:
                if not Category.query.filter_by(name=name).first():
                    db.session.add(Category(name=name))
            db.session.commit()
    app.run(debug=True)
