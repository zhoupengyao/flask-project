# AGENTS.md

## 项目说明

Flask 二手书店（`gardener_books`）。Python 3.11，MySQL + Bootstrap 5。

## 运行

```bash
python main.py
```

首次运行自动建表并创建默认管理员（`admin` / `admin123`）和 8 个图书分类。

也可执行 `flask init-db` 完成相同初始化。

## 目录结构

- `main.py` — 应用入口
- `config.py` — 数据库等配置（MySQL root:123456@localhost:3306/gardener_books）
- `app/` — 应用包
  - `models.py` — 数据模型（User, Book, Category, CartItem, Order, OrderItem）
  - `routes/auth.py` — 注册/登录/登出
  - `routes/books.py` — 图书浏览、搜索、分类筛选
  - `routes/cart.py` — 购物车、下单、订单历史
  - `routes/admin.py` — 管理员后台（图书 CRUD、订单管理、用户管理）
  - `templates/` — Jinja2 模板

## 开发约定

- PyCharm 项目（`.idea/`），已配置 Black 作为格式化工具。
- 依赖写入 `requirements.txt`，使用 `pip install` 安装。
- 尚未接入测试、lint 和 CI。

## 管理员权限

`User.is_admin=True` 的用户可访问 `/admin`。已预置账号 `admin` / `admin123`。
