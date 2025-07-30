from flask import jsonify
from app.api import api as bp

def bad_request(message):
    """400 错误响应"""
    response = jsonify({
        'error': 'Bad Request',
        'message': message,
        'status_code': 400
    })
    response.status_code = 400
    return response

def unauthorized(message='Unauthorized'):
    """401 错误响应"""
    response = jsonify({
        'error': 'Unauthorized',
        'message': message,
        'status_code': 401
    })
    response.status_code = 401
    return response

def forbidden(message='Forbidden'):
    """403 错误响应"""
    response = jsonify({
        'error': 'Forbidden',
        'message': message,
        'status_code': 403
    })
    response.status_code = 403
    return response

def not_found(message='Resource not found'):
    """404 错误响应"""
    response = jsonify({
        'error': 'Not Found',
        'message': message,
        'status_code': 404
    })
    response.status_code = 404
    return response

def method_not_allowed(message='Method not allowed'):
    """405 错误响应"""
    response = jsonify({
        'error': 'Method Not Allowed',
        'message': message,
        'status_code': 405
    })
    response.status_code = 405
    return response

def conflict(message='Resource conflict'):
    """409 错误响应"""
    response = jsonify({
        'error': 'Conflict',
        'message': message,
        'status_code': 409
    })
    response.status_code = 409
    return response

def validation_error(errors):
    """422 验证错误响应"""
    response = jsonify({
        'error': 'Validation Error',
        'message': 'Input validation failed',
        'errors': errors,
        'status_code': 422
    })
    response.status_code = 422
    return response

def internal_error(message='Internal server error'):
    """500 错误响应"""
    response = jsonify({
        'error': 'Internal Server Error',
        'message': message,
        'status_code': 500
    })
    response.status_code = 500
    return response

def service_unavailable(message='Service temporarily unavailable'):
    """503 错误响应"""
    response = jsonify({
        'error': 'Service Unavailable',
        'message': message,
        'status_code': 503
    })
    response.status_code = 503
    return response

@bp.errorhandler(400)
def handle_bad_request(error):
    """处理400错误"""
    return bad_request('Bad request')

@bp.errorhandler(401)
def handle_unauthorized(error):
    """处理401错误"""
    return unauthorized()

@bp.errorhandler(403)
def handle_forbidden(error):
    """处理403错误"""
    return forbidden()

@bp.errorhandler(404)
def handle_not_found(error):
    """处理404错误"""
    return not_found()

@bp.errorhandler(405)
def handle_method_not_allowed(error):
    """处理405错误"""
    return method_not_allowed()

@bp.errorhandler(409)
def handle_conflict(error):
    """处理409错误"""
    return conflict()

@bp.errorhandler(422)
def handle_validation_error(error):
    """处理422错误"""
    return validation_error(getattr(error, 'data', {}))

@bp.errorhandler(500)
def handle_internal_error(error):
    """处理500错误"""
    return internal_error()

@bp.errorhandler(503)
def handle_service_unavailable(error):
    """处理503错误"""
    return service_unavailable()