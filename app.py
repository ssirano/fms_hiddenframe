from flask import Flask, render_template, redirect, url_for, session, jsonify
from controllers.login import login_bp
from controllers.common import common_bp
from controllers.base import base_bp
from controllers.fm.em_list import em_list_bp
from config import get_config
from db import test_connection, init_database
import os

def create_app():
    """애플리케이션 팩토리"""
    app = Flask(__name__)
    
    # 설정 로드
    config_class = get_config()
    app.config.from_object(config_class)
    
    # 설정 초기화
    config_class.init_app(app)
    
    # Blueprint 등록
    app.register_blueprint(login_bp, url_prefix='/login')
    app.register_blueprint(common_bp, url_prefix='/common')
    app.register_blueprint(base_bp)
    app.register_blueprint(em_list_bp, url_prefix='/fm')
    
    # 메인 라우트
    @app.route('/')
    def index():
        """메인 페이지 - 로그인 체크 후 리다이렉트"""
        if 'user' in session:
            return redirect(url_for('base.main'))
        else:
            return render_template('login.html')
    
    # 에러 핸들러 - 간단한 JSON 응답으로 수정
    @app.errorhandler(404)
    def page_not_found(e):
        if 'static' in str(e):
            # 정적 파일 404는 조용히 처리
            return jsonify({'error': 'File not found'}), 404
        return jsonify({'error': 'Page not found'}), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'error': 'Forbidden'}), 403
    
    # 헬스체크 엔드포인트
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'FMS 애플리케이션이 정상 작동 중입니다.'}
    
    # 애플리케이션 시작 시 데이터베이스 연결 테스트
    with app.app_context():
        if not test_connection():
            print("❌ 데이터베이스 연결 실패 - 애플리케이션 시작을 중단합니다.")
            return None
        
        print("✅ 데이터베이스 연결 성공")
        init_database()
    
    return app

# 애플리케이션 생성
app = create_app()

if app is None:
    print("애플리케이션 생성 실패")
    exit(1)

if __name__ == '__main__':
    # 개발 서버 실행
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 FMS 애플리케이션 시작")
    print(f"   - 모드: {'개발' if debug_mode else '운영'}")
    print(f"   - 주소: http://{host}:{port}")
    print(f"   - 디버그: {debug_mode}")
    
    app.run(debug=debug_mode, host=host, port=port)