from flask import Blueprint, request, jsonify, session, send_file, make_response
from controllers.auth import login_required
from sqlalchemy import text
from db import engine
import os
from datetime import datetime
from werkzeug.utils import secure_filename

blpds_update_bp = Blueprint('blpds_update', __name__)

@blpds_update_bp.route('/blpds_update/get_data', methods=['POST'])
@login_required
def get_data():
    """건물 이력 상세 데이터 조회"""
    try:
        request_data = request.get_json()
        auto_number = request_data.get('auto_number')
        bl_id = request_data.get('bl_id')
        
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
            
            # 이력 데이터 조회
            sql = text("""
                SELECT pds.auto_number, pds.bl_id, pds.title, pds.contents, 
                       pds.em_name as reg_man_name, pds.reg_man,
                       DATE_FORMAT(pds.reg_date, '%Y-%m-%d %H:%i:%s') as reg_date,
                       pds.filename, pds.maskname, pds.filetype
                FROM blpds pds
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
    """첨부파일 다운로드"""
    try:
        auto_number = request.args.get('auto_number')
        
        if not auto_number:
            return jsonify({'success': False, 'message': 'auto_number가 필요합니다.'})
        
        with engine.connect() as conn:
            sql = text("""
                SELECT filename, maskname, bl_id
                FROM blpds 
                WHERE auto_number = :auto_number
            """)
            
            result = conn.execute(sql, {"auto_number": auto_number}).fetchone()
            
            if result and result['filename']:
                # 실제 파일 경로 구성 (환경에 따라 수정 필요)
                file_path = f"/path/to/files/{result['maskname'] or result['filename']}"
                
                # 파일이 존재하는지 확인
                if os.path.exists(file_path):
                    return send_file(
                        file_path, 
                        as_attachment=True, 
                        download_name=result['filename']
                    )
                else:
                    return jsonify({'success': False, 'message': '파일을 찾을 수 없습니다.'})
            else:
                return jsonify({'success': False, 'message': '첨부파일이 없습니다.'})
                
    except Exception as e:
        print(f"🏢 파일 다운로드 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@blpds_update_bp.route('/blpds_update/view_file')
@login_required
def view_file():
    """이미지 파일 보기"""
    try:
        auto_number = request.args.get('auto_number')
        
        if not auto_number:
            return jsonify({'success': False, 'message': 'auto_number가 필요합니다.'})
        
        with engine.connect() as conn:
            sql = text("""
                SELECT filename, maskname, filetype
                FROM blpds 
                WHERE auto_number = :auto_number AND filetype = '1'
            """)
            
            result = conn.execute(sql, {"auto_number": auto_number}).fetchone()
            
            if result and result['maskname']:
                # 실제 이미지 파일 경로 구성
                file_path = f"/path/to/images/{result['maskname']}"
                
                if os.path.exists(file_path):
                    return send_file(file_path)
                else:
                    # 기본 이미지 반환
                    return send_file('/static/images/common/no_image.png')
            else:
                return send_file('/static/images/common/no_image.png')
                
    except Exception as e:
        print(f"🏢 이미지 보기 오류: {str(e)}")
        return send_file('/static/images/common/no_image.png')

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