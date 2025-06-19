from flask import Blueprint, request, jsonify, make_response, json
from controllers.auth import login_required
from sqlalchemy import text
from db import engine
from utils.common_functions import build_query_conditions

common_bp = Blueprint('common', __name__)

@common_bp.route('/getValue', methods=['POST'])
@common_bp.route('/getValue_wrtype_id', methods=['POST'])
@common_bp.route('/getValue_prob_id', methods=['POST'])
@common_bp.route('/getValue_bl_id', methods=['POST'])
@common_bp.route('/getValue_caus_id', methods=['POST'])
@common_bp.route('/getValue_emclass_id', methods=['POST'])
@common_bp.route('/getValue_repr_id', methods=['POST'])
@login_required
def getValue():
    """공통 셀렉트 옵션 데이터 조회"""
    try:
        request_data = request.get_json()
        table = request_data.get('collection')
        id_field = request_data.get('id_field')
        text_field = request_data.get('text_field')
        sort_field = request_data.get('sort_field')
        
        # 동적 조건 구성
        conditions = {
            'findKey_01': request_data.get('findVal_01') if request_data.get('findKey_01') else None,
            'findKey_02': request_data.get('findVal_02') if request_data.get('findKey_02') else None,
        }
        
        where_conditions, params = build_query_conditions(conditions)
        
        where_sql = ""
        if where_conditions:
            where_sql = "WHERE " + " AND ".join(where_conditions)

        sort_sql = f"ORDER BY {sort_field}" if sort_field else ""

        sql = text(f"""
            SELECT {id_field}, {text_field} 
            FROM {table}
            {where_sql}
            {sort_sql}
        """)

        with engine.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            result_data = [{id_field: row[id_field], text_field: row[text_field]} for row in rows]

        result = {'success': True, 'data': result_data}
        response = make_response(json.dumps(result, ensure_ascii=False))
        response.mimetype = 'application/json; charset=utf-8'
        return response

    except Exception as e:
        print(f"getValue 오류 발생: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@common_bp.route('/getValueDistinct', methods=['POST'])
@common_bp.route('/getValueDistinct_wrtype_id', methods=['POST'])
@login_required
def getValueDistinct():
    """중복 제거된 셀렉트 옵션 데이터 조회"""
    try:
        request_data = request.get_json()
        table = request_data.get('collection')
        id_field = request_data.get('id_field')
        
        # 동적 조건 구성
        conditions = {
            'findKey_01': request_data.get('findVal_01') if request_data.get('findKey_01') else None,
            'findKey_02': request_data.get('findVal_02') if request_data.get('findKey_02') else None,
        }
        
        where_conditions, params = build_query_conditions(conditions)
        
        where_sql = ""
        if where_conditions:
            where_sql = "WHERE " + " AND ".join(where_conditions)

        sql = text(f"""
            SELECT DISTINCT {id_field}
            FROM {table}
            {where_sql}
        """)

        with engine.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            result_data = [{id_field: row[id_field]} for row in rows]

        result = {'success': True, 'data': result_data}
        response = make_response(json.dumps(result, ensure_ascii=False))
        response.mimetype = 'application/json; charset=utf-8'
        return response

    except Exception as e:
        print(f"getValueDistinct 오류 발생: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@common_bp.route('/get_uncompleted_count', methods=['POST'])
@login_required
def get_uncompleted_count():
    """미완료 건수 조회"""
    try:
        request_data = request.get_json()
        table = request_data.get('collection')
        
        # 동적 조건 구성
        conditions = {
            'findKey_01': request_data.get('findVal_01') if request_data.get('findKey_01') else None,
            'findKey_02': request_data.get('findVal_02') if request_data.get('findKey_02') else None,
        }
        
        where_conditions, params = build_query_conditions(conditions)
        
        where_sql = ""
        if where_conditions:
            where_sql = "WHERE " + " AND ".join(where_conditions)

        sql = text(f"""
            SELECT COUNT(*) AS cnt
            FROM {table}
            {where_sql}
        """)

        with engine.connect() as conn:
            row = conn.execute(sql, params).fetchone()
            uncompleted_count = row['cnt']

        return jsonify({"success": True, "uncompleted_count": uncompleted_count})

    except Exception as e:
        print(f"get_uncompleted_count 오류 발생: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@common_bp.route('/get_bl_list', methods=['POST'])
@login_required
def get_bl_list():
    """건물 목록 조회 - 권한 기반"""
    try:
        request_data = request.get_json()
        em_id = request_data.get('em_id')
        prop_id = request_data.get('prop_id')
        bl_id = request_data.get('bl_id')  # optional
        
        print(f"🔵 get_bl_list 요청: em_id={em_id}, prop_id={prop_id}, bl_id={bl_id}")
        
        with engine.connect() as conn:
            if prop_id:
                # prop_id가 있는 경우: 권한 확인 후 해당 사업장의 건물만 조회
                auth_check_query = text("""
                    SELECT COUNT(*) as cnt
                    FROM emcontrol ec
                    WHERE ec.em_id = :em_id AND ec.prop_id = :prop_id
                """)
                auth_result = conn.execute(auth_check_query, {"em_id": em_id, "prop_id": prop_id}).fetchone()
                
                if not auth_result or auth_result['cnt'] == 0:
                    print(f"🟡 권한 없음, 빈 배열 반환: em_id={em_id}, prop_id={prop_id}")
                    return jsonify({'success': True, 'data': []})
                
                # 해당 prop_id의 건물 목록 조회
                base_query = """
                    SELECT b.bl_id, b.name AS bl_name
                    FROM bl b
                    WHERE b.prop_id = :prop_id
                """
                params = {'prop_id': prop_id}
                
                if bl_id:
                    base_query += " AND b.bl_id = :bl_id"
                    params['bl_id'] = bl_id
                
                base_query += " ORDER BY b.bl_id ASC"
                
            else:
                # prop_id가 없는 경우: emcontrol에서 직접 조회
                base_query = """
                    SELECT DISTINCT ec.bl_id, b.name AS bl_name
                    FROM emcontrol ec
                    JOIN bl b ON ec.bl_id = b.bl_id
                    WHERE ec.em_id = :em_id
                """
                params = {'em_id': em_id}
                
                if bl_id:
                    base_query += " AND ec.bl_id = :bl_id"
                    params['bl_id'] = bl_id
                
                base_query += " ORDER BY ec.bl_id ASC"
            
            result_rows = conn.execute(text(base_query), params).fetchall()
            result_data = [
                {"bl_id": row['bl_id'], "bl_name": row['bl_name']}
                for row in result_rows
            ]
            
            print(f"🟢 건물 목록 조회 결과: {len(result_data)}개")

            result = {'success': True, 'data': result_data}
            response = make_response(json.dumps(result, ensure_ascii=False))
            response.mimetype = 'application/json; charset=utf-8'
            return response

    except Exception as e:
        print(f"🔴 건물 목록 조회 중 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': '건물 목록을 가져오는 중 오류가 발생했습니다.'
        })

@common_bp.route('/get_select_options', methods=['POST'])
@login_required
def get_select_options():
    """범용 셀렉트 옵션 조회 API"""
    try:
        request_data = request.get_json()
        table = request_data.get('table')
        id_field = request_data.get('id_field')
        text_field = request_data.get('text_field')
        conditions = request_data.get('conditions', {})
        order_by = request_data.get('order_by')
        
        if not table or not id_field or not text_field:
            return jsonify({'success': False, 'message': '필수 파라미터가 누락되었습니다.'})
        
        where_conditions, params = build_query_conditions(conditions)
        
        base_query = f"SELECT {id_field}, {text_field} FROM {table}"
        
        if where_conditions:
            base_query += " WHERE " + " AND ".join(where_conditions)
        
        if order_by:
            base_query += f" ORDER BY {order_by}"
        
        with engine.connect() as conn:
            rows = conn.execute(text(base_query), params).fetchall()
            result_data = [
                {"id": row[id_field], "text": row[text_field]} 
                for row in rows
            ]
        
        result = {'success': True, 'data': result_data}
        response = make_response(json.dumps(result, ensure_ascii=False))
        response.mimetype = 'application/json; charset=utf-8'
        return response
    
    except Exception as e:
        print(f"get_select_options 오류 발생: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})