import pytest
from app import create_app
from db import db


@pytest.fixture
def app():
    # 1. 创建测试专用的 App
    app = create_app()

    # 2. 配置测试环境 (使用内存数据库，不污染本地文件)
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,  # 关闭 CSRF 方便测试 POST
        "SECRET_KEY": "test_secret_key"
    })

    # 3. 激活上下文并建表
    with app.app_context():
        db.create_all()
        yield app

        # 4. 测试结束后清理
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
