import math
from flask import Blueprint, request, jsonify, make_response, json
from controllers.auth import login_required
from sqlalchemy import text
from db import engine, get_session
from datetime import datetime

rmtenant_update_bp = Blueprint('rmtenant_update', __name__)

##### /rmtenant_update/get_tenant_data - 입주사 정보 조회 #####
@rmtenant_update_bp.route('/rmtenant_update/get_tenant_data', methods=['POST'])
@login_required
def get_tenant_data():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        rmtenant_id = data.get('rmtenant_id')

        print(f"🔵 [rmtenant_update] 입주사 정보 조회 요청: em_id={em_id}, rmtenant_id={rmtenant_id}")

        if not all([em_id, rmtenant_id]):
            return jsonify({
                'success': False,
                'message': '사용자 ID 또는 입주사 ID가 누락되었습니다.'
            }), 400

        # JSP와 동일한 쿼리 - rmtenant 테이블에서 모든 정보 조회
        sql = text("""
            SELECT 
                rmtenant_id, 
                tenant_name, 
                prop_id, 
                bl_id, 
                bl_name, 
                fl_id, 
                fl_name, 
                rm_id, 
                rm_name, 
                comments, 
                em_reg, 
                TO_CHAR(date_reg, 'YYYY-MM-DD') AS date_reg, 
                TO_CHAR(move_in, 'YYYY-MM-DD') AS move_in, 
                TO_CHAR(move_out, 'YYYY-MM-DD') AS move_out, 
                area_rm, 
                area_rm_local, 
                area_contract, 
                area_contract_local, 
                area_lease, 
                area_lease_local
            FROM rmtenant
            WHERE rmtenant_id = :rmtenant_id
        """)

        with get_session() as session_obj:
            result = session_obj.execute(sql, {'rmtenant_id': rmtenant_id}).fetchone()
            
            if not result:
                return jsonify({
                    'success': False,
                    'message': '해당 입주사 정보를 찾을 수 없습니다.'
                }), 404
            
            tenant_data = dict(result)
            
            # Null 값 처리
            for key, value in tenant_data.items():
                if value is None:
                    tenant_data[key] = ''

        print(f"🟢 [rmtenant_update] 입주사 정보 조회 완료: {rmtenant_id}")
        
        return jsonify({
            'success': True,
            'message': '입주사 정보 조회 성공',
            'data': tenant_data
        })

    except Exception as e:
        print(f"🔴 [rmtenant_update] get_tenant_data 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'입주사 정보 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /rmtenant_update/save_tenant - 입주사 정보 저장 #####
@rmtenant_update_bp.route('/rmtenant_update/save_tenant', methods=['POST'])
@login_required
def save_tenant():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        rmtenant_id = data.get('rmtenant_id')
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

        print(f"🔵 [rmtenant_update] 입주사 저장 요청: rmtenant_id={rmtenant_id}, tenant_name={tenant_name}, bl_id={bl_id}, fl_id={fl_id}")

        # JSP와 동일한 유효성 검사
        if not all([em_id, rmtenant_id, tenant_name, bl_id, fl_id]):
            return jsonify({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다. (사용자ID, 입주사ID, 입주사명, 건물, 층)'
            }), 400

        # 날짜 처리 (빈 값은 NULL로 변환)
        move_in_param = move_in if move_in else None
        move_out_param = move_out if move_out else None

        # 면적 필드 처리 (빈 값은 NULL로 변환)
        area_rm_param = float(area_rm) if area_rm and area_rm.replace('.', '').isdigit() else None
        area_rm_local_param = float(area_rm_local) if area_rm_local and area_rm_local.replace('.', '').isdigit() else None
        area_contract_param = float(area_contract) if area_contract and area_contract.replace('.', '').isdigit() else None
        area_contract_local_param = float(area_contract_local) if area_contract_local and area_contract_local.replace('.', '').isdigit() else None
        area_lease_param = float(area_lease) if area_lease and area_lease.replace('.', '').isdigit() else None
        area_lease_local_param = float(area_lease_local) if area_lease_local and area_lease_local.replace('.', '').isdigit() else None

        # 입주사 정보 업데이트 쿼리
        update_sql = text("""
            UPDATE rmtenant SET
                tenant_name = :tenant_name,
                bl_id = :bl_id,
                fl_id = :fl_id,
                rm_id = :rm_id,
                move_in = :move_in,
                move_out = :move_out,
                area_rm = :area_rm,
                area_rm_local = :area_rm_local,
                area_contract = :area_contract,
                area_contract_local = :area_contract_local,
                area_lease = :area_lease,
                area_lease_local = :area_lease_local,
                comments = :comments
            WHERE rmtenant_id = :rmtenant_id
        """)

        with get_session() as session_obj:
            result = session_obj.execute(update_sql, {
                'rmtenant_id': rmtenant_id,
                'tenant_name': tenant_name,
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
                'comments': comments
            })
            
            session_obj.commit()
            
            if result.rowcount == 0:
                return jsonify({
                    'success': False,
                    'message': '업데이트할 입주사 정보를 찾을 수 없습니다.'
                }), 404

        print(f"🟢 [rmtenant_update] 입주사 저장 완료: {rmtenant_id}")
        
        return jsonify({
            'success': True,
            'message': '입주사 정보가 성공적으로 수정되었습니다.'
        })

    except Exception as e:
        print(f"🔴 [rmtenant_update] save_tenant 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'입주사 정보 저장 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /rmtenant_update/delete_tenant - 입주사 정보 삭제 #####
@rmtenant_update_bp.route('/rmtenant_update/delete_tenant', methods=['POST'])
@login_required
def delete_tenant():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        rmtenant_id = data.get('rmtenant_id')

        print(f"🔵 [rmtenant_update] 입주사 삭제 요청: em_id={em_id}, rmtenant_id={rmtenant_id}")

        if not all([em_id, rmtenant_id]):
            return jsonify({
                'success': False,
                'message': '사용자 ID 또는 입주사 ID가 누락되었습니다.'
            }), 400

        # 입주사 정보 삭제 쿼리
        delete_sql = text("""
            DELETE FROM rmtenant
            WHERE rmtenant_id = :rmtenant_id
        """)

        with get_session() as session_obj:
            result = session_obj.execute(delete_sql, {
                'rmtenant_id': rmtenant_id
            })
            
            session_obj.commit()
            
            if result.rowcount == 0:
                return jsonify({
                    'success': False,
                    'message': '삭제할 입주사 정보를 찾을 수 없습니다.'
                }), 404

        print(f"🟢 [rmtenant_update] 입주사 삭제 완료: {rmtenant_id}")
        
        return jsonify({
            'success': True,
            'message': '입주사 정보가 성공적으로 삭제되었습니다.'
        })

    except Exception as e:
        print(f"🔴 [rmtenant_update] delete_tenant 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'입주사 정보 삭제 중 오류가 발생했습니다: {str(e)}'
        }), 500