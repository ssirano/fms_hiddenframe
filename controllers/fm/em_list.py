from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from controllers.auth import login_required
from sqlalchemy import text
from db import engine
import math
from utils.common_functions import get_user_info, get_user_menu_data

em_list_bp = Blueprint('em', __name__)

@em_list_bp.route('/em_list')
@login_required
def em_list():
    """직원 목록 페이지 (MPA)"""
    try:
        em_id = session.get('user')
        if not em_id:
            return redirect(url_for('index'))

        # 사용자 정보 및 메뉴 데이터 조회
        user_info = get_user_info(em_id)
        if not user_info:
            return redirect(url_for('index'))
        menu_data = get_user_menu_data(em_id)

        # 요청 파라미터
        page_no = int(request.args.get('page_no', 1))
        prop_id = request.args.get('prop_id_chk', '')
        emclass_id = request.args.get('emclass_id', '')
        emstd_id   = request.args.get('emstd_id', '')
        status     = request.args.get('status', '')
        name_sch   = request.args.get('name_sch', '')
        order_by   = request.args.get('order', 'basic')
        desc       = request.args.get('desc', 'asc')
        page_size  = 20

        with engine.connect() as conn:
            # 사업장 목록 조회
            prop_list = conn.execute(text(
                "SELECT prop.prop_id, prop.name FROM prop JOIN emcontrol ec ON prop.prop_id=ec.prop_id WHERE ec.em_id=:em_id ORDER BY prop.prop_id"
            ), {"em_id": em_id}).fetchall()

            # 기본 prop_id 지정: 없으면 첫 번째
            if not prop_id and prop_list:
                prop_id = prop_list[0]['prop_id']

            # 파트 목록 조회
            emclass_list = conn.execute(text(
                "SELECT DISTINCT emclass_id FROM em WHERE prop_id=:prop_id ORDER BY emclass_id"
            ), {"prop_id": prop_id}).fetchall()

            # 직급 목록 조회
            emstd_list = conn.execute(text(
                "SELECT DISTINCT emstd_id FROM em WHERE prop_id=:prop_id ORDER BY emstd_id"
            ), {"prop_id": prop_id}).fetchall()

            # 상태 목록 조회
            status_list = conn.execute(text(
                "SELECT DISTINCT status FROM em WHERE prop_id=:prop_id AND status IS NOT NULL ORDER BY status"
            ), {"prop_id": prop_id}).fetchall()

            # 직원 목록 및 페이징
            filters = []
            params = {"prop_id": prop_id}
            filters.append("e.prop_id=:prop_id")
            if emclass_id:
                filters.append("e.emclass_id=:emclass_id"); params['emclass_id']=emclass_id
            if emstd_id:
                filters.append("e.emstd_id=:emstd_id"); params['emstd_id']=emstd_id
            if status:
                filters.append("e.status=:status"); params['status']=status
            if name_sch:
                filters.append("e.name LIKE :name_sch"); params['name_sch']=f"%{name_sch}%"
            where_clause = ' AND '.join(filters)

            # 전체 카운트
            total_count = conn.execute(text(
                f"SELECT COUNT(*) AS cnt FROM em e WHERE {where_clause}"
            ), params).fetchone()['cnt']
            total_pages = math.ceil(total_count / page_size)

            # 페이징 및 정렬
            offset = (page_no - 1) * page_size
            order_map = {
                'basic': 'e.emclass_id, e.name', 'name':'e.name',
                'emstd_id':'e.emstd_id', 'emclass_id':'e.emclass_id',
                'status':'e.status', 'mobile_phone':'e.mobile_phone'
            }
            order_field = order_map.get(order_by, 'e.emclass_id, e.name')
            order_dir = 'DESC' if desc=='desc' else 'ASC'

            rows = conn.execute(text(
                f"SELECT e.em_id,e.name,e.emstd_id,e.emclass_id,e.status,e.mobile_phone "
                f"FROM em e WHERE {where_clause} "
                f"ORDER BY {order_field} {order_dir} "
                f"LIMIT :limit OFFSET :offset"
            ), {**params, 'limit':page_size, 'offset':offset}).fetchall()

            employees = [dict(r) for r in rows]

        return render_template(
            'fm/em_list.html',
            user_info=user_info,
            menu_data=menu_data,
            prop_list=prop_list,
            emclass_list=emclass_list,
            emstd_list=emstd_list,
            status_list=status_list,
            em_list=employees,
            total_count=total_count,
            total_pages=total_pages,
            current_page=page_no,
            search_params={
                'prop_id_chk': prop_id,
                'emclass_id': emclass_id,
                'emstd_id': emstd_id,
                'status': status,
                'name_sch': name_sch,
                'order': order_by,
                'desc': desc
            }
        )
    except Exception as e:
        print(f"직원 목록 페이지 오류: {e}")
        return redirect(url_for('base.main'))

@em_list_bp.route('/em_entry', methods=['POST'])
@login_required
def em_entry():
    """직원 관련 AJAX API"""
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

@em_list_bp.route('/em_detail/<em_id>')
@login_required
def em_detail(em_id):
    try:
        if not session.get('user'):
            return '<p class="text-danger">로그인이 필요합니다.</p>'
        with engine.connect() as conn:
            row = conn.execute(text(
                "SELECT e.*, p.name AS prop_name"
                " FROM em e LEFT JOIN prop p ON e.prop_id=p.prop_id"
                " WHERE e.em_id=:em_id"
            ), {'em_id': em_id}).fetchone()
            if not row:
                return '<p class="text-danger">직원 정보를 찾을 수 없습니다.</p>'
        employee = dict(row)
        return render_template('fm/em_detail.html', employee=employee)
    except Exception as e:
        print(f"직원 상세 정보 오류: {e}")
        return '<p class="text-danger">오류가 발생했습니다.</p>'

def get_employee_list_ajax(request_data):
    """직원 목록 AJAX 조회"""
    try:
        em_id = session.get('user')
        page_no = int(request_data.get('page_no', 1))
        emclass_id = request_data.get('emclass_id', '')
        emstd_id = request_data.get('emstd_id', '')
        status = request_data.get('status', '')
        name_sch = request_data.get('name_sch', '')
        prop_id_chk = request_data.get('prop_id_chk', '')
        order_by = request_data.get('order', 'basic')
        desc = request_data.get('desc', 'asc')
        
        with engine.connect() as conn:
            if not prop_id_chk:
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
            
            result = get_employee_list(conn, prop_id_chk, emclass_id, emstd_id, status, name_sch, order_by, desc, page_no)
            
            return jsonify({
                'success': True,
                'data': result['employees'],
                'total_count': result['total_count'],
                'total_pages': result['total_pages'],
                'current_page': page_no
            })
    
    except Exception as e:
        print(f"직원 목록 AJAX 오류: {str(e)}")
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
        where_conditions.append("1=0")
    
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
    total_pages = math.ceil(total_count / page_size)
    
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
        
        with engine.connect() as conn:
            sql = text("""
                SELECT e.em_id, e.name, e.birthday, e.phone, e.mobile_phone, 
                       e.email, e.address, e.sex, e.emclass_id, e.emstd_id,
                       e.com_id, e.dvp_id, e.date_start, e.date_end, 
                       e.date_reg, e.date_modi, e.top_size, e.bottom_size,
                       e.signature, e.maskname, e.work_address,
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
        
        with engine.connect() as conn:
            sql = text("""
                SELECT auto_number, em_id, filetype, comments, filename, reg_date
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

def get_employee_licenses(request_data):
    """직원 자격증 정보 조회"""
    try:
        em_id = request_data.get('em_id')
        
        with engine.connect() as conn:
            sql = text("""
                SELECT licenceem_id, em_id, licence_id, certici_date, description
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