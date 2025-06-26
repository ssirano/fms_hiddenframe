from flask import Flask, render_template, redirect, url_for, session, jsonify, send_from_directory
from controllers.login import login_bp
from controllers.common import common_bp
from controllers.base import base_bp
from controllers.fm.em_list import em_list_bp
from controllers.fm.prop_list import prop_list_bp
from controllers.fm.prop_update import prop_update_bp
from controllers.fm.bl_list import bl_list_bp
from controllers.fm.bl_update import bl_update_bp
from controllers.fm.blpds_update import blpds_update_bp 
from controllers.fm.blpds_insert import blpds_insert_bp
from controllers.fm.fl_list import fl_list_bp
from controllers.fm.fl_update import fl_update_bp
from controllers.fm.rm_list import rm_list_bp
from controllers.fm.rm_update import rm_update_bp
from controllers.fm.rm_insert import rm_insert_bp
from controllers.fm.rm_tenant import rm_tenant_bp
from controllers.fm.rmtenant_list import rmtenant_list_bp
from controllers.fm.rmtenant_update import rmtenant_update_bp
from controllers.fm.rmtenant_insert import rmtenant_insert_bp
from controllers.dms.dms_list import dms_list_bp
from controllers.dms.dms_update import dms_update_bp
from controllers.dms.dms_insert import dms_insert_bp
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
    app.register_blueprint(prop_list_bp, url_prefix='/fm')
    app.register_blueprint(prop_update_bp, url_prefix='/fm')
    app.register_blueprint(bl_list_bp, url_prefix='/fm')
    app.register_blueprint(bl_update_bp, url_prefix='/fm')
    app.register_blueprint(blpds_update_bp, url_prefix='/fm')
    app.register_blueprint(blpds_insert_bp, url_prefix='/fm')
    app.register_blueprint(fl_list_bp, url_prefix='/fm')
    app.register_blueprint(fl_update_bp, url_prefix='/fm')
    app.register_blueprint(rm_list_bp, url_prefix='/fm')
    app.register_blueprint(rm_update_bp, url_prefix='/fm')
    app.register_blueprint(rm_insert_bp, url_prefix='/fm')
    app.register_blueprint(rm_tenant_bp, url_prefix='/fm') 
    app.register_blueprint(rmtenant_list_bp, url_prefix='/fm')
    app.register_blueprint(rmtenant_update_bp, url_prefix='/fm')
    app.register_blueprint(rmtenant_insert_bp, url_prefix='/fm')
    app.register_blueprint(dms_list_bp, url_prefix='/fm')
    app.register_blueprint(dms_update_bp, url_prefix='/fm')
    app.register_blueprint(dms_insert_bp, url_prefix='/fm')
    
    
    
    # 메인 라우트
    
    BL_PDS_PATH = r"C:\Users\USER04\Documents\python_fms_hiddenframe\upload\bl_pds"

    @app.route('/bl_pds/<path:filename>')
    def serve_bl_pds_files(filename):
        """bl_pds 폴더의 파일들을 정적으로 서빙 (JSP 방식과 동일)"""
        try:
            print(f"🏢 bl_pds 파일 요청: {filename}")
            print(f"🏢 파일 경로: {os.path.join(BL_PDS_PATH, filename)}")
            
            # 파일 존재 여부 확인
            file_path = os.path.join(BL_PDS_PATH, filename)
            if os.path.exists(file_path):
                print(f"✅ 파일 존재: {file_path}")
                return send_from_directory(BL_PDS_PATH, filename)
            else:
                print(f"🔴 파일 없음: {file_path}")
                # 기본 이미지 반환
                return send_from_directory('static/images/common', 'no_image.png')
                
        except Exception as e:
            print(f"🔴 bl_pds 파일 서빙 오류: {str(e)}")
            return send_from_directory('static/images/common', 'no_image.png')

    @app.route('/debug/bl_pds_files')
    def list_bl_pds_files():
        """bl_pds 폴더의 파일 목록 확인"""
        try:
            if not os.path.exists(BL_PDS_PATH):
                return jsonify({
                    'success': False,
                    'message': f'bl_pds 폴더가 존재하지 않습니다: {BL_PDS_PATH}'
                })
            
            files = os.listdir(BL_PDS_PATH)
            image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'))]
            
            file_details = []
            for filename in image_files[:20]:  # 처음 20개만
                file_path = os.path.join(BL_PDS_PATH, filename)
                try:
                    stat = os.stat(file_path)
                    file_details.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'url': f'/bl_pds/{filename}'
                    })
                except Exception as e:
                    file_details.append({
                        'filename': filename,
                        'error': str(e)
                    })
            
            return jsonify({
                'success': True,
                'bl_pds_path': BL_PDS_PATH,
                'total_files': len(files),
                'image_files_count': len(image_files),
                'sample_files': file_details
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'bl_pds_path': BL_PDS_PATH
            })

    # ⭐ 특정 파일 존재 여부 확인
    @app.route('/debug/check_bl_pds_file/<path:filename>')
    def check_bl_pds_file(filename):
        """특정 파일의 존재 여부 확인"""
        file_path = os.path.join(BL_PDS_PATH, filename) 
        
        result = {
            'filename': filename,
            'bl_pds_path': BL_PDS_PATH,
            'full_path': file_path,
            'exists': os.path.exists(file_path),
            'url': f'/bl_pds/{filename}'
        }
        
        if result['exists']:
            try:
                stat = os.stat(file_path)
                result['size'] = stat.st_size
                result['modified'] = stat.st_mtime
            except Exception as e:
                result['stat_error'] = str(e)
        
        return jsonify(result)
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
    
    print("\n=== fl_list 라우트 등록 상태 확인 ===")
    fl_routes = []
    for rule in app.url_map.iter_rules():
        if 'fl_list' in rule.rule: 
            fl_routes.append(rule)
            print(f"✅ {rule.rule} -> {rule.endpoint} [{', '.join(rule.methods)}]")
    
    if len(fl_routes) == 0:
        print("🔴 fl_list 관련 라우트가 하나도 등록되지 않았습니다!")
        print("🔍 가능한 원인:")
        print("   1. controllers/fm/fl_list.py 파일이 없음")
        print("   2. fl_list.py에서 import 오류 발생")
        print("   3. fl_list.py에서 문법 오류 발생")
        print("   4. __init__.py 파일 누락")
    else:
        print(f"✅ fl_list 관련 라우트 {len(fl_routes)}개 정상 등록됨")
    
    print("=====================================\n")
    
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
    
    app.run(debug=True, host=host, port=port) 