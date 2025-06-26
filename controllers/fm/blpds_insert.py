from flask import Blueprint, request, jsonify, session
from controllers.auth import login_required
from sqlalchemy import text
from db import engine
import os
from datetime import datetime
from werkzeug.utils import secure_filename
import uuid

blpds_insert_bp = Blueprint('blpds_insert', __name__)

# 업로드 경로 설정
UPLOAD_BASE_PATH = r'C:\Users\USER04\Documents\python_fms_hiddenframe\upload'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'doc', 'docx', 'xls', 'xlsx', 'hwp'}

def allowed_file(filename):
    """허용된 파일 확장자인지 확인"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, bl_id, file_type):
    """파일 저장 및 마스크명 생성"""
    try:
        if not file or not file.filename:
            return None, None
        
        # 원본 파일명 안전하게 처리
        original_filename = secure_filename(file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        
        # 마스크 파일명 생성 (UUID + 타임스탬프)
        maskname = f"{bl_id}_{file_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{file_extension}"
        
        # 업로드 디렉터리 생성
        upload_dir = os.path.join(UPLOAD_BASE_PATH, 'bl_pds')
        os.makedirs(upload_dir, exist_ok=True)
        
        # 파일 저장
        file_path = os.path.join(upload_dir, maskname)
        file.save(file_path)
        
        print(f"🏢 파일 저장 완료: {file_path}")
        return original_filename, maskname
        
    except Exception as e:
        print(f"🏢 파일 저장 오류: {str(e)}")
        return None, None

@blpds_insert_bp.route('/blpds_insert/save_data', methods=['POST'])
@login_required
def save_data():
    """건물 이력 등록"""
    try:
        # 폼 데이터 받기
        bl_id = request.form.get('bl_id')
        title = request.form.get('title')
        contents = request.form.get('contents', '')
        file_type = request.form.get('type', '2')  # 1:이미지, 2:텍스트, 3:파일
        reg_man = request.form.get('reg_man')
        
        print(f"🏢 blpds_insert 저장 요청: bl_id={bl_id}, title={title}, type={file_type}")
        
        # 필수 필드 검증
        if not all([bl_id, title, reg_man]):
            return jsonify({
                'success': False, 
                'message': '필수 필드가 누락되었습니다. (건물ID, 제목, 등록자)'
            })
        
        em_id = session.get('user')
        current_time = datetime.now()
        
        with engine.begin() as conn:  # begin()을 사용하여 자동 커밋
            # 권한 체크
            auth_check_sql = text("""
                SELECT COUNT(*) as cnt
                FROM emcontrol ec
                WHERE ec.em_id = :em_id 
                AND (ec.bl_id = :bl_id OR ec.prop_id = (SELECT prop_id FROM bl WHERE bl_id = :bl_id))
            """)
            auth_result = conn.execute(auth_check_sql, {"em_id": em_id, "bl_id": bl_id}).fetchone()
            has_permission = auth_result['cnt'] > 0 if auth_result else False
            
            if not has_permission:
                return jsonify({'success': False, 'message': '등록 권한이 없습니다.'})
            
            # auto_number 생성
            auto_number_sql = text("""
                SELECT COALESCE(MAX(auto_number), 0) + 1 as next_id 
                FROM blpds
            """)
            auto_result = conn.execute(auto_number_sql).fetchone()
            auto_number = auto_result['next_id'] if auto_result else 1
            
            # 파일 처리
            filename = None
            maskname = None
            
            if 'file' in request.files:
                file = request.files['file']
                if file and file.filename and allowed_file(file.filename):
                    filename, maskname = save_uploaded_file(file, bl_id, file_type)
                    
                    if not filename:  # 파일 저장 실패
                        return jsonify({
                            'success': False, 
                            'message': '파일 저장에 실패했습니다.'
                        })
            
            # 텍스트 이력인데 내용이 없으면 오류
            if file_type == '2' and not contents.strip():
                return jsonify({
                    'success': False, 
                    'message': '텍스트 이력의 경우 내용을 입력해주세요.'
                })
            
            # 데이터베이스 저장
            insert_sql = text("""
                INSERT INTO blpds (
                    auto_number, bl_id, title, contents, filename, maskname, 
                    filetype, reg_man, reg_date
                ) VALUES (
                    :auto_number, :bl_id, :title, :contents, :filename, :maskname,
                    :filetype, :reg_man, :reg_date
                )
            """)
            
            result = conn.execute(insert_sql, {
                'auto_number': auto_number,
                'bl_id': bl_id,
                'title': title,
                'contents': contents,
                'filename': filename,
                'maskname': maskname,
                'filetype': file_type,
                'reg_man': reg_man,
                'reg_date': current_time
            })
            
            # engine.begin()을 사용했으므로 자동으로 커밋됨
            
            if result.rowcount > 0:
                print(f"🏢 이력 등록 성공: auto_number={auto_number}")
                return jsonify({
                    'success': True, 
                    'message': '등록이 완료되었습니다.',
                    'auto_number': auto_number
                })
            else:
                return jsonify({'success': False, 'message': '등록에 실패했습니다.'})
            
    except Exception as e:
        print(f"🏢 blpds_insert 저장 오류: {str(e)}")
        return jsonify({'success': False, 'message': f'저장 중 오류가 발생했습니다: {str(e)}'})

@blpds_insert_bp.route('/blpds_insert/check_permission', methods=['POST'])
@login_required
def check_permission():
    """등록 권한 체크"""
    try:
        request_data = request.get_json()
        bl_id = request_data.get('bl_id')
        
        if not bl_id:
            return jsonify({'success': False, 'message': 'bl_id가 필요합니다.'})
        
        em_id = session.get('user')
        
        with engine.begin() as conn:  # begin()으로 변경
            auth_check_sql = text("""
                SELECT COUNT(*) as cnt
                FROM emcontrol ec
                WHERE ec.em_id = :em_id 
                AND (ec.bl_id = :bl_id OR ec.prop_id = (SELECT prop_id FROM bl WHERE bl_id = :bl_id))
            """)
            auth_result = conn.execute(auth_check_sql, {"em_id": em_id, "bl_id": bl_id}).fetchone()
            has_permission = auth_result['cnt'] > 0 if auth_result else False
            
            return jsonify({
                'success': True,
                'has_permission': has_permission
            })
            
    except Exception as e:
        print(f"🏢 권한 체크 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@blpds_insert_bp.route('/blpds_insert/get_bl_info', methods=['POST'])
@login_required
def get_bl_info():
    """건물 정보 조회 (등록 폼 초기화용)"""
    try:
        request_data = request.get_json()
        bl_id = request_data.get('bl_id')
        
        if not bl_id:
            return jsonify({'success': False, 'message': 'bl_id가 필요합니다.'})
        
        with engine.connect() as conn:  # 조회만 하므로 connect() 사용
            bl_info_sql = text("""
                SELECT bl_id, name as bl_name, prop_id
                FROM bl
                WHERE bl_id = :bl_id
            """)
            
            result = conn.execute(bl_info_sql, {"bl_id": bl_id}).fetchone()
            
            if result:
                bl_info = dict(result)
                return jsonify({
                    'success': True,
                    'data': bl_info
                })
            else:
                return jsonify({'success': False, 'message': '건물 정보를 찾을 수 없습니다.'})
                
    except Exception as e:
        print(f"🏢 건물 정보 조회 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@blpds_insert_bp.route('/blpds_insert/get_types', methods=['GET'])
@login_required
def get_types():
    """이력 타입 목록 조회"""
    try:
        types = [
            {'value': '1', 'label': '이미지 이력', 'description': '건물 사진 및 이미지 관리'},
            {'value': '2', 'label': '텍스트 이력', 'description': '텍스트 기반 이력 관리'},
            {'value': '3', 'label': '파일 이력', 'description': '문서 및 첨부파일 관리'}
        ]
        
        return jsonify({
            'success': True,
            'data': types
        })
        
    except Exception as e:
        print(f"🏢 타입 목록 조회 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@blpds_insert_bp.route('/blpds_insert/validate_file', methods=['POST'])
@login_required
def validate_file():
    """파일 유효성 검사"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '파일이 선택되지 않았습니다.'})
        
        file = request.files['file']
        file_type = request.form.get('type', '1')
        
        if not file.filename:
            return jsonify({'success': False, 'message': '파일을 선택해주세요.'})
        
        # 파일 확장자 체크
        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'message': f'허용되지 않는 파일 형식입니다. 허용 형식: {", ".join(ALLOWED_EXTENSIONS)}'
            })
        
        # 파일 크기 체크 (10MB)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            return jsonify({
                'success': False, 
                'message': '파일 크기는 10MB를 초과할 수 없습니다.'
            })
        
        # 이미지 타입인 경우 이미지 파일인지 확인
        if file_type == '1':
            image_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            if file_extension not in image_extensions:
                return jsonify({
                    'success': False, 
                    'message': '이미지 이력의 경우 이미지 파일만 업로드 가능합니다.'
                })
        
        return jsonify({
            'success': True,
            'message': '유효한 파일입니다.',
            'file_info': {
                'name': file.filename,
                'size': file_size,
                'size_mb': round(file_size / 1024 / 1024, 2)
            }
        })
        
    except Exception as e:
        print(f"🏢 파일 유효성 검사 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})