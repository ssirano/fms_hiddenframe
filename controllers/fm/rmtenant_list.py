import math
from flask import Blueprint, request, jsonify, make_response, json
from controllers.auth import login_required
from sqlalchemy import text
from db import engine, get_session
from datetime import datetime

rmtenant_list_bp = Blueprint('rmtenant_list', __name__)

##### /rmtenant_list/get_bl_list - 건물 목록 조회 #####
@rmtenant_list_bp.route('/rmtenant_list/get_bl_list', methods=['POST'])
@login_required
def get_bl_list():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')

        if not all([em_id, prop_id]):
            return jsonify({
                'success': False,
                'message': '사용자 ID 또는 사업장 ID가 누락되었습니다.'
            }), 400

        # JSP와 동일한 쿼리
        sql = text("""
            SELECT bl_id, name AS bl_name
            FROM bl
            WHERE bl_id IS NOT NULL 
            AND prop_id = :prop_id
            ORDER BY name ASC
        """)

        with get_session() as session_obj:
            result = session_obj.execute(sql, {'prop_id': prop_id}).fetchall()
            bl_list = [dict(row) for row in result]

        return jsonify({
            'success': True,
            'message': '건물 목록 조회 성공',
            'data': bl_list
        })

    except Exception as e:
        print(f"🔴 [rmtenant_list] get_bl_list 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'건물 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /rmtenant_list/get_fl_list - 층 목록 조회 #####
@rmtenant_list_bp.route('/rmtenant_list/get_fl_list', methods=['POST'])
@login_required
def get_fl_list():
    try:
        data = request.get_json()
        prop_id = data.get('prop_id')
        bl_id = data.get('bl_id')

        if not all([prop_id, bl_id]):
            return jsonify({
                'success': False,
                'message': '사업장 ID 또는 건물 ID가 누락되었습니다.'
            }), 400

        # JSP와 동일한 쿼리
        sql = text("""
            SELECT fl_id, name AS fl_name
            FROM fl
            WHERE fl_id IS NOT NULL 
            AND prop_id = :prop_id 
            AND bl_id = :bl_id
            ORDER BY name ASC
        """)

        with get_session() as session_obj:
            result = session_obj.execute(sql, {'prop_id': prop_id, 'bl_id': bl_id}).fetchall()
            fl_list = [dict(row) for row in result]

        return jsonify({
            'success': True,
            'message': '층 목록 조회 성공',
            'data': fl_list
        })

    except Exception as e:
        print(f"🔴 [rmtenant_list] get_fl_list 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'층 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /rmtenant_list/get_rm_list - 실 목록 조회 #####
@rmtenant_list_bp.route('/rmtenant_list/get_rm_list', methods=['POST'])
@login_required
def get_rm_list():
    try:
        data = request.get_json()
        prop_id = data.get('prop_id')
        bl_id = data.get('bl_id')
        fl_id = data.get('fl_id')

        if not all([prop_id, bl_id, fl_id]):
            return jsonify({
                'success': False,
                'message': '사업장 ID, 건물 ID 또는 층 ID가 누락되었습니다.'
            }), 400

        # JSP와 동일한 쿼리
        sql = text("""
            SELECT rm_id, name AS rm_name
            FROM rm
            WHERE bl_id IS NOT NULL 
            AND prop_id = :prop_id 
            AND bl_id = :bl_id 
            AND fl_id = :fl_id
            ORDER BY name ASC
        """)

        with get_session() as session_obj:
            result = session_obj.execute(sql, {
                'prop_id': prop_id, 
                'bl_id': bl_id, 
                'fl_id': fl_id
            }).fetchall()
            rm_list = [dict(row) for row in result]

        return jsonify({
            'success': True,
            'message': '실 목록 조회 성공',
            'data': rm_list
        })

    except Exception as e:
        print(f"🔴 [rmtenant_list] get_rm_list 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'실 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /rmtenant_list/get_rmtenant_data - 입주사 목록 조회 (메인 데이터) #####
@rmtenant_list_bp.route('/rmtenant_list/get_rmtenant_data', methods=['POST'])
@login_required
def get_rmtenant_data():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')
        move_status = data.get('move_status', '입실')  # 기본값 입실
        bl_id_search = data.get('bl_id')
        fl_id_search = data.get('fl_id')
        rm_id_search = data.get('rm_id')
        search_keyword = data.get('keyword')
        page_size = int(data.get('page_size', 20))
        page_number = int(data.get('page_number', 1))
        sort_column = data.get('sort_column', 'bl_id')  # 기본 정렬 컬럼
        sort_direction = data.get('sort_direction', 'ASC')  # 기본 정렬 방향

        print(f"🔵 [rmtenant_list] 입주사 목록 조회 요청: prop_id={prop_id}, move_status={move_status}, bl_id={bl_id_search}, fl_id={fl_id_search}, rm_id={rm_id_search}, keyword={search_keyword}, page={page_number}, size={page_size}, sort={sort_column} {sort_direction}")

        if not all([em_id, prop_id]):
            return jsonify({
                'success': False,
                'message': '사용자 ID 또는 사업장 ID가 누락되었습니다.'
            }), 400

        # JSP와 동일한 기본 쿼리 구조
        base_sql = """
            FROM rmtenant
            WHERE prop_id = :prop_id
        """
        
        # 조건절 추가
        conditions = []
        params = {'em_id': em_id, 'prop_id': prop_id}

        # 입주상태 필터 (JSP 로직과 동일)
        if move_status == '입실':
            conditions.append("move_out IS NULL")  # 퇴실날짜가 없으면 입실
        elif move_status == '퇴실':
            conditions.append("move_out IS NOT NULL")  # 퇴실날짜가 있으면 퇴실
        # '전체'인 경우 조건 추가 안함

        # 건물 필터
        if bl_id_search:
            conditions.append("bl_id = :bl_id_search")
            params['bl_id_search'] = bl_id_search

        # 층 필터
        if fl_id_search:
            conditions.append("fl_id = :fl_id_search")
            params['fl_id_search'] = fl_id_search

        # 실 필터
        if rm_id_search:
            conditions.append("rm_id = :rm_id_search")
            params['rm_id_search'] = rm_id_search

        # 입주사명 검색 (JSP와 동일한 로직 - 공백으로 구분된 여러 키워드 AND 검색)
        if search_keyword:
            keyword_parts = search_keyword.strip().split()
            if keyword_parts:
                keyword_conditions = []
                for i, keyword in enumerate(keyword_parts[:50]):  # 최대 50개까지만
                    if keyword.strip():  # 빈 문자열 제외
                        keyword_conditions.append(f"LOWER(tenant_name) LIKE LOWER(:keyword_{i})")
                        params[f'keyword_{i}'] = f'%{keyword}%'
                
                if keyword_conditions:
                    conditions.append(f"({' AND '.join(keyword_conditions)})")
        
        if conditions:
            base_sql += " AND " + " AND ".join(conditions)

        # 총 개수 조회
        count_sql = text(f"SELECT COUNT(*) {base_sql}")
        
        # 데이터 조회 (JSP와 동일한 컬럼들)
        main_sql = f"""
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
                area_lease_local
            {base_sql}
        """

        # 정렬 조건 (JSP 기본 정렬: bl_id, fl_id, rm_id, rmtenant_id ASC)
        valid_sort_columns = ['bl_id', 'bl_name', 'fl_id', 'fl_name', 'rm_id', 'rm_name', 'tenant_name', 'move_in', 'move_out', 'area_lease_local', 'rmtenant_id']
        if sort_column not in valid_sort_columns:
            sort_column = 'bl_id'  # 기본값
        if sort_direction.upper() not in ['ASC', 'DESC']:
            sort_direction = 'ASC'  # 기본값
        
        # JSP와 동일한 기본 정렬 적용
        order_by_clause = f" ORDER BY bl_id ASC, fl_id ASC, rm_id ASC, rmtenant_id ASC"
        
        # 클라이언트가 특정 컬럼으로 정렬을 요청한 경우 우선 적용
        if sort_column != 'bl_id' or sort_direction.upper() != 'ASC':
            order_by_clause = f" ORDER BY {sort_column} {sort_direction}, bl_id ASC, fl_id ASC, rm_id ASC, rmtenant_id ASC"
        
        main_sql += order_by_clause

        with get_session() as session_obj:
            # 총 개수 실행
            total_count = session_obj.execute(count_sql, params).scalar()

            # 페이지네이션 적용
            offset = (page_number - 1) * page_size
            if page_size != 'All':  # 'All'일 경우 페이지네이션 미적용
                main_sql += f" LIMIT :limit OFFSET :offset"
                params['limit'] = page_size
                params['offset'] = offset
            
            # 메인 데이터 실행
            result = session_obj.execute(text(main_sql), params).fetchall()
            
            rmtenant_data = []
            for row in result:
                item = dict(row)
                # Null 값 처리
                for key, value in item.items():
                    if value is None:
                        item[key] = ''
                rmtenant_data.append(item)

            total_pages = math.ceil(total_count / page_size) if page_size != 'All' and page_size > 0 else 1
            
            response_data = {
                'success': True,
                'message': '입주사 목록 조회 성공',
                'result_data': rmtenant_data,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page_number
            }
            
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.mimetype = 'application/json; charset=utf-8'
            return response

    except Exception as e:
        print(f"🔴 [rmtenant_list] get_rmtenant_data 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'입주사 목록 조회 중 오류가 발생했습니다: {str(e)}',
            'result_data': [],
            'total_count': 0,
            'total_pages': 1,
            'current_page': 1
        }), 500