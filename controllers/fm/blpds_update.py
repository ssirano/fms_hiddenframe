from flask import Blueprint, request, jsonify, session, send_file, make_response
from controllers.auth import login_required
from sqlalchemy import text
from db import engine
import os
from datetime import datetime
from werkzeug.utils import secure_filename

blpds_update_bp = Blueprint('blpds_update', __name__)

def safe_int(value):
    """값을 안전하게 정수로 변환"""
    try:
        if value is None:
            return None
        # float이든 string이든 일단 float으로 변환 후 int로 변환
        return int(float(value))
    except (ValueError, TypeError):
        return None
@blpds_update_bp.route('/blpds_update/get_data', methods=['POST'])
@login_required
def get_data():
    """건물 이력 상세 데이터 조회"""
    try:
        request_data = request.get_json()
        # POST JSON body에서 auto_number 가져오기 (URL 파라미터가 아님)
        auto_number_param = request_data.get('auto_number')
        bl_id = request_data.get('bl_id')
        
        auto_number = safe_int(auto_number_param)
        print(f"🏢 blpds_update 데이터 조회 요청: auto_number={auto_number}, bl_id={bl_id}")
        
        if not auto_number:
            return jsonify({'success': False, 'message': 'auto_number가 필요합니다.'})
        
        with engine.connect() as conn:
            # 권한 체크
            em_id = session.get('user')
            if bl_id:
                auth_check_sql = text("""
                    SELECT COUNT(*) as cnt
                    FROM emcontrol ec
                    WHERE ec.em_id = :em_id 
                    AND (ec.bl_id = :bl_id OR ec.prop_id = (SELECT prop_id FROM bl WHERE bl_id = :bl_id))
                """)
                auth_result = conn.execute(auth_check_sql, {"em_id": em_id, "bl_id": bl_id}).fetchone()
                has_permission = auth_result['cnt'] > 0 if auth_result else False
            else:
                has_permission = True  # bl_id가 없으면 일단 허용
            
            # 이력 데이터 조회 + 등록자 이름 추가
            sql = text("""
                SELECT pds.auto_number, pds.bl_id, pds.title, pds.contents, 
                       pds.reg_man,
                       em.name as reg_man_name,
                       DATE_FORMAT(pds.reg_date, '%Y-%m-%d %H:%i:%s') as reg_date,
                       pds.filename, pds.maskname, pds.filetype
                FROM blpds pds
                LEFT JOIN em ON pds.reg_man = em.em_id
                WHERE pds.auto_number = :auto_number
            """)
            
            result = conn.execute(sql, {"auto_number": auto_number}).fetchone()
            
            if result:
                data = dict(result)
                print(f"🏢 조회된 데이터: {data}")
                
                return jsonify({
                    'success': True,
                    'data': data,
                    'has_permission': has_permission
                })
            else:
                return jsonify({'success': False, 'message': '해당 이력을 찾을 수 없습니다.'})
                
    except Exception as e:
        print(f"🏢 blpds_update 데이터 조회 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})


@blpds_update_bp.route('/blpds_update/save_data', methods=['POST'])
@login_required
def save_data():
    """건물 이력 데이터 저장"""
    try:
        auto_number = request.form.get('auto_number')
        bl_id = request.form.get('bl_id')
        title = request.form.get('title')
        contents = request.form.get('contents')
        file_type = request.form.get('type', '2')
        
        if not auto_number:
            return jsonify({'success': False, 'message': 'auto_number가 필요합니다.'})
        
        em_id = session.get('user')
        current_time = datetime.now()
        
        with engine.connect() as conn:
            # 권한 체크
            if bl_id:
                auth_check_sql = text("""
                    SELECT COUNT(*) as cnt
                    FROM emcontrol ec
                    WHERE ec.em_id = :em_id 
                    AND (ec.bl_id = :bl_id OR ec.prop_id = (SELECT prop_id FROM bl WHERE bl_id = :bl_id))
                """)
                auth_result = conn.execute(auth_check_sql, {"em_id": em_id, "bl_id": bl_id}).fetchone()
                has_permission = auth_result['cnt'] > 0 if auth_result else False
                
                if not has_permission:
                    return jsonify({'success': False, 'message': '수정 권한이 없습니다.'})
            
            # 파일 처리
            filename = None
            maskname = None
            if 'file' in request.files:
                file = request.files['file']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    # 파일 저장 로직은 필요에 따라 구현
                    # maskname = save_uploaded_file(file, bl_id)
            
            # 데이터 업데이트
            update_sql = text("""
                UPDATE blpds 
                SET title = :title, contents = :contents, 
                    filename = COALESCE(:filename, filename),
                    maskname = COALESCE(:maskname, maskname),
                    date_modi = :date_modi
                WHERE auto_number = :auto_number
            """)
            
            result = conn.execute(update_sql, {
                'title': title,
                'contents': contents,
                'filename': filename,
                'maskname': maskname,
                'date_modi': current_time,
                'auto_number': auto_number
            })
            
            conn.commit()
            
            if result.rowcount > 0:
                return jsonify({'success': True, 'message': '저장이 완료되었습니다.'})
            else:
                return jsonify({'success': False, 'message': '변경사항이 없습니다.'})
            
    except Exception as e:
        print(f"🏢 blpds_update 저장 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@blpds_update_bp.route('/blpds_update/delete_data', methods=['POST'])
@login_required
def delete_data():
    """건물 이력 데이터 삭제"""
    try:
        request_data = request.get_json()
        auto_number = request_data.get('auto_number')
        
        if not auto_number:
            return jsonify({'success': False, 'message': 'auto_number가 필요합니다.'})
        
        em_id = session.get('user')
        
        with engine.connect() as conn:
            # 권한 체크 (삭제할 데이터의 bl_id로 권한 확인)
            check_sql = text("""
                SELECT bl_id FROM blpds WHERE auto_number = :auto_number
            """)
            check_result = conn.execute(check_sql, {"auto_number": auto_number}).fetchone()
            
            if check_result:
                bl_id = check_result['bl_id']
                auth_check_sql = text("""
                    SELECT COUNT(*) as cnt
                    FROM emcontrol ec
                    WHERE ec.em_id = :em_id 
                    AND (ec.bl_id = :bl_id OR ec.prop_id = (SELECT prop_id FROM bl WHERE bl_id = :bl_id))
                """)
                auth_result = conn.execute(auth_check_sql, {"em_id": em_id, "bl_id": bl_id}).fetchone()
                has_permission = auth_result['cnt'] > 0 if auth_result else False
                
                if not has_permission:
                    return jsonify({'success': False, 'message': '삭제 권한이 없습니다.'})
            
            # 데이터 삭제
            delete_sql = text("""
                DELETE FROM blpds WHERE auto_number = :auto_number
            """)
            
            result = conn.execute(delete_sql, {"auto_number": auto_number})
            conn.commit()
            
            if result.rowcount > 0:
                return jsonify({'success': True, 'message': '삭제가 완료되었습니다.'})
            else:
                return jsonify({'success': False, 'message': '삭제할 데이터를 찾을 수 없습니다.'})
            
    except Exception as e:
        print(f"🏢 blpds_update 삭제 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@blpds_update_bp.route('/blpds_update/download_file')
@login_required
def download_file():
    """첨부파일 다운로드 (JSP 방식 호환)"""
    try:
        auto_number_param = request.args.get('auto_number')
        auto_number = safe_int(auto_number_param)
        
        if not auto_number:
            return jsonify({'success': False, 'message': 'auto_number가 필요합니다.'})
        
        with engine.connect() as conn:
            sql = text("""
                SELECT filename, maskname, bl_id
                FROM blpds 
                WHERE auto_number = :auto_number
            """)
            
            result = conn.execute(sql, {"auto_number": auto_number}).fetchone()
            
            if result and result['maskname']:
                file_data = dict(result)
                
                # ⭐ bl_pds 절대 경로에서 파일 찾기
                bl_pds_file_path = os.path.join(BL_PDS_PATH, file_data['maskname'])
                
                print(f"🏢 다운로드 요청: {file_data['filename']}")
                print(f"🏢 파일 경로: {bl_pds_file_path}")
                
                if os.path.exists(bl_pds_file_path):
                    return send_file(
                        bl_pds_file_path, 
                        as_attachment=True, 
                        download_name=file_data['filename']
                    )
                else:
                    print(f"🔴 다운로드 파일 없음: {bl_pds_file_path}")
                    return jsonify({'success': False, 'message': '파일을 찾을 수 없습니다.'})
            else:
                return jsonify({'success': False, 'message': '첨부파일이 없습니다.'})
                
    except Exception as e:
        print(f"🏢 파일 다운로드 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})


BL_PDS_PATH = r"C:\Users\USER04\Documents\python_fms_hiddenframe\upload\bl_pds"
@blpds_update_bp.route('/blpds_update/view_file')
@login_required
def view_file():
    auto_number_param = request.args.get('auto_number')
    auto_number = safe_int(auto_number_param)

    print(f"🏢 [blpds_update] view_file 폴백 엔드포인트 호출: auto_number={auto_number}")

    if not auto_number:
        print("🔴 auto_number가 없음")
        return send_file('static/images/common/no_image.png')
    
    try:
        with engine.connect() as conn:
            sql = text("""
                SELECT filename, maskname, filetype
                FROM blpds 
                WHERE auto_number = :auto_number
            """)
            
            result = conn.execute(sql, {"auto_number": auto_number}).fetchone()
            
            if result and result['maskname']:
                file_data = dict(result)
                maskname = file_data['maskname']
                
                # ⭐ bl_pds 절대 경로에서 파일 찾기
                bl_pds_file_path = os.path.join(BL_PDS_PATH, maskname)
                
                print(f"🏢 [blpds_update] 폴백에서 파일 경로 확인: {bl_pds_file_path}")
                
                if os.path.exists(bl_pds_file_path):
                    print(f"✅ 파일 찾음: {bl_pds_file_path}")
                    
                    file_ext = maskname.lower().split('.')[-1]
                    mimetype_map = {
                        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
                        'gif': 'image/gif', 'bmp': 'image/bmp', 'webp': 'image/webp',
                        'svg': 'image/svg+xml'
                    }
                    
                    mimetype = mimetype_map.get(file_ext, 'image/jpeg')
                    
                    return send_file(
                        bl_pds_file_path,
                        mimetype=mimetype,
                        as_attachment=False,
                        download_name=file_data['filename']
                    )
                else:
                    print(f"🔴 파일 없음: {bl_pds_file_path}")
                    return send_file('static/images/common/no_image.png')
            else:
                print("🔴 데이터베이스에 파일 정보 없음")
                return send_file('static/images/common/no_image.png')
                
    except Exception as e:
        print(f"🔴 [blpds_update] 폴백 엔드포인트 오류: {str(e)}")
        return send_file('static/images/common/no_image.png')

@blpds_update_bp.route('/blpds_update/set_default_photo', methods=['POST'])
@login_required
def set_default_photo():
    """기본사진으로 설정"""
    try:
        request_data = request.get_json()
        bl_id = request_data.get('bl_id')
        maskname = request_data.get('maskname')
        
        if not bl_id or not maskname:
            return jsonify({'success': False, 'message': '필수 파라미터가 누락되었습니다.'})
        
        em_id = session.get('user')
        
        with engine.connect() as conn:
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
                return jsonify({'success': False, 'message': '권한이 없습니다.'})
            
            # 건물 테이블의 maskname 업데이트
            update_sql = text("""
                UPDATE bl SET maskname = :maskname WHERE bl_id = :bl_id
            """)
            
            result = conn.execute(update_sql, {
                'maskname': maskname,
                'bl_id': bl_id
            })
            
            conn.commit()
            
            if result.rowcount > 0:
                return jsonify({'success': True, 'message': '기본사진으로 설정되었습니다.'})
            else:
                return jsonify({'success': False, 'message': '설정에 실패했습니다.'})
            
    except Exception as e:
        print(f"🏢 기본사진 설정 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})  
    
@blpds_update_bp.route('/blpds_update/debug_file/<int:auto_number>')
@login_required
def debug_file(auto_number):
    """파일 존재 여부 디버깅"""
    try:
        with engine.connect() as conn:
            sql = text("""
                SELECT auto_number, filename, maskname, filetype, title
                FROM blpds 
                WHERE auto_number = :auto_number
            """)
            
            result = conn.execute(sql, {"auto_number": auto_number}).fetchone()
            
            debug_info = {
                'auto_number': auto_number,
                'database_record': dict(result) if result else None,
                'current_directory': os.getcwd(),
                'file_checks': [],
                'uploads_directory_exists': False,
                'uploads_files': []
            }
            
            if result:
                maskname = result['maskname']
                if maskname:
                    # 여러 경로 확인
                    possible_paths = [
                        os.path.join('static', 'uploads', maskname),
                        os.path.join('uploads', maskname),
                        maskname,
                        os.path.join(os.getcwd(), 'static', 'uploads', maskname)
                    ]
                    
                    for path in possible_paths:
                        exists = os.path.exists(path)
                        size = os.path.getsize(path) if exists else 0
                        debug_info['file_checks'].append({
                            'path': path,
                            'exists': exists,
                            'size': size
                        })
            
            # uploads 디렉토리 확인
            uploads_dir = os.path.join('static', 'uploads')
            if os.path.exists(uploads_dir):
                debug_info['uploads_directory_exists'] = True
                try:
                    files = os.listdir(uploads_dir)[:20]  # 최대 20개
                    debug_info['uploads_files'] = files
                except:
                    debug_info['uploads_files'] = ['읽기 오류']
            
            return jsonify(debug_info)
            
    except Exception as e:
        return jsonify({
            'error': str(e),
            'auto_number': auto_number
        })