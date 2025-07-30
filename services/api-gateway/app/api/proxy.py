from flask import request, jsonify, current_app, g
from app.api import bp
from app.extensions import make_service_request, rate_limit
from urllib.parse import urljoin
import json

@bp.route('/users', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@bp.route('/users/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@rate_limit("200 per hour")
def proxy_user_service(path):
    """代理用户服务请求"""
    try:
        # 构建目标路径
        if path:
            target_path = f'/api/users/{path}'
        else:
            target_path = '/api/users'
        
        # 添加查询参数
        if request.query_string:
            target_path += f'?{request.query_string.decode()}'
        
        # 准备请求数据
        data = None
        if request.is_json:
            data = request.get_json()
        elif request.form:
            data = dict(request.form)
        elif request.data:
            try:
                data = json.loads(request.data)
            except:
                data = request.data
        
        # 准备请求头
        headers = {}
        # 转发认证头
        if 'Authorization' in request.headers:
            headers['Authorization'] = request.headers['Authorization']
        # 转发Content-Type
        if 'Content-Type' in request.headers:
            headers['Content-Type'] = request.headers['Content-Type']
        # 转发用户代理
        if 'User-Agent' in request.headers:
            headers['User-Agent'] = request.headers['User-Agent']
        # 添加网关标识
        headers['X-Gateway'] = 'api-gateway'
        headers['X-Forwarded-For'] = request.remote_addr
        
        current_app.logger.info(f'代理用户服务请求: {request.method} {target_path}')
        
        # 发送请求到用户服务
        response = make_service_request(
            service_name='user-service',
            path=target_path,
            method=request.method,
            data=data,
            headers=headers
        )
        
        # 构建响应
        response_data = response.text
        try:
            response_data = response.json()
        except:
            pass
        
        # 转发响应头
        response_headers = {}
        for key, value in response.headers.items():
            if key.lower() not in ['content-length', 'transfer-encoding', 'connection']:
                response_headers[key] = value
        
        return jsonify(response_data) if isinstance(response_data, (dict, list)) else response_data, \
               response.status_code, response_headers
    
    except Exception as e:
        current_app.logger.error(f'用户服务代理失败: {e}')
        return jsonify({
            'error': 'Service Unavailable',
            'message': f'User service is currently unavailable: {str(e)}',
            'service': 'user-service'
        }), 503

@bp.route('/blog', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@bp.route('/blog/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@rate_limit("500 per hour")
def proxy_blog_service(path):
    """代理博客服务请求"""
    try:
        # 构建目标路径
        if path:
            target_path = f'/api/{path}'
        else:
            target_path = '/api/posts'  # 默认到文章列表
        
        # 添加查询参数
        if request.query_string:
            target_path += f'?{request.query_string.decode()}'
        
        # 准备请求数据
        data = None
        if request.is_json:
            data = request.get_json()
        elif request.form:
            data = dict(request.form)
        elif request.data:
            try:
                data = json.loads(request.data)
            except:
                data = request.data
        
        # 准备请求头
        headers = {}
        # 转发认证头
        if 'Authorization' in request.headers:
            headers['Authorization'] = request.headers['Authorization']
        # 转发Content-Type
        if 'Content-Type' in request.headers:
            headers['Content-Type'] = request.headers['Content-Type']
        # 转发用户代理
        if 'User-Agent' in request.headers:
            headers['User-Agent'] = request.headers['User-Agent']
        # 添加网关标识
        headers['X-Gateway'] = 'api-gateway'
        headers['X-Forwarded-For'] = request.remote_addr
        
        current_app.logger.info(f'代理博客服务请求: {request.method} {target_path}')
        
        # 发送请求到博客服务
        response = make_service_request(
            service_name='blog-service',
            path=target_path,
            method=request.method,
            data=data,
            headers=headers
        )
        
        # 构建响应
        response_data = response.text
        try:
            response_data = response.json()
        except:
            pass
        
        # 转发响应头
        response_headers = {}
        for key, value in response.headers.items():
            if key.lower() not in ['content-length', 'transfer-encoding', 'connection']:
                response_headers[key] = value
        
        return jsonify(response_data) if isinstance(response_data, (dict, list)) else response_data, \
               response.status_code, response_headers
    
    except Exception as e:
        current_app.logger.error(f'博客服务代理失败: {e}')
        return jsonify({
            'error': 'Service Unavailable',
            'message': f'Blog service is currently unavailable: {str(e)}',
            'service': 'blog-service'
        }), 503

@bp.route('/auth/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@rate_limit("100 per hour")
def proxy_auth_service(path):
    """代理认证服务请求（用户服务的认证接口）"""
    try:
        # 构建目标路径
        target_path = f'/api/auth/{path}'
        
        # 添加查询参数
        if request.query_string:
            target_path += f'?{request.query_string.decode()}'
        
        # 准备请求数据
        data = None
        if request.is_json:
            data = request.get_json()
        elif request.form:
            data = dict(request.form)
        elif request.data:
            try:
                data = json.loads(request.data)
            except:
                data = request.data
        
        # 准备请求头
        headers = {}
        # 转发认证头
        if 'Authorization' in request.headers:
            headers['Authorization'] = request.headers['Authorization']
        # 转发Content-Type
        if 'Content-Type' in request.headers:
            headers['Content-Type'] = request.headers['Content-Type']
        # 转发用户代理
        if 'User-Agent' in request.headers:
            headers['User-Agent'] = request.headers['User-Agent']
        # 添加网关标识
        headers['X-Gateway'] = 'api-gateway'
        headers['X-Forwarded-For'] = request.remote_addr
        
        current_app.logger.info(f'代理认证服务请求: {request.method} {target_path}')
        
        # 发送请求到用户服务的认证接口
        response = make_service_request(
            service_name='user-service',
            path=target_path,
            method=request.method,
            data=data,
            headers=headers
        )
        
        # 构建响应
        response_data = response.text
        try:
            response_data = response.json()
        except:
            pass
        
        # 转发响应头
        response_headers = {}
        for key, value in response.headers.items():
            if key.lower() not in ['content-length', 'transfer-encoding', 'connection']:
                response_headers[key] = value
        
        return jsonify(response_data) if isinstance(response_data, (dict, list)) else response_data, \
               response.status_code, response_headers
    
    except Exception as e:
        current_app.logger.error(f'认证服务代理失败: {e}')
        return jsonify({
            'error': 'Service Unavailable',
            'message': f'Authentication service is currently unavailable: {str(e)}',
            'service': 'user-service'
        }), 503

@bp.route('/health/<service_name>')
def proxy_health_check(service_name):
    """代理服务健康检查"""
    try:
        # 检查服务名是否有效
        backend_services = current_app.config['BACKEND_SERVICES']
        if service_name not in backend_services:
            return jsonify({
                'error': 'Invalid Service',
                'message': f'Service {service_name} not found',
                'available_services': list(backend_services.keys())
            }), 404
        
        # 获取健康检查路径
        health_path = backend_services[service_name].get('health_check', '/healthz')
        
        current_app.logger.info(f'代理健康检查: {service_name}{health_path}')
        
        # 发送健康检查请求
        response = make_service_request(
            service_name=service_name,
            path=health_path,
            method='GET'
        )
        
        # 构建响应
        response_data = response.text
        try:
            response_data = response.json()
        except:
            pass
        
        return jsonify(response_data) if isinstance(response_data, (dict, list)) else response_data, \
               response.status_code
    
    except Exception as e:
        current_app.logger.error(f'健康检查代理失败 {service_name}: {e}')
        return jsonify({
            'error': 'Health Check Failed',
            'message': f'Health check for {service_name} failed: {str(e)}',
            'service': service_name
        }), 503

# 通用代理路由（用于处理其他未匹配的路径）
@bp.route('/<service_name>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@rate_limit("300 per hour")
def proxy_generic_service(service_name, path):
    """通用服务代理"""
    try:
        # 检查服务名是否有效
        backend_services = current_app.config['BACKEND_SERVICES']
        if service_name not in backend_services:
            return jsonify({
                'error': 'Invalid Service',
                'message': f'Service {service_name} not found',
                'available_services': list(backend_services.keys())
            }), 404
        
        # 构建目标路径
        service_config = backend_services[service_name]
        path_prefix = service_config.get('path_prefix', '')
        
        if path_prefix:
            target_path = f'{path_prefix}/{path}'
        else:
            target_path = f'/api/{path}'
        
        # 添加查询参数
        if request.query_string:
            target_path += f'?{request.query_string.decode()}'
        
        # 准备请求数据
        data = None
        if request.is_json:
            data = request.get_json()
        elif request.form:
            data = dict(request.form)
        elif request.data:
            try:
                data = json.loads(request.data)
            except:
                data = request.data
        
        # 准备请求头
        headers = {}
        # 转发认证头
        if 'Authorization' in request.headers:
            headers['Authorization'] = request.headers['Authorization']
        # 转发Content-Type
        if 'Content-Type' in request.headers:
            headers['Content-Type'] = request.headers['Content-Type']
        # 转发用户代理
        if 'User-Agent' in request.headers:
            headers['User-Agent'] = request.headers['User-Agent']
        # 添加网关标识
        headers['X-Gateway'] = 'api-gateway'
        headers['X-Forwarded-For'] = request.remote_addr
        
        current_app.logger.info(f'代理通用服务请求: {service_name} {request.method} {target_path}')
        
        # 发送请求到目标服务
        response = make_service_request(
            service_name=service_name,
            path=target_path,
            method=request.method,
            data=data,
            headers=headers
        )
        
        # 构建响应
        response_data = response.text
        try:
            response_data = response.json()
        except:
            pass
        
        # 转发响应头
        response_headers = {}
        for key, value in response.headers.items():
            if key.lower() not in ['content-length', 'transfer-encoding', 'connection']:
                response_headers[key] = value
        
        return jsonify(response_data) if isinstance(response_data, (dict, list)) else response_data, \
               response.status_code, response_headers
    
    except Exception as e:
        current_app.logger.error(f'通用服务代理失败 {service_name}: {e}')
        return jsonify({
            'error': 'Service Unavailable',
            'message': f'Service {service_name} is currently unavailable: {str(e)}',
            'service': service_name
        }), 503