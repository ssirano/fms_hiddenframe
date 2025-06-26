import math
from flask import Blueprint, request, jsonify, make_response, json
from controllers.auth import login_required
from sqlalchemy import text
from db import engine, get_session
from datetime import datetime

dms_list_bp = Blueprint('dms_list', __name__)

##### /dms_list/get_data - 도면정보 목록 조회 #####
@dms_list_bp.route('/dms_list/get_data', methods=['POST'])
@login_required
def get_data():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')
        bl_id = data.get('bl_id')
        fl_id = data.get('fl_id')
        search_keyword = data.get('keyword')
        page_size = int(data.get('page_size', 18))
        page_number = int(data.get('page_number', 1))
        sort_column = data.get('sort_column', 'dms_id')
        sort_direction = data.get('sort_direction', 'DESC')

        print(f"🔵 [dms_list] 도면정보 목록 조회 요청: prop_id={prop_id}, bl_id={bl_id}, fl_id={fl_id}, keyword={search_keyword}, page={page_number}, size={page_size}")

        if not all([em_id, prop_id]):
            return jsonify({
                'success': False,
                'message': '사용자 ID 또는 사업장 ID가 누락되었습니다.'
            }), 400

        # 기본 쿼리 (JSP 원본 기반)
        base_sql = """
            FROM dms pd
            LEFT JOIN prop prop ON pd.prop_id = prop.prop_id
            LEFT JOIN bl bl ON pd.bl_id = bl.bl_id
            LEFT JOIN fl fl ON pd.bl_id = fl.bl_id AND pd.fl_id = fl.fl_id
            LEFT JOIN em em ON pd.em_id = em.em_id
            WHERE pd.prop_id = :prop_id
        """
        
        # 조건절 추가
        conditions = []
        params = {'em_id': em_id, 'prop_id': prop_id}

        # 건물 필터
        if bl_id:
            conditions.append("pd.bl_id = :bl_id")
            params['bl_id'] = bl_id

        # 층 필터
        if fl_id:
            conditions.append("pd.fl_id = :fl_id")
            params['fl_id'] = fl_id

        # 키워드 검색 (JSP 원본 로직)
        if search_keyword:
            keyword_parts = search_keyword.strip().split()
            if keyword_parts:
                keyword_conditions = []
                for i, keyword in enumerate(keyword_parts[:50]):  # 최대 50개 키워드
                    if keyword.strip():
                        keyword = keyword.replace("'", "''")  # SQL 인젝션 방지
                        keyword_conditions.append(f"(LOWER(pd.contents) LIKE LOWER(:keyword_{i}) OR LOWER(em.name) LIKE LOWER(:keyword_{i}))")
                        params[f'keyword_{i}'] = f'%{keyword}%'
                
                if keyword_conditions:
                    conditions.append(f"({' AND '.join(keyword_conditions)})")
        
        if conditions:
            base_sql += " AND " + " AND ".join(conditions)

        # 총 개수 조회
        count_sql = text(f"SELECT COUNT(*) {base_sql}")
        
        # 메인 데이터 조회 (JSP 원본 SELECT 절)
        main_sql = f"""
            SELECT 
                pd.dms_id,
                pd.contents,
                DATE_FORMAT(pd.date_reg, '%Y-%m-%d') as date_reg,
                em.name as em_name,
                prop.name as prop_name,
                prop.prop_id,
                bl.name as bl_name,
                bl.bl_id,
                fl.name as fl_name,
                fl.fl_id,
                em.em_id
            {base_sql}
        """

        # 정렬 조건 (JSP 원본 정렬 로직)
        valid_sort_columns = ['dms_id', 'contents', 'date_reg', 'em_name', 'prop_name', 'bl_name', 'fl_name']
        if sort_column not in valid_sort_columns:
            sort_column = 'dms_id'
        if sort_direction.upper() not in ['ASC', 'DESC']:
            sort_direction = 'DESC'
        
        main_sql += f" ORDER BY {sort_column} {sort_direction}"

        with get_session() as session_obj:
            # 총 개수 실행
            total_count = session_obj.execute(count_sql, params).scalar()

            # 페이지네이션 적용
            offset = (page_number - 1) * page_size
            main_sql += f" LIMIT :limit OFFSET :offset"
            params['limit'] = page_size
            params['offset'] = offset
            
            # 메인 데이터 실행
            result = session_obj.execute(text(main_sql), params).fetchall()
            
            data_list = []
            for row in result:
                item = dict(row)
                
                # Null 값 처리
                for key, value in item.items():
                    if value is None:
                        item[key] = ''
                
                # 첨부파일 정보 조회 (JSP 원본 로직)
                attachment_sql = text("""
                    SELECT dms_image_id, filename 
                    FROM dms_image 
                    WHERE dms_id = :dms_id 
                    ORDER BY dms_image_id ASC
                """)
                
                attachments = session_obj.execute(attachment_sql, {'dms_id': item['dms_id']}).fetchall()
                item['attachments'] = [dict(att) for att in attachments]
                
                data_list.append(item)

            total_pages = math.ceil(total_count / page_size) if page_size > 0 else 1
            
            response_data = {
                'success': True,
                'message': '도면정보 목록 조회 성공',
                'result_data': data_list,
                'total_count': total_count,
                'total_pages': total_pages,
                'current_page': page_number
            }
            
            response = make_response(json.dumps(response_data, ensure_ascii=False))
            response.mimetype = 'application/json; charset=utf-8'
            return response

    except Exception as e:
        print(f"🔴 [dms_list] get_data 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'도면정보 목록 조회 중 오류가 발생했습니다: {str(e)}',
            'result_data': [],
            'total_count': 0,
            'total_pages': 1,
            'current_page': 1
        }), 500

##### /dms_list/get_bl_list - 건물 목록 조회 #####
@dms_list_bp.route('/dms_list/get_bl_list', methods=['POST'])
@login_required
def get_bl_list():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')

        print(f"🔵 [dms_list] 건물 목록 조회 요청: prop_id={prop_id}")

        if not all([em_id, prop_id]):
            return jsonify({
                'success': False,
                'message': '사용자 ID 또는 사업장 ID가 누락되었습니다.'
            }), 400

        # 건물 목록 조회 (JSP 원본 쿼리)
        sql = text("""
            SELECT bl_id, name as bl_name 
            FROM bl 
            WHERE prop_id = :prop_id 
            ORDER BY name ASC
        """)

        with get_session() as session_obj:
            result = session_obj.execute(sql, {'prop_id': prop_id}).fetchall()
            bl_list = [dict(row) for row in result]
            
            # Null 값 처리
            for item in bl_list:
                for key, value in item.items():
                    if value is None:
                        item[key] = ''

        return jsonify({
            'success': True,
            'message': '건물 목록 조회 성공',
            'data': bl_list
        })

    except Exception as e:
        print(f"🔴 [dms_list] get_bl_list 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'건물 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /dms_list/get_fl_list - 층 목록 조회 #####
@dms_list_bp.route('/dms_list/get_fl_list', methods=['POST'])
@login_required
def get_fl_list():
    try:
        data = request.get_json()
        prop_id = data.get('prop_id')
        bl_id = data.get('bl_id')

        print(f"🔵 [dms_list] 층 목록 조회 요청: prop_id={prop_id}, bl_id={bl_id}")

        if not all([prop_id, bl_id]):
            return jsonify({
                'success': False,
                'message': '사업장 ID 또는 건물 ID가 누락되었습니다.'
            }), 400

        # 층 목록 조회 (JSP 원본 쿼리)
        sql = text("""
            SELECT fl_id, name as fl_name 
            FROM fl 
            WHERE prop_id = :prop_id AND bl_id = :bl_id 
            ORDER BY name ASC
        """)

        with get_session() as session_obj:
            result = session_obj.execute(sql, {
                'prop_id': prop_id, 
                'bl_id': bl_id
            }).fetchall()
            fl_list = [dict(row) for row in result]
            
            # Null 값 처리
            for item in fl_list:
                for key, value in item.items():
                    if value is None:
                        item[key] = ''

        return jsonify({
            'success': True,
            'message': '층 목록 조회 성공',
            'data': fl_list
        })

    except Exception as e:
        print(f"🔴 [dms_list] get_fl_list 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'층 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /dms_list/download - 첨부파일 다운로드 #####
@dms_list_bp.route('/dms_list/download', methods=['GET'])
@login_required
def download_file():
    try:
        dms_id = request.args.get('dms_id')
        file_id = request.args.get('file_id')

        print(f"🔵 [dms_list] 파일 다운로드 요청: dms_id={dms_id}, file_id={file_id}")

        if not all([dms_id, file_id]):
            return jsonify({
                'success': False,
                'message': 'DMS ID 또는 파일 ID가 누락되었습니다.'
            }), 400

        # 파일 정보 조회
        sql = text("""
            SELECT filename, file_path 
            FROM dms_image 
            WHERE dms_id = :dms_id AND dms_image_id = :file_id
        """)

        with get_session() as session_obj:
            result = session_obj.execute(sql, {
                'dms_id': dms_id,
                'file_id': file_id
            }).fetchone()
            
            if not result:
                return jsonify({
                    'success': False,
                    'message': '파일을 찾을 수 없습니다.'
                }), 404
            
            file_info = dict(result)

        # 실제 파일 다운로드 로직은 별도 구현 필요
        # 여기서는 파일 정보만 반환
        return jsonify({
            'success': True,
            'message': '파일 정보 조회 성공',
            'data': file_info
        })

    except Exception as e:
        print(f"🔴 [dms_list] download 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'파일 다운로드 중 오류가 발생했습니다: {str(e)}'
        }), 500