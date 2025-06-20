from flask import Blueprint, request, jsonify, session, make_response, json
from controllers.auth import login_required
from sqlalchemy import text
from db import engine
import math

em_list_bp = Blueprint('em', __name__)

@em_list_bp.route('/em_entry', methods=['POST'])
@login_required
def em_entry():
    """직원 관련 AJAX API - SPA 전용"""
    try:
        request_data = request.get_json()
        c_type = request_data.get('c_type')
        
        if c_type == 'list':
            return get_employee_list_ajax(request_data)
        elif c_type == 'detail':
            return get_employee_detail(request_data)
        elif c_type == 'history':
            return get_employee_history(request_data)
        elif c_type == 'license':
            return get_employee_licenses(request_data)
        else:
            return jsonify({'success': False, 'message': '잘못된 요청 타입입니다.'})
    
    except Exception as e:
        print(f"em_entry 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

def get_employee_list_ajax(request_data):
    """직원 목록 AJAX 조회 - SPA 최적화"""
    try:
        em_id = session.get('user')
        if not em_id:
            print(f"❌ 로그인 정보 없음")
            return jsonify({'success': False, 'message': '로그인이 필요합니다.'})

        # 검색 파라미터 추출
        page_no = int(request_data.get('page_no', 1))
        emclass_id = request_data.get('emclass_id', '')
        emstd_id = request_data.get('emstd_id', '')
        status = request_data.get('status', '')
        name_sch = request_data.get('name_sch', '')
        prop_id_chk = request_data.get('prop_id_chk', '')
        order_by = request_data.get('order', 'basic')
        desc = request_data.get('desc', 'asc')
        page_size = 20
        
        print(f"📝 직원 검색 요청 받음:")
        print(f"   - em_id: {em_id}")
        print(f"   - prop_id_chk: {prop_id_chk}")
        print(f"   - emclass_id: {emclass_id}")
        print(f"   - page_no: {page_no}")
        
        with engine.connect() as conn:
            # 기본 prop_id 설정
            if not prop_id_chk:
                print(f"🔍 prop_id_chk가 없어서 기본값 조회 시작")
                prop_sql = text("""
                    SELECT prop.prop_id 
                    FROM prop, emcontrol 
                    WHERE emcontrol.em_id = :em_id 
                    AND prop.prop_id = emcontrol.prop_id 
                    LIMIT 1
                """)
                prop_result = conn.execute(prop_sql, {"em_id": em_id}).fetchone()
                if prop_result:
                    prop_id_chk = prop_result['prop_id']
                    print(f"✅ 기본 prop_id 설정: {prop_id_chk}")
                else:
                    print(f"❌ 기본 prop_id를 찾을 수 없음")
                    return jsonify({'success': False, 'message': '접근 가능한 사업소가 없습니다.'})
            
            # 직원 목록 조회
            print(f"🔍 직원 목록 조회 시작, prop_id: {prop_id_chk}")
            result = get_employee_list(conn, prop_id_chk, emclass_id, emstd_id, status, name_sch, order_by, desc, page_no, page_size)
            
            print(f"✅ 직원 목록 조회 완료:")
            print(f"   - 총 건수: {result['total_count']}")
            print(f"   - 현재 페이지: {page_no}")
            print(f"   - 총 페이지: {result['total_pages']}")
            print(f"   - 반환 데이터: {len(result['employees'])}건")
            
            return jsonify({
                'success': True,
                'data': result['employees'],
                'total_count': result['total_count'],
                'total_pages': result['total_pages'],
                'current_page': page_no
            })
    
    except Exception as e:
        print(f"❌ 직원 목록 AJAX 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})

def get_employee_list(conn, prop_id_chk, emclass_id, emstd_id, status, name_sch, order_by, desc, page_no, page_size=20):
    """직원 목록 조회 공통 함수"""
    
    # WHERE 조건 구성
    where_conditions = []
    params = {}
    
    if prop_id_chk:
        where_conditions.append("e.prop_id = :prop_id")
        params["prop_id"] = prop_id_chk
        
    if emclass_id:
        where_conditions.append("e.emclass_id = :emclass_id")
        params["emclass_id"] = emclass_id
        
    if emstd_id:
        where_conditions.append("e.emstd_id = :emstd_id")
        params["emstd_id"] = emstd_id
        
    if status:
        where_conditions.append("e.status = :status")
        params["status"] = status
        
    if name_sch:
        where_conditions.append("e.name LIKE :name_sch")
        params["name_sch"] = f"%{name_sch}%"
    
    if not where_conditions:
        where_conditions.append("1=0")  # 조건이 없으면 빈 결과
    
    where_clause = " AND ".join(where_conditions)
    
    # ORDER BY 처리
    order_mapping = {
        'basic': 'e.emclass_id, e.name',
        'prop_id': 'e.prop_id',
        'name': 'e.name',
        'emstd_id': 'e.emstd_id',
        'emclass_id': 'e.emclass_id',
        'status': 'e.status',
        'mobile_phone': 'e.mobile_phone'
    }
    
    order_field = order_mapping.get(order_by, 'e.emclass_id, e.name')
    order_direction = 'DESC' if desc == 'desc' else 'ASC'
    
    # 전체 카운트 조회
    count_sql = text(f"""
        SELECT COUNT(*) as total_count
        FROM em e
        WHERE {where_clause}
    """)
    
    total_count = conn.execute(count_sql, params).fetchone()['total_count']
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
    
    # 페이징 처리
    offset = (page_no - 1) * page_size
    params.update({"limit": page_size, "offset": offset})
    
    # 직원 목록 조회
    list_sql = text(f"""
        SELECT e.em_id, e.prop_id, e.name, e.emstd_id, e.emclass_id, 
               e.status, e.mobile_phone, e.maskname
        FROM em e
        WHERE {where_clause}
        ORDER BY {order_field} {order_direction}
        LIMIT :limit OFFSET :offset
    """)
    
    employees = conn.execute(list_sql, params).fetchall()
    
    return {
        'employees': [dict(row) for row in employees],
        'total_count': total_count,
        'total_pages': total_pages
    }

def get_employee_detail(request_data):
    """직원 상세 정보 조회"""
    try:
        em_id = request_data.get('em_id')
        
        if not em_id:
            return jsonify({'success': False, 'message': '직원 ID가 필요합니다.'})
        
        with engine.connect() as conn:
            sql = text("""
                SELECT e.em_id, e.name, e.birthday, e.phone, e.mobile_phone, 
                       e.email, e.address, e.sex, e.emclass_id, e.emstd_id,
                       e.com_id, e.dvp_id, e.date_start, e.date_end, 
                       e.date_reg, e.date_modi, e.top_size, e.bottom_size,
                       e.signature, e.maskname, e.work_address, e.status,
                       p.name as prop_name
                FROM em e
                LEFT JOIN prop p ON e.prop_id = p.prop_id
                WHERE e.em_id = :em_id
            """)
            
            result = conn.execute(sql, {"em_id": em_id}).fetchone()
            
            if result:
                return jsonify({
                    'success': True,
                    'data': dict(result)
                })
            else:
                return jsonify({'success': False, 'message': '직원 정보를 찾을 수 없습니다.'})
                
    except Exception as e:
        print(f"직원 상세 정보 조회 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

def get_employee_history(request_data):
    """직원 이력 조회"""
    try:
        em_id = request_data.get('em_id')
        
        if not em_id:
            return jsonify({'success': False, 'message': '직원 ID가 필요합니다.'})
        
        with engine.connect() as conn:
            sql = text("""
                SELECT auto_number, em_id, filetype, comments, filename, 
                       DATE_FORMAT(reg_date, '%Y-%m-%d %H:%i:%s') as reg_date
                FROM empds
                WHERE em_id = :em_id
                ORDER BY auto_number DESC
            """)
            
            results = conn.execute(sql, {"em_id": em_id}).fetchall()
            
            return jsonify({
                'success': True,
                'data': [dict(row) for row in results]
            })
                
    except Exception as e:
        print(f"직원 이력 조회 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@em_list_bp.route('/em_list_excel', methods=['GET'])
@login_required
def em_list_excel():
    """직원 목록 엑셀 다운로드"""
    try:
        from flask import Response
        import io
        import csv
        
        # 검색 파라미터 추출
        prop_id_chk = request.args.get('prop_id_chk', '')
        emclass_id = request.args.get('emclass_id', '')
        emstd_id = request.args.get('emstd_id', '')
        status = request.args.get('status', '')
        name_sch = request.args.get('name_sch', '')
        
        with engine.connect() as conn:
            # WHERE 조건 구성
            where_conditions = []
            params = {}
            
            if prop_id_chk:
                where_conditions.append("e.prop_id = :prop_id")
                params["prop_id"] = prop_id_chk
                
            if emclass_id:
                where_conditions.append("e.emclass_id = :emclass_id")
                params["emclass_id"] = emclass_id
                
            if emstd_id:
                where_conditions.append("e.emstd_id = :emstd_id")
                params["emstd_id"] = emstd_id
                
            if status:
                where_conditions.append("e.status = :status")
                params["status"] = status
                
            if name_sch:
                where_conditions.append("e.name LIKE :name_sch")
                params["name_sch"] = f"%{name_sch}%"
            
            if not where_conditions:
                where_conditions.append("1=0")
            
            where_clause = " AND ".join(where_conditions)
            
            # 엑셀용 데이터 조회
            excel_sql = text(f"""
                SELECT e.prop_id as '사업소', e.em_id as '직원ID', e.name as '이름',
                       e.emstd_id as '직급', e.emclass_id as '파트', e.status as '상태',
                       e.mobile_phone as '핸드폰', e.email as '이메일',
                       e.date_start as '입사일', e.date_end as '퇴사일'
                FROM em e
                WHERE {where_clause}
                ORDER BY e.emclass_id ASC, e.name ASC
            """)
            
            results = conn.execute(excel_sql, params).fetchall()
            
            # CSV 생성
            output = io.StringIO()
            writer = csv.writer(output)
            
            if results:
                # 헤더 작성
                headers = list(results[0].keys())
                writer.writerow(headers)
                
                # 데이터 작성
                for row in results:
                    writer.writerow([str(value) if value is not None else '' for value in row.values()])
            
            # Response 생성
            csv_data = output.getvalue()
            output.close()
            
            response = Response(
                csv_data.encode('utf-8-sig'),  # BOM 추가로 한글 깨짐 방지
                mimetype='text/csv',
                headers={
                    "Content-Disposition": f"attachment; filename=employee_list_{prop_id_chk}.csv"
                }
            )
            
            return response
            
    except Exception as e:
        print(f"엑셀 다운로드 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
def get_employee_licenses(request_data):
    """직원 자격증 정보 조회"""
    try:
        em_id = request_data.get('em_id')
        
        if not em_id:
            return jsonify({'success': False, 'message': '직원 ID가 필요합니다.'})
        
        with engine.connect() as conn:
            sql = text("""
                SELECT licenceem_id, em_id, licence_id, 
                       DATE_FORMAT(certici_date, '%Y-%m-%d') as certici_date,
                       description
                FROM licenceem
                WHERE em_id = :em_id
                ORDER BY licenceem_id DESC
            """)
            
            results = conn.execute(sql, {"em_id": em_id}).fetchall()
            
            return jsonify({
                'success': True,
                'data': [dict(row) for row in results]
            })
                
    except Exception as e:
        print(f"직원 자격증 정보 조회 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})