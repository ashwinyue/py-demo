#!/usr/bin/env python3
"""
Nacos配置管理脚本
用于发布、获取、删除Nacos配置
"""

import json
import os
import sys
import argparse
from nacos import NacosClient


def get_nacos_client():
    """获取Nacos客户端"""
    server_addresses = os.environ.get('NACOS_HOST', 'localhost') + ':' + os.environ.get('NACOS_PORT', '8848')
    namespace = os.environ.get('NACOS_NAMESPACE', 'public')
    username = os.environ.get('NACOS_USERNAME')
    password = os.environ.get('NACOS_PASSWORD')
    
    try:
        client = NacosClient(
            server_addresses=server_addresses,
            namespace=namespace,
            username=username,
            password=password
        )
        return client
    except Exception as e:
        print(f"连接Nacos失败: {e}")
        return None


def publish_config(client, data_id, group, content):
    """发布配置"""
    try:
        result = client.publish_config(data_id, group, content)
        if result:
            print(f"✅ 发布配置成功: {data_id}")
        else:
            print(f"❌ 发布配置失败: {data_id}")
        return result
    except Exception as e:
        print(f"❌ 发布配置异常 {data_id}: {e}")
        return False


def get_config(client, data_id, group):
    """获取配置"""
    try:
        content = client.get_config(data_id, group)
        if content:
            print(f"✅ 获取配置成功: {data_id}")
            print(f"配置内容:\n{content}")
        else:
            print(f"⚠️  配置不存在: {data_id}")
        return content
    except Exception as e:
        print(f"❌ 获取配置异常 {data_id}: {e}")
        return None


def remove_config(client, data_id, group):
    """删除配置"""
    try:
        result = client.remove_config(data_id, group)
        if result:
            print(f"✅ 删除配置成功: {data_id}")
        else:
            print(f"❌ 删除配置失败: {data_id}")
        return result
    except Exception as e:
        print(f"❌ 删除配置异常 {data_id}: {e}")
        return False


def list_configs(client, group):
    """列出配置"""
    try:
        # 注意：nacos-sdk-python可能不支持列出所有配置的API
        # 这里只是示例，实际使用时可能需要通过Nacos控制台或API接口
        print(f"⚠️  SDK不支持列出配置，请使用Nacos控制台查看组 '{group}' 下的配置")
    except Exception as e:
        print(f"❌ 列出配置异常: {e}")


def load_example_configs():
    """加载示例配置"""
    config_file = os.path.join(os.path.dirname(__file__), '..', 'configs', 'nacos-config-examples.json')
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {config_file}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ 配置文件格式错误: {e}")
        return None


def publish_all_examples(client, group):
    """发布所有示例配置"""
    examples = load_example_configs()
    if not examples:
        return
    
    print(f"开始发布示例配置到组: {group}")
    print("-" * 50)
    
    success_count = 0
    total_count = len(examples)
    
    for data_id, config_info in examples.items():
        config_content = json.dumps(config_info['config'], ensure_ascii=False, indent=2)
        
        print(f"发布配置: {data_id}")
        print(f"描述: {config_info['description']}")
        
        if publish_config(client, data_id, group, config_content):
            success_count += 1
        
        print()
    
    print(f"发布完成: {success_count}/{total_count} 成功")


def main():
    parser = argparse.ArgumentParser(description='Nacos配置管理工具')
    parser.add_argument('action', choices=['publish', 'get', 'remove', 'list', 'publish-examples'],
                       help='操作类型')
    parser.add_argument('--data-id', help='配置ID')
    parser.add_argument('--group', default='DEFAULT_GROUP', help='配置组，默认为DEFAULT_GROUP')
    parser.add_argument('--content', help='配置内容')
    parser.add_argument('--file', help='配置文件路径')
    
    args = parser.parse_args()
    
    # 获取Nacos客户端
    client = get_nacos_client()
    if not client:
        sys.exit(1)
    
    if args.action == 'publish':
        if not args.data_id:
            print("❌ 发布配置需要指定 --data-id")
            sys.exit(1)
        
        content = args.content
        if args.file:
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"❌ 读取文件失败: {e}")
                sys.exit(1)
        
        if not content:
            print("❌ 需要指定配置内容 (--content) 或配置文件 (--file)")
            sys.exit(1)
        
        publish_config(client, args.data_id, args.group, content)
    
    elif args.action == 'get':
        if not args.data_id:
            print("❌ 获取配置需要指定 --data-id")
            sys.exit(1)
        
        get_config(client, args.data_id, args.group)
    
    elif args.action == 'remove':
        if not args.data_id:
            print("❌ 删除配置需要指定 --data-id")
            sys.exit(1)
        
        remove_config(client, args.data_id, args.group)
    
    elif args.action == 'list':
        list_configs(client, args.group)
    
    elif args.action == 'publish-examples':
        publish_all_examples(client, args.group)


if __name__ == '__main__':
    main()