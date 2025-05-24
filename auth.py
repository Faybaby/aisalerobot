from flask import request, jsonify
import jwt
import datetime
from functools import wraps

# JWT配置
SECRET_KEY = 'xiaoyingsalesassistant2025'
TOKEN_EXPIRATION = 24  # 小时

# 生成JWT令牌
def create_token(username):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRATION),
        'iat': datetime.datetime.utcnow(),
        'sub': username
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

# JWT验证装饰器
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        # 检查Authorization头
        if auth_header:
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
        
        if not token:
            return jsonify({
                'status': 'error',
                'code': 401,
                'message': '缺少认证令牌'
            }), 401
        
        try:
            # 解码验证令牌
            jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({
                'status': 'error',
                'code': 401,
                'message': '令牌已过期'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'status': 'error',
                'code': 401,
                'message': '无效的令牌'
            }), 401
            
        return f(*args, **kwargs)
    
    return decorated