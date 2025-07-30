import os
import click
from flask import Flask
from flask.cli import with_appcontext
from app import create_app
from app.extensions import (
    get_redis_client, get_nacos_client, discover_service,
    get_service_stats, get_service_health, health_check_service
)

# 创建应用实例
app = create_app(os.getenv('FLASK_CONFIG') or 'development')

@app.shell_context_processor
def make_shell_context():
    """Flask shell 上下文"""
    return {
        'redis_client': get_redis_client(),
        'nacos_client': get_nacos_client(),
        'discover_service': discover_service,
        'get_service_stats': get_service_stats,
        'get_service_health': get_service_health
    }

@app.cli.command()
@with_appcontext
def test_connections():
    """测试外部服务连接"""
    results = []
    
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
            services = nacos_client.list_naming_instance('api-gateway')
            results.append('✓ Nacos连接正常')
        else:
            results.append('✗ Nacos客户端未初始化')
    except Exception as e:
        results.append(f'✗ Nacos连接失败: {e}')
    
    # 测试后端服务连接
    backend_services = app.config['BACKEND_SERVICES']
    for service_name in backend_services.keys():
        try:
            is_healthy = health_check_service(service_name)
            if is_healthy:
                results.append(f'✓ {service_name}服务连接正常')
            else:
                results.append(f'✗ {service_name}服务连接失败')
        except Exception as e:
            results.append(f'✗ {service_name}服务连接失败: {e}')
    
    for result in results:
        click.echo(result)

@app.cli.command()
@with_appcontext
def discover_services():
    """发现所有服务"""
    try:
        backend_services = app.config['BACKEND_SERVICES']
        
        click.echo('服务发现结果:')
        click.echo('=' * 50)
        
        for service_name in backend_services.keys():
            try:
                instances = discover_service(service_name)
                click.echo(f'\n服务: {service_name}')
                click.echo(f'实例数量: {len(instances)}')
                
                if instances:
                    for i, instance in enumerate(instances, 1):
                        click.echo(f'  实例{i}: {instance["ip"]}:{instance["port"]} (权重: {instance.get("weight", 1.0)})')
                else:
                    click.echo('  没有可用实例')
            except Exception as e:
                click.echo(f'\n服务: {service_name}')
                click.echo(f'  发现失败: {e}')
        
        click.echo('\n' + '=' * 50)
    
    except Exception as e:
        click.echo(f'服务发现失败: {e}', err=True)

@app.cli.command()
@with_appcontext
def show_stats():
    """显示服务统计信息"""
    try:
        stats = get_service_stats()
        health = get_service_health()
        
        click.echo('服务统计信息:')
        click.echo('=' * 50)
        
        if stats:
            for service_name, service_stats in stats.items():
                click.echo(f'\n服务: {service_name}')
                click.echo(f'  成功请求: {service_stats.get("success_count", 0)}')
                click.echo(f'  失败请求: {service_stats.get("failure_count", 0)}')
                click.echo(f'  最后请求时间: {service_stats.get("last_request_time", "N/A")}')
                
                # 显示健康状态
                service_health = health.get(service_name, {})
                if service_health:
                    click.echo(f'  健康状态: {"健康" if service_health.get("healthy") else "不健康"}')
                    click.echo(f'  最后检查时间: {service_health.get("last_check", "N/A")}')
        else:
            click.echo('没有统计数据')
        
        click.echo('\n' + '=' * 50)
    
    except Exception as e:
        click.echo(f'获取统计信息失败: {e}', err=True)

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
@click.option('--service', help='指定服务名称')
@with_appcontext
def health_check(service):
    """执行健康检查"""
    try:
        backend_services = app.config['BACKEND_SERVICES']
        
        if service:
            if service not in backend_services:
                click.echo(f'服务 {service} 不存在', err=True)
                click.echo(f'可用服务: {list(backend_services.keys())}')
                return
            
            services_to_check = [service]
        else:
            services_to_check = list(backend_services.keys())
        
        click.echo('健康检查结果:')
        click.echo('=' * 50)
        
        for service_name in services_to_check:
            try:
                is_healthy = health_check_service(service_name)
                status = '✓ 健康' if is_healthy else '✗ 不健康'
                click.echo(f'{service_name}: {status}')
            except Exception as e:
                click.echo(f'{service_name}: ✗ 检查失败 - {e}')
        
        click.echo('\n' + '=' * 50)
    
    except Exception as e:
        click.echo(f'健康检查失败: {e}', err=True)

@app.cli.command()
@with_appcontext
def show_config():
    """显示网关配置"""
    try:
        click.echo('API网关配置:')
        click.echo('=' * 50)
        
        config_items = [
            ('服务名称', app.config['SERVICE_NAME']),
            ('服务地址', f"{app.config['SERVICE_HOST']}:{app.config['SERVICE_PORT']}"),
            ('Redis地址', f"{app.config['REDIS_HOST']}:{app.config['REDIS_PORT']}"),
            ('Nacos地址', app.config['NACOS_SERVER']),
            ('默认限流', app.config['RATE_LIMIT_DEFAULT']),
            ('请求超时', f"{app.config['REQUEST_TIMEOUT']}秒"),
            ('连接超时', f"{app.config['CONNECT_TIMEOUT']}秒"),
            ('熔断阈值', app.config['CIRCUIT_BREAKER_FAILURE_THRESHOLD']),
            ('负载均衡策略', app.config['LOAD_BALANCER_STRATEGY'])
        ]
        
        for key, value in config_items:
            click.echo(f'{key}: {value}')
        
        click.echo('\n后端服务配置:')
        backend_services = app.config['BACKEND_SERVICES']
        for service_name, config in backend_services.items():
            click.echo(f'  {service_name}:')
            click.echo(f'    路径前缀: {config.get("path_prefix", "N/A")}')
            click.echo(f'    健康检查: {config.get("health_check", "N/A")}')
            click.echo(f'    超时时间: {config.get("timeout", "N/A")}秒')
            click.echo(f'    重试次数: {config.get("retries", "N/A")}')
            if 'fallback_url' in config:
                click.echo(f'    备用地址: {config["fallback_url"]}')
        
        click.echo('\n' + '=' * 50)
    
    except Exception as e:
        click.echo(f'显示配置失败: {e}', err=True)

@app.cli.command()
@click.option('--host', default='0.0.0.0', help='监听地址')
@click.option('--port', default=5000, help='监听端口')
@click.option('--debug', is_flag=True, help='调试模式')
def run_dev(host, port, debug):
    """运行开发服务器"""
    click.echo(f'启动API网关开发服务器: {host}:{port}')
    if debug:
        click.echo('调试模式已启用')
    
    app.run(
        host=host,
        port=port,
        debug=debug
    )

if __name__ == '__main__':
    # 开发环境下直接运行
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )