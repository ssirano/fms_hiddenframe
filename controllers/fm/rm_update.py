import math
from flask import Blueprint, request, jsonify, make_response, json
from controllers.auth import login_required
from sqlalchemy import text
from db import engine, get_session
from datetime import datetime

rm_update_bp = Blueprint('rm_update', __name__)

##### /rm_update/get_room_info - 실정보 조회 #####
@rm_update_bp.route('/rm_update/get_room_info', methods=['POST'])
@login_required
def get_room_info():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')
        bl_id = data.get('bl_id')
        fl_id = data.get('fl_id')
        rm_id = data.get('rm_id')

        print(f"🔵 [rm_update] 실정보 조회 요청: prop_id={prop_id}, bl_id={bl_id}, fl_id={fl_id}, rm_id={rm_id}")

        if not all([em_id, prop_id, bl_id, fl_id, rm_id]):
            return jsonify({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다.'
            }), 400

        # JSP와 동일한 쿼리 - rm 테이블에서 기본 정보 조회
        sql = text("""
            SELECT 
                r.prop_id, 
                r.bl_id, 
                r.fl_id, 
                r.rm_id, 
                r.name AS rm_name,
                r.maskname,
                p.name AS prop_name,
                b.name AS bl_name,
                f.name AS fl_name
            FROM rm r
            LEFT JOIN prop p ON r.prop_id = p.prop_id
            LEFT JOIN bl b ON r.bl_id = b.bl_id AND r.prop_id = b.prop_id
            LEFT JOIN fl f ON r.fl_id = f.fl_id AND r.bl_id = f.bl_id AND r.prop_id = f.prop_id
            WHERE r.prop_id = :prop_id 
            AND r.bl_id = :bl_id 
            AND r.fl_id = :fl_id 
            AND r.rm_id = :rm_id
            AND r.prop_id IN (
                SELECT prop_id FROM emcontrol 
                WHERE em_id = :em_id AND prop_id = :prop_id
            )
        """)

        with get_session() as session_obj:
            result = session_obj.execute(sql, {
                'em_id': em_id,
                'prop_id': prop_id,
                'bl_id': bl_id,
                'fl_id': fl_id,
                'rm_id': rm_id
            }).fetchone()
            
            if not result:
                return jsonify({
                    'success': False,
                    'message': '실정보를 찾을 수 없습니다.'
                }), 404
            
            # 결과를 딕셔너리로 변환
            room_info = dict(result)
            
            # Null 값 빈 문자열로 변환
            for key, value in room_info.items():
                if value is None:
                    room_info[key] = ''

        print(f"🟢 [rm_update] 실정보 조회 완료: {rm_id}")
        
        return jsonify({
            'success': True,
            'message': '실정보 조회 성공',
            'data': room_info
        })

    except Exception as e:
        print(f"🔴 [rm_update] get_room_info 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'실정보 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /rm_update/get_tenant_list - 입주사 목록 조회 #####
@rm_update_bp.route('/rm_update/get_tenant_list', methods=['POST'])
@login_required
def get_tenant_list():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')
        bl_id = data.get('bl_id')
        fl_id = data.get('fl_id')
        rm_id = data.get('rm_id')
        include_moved_out = data.get('include_moved_out', False)
        keyword = data.get('keyword', '').strip()

        print(f"🔵 [rm_update] 입주사 목록 조회: prop_id={prop_id}, bl_id={bl_id}, fl_id={fl_id}, rm_id={rm_id}, include_moved_out={include_moved_out}, keyword={keyword}")

        if not all([em_id, prop_id, bl_id, fl_id, rm_id]):
            return jsonify({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다.'
            }), 400

        # JSP와 동일한 쿼리 구조 (DATE_FORMAT으로 수정)
        base_sql = """
            SELECT 
                rmtenant_id, 
                tenant_name, 
                em_reg, 
                bl_id, 
                bl_name, 
                fl_id, 
                fl_name, 
                rm_id, 
                rm_name, 
                prop_id, 
                DATE_FORMAT(date_reg, '%Y-%m-%d') AS date_reg, 
                DATE_FORMAT(move_in, '%Y-%m-%d') AS move_in, 
                DATE_FORMAT(move_out, '%Y-%m-%d') AS move_out, 
                comments
            FROM rmtenant
            WHERE prop_id = :prop_id 
            AND bl_id = :bl_id 
            AND fl_id = :fl_id 
            AND rm_id = :rm_id
        """
        
        params = {
            'prop_id': prop_id,
            'bl_id': bl_id,
            'fl_id': fl_id,
            'rm_id': rm_id
        }
        
        # 퇴실포함 체크박스가 체크되지 않았을 때 (JSP 로직과 동일)
        if not include_moved_out:
            base_sql += " AND move_out IS NULL"
        
        # 키워드 검색 (JSP 로직과 동일)
        if keyword:
            # 공백으로 분리하여 각각 검색
            keywords = keyword.split()
            if keywords:
                base_sql += " AND ("
                keyword_conditions = []
                for i, kw in enumerate(keywords[:50]):  # 최대 50개까지
                    if kw.strip():
                        param_key = f'keyword_{i}'
                        keyword_conditions.append(f"LOWER(tenant_name) LIKE LOWER(:{param_key})")
                        params[param_key] = f'%{kw.strip()}%'
                
                if keyword_conditions:
                    base_sql += " AND ".join(keyword_conditions)
                base_sql += ")"
        
        base_sql += " ORDER BY tenant_name ASC"

        with get_session() as session_obj:
            result = session_obj.execute(text(base_sql), params).fetchall()
            
            tenant_list = []
            for row in result:
                tenant_item = dict(row)
                
                # Null 값 빈 문자열로 변환
                for key, value in tenant_item.items():
                    if value is None:
                        tenant_item[key] = ''
                
                tenant_list.append(tenant_item)

        print(f"🟢 [rm_update] 입주사 목록 조회 완료: {len(tenant_list)}개")
        
        return jsonify({
            'success': True,
            'message': '입주사 목록 조회 성공',
            'data': tenant_list
        })

    except Exception as e:
        print(f"🔴 [rm_update] get_tenant_list 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'입주사 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500 

##### /rm_update/save_room - 실정보 저장 #####
@rm_update_bp.route('/rm_update/save_room', methods=['POST'])
@login_required
def save_room():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id_old = data.get('prop_id_old')
        bl_id_old = data.get('bl_id_old')
        fl_id_old = data.get('fl_id_old')
        rm_id_old = data.get('rm_id_old')
        rm_name = data.get('rm_name', '').strip()

        print(f"🔵 [rm_update] 실정보 저장 요청: prop_id={prop_id_old}, bl_id={bl_id_old}, fl_id={fl_id_old}, rm_id={rm_id_old}, rm_name={rm_name}")

        if not all([em_id, prop_id_old, bl_id_old, fl_id_old, rm_id_old, rm_name]):
            return jsonify({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다.'
            }), 400

        # 실정보 업데이트 (컬럼명 수정 - 실제 테이블 구조에 맞게)
        update_sql = text("""
            UPDATE rm 
            SET name = :rm_name
            WHERE prop_id = :prop_id 
            AND bl_id = :bl_id 
            AND fl_id = :fl_id 
            AND rm_id = :rm_id
        """)

        with get_session() as session_obj:
            # 실정보 업데이트 실행
            result = session_obj.execute(update_sql, {
                'rm_name': rm_name,
                'prop_id': prop_id_old,
                'bl_id': bl_id_old,
                'fl_id': fl_id_old,
                'rm_id': rm_id_old
            })
            
            session_obj.commit()
            
            if result.rowcount == 0:
                return jsonify({
                    'success': False,
                    'message': '수정할 실정보를 찾을 수 없습니다.'
                }), 404

        print(f"🟢 [rm_update] 실정보 저장 완료: {rm_id_old}")
        
        return jsonify({
            'success': True,
            'message': '실정보가 성공적으로 저장되었습니다.'
        })

    except Exception as e:
        print(f"🔴 [rm_update] save_room 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'실정보 저장 중 오류가 발생했습니다: {str(e)}'
        }), 500
        
##### /rm_update/delete_room - 실정보 삭제 #####
@rm_update_bp.route('/rm_update/delete_room', methods=['POST'])
@login_required
def delete_room():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')
        bl_id = data.get('bl_id')
        fl_id = data.get('fl_id')
        rm_id = data.get('rm_id')

        print(f"🔵 [rm_update] 실정보 삭제 요청: prop_id={prop_id}, bl_id={bl_id}, fl_id={fl_id}, rm_id={rm_id}")

        if not all([em_id, prop_id, bl_id, fl_id, rm_id]):
            return jsonify({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다.'
            }), 400

        # 권한 체크 - scalar() 사용으로 간소화
        auth_sql = text("""
            SELECT COUNT(*) 
            FROM emcontrol
            WHERE em_id = :em_id AND prop_id = :prop_id
        """)

        # 관련 입주사 정보 먼저 삭제 (외래키 제약조건 때문)
        delete_tenant_sql = text("""
            DELETE FROM rmtenant 
            WHERE prop_id = :prop_id 
            AND bl_id = :bl_id 
            AND fl_id = :fl_id 
            AND rm_id = :rm_id
        """)

        # 실정보 삭제
        delete_room_sql = text("""
            DELETE FROM rm 
            WHERE prop_id = :prop_id 
            AND bl_id = :bl_id 
            AND fl_id = :fl_id 
            AND rm_id = :rm_id
        """)

        with get_session() as session_obj:
            # 권한 체크 - scalar() 사용
            auth_count = session_obj.execute(auth_sql, {
                'em_id': em_id,
                'prop_id': prop_id
            }).scalar()
            
            if auth_count == 0:
                return jsonify({
                    'success': False,
                    'message': '해당 사업장에 대한 권한이 없습니다.'
                }), 403
            
            # 관련 입주사 정보 삭제
            tenant_result = session_obj.execute(delete_tenant_sql, {
                'prop_id': prop_id,
                'bl_id': bl_id,
                'fl_id': fl_id,
                'rm_id': rm_id
            })
            
            print(f"🟡 [rm_update] 관련 입주사 정보 삭제: {tenant_result.rowcount}개")
            
            # 실정보 삭제
            room_result = session_obj.execute(delete_room_sql, {
                'prop_id': prop_id,
                'bl_id': bl_id,
                'fl_id': fl_id,
                'rm_id': rm_id
            })
            
            session_obj.commit()
            
            if room_result.rowcount == 0:
                return jsonify({
                    'success': False,
                    'message': '삭제할 실정보를 찾을 수 없습니다.'
                }), 404

        print(f"🟢 [rm_update] 실정보 삭제 완료: {rm_id}")
        
        return jsonify({
            'success': True,
            'message': '실정보가 성공적으로 삭제되었습니다.'
        })

    except Exception as e:
        print(f"🔴 [rm_update] delete_room 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'실정보 삭제 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /rm_update/refresh_tenant_list - 입주사 목록 새로고침 (팝업 창에서 호출) #####
@rm_update_bp.route('/rm_update/refresh_tenant_list', methods=['POST'])
@login_required
def refresh_tenant_list():
    """입주사 등록/수정 후 목록 새로고침을 위한 API"""
    return get_tenant_list()