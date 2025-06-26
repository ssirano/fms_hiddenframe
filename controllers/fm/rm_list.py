import math
from flask import Blueprint, request, jsonify, make_response, json
from controllers.auth import login_required
from sqlalchemy import text
from db import engine, get_session # get_session 추가
from datetime import datetime

rm_list_bp = Blueprint('rm_list', __name__)

##### /rm_list/get_bl_list - 건물 목록 조회 (fl_list에서 재활용) #####
@rm_list_bp.route('/rm_list/get_bl_list', methods=['POST'])
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

        # JSP와 동일한 쿼리로 변경 (emcontrol 체크 제거)
        sql = text("""
            SELECT bl_id, name AS bl_name
            FROM bl
            WHERE prop_id = :prop_id
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
        print(f"🔴 [rm_list] get_bl_list 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'건물 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500
        
##### /rm_list/get_fl_list - 층 목록 조회 (bl_id 기준) #####
@rm_list_bp.route('/rm_list/get_fl_list', methods=['POST'])
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

        # JSP와 동일한 쿼리로 변경
        sql = text("""
            SELECT fl_id, name AS fl_name
            FROM fl
            WHERE prop_id = :prop_id AND bl_id = :bl_id
            ORDER BY fl_id, name ASC
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
        print(f"🔴 [rm_list] get_fl_list 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'층 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500


##### /rm_list/get_rm_data - 실 목록 조회 (메인 데이터) #####
@rm_list_bp.route('/rm_list/get_rm_data', methods=['POST'])
@login_required
def get_rm_data():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')
        bl_id_search = data.get('bl_id')
        fl_id_search = data.get('fl_id')
        search_keyword = data.get('keyword')
        page_size = int(data.get('page_size', 10))
        page_number = int(data.get('page_number', 1))
        sort_column = data.get('sort_column', 'prop_id') # 기본 정렬 컬럼
        sort_direction = data.get('sort_direction', 'ASC') # 기본 정렬 방향

        print(f"🔵 [rm_list] 실 목록 조회 요청: prop_id={prop_id}, bl_id={bl_id_search}, fl_id={fl_id_search}, keyword={search_keyword}, page={page_number}, size={page_size}, sort={sort_column} {sort_direction}")

        if not all([em_id, prop_id]):
            return jsonify({
                'success': False,
                'message': '사용자 ID 또는 사업장 ID가 누락되었습니다.'
            }), 400

        # 기본 쿼리 (JOIN을 통해 필요한 이름 정보 미리 가져오기)
        base_sql = """
            FROM rm r
            LEFT JOIN prop p ON r.prop_id = p.prop_id
            LEFT JOIN bl b ON r.bl_id = b.bl_id AND r.prop_id = b.prop_id
            LEFT JOIN fl f ON r.fl_id = f.fl_id AND r.bl_id = f.bl_id AND r.prop_id = f.prop_id
            WHERE r.rm_id IS NOT NULL
            AND r.prop_id IN ( SELECT prop_id FROM emcontrol WHERE em_id = :em_id AND prop_id = :prop_id )
        """
        
        # 조건절 추가
        conditions = []
        params = {'em_id': em_id, 'prop_id': prop_id}

        if bl_id_search:
            conditions.append("r.bl_id = :bl_id_search")
            params['bl_id_search'] = bl_id_search
        if fl_id_search:
            conditions.append("r.fl_id = :fl_id_search")
            params['fl_id_search'] = fl_id_search
        if search_keyword:
            conditions.append("(LOWER(r.rm_id) LIKE LOWER(:keyword) OR LOWER(r.name) LIKE LOWER(:keyword) OR LOWER(p.name) LIKE LOWER(:keyword) OR LOWER(b.name) LIKE LOWER(:keyword) OR LOWER(f.name) LIKE LOWER(:keyword))")
            params['keyword'] = f'%{search_keyword}%'
        
        if conditions:
            base_sql += " AND " + " AND ".join(conditions)

        # 총 개수 조회
        count_sql = text(f"SELECT COUNT(*) {base_sql}")
        
        # 데이터 조회
        # tenant_name을 가져오는 부분은 서브쿼리 또는 별도 조인으로 처리해야 함
        # 여기서는 JSP의 로직을 따라 DISTINCT tenant_name을 콤마로 연결
        main_sql = f"""
            SELECT
                r.prop_id, p.name AS prop_name,
                r.bl_id, b.name AS bl_name,
                r.fl_id, f.name AS fl_name,
                r.rm_id, r.name AS rm_name,
                (
                    SELECT GROUP_CONCAT(DISTINCT rt.tenant_name ORDER BY rt.tenant_name ASC SEPARATOR ', ')
                    FROM rmtenant rt
                    WHERE rt.prop_id = r.prop_id
                    AND rt.bl_id = r.bl_id
                    AND rt.fl_id = r.fl_id
                    AND rt.rm_id = r.rm_id
                    AND rt.rmtenant_id NOT IN (
                        SELECT rmtenant_id FROM rmtenant
                        WHERE prop_id = r.prop_id AND bl_id = r.bl_id AND fl_id = r.fl_id AND rm_id = r.rm_id
                        AND (move_in > CURDATE() OR move_out < CURDATE())
                    )
                ) AS tenant_names
            {base_sql}
        """

        # 정렬 조건
        # 클라이언트에서 보낸 sort_column에 따라 정렬, 기본은 prop_id, bl_id, fl_id, rm_id 오름차순
        valid_sort_columns = ['prop_id', 'prop_name', 'bl_id', 'bl_name', 'fl_id', 'fl_name', 'rm_id', 'rm_name', 'tenant_names']
        if sort_column not in valid_sort_columns:
            sort_column = 'prop_id' # 기본값
        if sort_direction.upper() not in ['ASC', 'DESC']:
            sort_direction = 'ASC' # 기본값
        
        # JSP 코드에 기본 정렬이 prop_id, bl_id, fl_id, rm_id ASC로 되어있음.
        # DefSorting 파라미터가 "4"가 아니면 이 기본 정렬이 적용됨.
        # 여기서는 단일 sort_column/direction만 받도록 간소화하거나,
        # DefSorting과 같이 여러 컬럼을 복합적으로 정렬할 수 있도록 구현해야 함.
        # 우선은 단일 정렬을 따르도록 구현.
        # 복합 정렬이 필요하다면 아래 ORDER BY 구문을 조정해야 합니다.
        order_by_clause = f" ORDER BY {sort_column} {sort_direction}"
        # 만약 DefSorting과 같은 복합정렬이 항상 우선이라면:
        # order_by_clause = " ORDER BY r.prop_id, r.bl_id, r.fl_id, r.rm_id ASC"
        # 그리고 sort_column/direction은 필터링 후에 보조 정렬로 사용되거나 다른 방식으로 처리됨.
        # 여기서는 클라이언트가 보낸 sort_column/direction을 우선으로 가정합니다.
        
        main_sql += order_by_clause


        with get_session() as session_obj:
            # 총 개수 실행
            total_count = session_obj.execute(count_sql, params).scalar_one()

            # 페이지네이션 적용
            offset = (page_number - 1) * page_size
            if page_size != 'All': # 'All' 일 경우 페이지네이션 미적용
                main_sql += f" LIMIT :limit OFFSET :offset"
                params['limit'] = page_size
                params['offset'] = offset
            
            # 메인 데이터 실행
            result = session_obj.execute(text(main_sql), params).fetchall()
            
            rm_data = []
            for row in result:
                item = dict(row)
                # area_fl_formatted는 fl_list에서 사용된 필드. rm_list에는 필요 없지만,
                # 만약 rm 테이블에 면적 관련 컬럼이 있다면 여기서 포맷팅 가능.
                # 예: item['area_rm_formatted'] = f"{float(item['area_rm']):,.2f}"
                rm_data.append(item)

            total_pages = math.ceil(total_count / page_size) if page_size != 'All' and page_size > 0 else 1

            # Null 값 빈 문자열로 변환 (프론트엔드 렌더링 편의)
            for item in rm_data:
                for key, value in item.items():
                    if value is None:
                        item[key] = ''
            
            response_data = {
                'success': True,
                'message': '실 목록 조회 성공',
                'result_data': rm_data,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page_number,
                # 'total_area': 0 # rm_list에 총 면적 개념이 없으므로 필요 시 추가
            }
            
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.mimetype = 'application/json; charset=utf-8'
            return response

    except Exception as e:
        print(f"🔴 [rm_list] get_rm_data 오류 발생: {str(e)}")
        # 개발 환경에서 디버깅을 위해 에러 메시지를 포함하여 반환
        return jsonify({
            'success': False,
            'message': f'실 목록 조회 중 오류가 발생했습니다: {str(e)}',
            'result_data': [],
            'total_count': 0,
            'total_pages': 1,
            'current_page': 1
        }), 500  