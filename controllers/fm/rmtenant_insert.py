import math
from flask import Blueprint, request, jsonify, make_response, json
from controllers.auth import login_required
from sqlalchemy import text
from db import engine, get_session
from datetime import datetime

rmtenant_insert_bp = Blueprint('rmtenant_insert', __name__)

##### /rmtenant_insert/save_tenant - 입주사 정보 등록 #####
@rmtenant_insert_bp.route('/rmtenant_insert/save_tenant', methods=['POST'])
@login_required
def save_tenant():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')
        tenant_name = data.get('tenant_name', '').strip()
        bl_id = data.get('bl_id')
        fl_id = data.get('fl_id')
        rm_id = data.get('rm_id')
        move_in = data.get('move_in')
        move_out = data.get('move_out')
        area_rm = data.get('area_rm', '')
        area_rm_local = data.get('area_rm_local', '')
        area_contract = data.get('area_contract', '')
        area_contract_local = data.get('area_contract_local', '')
        area_lease = data.get('area_lease', '')
        area_lease_local = data.get('area_lease_local', '')
        comments = data.get('comments', '')

        print(f"🔵 [rmtenant_insert] 입주사 등록 요청: tenant_name={tenant_name}, bl_id={bl_id}, fl_id={fl_id}")

        # JSP와 동일한 유효성 검사
        if not all([em_id, prop_id, tenant_name, bl_id, fl_id]):
            return jsonify({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다. (사용자ID, 사업장ID, 입주사명, 건물, 층)'
            }), 400

        # 날짜 처리 (빈 값은 NULL로 변환)
        move_in_param = move_in if move_in else None
        move_out_param = move_out if move_out else None

        # 면적 필드 처리 (빈 값은 NULL로 변환)
        area_rm_param = float(area_rm) if area_rm and area_rm.replace('.', '').replace(',', '').isdigit() else None
        area_rm_local_param = float(area_rm_local) if area_rm_local and area_rm_local.replace('.', '').replace(',', '').isdigit() else None
        area_contract_param = float(area_contract) if area_contract and area_contract.replace('.', '').replace(',', '').isdigit() else None
        area_contract_local_param = float(area_contract_local) if area_contract_local and area_contract_local.replace('.', '').replace(',', '').isdigit() else None
        area_lease_param = float(area_lease) if area_lease and area_lease.replace('.', '').replace(',', '').isdigit() else None
        area_lease_local_param = float(area_lease_local) if area_lease_local and area_lease_local.replace('.', '').replace(',', '').isdigit() else None

        # RMTENANT_ID 생성을 위한 최대값 조회
        max_id_sql = text("""
            SELECT COALESCE(MAX(RMTENANT_ID), 0) + 1 as next_id 
            FROM rmtenant
        """)

        with get_session() as session_obj:
            # 다음 ID 값 조회
            next_id = session_obj.execute(max_id_sql).scalar()
            
            # 입주사 정보 등록 쿼리 (RMTENANT_ID 포함, MySQL 호환성)
            insert_sql = text("""
                INSERT INTO rmtenant (
                    rmtenant_id,
                    tenant_name,
                    prop_id,
                    bl_id,
                    bl_name,
                    fl_id,
                    fl_name,
                    rm_id,
                    rm_name,
                    move_in,
                    move_out,
                    area_rm,
                    area_rm_local,
                    area_contract,
                    area_contract_local,
                    area_lease,
                    area_lease_local,
                    comments,
                    date_reg,
                    em_reg
                ) VALUES (
                    :rmtenant_id,
                    :tenant_name,
                    :prop_id,
                    :bl_id,
                    (SELECT name FROM bl WHERE bl_id = :bl_id AND prop_id = :prop_id),
                    :fl_id,
                    (SELECT name FROM fl WHERE fl_id = :fl_id AND bl_id = :bl_id AND prop_id = :prop_id),
                    :rm_id,
                    CASE WHEN :rm_id IS NOT NULL THEN 
                        (SELECT name FROM rm WHERE rm_id = :rm_id AND fl_id = :fl_id AND bl_id = :bl_id AND prop_id = :prop_id)
                    ELSE NULL END,
                    :move_in,
                    :move_out,
                    :area_rm,
                    :area_rm_local,
                    :area_contract,
                    :area_contract_local,
                    :area_lease,
                    :area_lease_local,
                    :comments,
                    NOW(),
                    :em_id
                )
            """)

        with get_session() as session_obj:
            # 다음 ID 값 조회
            next_id = session_obj.execute(max_id_sql).scalar()
            
            # 입주사 정보 등록 쿼리 (RMTENANT_ID 포함, MySQL 호환성)
            insert_sql = text("""
                INSERT INTO rmtenant (
                    rmtenant_id,
                    tenant_name,
                    prop_id,
                    bl_id,
                    bl_name,
                    fl_id,
                    fl_name,
                    rm_id,
                    rm_name,
                    move_in,
                    move_out,
                    area_rm,
                    area_rm_local,
                    area_contract,
                    area_contract_local,
                    area_lease,
                    area_lease_local,
                    comments,
                    date_reg,
                    em_reg
                ) VALUES (
                    :rmtenant_id,
                    :tenant_name,
                    :prop_id,
                    :bl_id,
                    (SELECT name FROM bl WHERE bl_id = :bl_id AND prop_id = :prop_id),
                    :fl_id,
                    (SELECT name FROM fl WHERE fl_id = :fl_id AND bl_id = :bl_id AND prop_id = :prop_id),
                    :rm_id,
                    CASE WHEN :rm_id IS NOT NULL THEN 
                        (SELECT name FROM rm WHERE rm_id = :rm_id AND fl_id = :fl_id AND bl_id = :bl_id AND prop_id = :prop_id)
                    ELSE NULL END,
                    :move_in,
                    :move_out,
                    :area_rm,
                    :area_rm_local,
                    :area_contract,
                    :area_contract_local,
                    :area_lease,
                    :area_lease_local,
                    :comments,
                    NOW(),
                    :em_id
                )
            """)

            result = session_obj.execute(insert_sql, {
                'rmtenant_id': next_id,
                'tenant_name': tenant_name,
                'prop_id': prop_id,
                'bl_id': bl_id,
                'fl_id': fl_id,
                'rm_id': rm_id if rm_id else None,
                'move_in': move_in_param,
                'move_out': move_out_param,
                'area_rm': area_rm_param,
                'area_rm_local': area_rm_local_param,
                'area_contract': area_contract_param,
                'area_contract_local': area_contract_local_param,
                'area_lease': area_lease_param,
                'area_lease_local': area_lease_local_param,
                'comments': comments,
                'em_id': em_id
            })
            
            session_obj.commit()
            
            if result.rowcount == 0:
                return jsonify({
                    'success': False,
                    'message': '입주사 정보 등록에 실패했습니다.'
                }), 500

        print(f"🟢 [rmtenant_insert] 입주사 등록 완료: {tenant_name}")
        
        return jsonify({
            'success': True,
            'message': '입주사 정보가 성공적으로 등록되었습니다.'
        })

    except Exception as e:
        print(f"🔴 [rmtenant_insert] save_tenant 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'입주사 정보 등록 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /rmtenant_insert/check_duplicate - 입주사명 중복 체크 (선택사항) #####
@rmtenant_insert_bp.route('/rmtenant_insert/check_duplicate', methods=['POST'])
@login_required
def check_duplicate():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')
        tenant_name = data.get('tenant_name', '').strip()
        bl_id = data.get('bl_id')
        fl_id = data.get('fl_id')
        rm_id = data.get('rm_id')

        print(f"🔵 [rmtenant_insert] 중복 체크 요청: tenant_name={tenant_name}, bl_id={bl_id}, fl_id={fl_id}, rm_id={rm_id}")

        if not all([em_id, prop_id, tenant_name]):
            return jsonify({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다.'
            }), 400

        # 같은 건물/층/실에 같은 입주사명이 있는지 체크
        base_conditions = "prop_id = :prop_id AND tenant_name = :tenant_name"
        params = {
            'prop_id': prop_id,
            'tenant_name': tenant_name
        }

        # 건물, 층, 실 조건 추가 (선택적)
        if bl_id:
            base_conditions += " AND bl_id = :bl_id"
            params['bl_id'] = bl_id
        if fl_id:
            base_conditions += " AND fl_id = :fl_id"
            params['fl_id'] = fl_id
        if rm_id:
            base_conditions += " AND rm_id = :rm_id"
            params['rm_id'] = rm_id

        # 현재 입실중인 입주사만 체크 (퇴실일이 없거나 미래인 경우) - MySQL 호환성 수정
        base_conditions += " AND (move_out IS NULL OR move_out >= NOW())"

        sql = text(f"""
            SELECT COUNT(*) as cnt
            FROM rmtenant
            WHERE {base_conditions}
        """)

        with get_session() as session_obj:
            count = session_obj.execute(sql, params).scalar()
            
            isDuplicate = count > 0

        print(f"🟢 [rmtenant_insert] 중복 체크 완료: {tenant_name} - {'중복' if isDuplicate else '사용가능'}")
        
        return jsonify({
            'success': True,
            'message': '중복 체크 완료',
            'isDuplicate': isDuplicate,
            'duplicateMessage': f'해당 위치에 이미 "{tenant_name}" 입주사가 있습니다.' if isDuplicate else None
        })

    except Exception as e:
        print(f"🔴 [rmtenant_insert] check_duplicate 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'중복 체크 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /rmtenant_insert/get_prop_list - 사업장 목록 조회 (필요시) #####
@rmtenant_insert_bp.route('/rmtenant_insert/get_prop_list', methods=['POST'])
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
        print(f"🔴 [rmtenant_insert] get_prop_list 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'사업장 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500