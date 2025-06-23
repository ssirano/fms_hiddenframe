from flask import Blueprint, request, jsonify, session, make_response, json
from controllers.auth import login_required
from sqlalchemy import text 
from db import engine, get_session
import math
import os
from werkzeug.utils import secure_filename
from datetime import datetime

prop_update_bp = Blueprint('prop_update', __name__)

# 이미지 업로드 설정
UPLOAD_FOLDER = r'C:\Program_Data\fms\uploads\prop_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB

# 폴더 생성
base_folders = ['C:\\Program_Data', 'C:\\Program_Data\\fms', 'C:\\Program_Data\\fms\\uploads', UPLOAD_FOLDER]
for folder in base_folders:
    if not os.path.exists(folder):
        os.makedirs(folder)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@prop_update_bp.route('/prop_update_entry', methods=['POST'])
@login_required
def prop_update_entry():
    """사업장 수정 관련 AJAX API - SPA 전용"""
    try:
        request_data = request.get_json()
        c_type = request_data.get('c_type')
        
        if c_type == 'detail':
            return get_prop_update_detail(request_data)
        elif c_type == 'history':
            return get_prop_update_history(request_data)
        elif c_type == 'save':
            return save_prop_update_data(request_data)
        elif c_type == 'upload':
            return handle_image_upload(request_data)
        else:
            return jsonify({'success': False, 'message': '잘못된 요청 타입입니다.'})
    
    except Exception as e:
        print(f"prop_update_entry 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

def get_prop_update_detail(request_data):
    """사업장 수정 상세 정보 조회"""
    try:
        prop_id = request_data.get('prop_id')
        
        if not prop_id:
            return jsonify({
                'success': False, 
                'message': '사업장 ID가 필요합니다.',
                'data': {}
            })

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
                p.overdue_daily_rate
            FROM prop p
            LEFT JOIN city c ON p.city_id = c.city_id
            WHERE p.prop_id = :prop_id
        """)

        sql_bl_cnt = text("""
            SELECT COUNT(*) AS bl_cnt
            FROM bl
            WHERE prop_id = :prop_id
        """)

        with engine.connect() as conn:
            # 기본 사업장 정보 조회
            row = conn.execute(sql, {"prop_id": prop_id}).fetchone()
            if not row:
                return jsonify({
                    'success': False, 
                    'message': f'사업장 ID "{prop_id}"에 해당하는 데이터가 없습니다.',
                    'data': {}
                })

            # 건물 수 조회
            bl_cnt_row = conn.execute(sql_bl_cnt, {"prop_id": prop_id}).fetchone()
            bl_cnt = bl_cnt_row['bl_cnt'] if bl_cnt_row else 0

            # 결과 데이터 구성
            result_data = dict(row)
            result_data['bl_cnt'] = bl_cnt

            # None 값들을 빈 문자열로 변환
            for key, value in result_data.items():
                if value is None:
                    result_data[key] = ''

            result = {
                'success': True, 
                'message': '데이터 조회 성공',
                'data': result_data
            }
            
            response = make_response(json.dumps(result, ensure_ascii=False))
            response.mimetype = 'application/json; charset=utf-8'
            return response

    except Exception as e:
        print(f"get_prop_update_detail 오류 발생: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'서버 오류가 발생했습니다: {str(e)}',
            'data': {}
        })

def get_prop_update_history(request_data):
    """사업장 이미지/이력 목록 조회"""
    try:
        prop_id = request_data.get('prop_id')
        page_no = int(request_data.get('page_no', 1))
        keyword = request_data.get('keyword', '')
        start_date = request_data.get('start_date')
        end_date = request_data.get('end_date')
        order_by = request_data.get('order', 'auto_number')
        desc = request_data.get('desc', 'desc')
        page_size = 20
        
        if not prop_id:
            return jsonify({'success': False, 'message': '사업장 ID가 필요합니다.'})

        with engine.connect() as conn:
            result = get_prop_history_list(
                conn, prop_id, keyword, start_date, end_date, 
                order_by, desc, page_no, page_size
            )
            
            return jsonify({
                'success': True,
                'data': result['history'],
                'total_count': result['total_count'],
                'total_pages': result['total_pages'],
                'current_page': page_no,
                'default_photo_t': result.get('default_photo_t')
            })
                
    except Exception as e:
        print(f"사업장 이력 조회 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

def get_prop_history_list(conn, prop_id, keyword, start_date, end_date, order_by, desc, page_no, page_size=20):
    """사업장 이력 목록 조회 공통 함수"""
    
    # WHERE 조건 구성
    where_conditions = ["pds.prop_id = :prop_id", "pds.filetype = '1'"]
    params = {"prop_id": prop_id}
    
    # 날짜 범위 검색
    if start_date and end_date:
        where_conditions.append("DATE(pds.reg_date) BETWEEN :start_date AND :end_date")
        params['start_date'] = start_date
        params['end_date'] = end_date

    # 키워드 검색
    if keyword and keyword.strip():
        where_conditions.append("""(
            pds.auto_number LIKE :keyword OR
            pds.title LIKE :keyword OR
            pds.em_name LIKE :keyword OR
            DATE_FORMAT(pds.reg_date, '%Y-%m-%d') LIKE :keyword OR
            pds.contents LIKE :keyword
        )""")
        params['keyword'] = f"%{keyword.strip()}%"
    
    where_clause = " AND ".join(where_conditions)
    
    # ORDER BY 처리
    order_mapping = {
        'auto_number': 'pds.auto_number',
        'title': 'pds.title',
        'em_name': 'pds.em_name',
        'reg_date': 'pds.reg_date',
        'file': 'pds.maskname'
    }
    
    order_field = order_mapping.get(order_by, 'pds.auto_number')
    order_direction = 'DESC' if desc == 'desc' else 'ASC'
    
    # 전체 카운트 조회
    count_sql = text(f"""
        SELECT COUNT(*) AS cnt
        FROM proppds pds
        WHERE {where_clause}
    """)
    
    total_count = conn.execute(count_sql, params).fetchone()['cnt']
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
    
    # 페이징 처리
    offset = (page_no - 1) * page_size
    params.update({"limit": page_size, "offset": offset})
    
    # 이력 목록 조회
    list_sql = text(f"""
        SELECT 
            pds.reg_man,
            DATE_FORMAT(pds.reg_date, '%Y-%m-%d') AS reg_date,
            pds.auto_number,
            pds.contents,
            pds.title,
            pds.maskname,
            pds.em_name
        FROM proppds pds
        WHERE {where_clause}
        ORDER BY {order_field} {order_direction}
        LIMIT :limit OFFSET :offset
    """)
    
    history = conn.execute(list_sql, params).fetchall()
    
    # 기본 사진 정보 조회
    mask_sql = text("SELECT maskname FROM prop WHERE prop_id = :prop_id")
    mask_row = conn.execute(mask_sql, {"prop_id": prop_id}).fetchone()
    default_photo_t = mask_row['maskname'] if mask_row else None
    
    return {
        'history': [dict(row) for row in history],
        'total_count': total_count,
        'total_pages': total_pages,
        'default_photo_t': default_photo_t
    }

def save_prop_update_data(request_data):
    """사업장 정보 저장"""
    try:
        prop_id = request_data.get('prop_id')

        if not prop_id:
            return jsonify({'success': False, 'message': '사업장 ID가 필요합니다.'})

        current_time = datetime.now()

        # 업데이트할 필드 정의
        fields = ['use1', 'phone', 'contact1', 'description', 'address1',
                  'overdue_monthly_rate', 'overdue_daily_rate']

        set_clauses = []
        params = {'prop_id': prop_id}

        # 실제로 전송된 데이터만 업데이트
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

        # with engine.connect() as conn: # 이 부분을 아래와 같이 변경
        with get_session() as session_obj: # get_session 컨텍스트 매니저 사용
            conn = session_obj.connection() # Connection 객체는 session_obj.connection()으로 얻음


            # 먼저 해당 prop_id가 존재하는지 확인
            check_sql = text("SELECT COUNT(*) as cnt FROM prop WHERE prop_id = :prop_id")
            check_result = conn.execute(check_sql, {"prop_id": prop_id}).fetchone()

            if check_result['cnt'] == 0:
                return jsonify({'success': False, 'message': f'사업장 ID "{prop_id}"가 존재하지 않습니다.'})

            # 업데이트 실행
            result = conn.execute(sql, params)
            # conn.commit() # session_obj가 commit을 관리하므로 삭제

            if result.rowcount > 0:
                return jsonify({
                    'success': True,
                    'message': '사업장 정보가 성공적으로 저장되었습니다.' # 메시지 변경
                })
            else:
                return jsonify({'success': False, 'message': '변경사항이 없습니다.'})

    except Exception as e:
        print(f'save_prop_update_data 오류 발생: {str(e)}')
        return jsonify({'success': False, 'message': f'데이터 저장 중 오류가 발생했습니다: {str(e)}'})


def handle_image_upload(request_data):
    """이미지 업로드 처리"""
    try:
        # 이 함수는 실제 파일 업로드를 처리하기 위해 별도의 엔드포인트가 필요합니다
        return jsonify({'success': False, 'message': '이미지 업로드는 별도 엔드포인트를 사용해주세요.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@prop_update_bp.route('/upload_images', methods=['POST'])
@login_required
def upload_images():
    """이미지 업로드 엔드포인트"""
    try:
        files = request.files.getlist('images[]')
        overwrite = request.form.get('overwrite', 'false').lower() == 'true'

        if not files:
            return jsonify({'success': False, 'message': '업로드된 파일이 없습니다.'})

        for file in files:
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            if file_size > MAX_FILE_SIZE:
                return jsonify({
                    'success': False,
                    'message': f'파일 크기는 {MAX_FILE_SIZE/1024/1024:.1f}MB를 초과할 수 없습니다.'
                })

        prop_id = request.form.get('prop_id')
        if not prop_id:
            return jsonify({'success': False, 'message': '사업장 ID가 필요합니다.'})

        prop_folder = os.path.join(UPLOAD_FOLDER, str(prop_id))
        if not os.path.exists(prop_folder):
            os.makedirs(prop_folder)

        uploaded_files = []

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%y%m%d_%H%M%S%f')
                unique_filename = f"{timestamp}_{filename}"
                file_path = os.path.join(prop_folder, unique_filename)

                if os.path.exists(file_path) and not overwrite:
                    return jsonify({
                        'success': False,
                        'duplicate': True,
                        'message': '동일한 파일이 이미 존재합니다. 덮어쓰시겠습니까?'
                    })

                file.save(file_path)

                uploaded_files.append({
                    'original_name': filename,
                    'saved_name': unique_filename,
                    'path': file_path
                })

        if uploaded_files:
            return jsonify({
                'success': True,
                'message': '파일이 성공적으로 업로드되었습니다.',
                'files': uploaded_files
            })
        else:
            return jsonify({
                'success': False,
                'message': '유효한 이미지 파일이 없습니다.'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'파일 업로드 중 오류가 발생했습니다: {str(e)}'
        })