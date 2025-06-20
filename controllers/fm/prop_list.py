from flask import Blueprint, request, jsonify, session, make_response, json
from controllers.auth import login_required
from sqlalchemy import text
from db import engine
import math

prop_list_bp = Blueprint('prop', __name__)

@prop_list_bp.route('/prop_entry', methods=['POST'])
@login_required
def prop_entry():
    """사업장 관련 AJAX API - SPA 전용"""
    try:
        request_data = request.get_json()
        c_type = request_data.get('c_type')
        
        if c_type == 'list':
            return get_prop_list_ajax(request_data)
        elif c_type == 'detail':
            return get_prop_detail(request_data)
        elif c_type == 'insert':
            return insert_prop_data(request_data)
        elif c_type == 'update':
            return update_prop_data(request_data)
        elif c_type == 'check_duplicate':
            return check_prop_duplicate(request_data)
        else:
            return jsonify({'success': False, 'message': '잘못된 요청 타입입니다.'})
    
    except Exception as e:
        print(f"prop_entry 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

def get_prop_list_ajax(request_data):
    """사업장 목록 AJAX 조회 - JSP와 동일한 검색 방식"""
    try:
        em_id = session.get('user')
        if not em_id:
            print(f"❌ 로그인 정보 없음")
            return jsonify({'success': False, 'message': '로그인이 필요합니다.'})

        # 검색 파라미터 추출 - JSP와 동일한 필드명
        page_no = int(request_data.get('page_no', 1))
        tb_prop_table = request_data.get('tb_prop_table', '')  # JSP와 동일한 필드명
        order_by = request_data.get('order', 'prop_id')
        desc = request_data.get('desc', 'asc')
        page_size = 20
        
        print(f"📝 사업장 검색 요청 받음:")
        print(f"   - em_id: {em_id}")
        print(f"   - tb_prop_table: {tb_prop_table}")
        print(f"   - page_no: {page_no}")
        
        with engine.connect() as conn:
            result = get_prop_list(conn, em_id, tb_prop_table, order_by, desc, page_no, page_size)
            
            print(f"✅ 사업장 목록 조회 완료:")
            print(f"   - 총 건수: {result['total_count']}")
            print(f"   - 현재 페이지: {page_no}")
            print(f"   - 총 페이지: {result['total_pages']}")
            print(f"   - 반환 데이터: {len(result['props'])}건")
            
            return jsonify({
                'success': True,
                'data': result['props'],
                'total_count': result['total_count'],
                'total_pages': result['total_pages'],
                'current_page': page_no,
                'total_bl_cnt': result.get('total_bl_cnt', 0)
            })
    
    except Exception as e:
        print(f"❌ 사업장 목록 AJAX 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})

def get_prop_list(conn, em_id, tb_prop_table, order_by, desc, page_no, page_size=20):
    """사업장 목록 조회 공통 함수 - JSP와 동일한 검색 로직"""
    
    # WHERE 조건 구성 - emcontrol 기반으로 권한 체크
    where_conditions = ["e.em_id = :em_id"]
    params = {"em_id": em_id}
    
    # JSP와 동일한 통합 검색 로직
    if tb_prop_table and tb_prop_table.strip():
        # 공백으로 분리된 검색어들 처리 (JSP와 동일)
        search_terms = tb_prop_table.strip().split()
        if search_terms:
            where_conditions.append("(")
            search_conditions = []
            
            for i, term in enumerate(search_terms[:50]):  # 최대 50개 검색어
                term = term.replace("'", "''")  # SQL 인젝션 방지
                if term:
                    term_conditions = []
                    param_key = f"search_term_{i}"
                    
                    # JSP와 동일한 검색 대상 필드들
                    term_conditions.extend([
                        f"(LOWER(p.prop_id)) LIKE (LOWER(:{param_key}))",
                        f"(LOWER(p.name)) LIKE (LOWER(:{param_key}))",
                        f"(LOWER(p.address1)) LIKE (LOWER(:{param_key}))",
                        f"(LOWER(p.contact1)) LIKE (LOWER(:{param_key}))",
                        f"(LOWER(p.use1)) LIKE (LOWER(:{param_key}))"
                    ])
                    
                    search_conditions.append(f"({' OR '.join(term_conditions)})")
                    params[param_key] = f"%{term}%"
            
            if search_conditions:
                where_conditions.append(' AND '.join(search_conditions))
            
            where_conditions.append(")")
    
    where_clause = " AND ".join(where_conditions)
    
    # ORDER BY 처리 - JSP와 동일
    order_mapping = {
        'prop_id': 'p.prop_id',
        'city_name': 'c.name',
        'prop_name': 'p.name',
        'address1': 'p.address1',
        'contact1': 'p.contact1',
        'use1': 'p.use1',
        'bl_cnt': 'bl_cnt'
    }
    
    order_field = order_mapping.get(order_by, 'p.name')  # JSP 기본 정렬
    order_direction = 'DESC' if desc == 'desc' else 'ASC'
    
    # 전체 카운트 조회
    count_sql = text(f"""
        SELECT COUNT(DISTINCT p.prop_id) as total_count
        FROM prop p
        LEFT JOIN city c ON p.city_id = c.city_id
        LEFT JOIN bl b ON p.prop_id = b.prop_id
        JOIN emcontrol e ON p.prop_id = e.prop_id
        WHERE {where_clause}
    """)
    
    total_count = conn.execute(count_sql, params).fetchone()['total_count']
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
    
    # 페이징 처리
    offset = (page_no - 1) * page_size
    params.update({"limit": page_size, "offset": offset})
    
    # 사업장 목록 조회 - JSP와 동일한 필드
    list_sql = text(f"""
        SELECT 
            c.name AS city_name,
            c.city_id AS city_id,
            p.name AS prop_name,
            p.prop_id AS prop_id,
            p.address1 AS address1,
            p.contact1 AS contact1,
            p.use1 AS use1,
            COUNT(DISTINCT b.bl_id) AS bl_cnt
        FROM prop p
        LEFT JOIN city c ON p.city_id = c.city_id
        LEFT JOIN bl b ON p.prop_id = b.prop_id
        JOIN emcontrol e ON p.prop_id = e.prop_id
        WHERE {where_clause}
        GROUP BY p.prop_id
        ORDER BY {order_field} {order_direction}
        LIMIT :limit OFFSET :offset
    """)
    
    props = conn.execute(list_sql, params).fetchall()
    
    # 총 건물 수 계산
    total_bl_cnt = sum(prop['bl_cnt'] for prop in props) if props else 0
    
    return {
        'props': [dict(row) for row in props],
        'total_count': total_count,
        'total_pages': total_pages,
        'total_bl_cnt': total_bl_cnt
    }

def get_prop_detail(request_data):
    """사업장 상세 정보 조회"""
    try:
        prop_id = request_data.get('prop_id')
        
        if not prop_id:
            return jsonify({'success': False, 'message': '사업장 ID가 필요합니다.'})
        
        with engine.connect() as conn:
            sql = text("""
                SELECT 
                    p.prop_id,
                    p.name AS prop_name,
                    p.city_id,
                    c.name AS city_name,
                    p.use1,
                    p.contact1,
                    p.description,
                    p.address1,
                    p.phone,
                    p.maskname,
                    p.overdue_monthly_rate,
                    p.overdue_daily_rate,
                    COUNT(DISTINCT b.bl_id) AS bl_cnt
                FROM prop p
                LEFT JOIN city c ON p.city_id = c.city_id
                LEFT JOIN bl b ON p.prop_id = b.prop_id
                WHERE p.prop_id = :prop_id
                GROUP BY p.prop_id
            """)
            
            result = conn.execute(sql, {"prop_id": prop_id}).fetchone()
            
            if result:
                return jsonify({
                    'success': True,
                    'data': dict(result)
                })
            else:
                return jsonify({'success': False, 'message': '사업장 정보를 찾을 수 없습니다.'})
                
    except Exception as e:
        print(f"사업장 상세 정보 조회 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

def insert_prop_data(request_data):
    """사업장 등록 - JSP와 동일한 로직"""
    try:
        em_id = session.get('user')
        if not em_id:
            return jsonify({'success': False, 'message': '로그인이 필요합니다.'})
        
        prop_id = request_data.get('prop_id')
        prop_name = request_data.get('prop_name')
        city_id = request_data.get('city_id')
        
        if not all([prop_id, prop_name]):
            return jsonify({'success': False, 'message': '사업장 코드와 이름은 필수 항목입니다.'})
        
        from datetime import datetime
        current_time = datetime.now()
        
        with engine.connect() as conn:
            # 중복 체크
            check_sql = text("SELECT COUNT(*) as cnt FROM prop WHERE prop_id = :prop_id")
            check_result = conn.execute(check_sql, {"prop_id": prop_id}).fetchone()
            
            if check_result['cnt'] > 0:
                return jsonify({'success': False, 'message': '이미 존재하는 사업장 ID입니다.'})
            
            # 삽입 - JSP와 동일한 필드들
            insert_sql = text("""
                INSERT INTO prop (
                    prop_id, name, city_id, use1, contact1, address1, phone,
                    overdue_monthly_rate, overdue_daily_rate, description,
                    date_reg, date_modi
                ) VALUES (
                    :prop_id, :prop_name, :city_id, :use1, :contact1, :address1, :phone,
                    :overdue_monthly_rate, :overdue_daily_rate, :description,
                    :date_reg, :date_modi
                )
            """)
            
            params = {
                'prop_id': prop_id,
                'prop_name': prop_name,
                'city_id': city_id if city_id else None,
                'use1': request_data.get('use1', ''),
                'contact1': request_data.get('contact1', ''),
                'address1': request_data.get('address1', ''),
                'phone': request_data.get('phone', ''),
                'overdue_monthly_rate': request_data.get('overdue_monthly_rate', 0),
                'overdue_daily_rate': request_data.get('overdue_daily_rate', 0),
                'description': request_data.get('description', ''),
                'date_reg': current_time,
                'date_modi': current_time
            }
            
            conn.execute(insert_sql, params)
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': '사업장이 성공적으로 등록되었습니다.',
                'prop_id': prop_id
            })
            
    except Exception as e:
        print(f"사업장 등록 오류: {str(e)}")
        return jsonify({'success': False, 'message': f'등록 중 오류가 발생했습니다: {str(e)}'})

def check_prop_duplicate(request_data):
    """사업장 코드 중복 체크"""
    try:
        prop_id = request_data.get('prop_id')
        
        if not prop_id:
            return jsonify({'success': False, 'message': '사업장 ID가 필요합니다.'})
        
        with engine.connect() as conn:
            sql = text("SELECT COUNT(*) as cnt FROM prop WHERE prop_id = :prop_id")
            result = conn.execute(sql, {"prop_id": prop_id}).fetchone()
            
            return jsonify({
                'success': True,
                'exists': result['cnt'] > 0
            })
            
    except Exception as e:
        print(f"중복 체크 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

def update_prop_data(request_data):
    """사업장 수정"""
    try:
        prop_id = request_data.get('prop_id')
        
        if not prop_id:
            return jsonify({'success': False, 'message': '사업장 ID가 필요합니다.'})

        from datetime import datetime
        current_time = datetime.now()

        # 업데이트할 필드 정의
        fields = ['use1', 'phone', 'contact1', 'description', 'address1',
                  'overdue_monthly_rate', 'overdue_daily_rate']

        set_clauses = []
        params = {'prop_id': prop_id}

        for field in fields:
            field_value = request_data.get(field)
            if field_value is not None:
                set_clauses.append(f"{field} = :{field}")
                params[field] = field_value.strip() if isinstance(field_value, str) else field_value

        # 항상 수정 시간 추가
        set_clauses.append("date_modi = :date_modi")
        params['date_modi'] = current_time

        if len(set_clauses) <= 1:
            return jsonify({'success': False, 'message': '업데이트할 데이터가 없습니다.'})

        set_sql = ", ".join(set_clauses)

        sql = text(f"""
            UPDATE prop
            SET {set_sql}
            WHERE prop_id = :prop_id
        """)

        with engine.connect() as conn:
            # 존재 여부 확인
            check_sql = text("SELECT COUNT(*) as cnt FROM prop WHERE prop_id = :prop_id")
            check_result = conn.execute(check_sql, {"prop_id": prop_id}).fetchone()
            
            if check_result['cnt'] == 0:
                return jsonify({'success': False, 'message': f'사업장 ID "{prop_id}"가 존재하지 않습니다.'})
            
            # 업데이트 실행
            result = conn.execute(sql, params)
            conn.commit()
            
            if result.rowcount > 0:
                return jsonify({
                    'success': True,
                    'message': '사업장 정보가 성공적으로 수정되었습니다.'
                })
            else:
                return jsonify({'success': False, 'message': '변경사항이 없습니다.'})

    except Exception as e:
        print(f'사업장 수정 오류: {str(e)}')
        return jsonify({'success': False, 'message': f'수정 중 오류가 발생했습니다: {str(e)}'})