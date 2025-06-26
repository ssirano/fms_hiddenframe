import math
from flask import Blueprint, request, jsonify, make_response, json
from controllers.auth import login_required
from sqlalchemy import text
from db import engine, get_session
from datetime import datetime

rm_insert_bp = Blueprint('rm_insert', __name__)

##### /rm_insert/get_prop_list - 사업장 목록 조회 #####
@rm_insert_bp.route('/rm_insert/get_prop_list', methods=['POST'])
@login_required
def get_prop_list():
    try:
        data = request.get_json()
        em_id = data.get('em_id')

        if not em_id:
            return jsonify({
                'success': False,
                'message': '사용자 ID가 누락되었습니다.'
            }), 400

        # JSP와 동일한 쿼리 - emcontrol 권한 체크 포함
        sql = text("""
            SELECT prop_id, name AS prop_name
            FROM prop 
            WHERE prop_id IN (
                SELECT prop_id FROM emcontrol 
                WHERE em_id = :em_id
            )
            ORDER BY name ASC
        """)

        with get_session() as session_obj:
            result = session_obj.execute(sql, {'em_id': em_id}).fetchall()
            prop_list = [dict(row) for row in result]

        return jsonify({
            'success': True,
            'message': '사업장 목록 조회 성공',
            'data': prop_list
        })

    except Exception as e:
        print(f"🔴 [rm_insert] get_prop_list 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'사업장 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /rm_insert/check_duplicate - 실코드 중복 체크 #####
@rm_insert_bp.route('/rm_insert/check_duplicate', methods=['POST'])
@login_required
def check_duplicate():
    try:
        data = request.get_json()
        prop_id = data.get('prop_id')
        bl_id = data.get('bl_id')
        fl_id = data.get('fl_id')
        rm_id = data.get('rm_id')

        print(f"🔵 [rm_insert] 중복 체크 요청: prop_id={prop_id}, bl_id={bl_id}, fl_id={fl_id}, rm_id={rm_id}")

        if not all([prop_id, bl_id, fl_id, rm_id]):
            return jsonify({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다.'
            }), 400

        # 중복 체크 쿼리
        sql = text("""
            SELECT COUNT(*) as cnt
            FROM rm
            WHERE prop_id = :prop_id 
            AND bl_id = :bl_id 
            AND fl_id = :fl_id 
            AND rm_id = :rm_id
        """)

        with get_session() as session_obj:
            count = session_obj.execute(sql, {
                'prop_id': prop_id,
                'bl_id': bl_id,
                'fl_id': fl_id,
                'rm_id': rm_id
            }).scalar()
            
            isDuplicate = count > 0

        print(f"🟢 [rm_insert] 중복 체크 완료: {rm_id} - {'중복' if isDuplicate else '사용가능'}")
        
        return jsonify({
            'success': True,
            'message': '중복 체크 완료',
            'isDuplicate': isDuplicate
        })

    except Exception as e:
        print(f"🔴 [rm_insert] check_duplicate 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'중복 체크 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /rm_insert/save_room - 실정보 저장 #####
@rm_insert_bp.route('/rm_insert/save_room', methods=['POST'])
@login_required
def save_room():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')
        bl_id = data.get('bl_id')
        fl_id = data.get('fl_id')
        rm_id = data.get('rm_id')
        rm_name = data.get('rm_name', '').strip()

        print(f"🔵 [rm_insert] 실정보 저장 요청: prop_id={prop_id}, bl_id={bl_id}, fl_id={fl_id}, rm_id={rm_id}, rm_name={rm_name}")

        if not all([em_id, prop_id, bl_id, fl_id, rm_id, rm_name]):
            return jsonify({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다.'
            }), 400

        # 중복 체크 먼저 수행
        duplicate_sql = text("""
            SELECT COUNT(*) as cnt
            FROM rm
            WHERE prop_id = :prop_id 
            AND bl_id = :bl_id 
            AND fl_id = :fl_id 
            AND rm_id = :rm_id
        """)

        # 실정보 저장 쿼리 (rm 테이블 구조에 맞게 - 기본 컬럼만)
        insert_sql = text("""
            INSERT INTO rm (prop_id, bl_id, fl_id, rm_id, name)
            VALUES (:prop_id, :bl_id, :fl_id, :rm_id, :rm_name)
        """)

        with get_session() as session_obj:
            # 중복 체크
            duplicate_count = session_obj.execute(duplicate_sql, {
                'prop_id': prop_id,
                'bl_id': bl_id,
                'fl_id': fl_id,
                'rm_id': rm_id
            }).scalar()
            
            if duplicate_count > 0:
                return jsonify({
                    'success': False,
                    'message': '이미 존재하는 실코드입니다.'
                }), 400
            
            # 실정보 저장
            result = session_obj.execute(insert_sql, {
                'prop_id': prop_id,
                'bl_id': bl_id,
                'fl_id': fl_id,
                'rm_id': rm_id,
                'rm_name': rm_name
            })
            
            session_obj.commit()
            
            if result.rowcount == 0:
                return jsonify({
                    'success': False,
                    'message': '실정보 저장에 실패했습니다.'
                }), 500

        print(f"🟢 [rm_insert] 실정보 저장 완료: {rm_id}")
        
        return jsonify({
            'success': True,
            'message': '실정보가 성공적으로 저장되었습니다.'
        })

    except Exception as e:
        print(f"🔴 [rm_insert] save_room 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'실정보 저장 중 오류가 발생했습니다: {str(e)}'
        }), 500 