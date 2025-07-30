#!/usr/bin/env python3
"""
创建示例数据脚本
用于在开发环境中生成测试数据
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal
from app.models import Post

def create_sample_posts(db: Session, count: int = 20) -> None:
    """创建示例文章"""
    print(f"正在创建 {count} 篇示例文章...")
    
    sample_posts = [
        {
            "title": "FastAPI入门指南",
            "content": "FastAPI是一个现代、快速的Web框架，用于构建API。它基于标准Python类型提示，具有自动API文档生成、数据验证等特性。本文将介绍如何开始使用FastAPI开发高性能的Web API。",
            "summary": "学习如何使用FastAPI构建现代Web API",
            "user_id": 1,
            "status": "published"
        },
        {
            "title": "Python异步编程详解",
            "content": "异步编程是Python中的重要概念，特别是在Web开发中。通过async/await语法，我们可以编写高效的并发代码。本文深入探讨Python异步编程的原理和最佳实践。",
            "summary": "深入理解Python异步编程的原理和应用",
            "user_id": 2,
            "status": "published"
        },
        {
            "title": "SQLAlchemy 2.0新特性",
            "content": "SQLAlchemy 2.0带来了许多重要的改进和新特性，包括更好的类型支持、改进的查询API等。本文介绍这些新特性以及如何迁移现有代码。",
            "summary": "探索SQLAlchemy 2.0的新功能和改进",
            "user_id": 1,
            "status": "published"
        },
        {
            "title": "Redis缓存策略",
            "content": "Redis是一个高性能的内存数据库，常用于缓存。本文介绍不同的Redis缓存策略，包括缓存穿透、缓存雪崩的解决方案。",
            "summary": "学习Redis缓存的最佳实践和策略",
            "user_id": 3,
            "status": "published"
        },
        {
            "title": "Docker容器化部署",
            "content": "Docker是现代应用部署的标准工具。本文介绍如何使用Docker容器化Python应用，包括Dockerfile编写、多阶段构建等技巧。",
            "summary": "掌握Docker容器化部署的技巧",
            "user_id": 2,
            "status": "published"
        },
        {
            "title": "API设计最佳实践",
            "content": "良好的API设计是成功应用的基础。本文介绍RESTful API设计原则、版本控制、错误处理等最佳实践。",
            "summary": "学习API设计的原则和最佳实践",
            "user_id": 1,
            "status": "draft"
        },
        {
            "title": "微服务架构模式",
            "content": "微服务架构是现代大型应用的主流架构模式。本文探讨微服务的优缺点、设计原则以及实施策略。",
            "summary": "深入了解微服务架构的设计和实现",
            "user_id": 3,
            "status": "published"
        },
        {
            "title": "数据库性能优化",
            "content": "数据库性能是应用性能的关键因素。本文介绍数据库索引优化、查询优化、连接池配置等性能优化技巧。",
            "summary": "提升数据库性能的实用技巧",
            "user_id": 2,
            "status": "published"
        },
        {
            "title": "前端与后端分离开发",
            "content": "前后端分离是现代Web开发的标准模式。本文介绍如何设计API接口、处理跨域问题、实现用户认证等。",
            "summary": "掌握前后端分离开发的要点",
            "user_id": 1,
            "status": "published"
        },
        {
            "title": "测试驱动开发(TDD)",
            "content": "测试驱动开发是一种重要的软件开发方法论。本文介绍TDD的原理、实践步骤以及在Python项目中的应用。",
            "summary": "学习测试驱动开发的方法和实践",
            "user_id": 3,
            "status": "draft"
        }
    ]
    
    # 如果需要更多文章，重复使用模板
    while len(sample_posts) < count:
        base_post = sample_posts[len(sample_posts) % len(sample_posts)]
        new_post = base_post.copy()
        new_post["title"] = f"{base_post['title']} (续{len(sample_posts) + 1})"
        sample_posts.append(new_post)
    
    # 创建文章
    for i, post_data in enumerate(sample_posts[:count]):
        # 设置创建时间（过去几天内的随机时间）
        days_ago = i % 30  # 最近30天内
        created_at = datetime.utcnow() - timedelta(days=days_ago, hours=i % 24)
        
        post = Post(
            title=post_data["title"],
            content=post_data["content"],
            summary=post_data["summary"],
            user_id=post_data["user_id"],
            status=post_data["status"],
            view_count=i * 10 + (i % 100),  # 模拟浏览次数
            like_count=i * 2 + (i % 50),    # 模拟点赞次数
            created_at=created_at,
            updated_at=created_at
        )
        
        db.add(post)
    
    db.commit()
    print(f"成功创建 {count} 篇示例文章")

def clear_existing_data(db: Session) -> None:
    """清除现有数据"""
    print("正在清除现有数据...")
    db.query(Post).delete()
    db.commit()
    print("现有数据已清除")

def main():
    """主函数"""
    print("开始创建示例数据...")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 清除现有数据（可选）
        response = input("是否清除现有数据？(y/N): ")
        if response.lower() in ['y', 'yes']:
            clear_existing_data(db)
        
        # 创建示例文章
        count = input("请输入要创建的文章数量 (默认20): ")
        try:
            count = int(count) if count else 20
        except ValueError:
            count = 20
        
        create_sample_posts(db, count)
        
        print("\n示例数据创建完成！")
        print("你可以通过以下方式查看数据:")
        print("1. 启动服务: make dev")
        print("2. 访问API文档: http://localhost:5002/docs")
        print("3. 获取文章列表: http://localhost:5002/api/posts/")
        
    except Exception as e:
        print(f"创建示例数据时出错: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()