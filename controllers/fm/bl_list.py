from flask import Blueprint, request, make_response, json
from sqlalchemy import text
from db import engine
import math

bl_list_bp = Blueprint('bl_list', __name__)

##### 새로운 통합 엔드포인트 - 다른 컨트롤러들과 일관성 유지 #####
@bl_list_bp.route('/bl_entry', methods=['POST'])
def bl_entry():
    """건물 관련 AJAX API - SPA 전용"""
    try:
        request_data = request.get_json()
        c_type = request_data.get('c_type')
        
        if c_type == 'list':
            return searchDataSheet_blList_data_new(request_data)
        else:
            return make_response(json.dumps({'success': False, 'message': '잘못된 요청 타입입니다.'}, ensure_ascii=False))
    
    except Exception as e:
        print(f"bl_entry 오류: {str(e)}")
        return make_response(json.dumps({'success': False, 'message': str(e)}, ensure_ascii=False))

def searchDataSheet_blList_data_new(request_data):
    """새로운 건물 목록 조회 함수"""
    try:
        em_id = request_data.get('em_id')
        prop_id = request_data.get('prop_id')
        
        print(f"🔵 건물 목록 조회 요청: em_id={em_id}, prop_id={prop_id}")
        
        if not em_id:
            return make_response(json.dumps({'success': False, 'message': 'em_id가 필요합니다.'}, ensure_ascii=False))
        
        if not prop_id:
            return make_response(json.dumps({'success': False, 'message': 'prop_id가 필요합니다.'}, ensure_ascii=False))
        
        # 권한 체크
        has_permission = check_prop_permission(em_id, prop_id)
        if not has_permission:
            print(f"🟡 권한 없음으로 빈 결과 반환: em_id={em_id}, prop_id={prop_id}")
            result = create_empty_result(request_data.get('page_size', 20))
            return make_response(json.dumps(result, ensure_ascii=False))
        
        # 기존 로직 사용
        base_sql, count_sql, params = build_bl_query(
            em_id=em_id,
            bl_id=request_data.get('bl_id'),
            prop_id=prop_id,
            sort_column=request_data.get('sort_column'),
            sort_direction=request_data.get('sort_direction'),
            keyword=request_data.get('keyword', '')
        )
        
        result = process_data_with_pagination_sql(
            base_sql=base_sql,
            count_sql=count_sql,
            params=params,
            page_params=request_data,
            get_extra_data=None
        )
        
        print("🟡 건물 목록 조회 결과:", result)
        
        return make_response(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        print(f"🔴 건물 목록 조회 중 오류 발생: {str(e)}")
        return make_response(json.dumps({'success': False, 'message': '서버 오류가 발생했습니다.'}, ensure_ascii=False))

##### 공통 pagination 처리 #####
def process_data_with_pagination_sql(base_sql, count_sql, params, page_params, get_extra_data=None):
    try:
        page_size = page_params.get('page_size', 20)
        page_number = int(page_params.get('page_number', 1))
        
        # ✅ page_number가 0 이하일 경우 1로 설정
        if page_number <= 0:
            page_number = 1
            print(f"🟡 page_number가 {page_params.get('page_number')}이므로 1로 수정")

        with engine.connect() as conn:
            # total count 조회
            total_count_row = conn.execute(text(count_sql), params).fetchone()
            total_count = total_count_row['cnt'] if total_count_row else 0

            # 페이지네이션 적용
            if page_size != 'All':
                page_size = int(page_size)
                total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

                if total_count == 0:
                    page_number = 1  # ✅ 0 대신 1로 설정
                    total_pages = 1   # ✅ 0 대신 1로 설정
                else:
                    if page_params.get('is_first_page'):
                        page_number = 1
                    elif page_params.get('is_last_page'):
                        page_number = total_pages
                    
                    # ✅ page_number가 total_pages를 초과하면 total_pages로 설정
                    if page_number > total_pages:
                        page_number = total_pages

                offset = (page_number - 1) * page_size
                
                # ✅ offset이 음수가 되지 않도록 보장
                if offset < 0:
                    offset = 0
                    page_number = 1
                    print(f"🟡 offset이 음수이므로 0으로 수정, page_number=1로 설정")
                
                limit_clause = f" LIMIT {page_size} OFFSET {offset} "
                print(f"🟢 페이지네이션: page_number={page_number}, page_size={page_size}, offset={offset}")
            else:
                limit_clause = ""
                total_pages = 1
                page_number = 1

            # 최종 쿼리 실행
            final_sql = base_sql + limit_clause
            print(f"🟢 최종 실행 SQL: {final_sql}")
            rows = conn.execute(text(final_sql), params).fetchall()

            # 데이터 변환
            result_data = [dict(row) for row in rows]

            # 기본 결과 구성
            result = {
                'success': True,
                'result_data': result_data,
                'current_page': page_number,
                'page_size': page_size,
                'total_pages': total_pages,
                'total_count': total_count
            }

            # 추가 데이터 처리
            if get_extra_data:
                extra_data = get_extra_data(result_data)
                result.update(extra_data)

            return result

    except Exception as e:
        print(f"process_data_with_pagination_sql 오류 발생: {str(e)}")
        return {'success': False, 'message': str(e)}

##### SQL 쿼리 빌더 #####
def build_bl_query(em_id=None, bl_id=None, prop_id=None, sort_column=None, sort_direction=None, keyword=None):
    params = {}
    where_clauses = []

    if not em_id:
        raise ValueError("em_id는 필수 값입니다.")
    params['em_id'] = em_id

    # bl_id 처리 (bl_id는 bl 테이블 직접 필터링)
    if bl_id:
        where_clauses.append("b.bl_id = :bl_id")
        params['bl_id'] = bl_id

    # prop_id 처리 (서브쿼리 내부에 반영)
    prop_id_filter_sql = ""
    if prop_id:
        params['prop_id'] = prop_id
        prop_id_filter_sql = "AND p2.prop_id = :prop_id"

    # keyword 처리
    if keyword:
        keyword_param = f"%{keyword}%"
        where_clauses.append("""(
            b.bl_id LIKE :keyword OR
            b.name LIKE :keyword OR
            b.address1 LIKE :keyword OR
            b.contact_phone LIKE :keyword
        )""")
        params['keyword'] = keyword_param

    # base_sql
    base_sql = f"""
        SELECT 
            b.bl_id,
            b.name AS bl_name,
            b.address1,
            b.contact_phone,
            b.area_total,
            b.count_fl,
            b.count_bf,
            b.prop_id
        FROM bl b
        JOIN prop p ON b.prop_id = p.prop_id
        WHERE b.prop_id IN (
            SELECT p2.prop_id
            FROM prop p2
            JOIN emcontrol e ON p2.prop_id = e.prop_id
            WHERE e.em_id = :em_id
            {prop_id_filter_sql}
        )
    """

    # count_sql
    count_sql = f"""
        SELECT COUNT(DISTINCT b.bl_id) AS cnt
        FROM bl b
        JOIN prop p ON b.prop_id = p.prop_id
        WHERE b.prop_id IN (
            SELECT p2.prop_id
            FROM prop p2
            JOIN emcontrol e ON p2.prop_id = e.prop_id
            WHERE e.em_id = :em_id
            {prop_id_filter_sql}
        )
    """

    # 외부 where_clauses 적용 (bl_id, keyword용)
    if where_clauses:
        base_sql += "\nAND " + " AND ".join(where_clauses)
        count_sql += "\nAND " + " AND ".join(where_clauses)

    print("✅ 최종 base_sql:\n", base_sql)
    print("✅ 최종 count_sql:\n", count_sql)
    print("✅ 최종 params:\n", params)

    # 정렬
    if sort_column and sort_direction:
        sort_order = "ASC" if sort_direction.lower() == 'asc' else "DESC"
        base_sql += f" ORDER BY {sort_column} {sort_order} "
    else:
        base_sql += " ORDER BY b.bl_id ASC "

    return base_sql, count_sql, params 

##### 권한 체크 공통 함수 #####
def check_prop_permission(em_id, prop_id):
    """prop_id에 대한 권한을 체크하는 공통 함수"""
    if not prop_id:
        return True  # prop_id가 없으면 권한 체크를 건너뜀
    
    try:
        with engine.connect() as conn:
            auth_check_sql = text("""
                SELECT COUNT(*) as cnt
                FROM emcontrol e
                WHERE e.em_id = :em_id AND e.prop_id = :prop_id
            """)
            auth_result = conn.execute(auth_check_sql, {"em_id": em_id, "prop_id": prop_id}).fetchone()
            has_permission = auth_result and auth_result['cnt'] > 0
            
            print(f"🔍 권한 체크: em_id={em_id}, prop_id={prop_id}, 권한={'있음' if has_permission else '없음'}")
            return has_permission
    except Exception as e:
        print(f"🔴 권한 체크 중 오류 발생: {str(e)}")
        return False

def create_empty_result(page_size):
    """빈 결과를 생성하는 공통 함수"""
    return {
        'success': True,
        'result_data': [],
        'current_page': 1,
        'page_size': page_size,
        'total_pages': 1,
        'total_count': 0
    }

##### 기존 라우트들 (호환성 유지) #####
@bl_list_bp.route('/bl_list/readDataSheet_blList_data', methods=['POST'])
def readDataSheet_blList_data():
    request_data = request.get_json()
    print("🔵 readDataSheet_blList_data 요청 데이터:", request_data)

    em_id = request_data.get('em_id')
    prop_id = request_data.get('prop_id')
    
    # ✅ 권한 체크
    if not check_prop_permission(em_id, prop_id):
        print(f"🟡 권한 없음으로 빈 결과 반환: em_id={em_id}, prop_id={prop_id}")
        result = create_empty_result(request_data.get('page_size', 10))
        response = make_response(json.dumps(result, ensure_ascii=False))
        response.mimetype = 'application/json; charset=utf-8'
        return response

    # ✅ 권한이 있는 경우 정상 처리
    base_sql, count_sql, params = build_bl_query(
        em_id=request_data.get('em_id'),
        bl_id=request_data.get('bl_id'),
        prop_id=request_data.get('prop_id')
    )

    result = process_data_with_pagination_sql(
        base_sql=base_sql,
        count_sql=count_sql,
        params=params,
        page_params=request_data,
        get_extra_data=None
    )

    print("🟡 readDataSheet_blList_data 결과:", result)

    response = make_response(json.dumps(result, ensure_ascii=False))
    response.mimetype = 'application/json; charset=utf-8'
    return response

@bl_list_bp.route('/bl_list/searchDataSheet_blList_data', methods=['POST'])
def searchDataSheet_blList_data():
    request_data = request.get_json()
    print("🔵 searchDataSheet_blList_data 요청 데이터:", request_data)

    em_id = request_data.get('em_id')
    prop_id = request_data.get('prop_id')
    
    # ✅ 권한 체크
    if not check_prop_permission(em_id, prop_id):
        print(f"🟡 권한 없음으로 빈 결과 반환: em_id={em_id}, prop_id={prop_id}")
        result = create_empty_result(request_data.get('page_size', 10))
        response = make_response(json.dumps(result, ensure_ascii=False))
        response.mimetype = 'application/json; charset=utf-8'
        return response

    # ✅ 권한이 있는 경우 정상 처리
    base_sql, count_sql, params = build_bl_query(
        em_id=request_data.get('em_id'),
        bl_id=request_data.get('bl_id'),
        prop_id=request_data.get('prop_id'),
        sort_column=request_data.get('sort_column'),
        sort_direction=request_data.get('sort_direction'),
        keyword=request_data.get('keyword', '')
    )

    result = process_data_with_pagination_sql(
        base_sql=base_sql,
        count_sql=count_sql,
        params=params,
        page_params=request_data,
        get_extra_data=None
    )

    print("🟡 searchDataSheet_blList_data 결과:", result)

    response = make_response(json.dumps(result, ensure_ascii=False))
    response.mimetype = 'application/json; charset=utf-8'
    return response