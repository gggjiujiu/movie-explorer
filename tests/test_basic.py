from models.user import User
from db import db


# 测试 1: 首页能不能打开
def test_home_page(client):
    # 访问根目录
    response = client.get("/")
    assert response.status_code == 200
    # 检查页面里有没有 "Log In" 这个词 (确保显示的是登录页)
    assert b"Log In" in response.data


# 测试 2: 没登录访问受限页面，应该被踢回首页
def test_access_without_login(client):
    # 尝试访问收藏夹
    response = client.get("/favourites", follow_redirects=True)

    # 检查是否成功加载了页面 (状态码 200)
    assert response.status_code == 200
    # 检查内容里是否有 "Log In" (说明被重定向回了首页)
    # 或者检查 Flash 消息 "Please log in"
    assert b"Log In" in response.data or b"Please log in" in response.data


# 测试 3: 数据库逻辑 (注册用户)
def test_user_creation(app):
    with app.app_context():
        # 创建一个假用户
        user = User(
            firstname="Test",
            lastname="User",
            email="test@example.com",
            account="test_user_1"
        )
        user.set_password("password123")

        # 存入测试数据库
        db.session.add(user)
        db.session.commit()

        # 查出来验证
        saved_user = User.query.filter_by(email="test@example.com").first()
        assert saved_user is not None
        assert saved_user.firstname == "Test"
        assert saved_user.check_password("password123") is True
