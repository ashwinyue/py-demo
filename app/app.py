from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import redis
import json
import requests
try:
    import nacos
except ImportError:
    nacos = None

app = Flask(__name__)

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///miniblog.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Redis配置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Nacos配置
NACOS_HOST = os.getenv('NACOS_HOST', 'localhost')
NACOS_PORT = int(os.getenv('NACOS_PORT', 8848))
NACOS_NAMESPACE = os.getenv('NACOS_NAMESPACE', 'public')

# 初始化Redis连接
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    redis_client.ping()
    print(f"Redis连接成功: {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    print(f"Redis连接失败: {e}")
    redis_client = None

# Nacos配置中心
nacos_server = f"{NACOS_HOST}:{NACOS_PORT}"
nacos_client = None

if nacos:
    try:
        nacos_client = nacos.NacosClient(nacos_server, namespace=NACOS_NAMESPACE)
        print(f"Nacos连接成功: {nacos_server}")
    except Exception as e:
        print(f"Nacos连接失败: {e}")
        nacos_client = None

db = SQLAlchemy(app)

# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

# 博客文章模型
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user_id': self.user_id,
            'author': self.author.username if self.author else None
        }

# 健康检查接口
@app.route('/healthz')
def health_check():
    status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'database': 'connected',
            'redis': 'connected' if redis_client else 'disconnected',
            'nacos': 'connected' if nacos_client else 'disconnected'
        }
    }
    return jsonify(status), 200

# 用户相关接口
@app.route('/api/users', methods=['GET'])
def get_users():
    # 尝试从Redis缓存获取
    cache_key = 'users:all'
    if redis_client:
        try:
            cached_users = redis_client.get(cache_key)
            if cached_users:
                return jsonify(json.loads(cached_users))
        except Exception as e:
            print(f"Redis get error: {e}")
    
    # 从数据库获取
    users = User.query.all()
    result = [user.to_dict() for user in users]
    
    # 缓存到Redis
    if redis_client:
        try:
            redis_client.setex(cache_key, 300, json.dumps(result))  # 缓存5分钟
        except Exception as e:
            print(f"Redis set error: {e}")
    
    return jsonify(result)

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'username' not in data or 'email' not in data:
        return jsonify({'error': 'Username and email are required'}), 400
    
    # 检查用户是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(username=data['username'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    
    # 清除用户列表缓存
    if redis_client:
        try:
            redis_client.delete('users:all')
        except Exception as e:
            print(f"Redis delete error: {e}")
    
    return jsonify(user.to_dict()), 201

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

# 博客文章相关接口
@app.route('/api/posts', methods=['GET'])
def get_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return jsonify([post.to_dict() for post in posts])

@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data or 'user_id' not in data:
        return jsonify({'error': 'Title, content and user_id are required'}), 400
    
    # 检查用户是否存在
    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    post = Post(title=data['title'], content=data['content'], user_id=data['user_id'])
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_dict()), 201

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify(post.to_dict())

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    
    if 'title' in data:
        post.title = data['title']
    if 'content' in data:
        post.content = data['content']
    
    post.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(post.to_dict())

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Post deleted successfully'})

# 获取用户的所有文章
@app.route('/api/users/<int:user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc()).all()
    return jsonify([post.to_dict() for post in posts])

# 初始化数据库
def init_db():
    with app.app_context():
        db.create_all()
        print("数据库表创建完成")

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
else:
    # 在gunicorn启动时也初始化数据库
    init_db()