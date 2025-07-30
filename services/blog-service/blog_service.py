import os
import click
from flask import Flask
from flask.cli import with_appcontext
from app import create_app, db
from app.models import Post, Category, Tag, Comment
from app.extensions import get_redis_client, get_nacos_client

# 创建应用实例
app = create_app(os.getenv('FLASK_CONFIG') or 'development')

@app.shell_context_processor
def make_shell_context():
    """Flask shell 上下文"""
    return {
        'db': db,
        'Post': Post,
        'Category': Category,
        'Tag': Tag,
        'Comment': Comment
    }

@app.cli.command()
@with_appcontext
def init_db():
    """初始化数据库"""
    try:
        db.create_all()
        click.echo('数据库初始化成功')
        
        # 创建默认分类
        default_categories = [
            {'name': '技术', 'slug': 'tech', 'description': '技术相关文章'},
            {'name': '生活', 'slug': 'life', 'description': '生活随笔'},
            {'name': '随笔', 'slug': 'notes', 'description': '个人随笔'}
        ]
        
        for cat_data in default_categories:
            existing_cat = Category.query.filter_by(slug=cat_data['slug']).first()
            if not existing_cat:
                category = Category(
                    name=cat_data['name'],
                    slug=cat_data['slug'],
                    description=cat_data['description']
                )
                db.session.add(category)
        
        # 创建默认标签
        default_tags = [
            {'name': 'Python', 'description': 'Python编程语言'},
            {'name': 'Flask', 'description': 'Flask Web框架'},
            {'name': '微服务', 'description': '微服务架构'},
            {'name': 'Docker', 'description': 'Docker容器技术'},
            {'name': 'Redis', 'description': 'Redis缓存数据库'}
        ]
        
        for tag_data in default_tags:
            existing_tag = Tag.query.filter_by(name=tag_data['name']).first()
            if not existing_tag:
                tag = Tag(
                    name=tag_data['name'],
                    description=tag_data['description']
                )
                db.session.add(tag)
        
        db.session.commit()
        click.echo('默认分类和标签创建成功')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'数据库初始化失败: {e}', err=True)

@app.cli.command()
@with_appcontext
def create_sample_data():
    """创建示例数据"""
    try:
        # 获取默认分类和标签
        tech_category = Category.query.filter_by(slug='tech').first()
        python_tag = Tag.query.filter_by(name='Python').first()
        flask_tag = Tag.query.filter_by(name='Flask').first()
        
        if not tech_category or not python_tag or not flask_tag:
            click.echo('请先运行 init-db 命令创建默认分类和标签', err=True)
            return
        
        # 创建示例文章
        sample_posts = [
            {
                'title': 'Flask微服务架构实践',
                'content': '''# Flask微服务架构实践

本文介绍如何使用Flask构建微服务架构。

## 微服务的优势

1. 独立部署
2. 技术栈灵活
3. 故障隔离
4. 团队独立开发

## 实现方案

使用Flask + Nacos + Redis构建微服务系统。

### 服务注册与发现

使用Nacos作为注册中心，实现服务的自动注册和发现。

### 缓存策略

使用Redis实现分布式缓存，提高系统性能。

## 总结

微服务架构虽然复杂，但带来的好处是显而易见的。''',
                'summary': '介绍Flask微服务架构的实践经验',
                'category_id': tech_category.id,
                'user_id': 1,  # 假设用户ID为1
                'status': 'published',
                'tags': [python_tag, flask_tag]
            },
            {
                'title': 'Redis缓存最佳实践',
                'content': '''# Redis缓存最佳实践

本文总结Redis在实际项目中的使用经验。

## 缓存策略

### 1. 缓存穿透

使用布隆过滤器或缓存空值来解决。

### 2. 缓存雪崩

设置随机过期时间，避免大量缓存同时失效。

### 3. 缓存击穿

使用互斥锁或逻辑过期来解决热点数据问题。

## 数据结构选择

根据业务场景选择合适的Redis数据结构。

## 监控与运维

建立完善的监控体系，及时发现和解决问题。''',
                'summary': 'Redis缓存使用的最佳实践总结',
                'category_id': tech_category.id,
                'user_id': 1,
                'status': 'published',
                'tags': [python_tag]
            }
        ]
        
        for post_data in sample_posts:
            # 检查文章是否已存在
            existing_post = Post.query.filter_by(title=post_data['title']).first()
            if existing_post:
                continue
            
            tags = post_data.pop('tags', [])
            post = Post(**post_data)
            
            # 添加标签
            for tag in tags:
                post.tags.append(tag)
            
            db.session.add(post)
        
        db.session.commit()
        click.echo('示例数据创建成功')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'示例数据创建失败: {e}', err=True)

@app.cli.command()
@with_appcontext
def test_connections():
    """测试外部服务连接"""
    results = []
    
    # 测试数据库连接
    try:
        db.session.execute('SELECT 1')
        results.append('✓ 数据库连接正常')
    except Exception as e:
        results.append(f'✗ 数据库连接失败: {e}')
    
    # 测试Redis连接
    try:
        redis_client = get_redis_client()
        if redis_client:
            redis_client.ping()
            results.append('✓ Redis连接正常')
        else:
            results.append('✗ Redis客户端未初始化')
    except Exception as e:
        results.append(f'✗ Redis连接失败: {e}')
    
    # 测试Nacos连接
    try:
        nacos_client = get_nacos_client()
        if nacos_client:
            # 尝试获取服务列表来测试连接
            services = nacos_client.list_naming_instance('blog-service')
            results.append('✓ Nacos连接正常')
        else:
            results.append('✗ Nacos客户端未初始化')
    except Exception as e:
        results.append(f'✗ Nacos连接失败: {e}')
    
    for result in results:
        click.echo(result)

@app.cli.command()
@with_appcontext
def clear_cache():
    """清除所有缓存"""
    try:
        redis_client = get_redis_client()
        if redis_client:
            # 获取所有缓存键
            keys = redis_client.keys('*')
            if keys:
                redis_client.delete(*keys)
                click.echo(f'已清除 {len(keys)} 个缓存键')
            else:
                click.echo('没有找到缓存数据')
        else:
            click.echo('Redis客户端未初始化', err=True)
    except Exception as e:
        click.echo(f'清除缓存失败: {e}', err=True)

@app.cli.command()
@click.option('--category', help='分类slug')
@click.option('--tag', help='标签名称')
@with_appcontext
def update_counts(category, tag):
    """更新统计数据"""
    try:
        updated = []
        
        if category:
            cat = Category.query.filter_by(slug=category).first()
            if cat:
                cat.update_post_count()
                updated.append(f'分类 {cat.name}')
        else:
            # 更新所有分类
            categories = Category.query.all()
            for cat in categories:
                cat.update_post_count()
                updated.append(f'分类 {cat.name}')
        
        if tag:
            tag_obj = Tag.query.filter_by(name=tag).first()
            if tag_obj:
                tag_obj.update_post_count()
                updated.append(f'标签 {tag_obj.name}')
        else:
            # 更新所有标签
            tags = Tag.query.all()
            for tag_obj in tags:
                tag_obj.update_post_count()
                updated.append(f'标签 {tag_obj.name}')
        
        # 更新所有文章的评论数
        posts = Post.query.all()
        for post in posts:
            post.update_comment_count()
        
        db.session.commit()
        
        click.echo('统计数据更新完成:')
        for item in updated:
            click.echo(f'  ✓ {item}')
        click.echo(f'  ✓ {len(posts)} 篇文章的评论数')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'统计数据更新失败: {e}', err=True)

if __name__ == '__main__':
    # 开发环境下直接运行
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True
    )