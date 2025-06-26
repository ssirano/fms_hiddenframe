from flask import Blueprint, request, jsonify, make_response, json
from controllers.auth import login_required  # 👈 추가
from sqlalchemy import text
from db import engine, get_session
from datetime import datetime

fl_update_bp = Blueprint('fl_update', __name__)

##### /getInputTagData - 층정보 조회 #####
@fl_update_bp.route('/fl_update/getInputTagData', methods=['POST'])  # 👈 /fm/ 제거
@login_required
def getInputTagData():
    try:
        data = request.get_json()
        prop_id = data.get('prop_id')
        bl_id = data.get('bl_id')
        fl_id = data.get('fl_id')
        
        print(f"🔵 [fl_update] 층정보 조회 요청: prop_id={prop_id}, bl_id={bl_id}, fl_id={fl_id}")
        
        if not all([prop_id, bl_id, fl_id]):
            return jsonify({
                'success': False, 
                'message': '사업장ID, 건물ID, 층ID가 모두 필요합니다.',
                'data': {}
            })

        # 층 기본 정보 조회
        sql = text("""
            SELECT 
                f.prop_id,
                p.name AS prop_name,
                f.bl_id,
                b.name AS bl_name,
                f.fl_id,
                f.name AS fl_name,
                f.area_fl
            FROM fl f
            LEFT JOIN bl b ON f.bl_id = b.bl_id AND f.prop_id = b.prop_id
            LEFT JOIN prop p ON f.prop_id = p.prop_id
            WHERE f.prop_id = :prop_id 
            AND f.bl_id = :bl_id 
            AND f.fl_id = :fl_id
        """)

        # 입주사 현황 조회
        sql_tenant = text("""
            SELECT DISTINCT tenant_name
            FROM rmtenant rt
            WHERE rt.prop_id = :prop_id 
            AND rt.bl_id = :bl_id 
            AND rt.fl_id = :fl_id
            AND rt.rmtenant_id NOT IN (
                SELECT rmtenant_id 
                FROM rmtenant 
                WHERE prop_id = :prop_id 
                AND bl_id = :bl_id 
                AND fl_id = :fl_id 
                AND (move_in > CURDATE() OR move_out < CURDATE())
            )
            ORDER BY tenant_name
        """)

        with engine.connect() as conn:
            # 기본 층 정보 조회
            row = conn.execute(sql, {
                "prop_id": prop_id, 
                "bl_id": bl_id, 
                "fl_id": fl_id
            }).fetchone()
            
            if not row:
                return jsonify({
                    'success': False, 
                    'message': f'층 정보를 찾을 수 없습니다. (사업장: {prop_id}, 건물: {bl_id}, 층: {fl_id})',
                    'data': {}
                })

            # 입주사 현황 조회
            tenant_rows = conn.execute(sql_tenant, {
                "prop_id": prop_id, 
                "bl_id": bl_id, 
                "fl_id": fl_id
            }).fetchall()
            
            tenant_names = ', '.join([t_row['tenant_name'] for t_row in tenant_rows]) if tenant_rows else ''

            # 결과 데이터 구성
            result_data = dict(row)
            result_data['tenant_names'] = tenant_names

            # None 값들을 빈 문자열로 변환
            for key, value in result_data.items():
                if value is None:
                    result_data[key] = ''

            print(f"🟢 [fl_update] 층정보 조회 완료: {fl_id}")

            result = {
                'success': True, 
                'message': '층 정보 조회 성공',
                'data': result_data
            }
            
            response = make_response(json.dumps(result, ensure_ascii=False))
            response.mimetype = 'application/json; charset=utf-8'
            return response

    except Exception as e:
        print(f"🔴 [fl_update] getInputTagData 오류 발생: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'서버 오류가 발생했습니다: {str(e)}',
            'data': {}
        })

##### /save_fl_data - 층정보 저장 #####
@fl_update_bp.route('/fl_update/save_fl_data', methods=['POST'])
@login_required
def save_fl_data():
    try:
        data = request.get_json()
        prop_id = data.get('prop_id')
        bl_id = data.get('bl_id')
        fl_id = data.get('fl_id')

        print(f"🔵 [fl_update] 층정보 저장 요청: prop_id={prop_id}, bl_id={bl_id}, fl_id={fl_id}")

        if not all([prop_id, bl_id, fl_id]):
            return jsonify({
                'success': False,
                'message': '사업장ID, 건물ID, 층ID가 모두 필요합니다.'
            })

        current_time = datetime.now()

        # 업데이트할 필드 정의 (수정 가능한 필드만)
        fields = ['name', 'area_fl']

        set_clauses = []
        params = {'prop_id': prop_id, 'bl_id': bl_id, 'fl_id': fl_id}

        # 실제로 전송된 데이터만 업데이트
        for field in fields:
            # 프론트엔드 필드명을 DB 필드명으로 매핑
            if field == 'name':
                field_value = data.get('fl_name')
            else:
                field_value = data.get(field)
                
            if field_value is not None:
                set_clauses.append(f"{field} = :{field}")
                params[field] = field_value.strip() if isinstance(field_value, str) else field_value

        # date_modi 컬럼이 테이블에 있다면 항상 현재 시간으로 업데이트
        # 만약 date_modi 컬럼이 없고, 이 부분이 오류를 일으킨다면 이 라인을 주석 처리하거나 제거
        # 또는 DB 스키마에 date_modi 컬럼을 추가하고 NULL 허용 또는 기본값 설정을 고려
        set_clauses.append("date_modi = :date_modi") # 👈 이 부분을 항상 추가하도록 변경하거나, 필요에 따라 조건부로 둠
        params['date_modi'] = current_time

        if len(set_clauses) == 0:
            return jsonify({
                'success': False,
                'message': '업데이트할 데이터가 없습니다.'
            })

        set_sql = ", ".join(set_clauses)

        sql = text(f"""
            UPDATE fl
            SET {set_sql}
            WHERE prop_id = :prop_id
            AND bl_id = :bl_id
            AND fl_id = :fl_id
        """)

        # ⭐️ 이 부분을 get_session()을 사용하는 방식으로 변경해야 합니다.
        with get_session() as session_obj: # 👈 변경: session_obj를 사용
            # 먼저 해당 층이 존재하는지 확인 (기존 로직 유지)
            check_sql = text("""
                SELECT COUNT(*) as cnt
                FROM fl
                WHERE prop_id = :prop_id
                AND bl_id = :bl_id
                AND fl_id = :fl_id
            """)
            check_result = session_obj.execute(check_sql, { # 👈 변경: session_obj 사용
                "prop_id": prop_id,
                "bl_id": bl_id,
                "fl_id": fl_id
            }).fetchone()

            if check_result['cnt'] == 0:
                session_obj.rollback() # 👈 변경: 롤백 추가 (선택 사항이지만 안전)
                return jsonify({
                    'success': False,
                    'message': f'층 정보가 존재하지 않습니다. (사업장: {prop_id}, 건물: {bl_id}, 층: {fl_id})'
                })

            # 업데이트 실행
            result = session_obj.execute(sql, params) # 👈 변경: session_obj 사용
            session_obj.commit() # 👈 변경: session_obj.commit()으로 호출

            if result.rowcount > 0:
                print(f"🟢 [fl_update] 층정보 저장 완료: {fl_id}")
                return jsonify({
                    'success': True,
                    'message': '층 정보가 성공적으로 저장되었습니다.',
                    'updated_fields': list(params.keys())
                })
            else:
                # 변경사항이 없을 경우에도 성공으로 간주할 수 있으나, 여기서는 메시지를 다르게 처리
                print(f"🟡 [fl_update] 층정보 변경사항 없음: {fl_id}")
                return jsonify({
                    'success': True, # 👈 변경: 업데이트할 데이터가 없거나 변경사항이 없어도 성공으로 간주 (또는 False로 조정)
                    'message': '업데이트할 데이터가 없거나 변경사항이 없습니다.'
                })

    except Exception as e:
        # 오류 발생 시 롤백 (with get_session() as session_obj: 사용 시 자동 롤백되거나, 명시적으로 호출 가능)
        # 단, 예외가 발생하면 with 블록이 종료되면서 세션이 자동으로 닫히고 롤백될 가능성이 높음.
        print(f'🔴 [fl_update] save_fl_data 오류 발생: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'데이터 저장 중 오류가 발생했습니다: {str(e)}'
        }), 500
        
##### /check_fl_exists - 층 존재 여부 확인 #####
@fl_update_bp.route('/fl_update/check_fl_exists', methods=['POST'])  # 👈 /fm/ 제거
@login_required
def check_fl_exists():
    """층이 존재하는지 확인하는 API"""
    try:
        data = request.get_json()
        prop_id = data.get('prop_id')
        bl_id = data.get('bl_id')
        fl_id = data.get('fl_id')
        
        if not all([prop_id, bl_id, fl_id]):
            return jsonify({
                'success': False,
                'exists': False,
                'message': '사업장ID, 건물ID, 층ID가 모두 필요합니다.'
            })

        sql = text("""
            SELECT f.prop_id, f.bl_id, f.fl_id, f.name as fl_name,
                   p.name as prop_name, b.name as bl_name
            FROM fl f
            LEFT JOIN bl b ON f.bl_id = b.bl_id AND f.prop_id = b.prop_id
            LEFT JOIN prop p ON f.prop_id = p.prop_id
            WHERE f.prop_id = :prop_id 
            AND f.bl_id = :bl_id 
            AND f.fl_id = :fl_id
        """)

        with engine.connect() as conn:
            row = conn.execute(sql, {
                "prop_id": prop_id, 
                "bl_id": bl_id, 
                "fl_id": fl_id
            }).fetchone()
            
            if row:
                return jsonify({
                    'success': True,
                    'exists': True,
                    'message': '층이 존재합니다.',
                    'data': {
                        'prop_id': row['prop_id'],
                        'prop_name': row['prop_name'],
                        'bl_id': row['bl_id'],
                        'bl_name': row['bl_name'],
                        'fl_id': row['fl_id'],
                        'fl_name': row['fl_name']
                    }
                })
            else:
                return jsonify({
                    'success': True,
                    'exists': False,
                    'message': '해당 층이 존재하지 않습니다.',
                    'data': {}
                })

    except Exception as e:
        print(f'🔴 [fl_update] check_fl_exists 오류 발생: {str(e)}')
        return jsonify({
            'success': False,
            'exists': False,
            'message': f'층 확인 중 오류가 발생했습니다: {str(e)}'
        }) 