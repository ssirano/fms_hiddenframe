from functools import wraps
from flask import session, redirect, url_for, request, jsonify

def login_required(f):
    """로그인 필수 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            # AJAX 요청인 경우 JSON 응답
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({
                    'success': False,
                    'message': '로그인이 필요합니다.',
                    'redirect': url_for('index')
                }), 401
            
            # 일반 페이지 요청인 경우 로그인 페이지로 리다이렉트
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """관리자 권한 필수 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({
                    'success': False,
                    'message': '로그인이 필요합니다.',
                    'redirect': url_for('index')
                }), 401
            return redirect(url_for('index'))
        
        # 여기에 관리자 권한 체크 로직 추가
        # 예: 사용자 정보를 DB에서 조회하여 권한 확인
        
        return f(*args, **kwargs)
    return decorated_function

def api_auth_required(f):
    """API 전용 인증 데코레이터 (JSON 응답만)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({
                'success': False,
                'message': '인증이 필요합니다.',
                'error_code': 'AUTH_REQUIRED'
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function