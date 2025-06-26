from flask import Blueprint, request, make_response, json, jsonify
from controllers.auth import login_required  # 추가
from sqlalchemy import text
from db import engine
import math

fl_list_bp = Blueprint('fl_list', __name__)

##### 공통 pagination 처리 #####
def process_data_with_pagination_sql(base_sql, count_sql, params, page_params, get_extra_data=None):
    """페이지네이션 처리를 위한 공통 함수"""
    try:
        page_size = page_params.get('page_size')
        page_number = int(page_params.get('page_number', 1))

        with engine.connect() as conn:
            # total count 조회
            total_count_row = conn.execute(text(count_sql), params).fetchone()
            total_count = total_count_row['cnt'] if total_count_row else 0

            # 페이지네이션 적용
            if page_size != 'All':
                page_size = int(page_size)
                total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

                if total_count == 0:
                    page_number = 1
                else:
                    if page_params.get('is_first_page'):
                        page_number = 1
                    elif page_params.get('is_last_page'):
                        page_number = total_pages

                # 페이지 번호 유효성 검사
                page_number = max(1, min(page_number, total_pages))
                
                offset = (page_number - 1) * page_size
                limit_clause = f" LIMIT {page_size} OFFSET {offset} "
            else:
                limit_clause = ""
                total_pages = 1
                page_number = 1

            # 최종 쿼리 실행
            final_sql = base_sql + limit_clause
            print(f"🔵 [fl_list] 실행 쿼리: {final_sql}")
            print(f"🔵 [fl_list] 쿼리 파라미터: {params}")
            
            rows = conn.execute(text(final_sql), params).fetchall()

            result_data = [{
                'prop_id': row['prop_id'],
                'prop_name': row['prop_name'],
                'bl_id': row['bl_id'],
                'bl_name': row['bl_name'],
                'fl_id': row['fl_id'],
                'fl_name': row['fl_name'],
                'area_fl': row['area_fl'],
                'area_fl_formatted': row['area_fl_formatted'],
                'tenant_names': row['tenant_names'] or ''
            } for row in rows]

            result = {
                'success': True,
                'result_data': result_data,
                'current_page': page_number,
                'page_size': page_size,
                'total_pages': total_pages,
                'total_count': total_count
            }

            # 추가 데이터
            if get_extra_data:
                extra_data = get_extra_data(result_data)
                result.update(extra_data)

            return result

    except Exception as e:
        print(f"🔴 [fl_list] process_data_with_pagination_sql 오류: {str(e)}")
        return {'success': False, 'message': str(e)}

##### 권한 체크 공통 함수 #####
def check_prop_permission(em_id, prop_id):
    """사업장에 대한 권한을 체크하는 함수"""
    try:
        with engine.connect() as conn:
            auth_sql = text("""
                SELECT COUNT(*) as cnt
                FROM emcontrol e
                WHERE e.em_id = :em_id AND e.prop_id = :prop_id
            """)
            auth_result = conn.execute(auth_sql, {"em_id": em_id, "prop_id": prop_id}).fetchone()
            
            has_permission = auth_result and auth_result['cnt'] > 0
            print(f"🔍 [fl_list] 권한 체크: em_id={em_id}, prop_id={prop_id}, 권한={'있음' if has_permission else '없음'}")
            return has_permission
            
    except Exception as e:
        print(f"🔴 [fl_list] 권한 체크 중 오류: {str(e)}")
        return False

##### SQL 쿼리 빌더 #####
def build_fl_query(em_id, prop_id=None, bl_id=None, sort_column=None, sort_direction=None, keyword=None):
    """층 정보 조회를 위한 SQL 쿼리 생성"""
    params = {'em_id': em_id}
    where_clauses = ["e.em_id = :em_id"]

    # 사업장 필터
    if prop_id and prop_id != '사업장 선택':
        where_clauses.append("f.prop_id = :prop_id")
        params['prop_id'] = prop_id

    # 건물 필터
    if bl_id and bl_id != '건물 선택' and bl_id.strip():
        where_clauses.append("f.bl_id = :bl_id")
        params['bl_id'] = bl_id

    # 키워드 검색
    if keyword and keyword.strip():
        keyword_param = f"%{keyword.strip()}%"
        where_clauses.append("""(
            p.name LIKE :keyword OR
            p.prop_id LIKE :keyword OR
            b.name LIKE :keyword OR
            b.bl_id LIKE :keyword OR
            f.fl_id LIKE :keyword OR
            f.name LIKE :keyword OR
            CAST(f.area_fl AS CHAR) LIKE :keyword OR
            COALESCE(GROUP_CONCAT(DISTINCT t.tenant_name SEPARATOR ', '), '') LIKE :keyword
        )""")
        params['keyword'] = keyword_param

    where_sql = "WHERE " + " AND ".join(where_clauses)

    # 기본 SELECT 쿼리 (입주사 현황 포함)
    base_sql = f"""
        SELECT 
            f.prop_id,
            p.name AS prop_name,
            f.bl_id,
            b.name AS bl_name,
            f.fl_id,
            f.name AS fl_name,
            COALESCE(f.area_fl, 0) AS area_fl,
            FORMAT(COALESCE(f.area_fl, 0), 0) AS area_fl_formatted,
            COALESCE(GROUP_CONCAT(DISTINCT t.tenant_name SEPARATOR ', '), '') AS tenant_names
        FROM fl f
        LEFT JOIN bl b ON f.bl_id = b.bl_id AND f.prop_id = b.prop_id
        LEFT JOIN prop p ON f.prop_id = p.prop_id
        LEFT JOIN emcontrol e ON f.prop_id = e.prop_id
        LEFT JOIN (
            SELECT DISTINCT rt.prop_id, rt.bl_id, rt.fl_id, rt.tenant_name
            FROM rmtenant rt
            WHERE rt.rmtenant_id NOT IN (
                SELECT rmtenant_id 
                FROM rmtenant 
                WHERE prop_id = rt.prop_id 
                AND bl_id = rt.bl_id 
                AND fl_id = rt.fl_id 
                AND (move_in > CURDATE() OR move_out < CURDATE())
            )
        ) t ON f.prop_id = t.prop_id AND f.bl_id = t.bl_id AND f.fl_id = t.fl_id
        {where_sql}
        GROUP BY f.prop_id, f.bl_id, f.fl_id, f.name, f.area_fl, p.name, b.name
    """

    # COUNT 쿼리
    count_sql = f"""
        SELECT COUNT(DISTINCT CONCAT(f.prop_id, '_', f.bl_id, '_', f.fl_id)) AS cnt
        FROM fl f
        LEFT JOIN bl b ON f.bl_id = b.bl_id AND f.prop_id = b.prop_id
        LEFT JOIN prop p ON f.prop_id = p.prop_id
        LEFT JOIN emcontrol e ON f.prop_id = e.prop_id
        LEFT JOIN (
            SELECT DISTINCT rt.prop_id, rt.bl_id, rt.fl_id, rt.tenant_name
            FROM rmtenant rt
            WHERE rt.rmtenant_id NOT IN (
                SELECT rmtenant_id 
                FROM rmtenant 
                WHERE prop_id = rt.prop_id 
                AND bl_id = rt.bl_id 
                AND fl_id = rt.fl_id 
                AND (move_in > CURDATE() OR move_out < CURDATE())
            )
        ) t ON f.prop_id = t.prop_id AND f.bl_id = t.bl_id AND f.fl_id = t.fl_id
        {where_sql}
    """

    # 정렬 처리
    if sort_column and sort_direction and sort_direction.lower() in ['asc', 'desc']:
        sort_order = "ASC" if sort_direction.lower() == 'asc' else "DESC"
        # 컬럼명 매핑
        column_mapping = {
            'prop_name': 'p.name',
            'bl_name': 'b.name',
            'fl_name': 'f.name',
            'area_fl': 'f.area_fl',
            'tenant_names': 'tenant_names'
        }
        db_column = column_mapping.get(sort_column, 'f.bl_id, f.fl_id')
        base_sql += f" ORDER BY {db_column} {sort_order} "
    else:
        base_sql += " ORDER BY f.bl_id ASC, f.fl_id ASC "

    return base_sql, count_sql, params

##### 🔧 수정된 라우트들 - /fm/ 제거 #####
@fl_list_bp.route('/fl_list/readDataSheet_flList_data', methods=['POST'])
@login_required
def readDataSheet_flList_data():
    """층 정보 목록 초기 조회"""
    try:
        request_data = request.get_json()
        em_id = request_data.get('em_id')
        prop_id = request_data.get('prop_id')
        
        print(f"🔵 [fl_list] 층 정보 목록 초기 조회: em_id={em_id}, prop_id={prop_id}")
        
        if not em_id or not prop_id:
            return jsonify({'success': False, 'message': 'em_id와 prop_id가 필요합니다.'})
        
        # 권한 체크
        if not check_prop_permission(em_id, prop_id):
            return jsonify({'success': False, 'message': '해당 사업장의 접근 권한이 없습니다.'})

        base_sql, count_sql, params = build_fl_query(
            em_id=em_id,
            prop_id=prop_id,
            bl_id=request_data.get('bl_id')
        )

        def get_total_area(result_data):
            total_area = sum(float(item['area_fl'] or 0) for item in result_data)
            return {'total_area': total_area}

        result = process_data_with_pagination_sql(
            base_sql=base_sql,
            count_sql=count_sql,
            params=params,
            page_params=request_data,
            get_extra_data=get_total_area
        )

        print(f"🟢 [fl_list] 층 정보 조회 완료: {len(result.get('result_data', []))}개")
        
        response = make_response(json.dumps(result, ensure_ascii=False))
        response.mimetype = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        print(f"🔴 [fl_list] 층 정보 조회 중 오류: {str(e)}")
        return jsonify({'success': False, 'message': f'서버 오류가 발생했습니다: {str(e)}'})

##### 층 정보 목록 검색 #####
@fl_list_bp.route('/fl_list/searchDataSheet_flList_data', methods=['POST'])
@login_required
def searchDataSheet_flList_data():
    """층 정보 목록 검색"""
    try:
        request_data = request.get_json()
        em_id = request_data.get('em_id')
        prop_id = request_data.get('prop_id')
        
        print(f"🔵 [fl_list] 층 정보 검색: em_id={em_id}, prop_id={prop_id}")
        print(f"🔵 [fl_list] 검색 조건: keyword={request_data.get('keyword')}, bl_id={request_data.get('bl_id')}")
        
        if not em_id or not prop_id:
            return jsonify({'success': False, 'message': 'em_id와 prop_id가 필요합니다.'})
        
        # 권한 체크
        if not check_prop_permission(em_id, prop_id):
            return jsonify({'success': False, 'message': '해당 사업장의 접근 권한이 없습니다.'})

        base_sql, count_sql, params = build_fl_query(
            em_id=em_id,
            prop_id=prop_id,
            bl_id=request_data.get('bl_id'),
            sort_column=request_data.get('sort_column'),
            sort_direction=request_data.get('sort_direction'),
            keyword=request_data.get('keyword', '').strip()
        )

        def get_total_area(result_data):
            total_area = sum(float(item['area_fl'] or 0) for item in result_data)
            return {'total_area': total_area}

        result = process_data_with_pagination_sql(
            base_sql=base_sql,
            count_sql=count_sql,
            params=params,
            page_params=request_data,
            get_extra_data=get_total_area
        )

        print(f"🟢 [fl_list] 층 정보 검색 완료: {len(result.get('result_data', []))}개")
        
        response = make_response(json.dumps(result, ensure_ascii=False))
        response.mimetype = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        print(f"🔴 [fl_list] 층 정보 검색 중 오류: {str(e)}")
        return jsonify({'success': False, 'message': f'서버 오류가 발생했습니다: {str(e)}'})

##### 건물 목록 조회 #####
@fl_list_bp.route('/fl_list/get_bl_list', methods=['POST'])
@login_required
def get_bl_list():
    """건물 목록 조회"""
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')
        
        print(f"🔵 [fl_list] 건물 목록 조회: em_id={em_id}, prop_id={prop_id}")
        
        if not em_id:
            return jsonify({
                'success': False, 
                'message': '사용자 ID가 필요합니다.',
                'data': []
            })

        if not prop_id:
            return jsonify({
                'success': False, 
                'message': '사업장 ID가 필요합니다.',
                'data': []
            })

        # 권한 체크
        if not check_prop_permission(em_id, prop_id):
            return jsonify({
                'success': False, 
                'message': '해당 사업장의 접근 권한이 없습니다.',
                'data': []
            })

        # 건물 목록 조회
        where_clauses = ["e.em_id = :em_id", "b.prop_id = :prop_id"]
        params = {'em_id': em_id, 'prop_id': prop_id}
        
        where_sql = "WHERE " + " AND ".join(where_clauses)

        sql = text(f"""
            SELECT DISTINCT
                b.bl_id,
                b.name AS bl_name,
                b.prop_id
            FROM bl b
            LEFT JOIN emcontrol e ON b.prop_id = e.prop_id
            {where_sql}
            ORDER BY b.name ASC
        """)

        with engine.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            
            result_data = [{
                'bl_id': row['bl_id'],
                'bl_name': row['bl_name'],
                'prop_id': row['prop_id']
            } for row in rows]

            print(f"🟢 [fl_list] 건물 목록 조회 완료: {len(result_data)}개")
            
            result = {
                'success': True, 
                'message': '건물 목록 조회 성공',
                'data': result_data
            }
            
            response = make_response(json.dumps(result, ensure_ascii=False))
            response.mimetype = 'application/json; charset=utf-8'
            return response

    except Exception as e:
        print(f"🔴 [fl_list] 건물 목록 조회 중 오류: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'서버 오류가 발생했습니다: {str(e)}',
            'data': []
        })

##### 층 정보 상세 조회 (fl_update용) #####
@fl_list_bp.route('/fl_list/get_fl_detail', methods=['POST'])
@login_required
def get_fl_detail():
    """층 정보 상세 조회 (fl_update 페이지용)"""
    try:
        request_data = request.get_json()
        em_id = request_data.get('em_id')
        prop_id = request_data.get('prop_id')
        bl_id = request_data.get('bl_id')
        fl_id = request_data.get('fl_id')
        
        print(f"🔵 [fl_list] 층 상세 정보 조회: prop_id={prop_id}, bl_id={bl_id}, fl_id={fl_id}")
        
        if not all([em_id, prop_id, bl_id, fl_id]):
            return jsonify({'success': False, 'message': '필수 파라미터가 누락되었습니다.'})
        
        # 권한 체크
        if not check_prop_permission(em_id, prop_id):
            return jsonify({'success': False, 'message': '해당 사업장의 접근 권한이 없습니다.'})

        with engine.connect() as conn:
            sql = text("""
                SELECT 
                    f.*,
                    p.name AS prop_name,
                    b.name AS bl_name
                FROM fl f
                LEFT JOIN prop p ON f.prop_id = p.prop_id
                LEFT JOIN bl b ON f.prop_id = b.prop_id AND f.bl_id = b.bl_id
                LEFT JOIN emcontrol e ON f.prop_id = e.prop_id
                WHERE f.prop_id = :prop_id 
                AND f.bl_id = :bl_id 
                AND f.fl_id = :fl_id
                AND e.em_id = :em_id
            """)
            
            result = conn.execute(sql, {
                'prop_id': prop_id,
                'bl_id': bl_id,
                'fl_id': fl_id,
                'em_id': em_id
            }).fetchone()
            
            if not result:
                return jsonify({'success': False, 'message': '층 정보를 찾을 수 없습니다.'})
            
            # 결과를 딕셔너리로 변환
            data = dict(result)
            
            # 날짜 필드 포맷팅
            date_fields = ['date_reg', 'date_modi']
            for field in date_fields:
                if data.get(field):
                    data[field] = data[field].strftime('%Y-%m-%d') if hasattr(data[field], 'strftime') else str(data[field])
            
            print(f"🟢 [fl_list] 층 상세 정보 조회 완료: {fl_id}")
            
            result_data = {
                'success': True,
                'data': data
            }
            
            response = make_response(json.dumps(result_data, ensure_ascii=False))
            response.mimetype = 'application/json; charset=utf-8'
            return response
            
    except Exception as e:
        print(f"🔴 [fl_list] 층 상세 정보 조회 중 오류: {str(e)}")
        return jsonify({'success': False, 'message': f'서버 오류가 발생했습니다: {str(e)}'})