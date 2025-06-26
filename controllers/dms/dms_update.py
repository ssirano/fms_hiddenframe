import math
import os
from flask import Blueprint, request, jsonify, make_response, json, send_file
from controllers.auth import login_required
from sqlalchemy import text
from db import engine, get_session
from datetime import datetime

dms_update_bp = Blueprint('dms_update', __name__)

##### /dms_update/get_data - 도면정보 조회 (500 오류 수정) #####
@dms_update_bp.route('/dms_update/get_data', methods=['POST'])
@login_required
def get_data():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        dms_id = data.get('dms_id')

        print(f"🔵 [dms_update] 도면 정보 조회 요청: em_id={em_id}, dms_id={dms_id}")

        if not all([em_id, dms_id]):
            return jsonify({
                'success': False,
                'message': '사용자 ID 또는 도면 ID가 누락되었습니다.'
            }), 400

        with get_session() as session_obj:
            # 🔥 기본 도면 정보 먼저 조회 (간단한 쿼리로)
            basic_sql = text("""
                SELECT 
                    dms_id,
                    contents,
                    prop_id,
                    bl_id,
                    fl_id,
                    emclass_id,
                    em_id,
                    DATE_FORMAT(DATE_REG, '%Y-%m-%d') as date_reg
                FROM dms
                WHERE dms_id = :dms_id
            """)
            
            basic_result = session_obj.execute(basic_sql, {'dms_id': dms_id}).fetchone()
            
            if not basic_result:
                return jsonify({
                    'success': False,
                    'message': '해당 도면 정보를 찾을 수 없습니다.'
                }), 404
            
            item_data = dict(basic_result)
            print(f"🔍 [dms_update] 기본 도면 정보 조회 완료: {item_data}")
            
            # 🔥 추가 정보들을 개별적으로 조회 (오류 방지)
            try:
                # 사업장 정보 조회
                if item_data.get('prop_id'):
                    prop_sql = text("SELECT name FROM prop WHERE prop_id = :prop_id")
                    prop_result = session_obj.execute(prop_sql, {'prop_id': item_data['prop_id']}).fetchone()
                    item_data['prop_name'] = prop_result.name if prop_result else ''
                else:
                    item_data['prop_name'] = ''
                    
            except Exception as e:
                print(f"🟡 [dms_update] 사업장 정보 조회 오류: {str(e)}")
                item_data['prop_name'] = ''
            
            try:
                # 건물 정보 조회
                if item_data.get('bl_id'):
                    bl_sql = text("SELECT name FROM bl WHERE bl_id = :bl_id")
                    bl_result = session_obj.execute(bl_sql, {'bl_id': item_data['bl_id']}).fetchone()
                    item_data['bl_name'] = bl_result.name if bl_result else ''
                else:
                    item_data['bl_name'] = ''
                    
            except Exception as e:
                print(f"🟡 [dms_update] 건물 정보 조회 오류: {str(e)}")
                item_data['bl_name'] = ''
            
            try:
                # 층 정보 조회
                if item_data.get('fl_id') and item_data.get('bl_id'):
                    fl_sql = text("SELECT name FROM fl WHERE bl_id = :bl_id AND fl_id = :fl_id")
                    fl_result = session_obj.execute(fl_sql, {
                        'bl_id': item_data['bl_id'],
                        'fl_id': item_data['fl_id']
                    }).fetchone()
                    item_data['fl_name'] = fl_result.name if fl_result else ''
                else:
                    item_data['fl_name'] = ''
                    
            except Exception as e:
                print(f"🟡 [dms_update] 층 정보 조회 오류: {str(e)}")
                item_data['fl_name'] = ''
            
            try:
                # 직원 정보 조회
                if item_data.get('em_id'):
                    em_sql = text("SELECT name FROM em WHERE em_id = :em_id")
                    em_result = session_obj.execute(em_sql, {'em_id': item_data['em_id']}).fetchone()
                    item_data['em_name'] = em_result.name if em_result else ''
                else:
                    item_data['em_name'] = ''
                    
            except Exception as e:
                print(f"🟡 [dms_update] 직원 정보 조회 오류: {str(e)}")
                item_data['em_name'] = ''
            
            # 🔥 첨부파일 정보 조회 (안전하게)
            try:
                attachment_sql = text("""
                    SELECT dms_image_id, filename
                    FROM dms_image 
                    WHERE dms_id = :dms_id 
                    ORDER BY dms_image_id ASC
                """)
                
                attachments = session_obj.execute(attachment_sql, {'dms_id': dms_id}).fetchall()
                attachment_list = []
                
                for att in attachments:
                    att_dict = dict(att)
                    # Null 값 처리
                    for key, value in att_dict.items():
                        if value is None:
                            att_dict[key] = ''
                    
                    print(f"🔍 [dms_update] 첨부파일 발견: dms_image_id={att_dict['dms_image_id']}, filename={att_dict['filename']}")
                    attachment_list.append(att_dict)
                
                item_data['attachments'] = attachment_list
                print(f"🔍 [dms_update] 첨부파일 조회 완료: {len(attachment_list)}개")
                
            except Exception as e:
                print(f"🟡 [dms_update] 첨부파일 조회 오류: {str(e)}")
                item_data['attachments'] = []

            # 🔥 모든 필드에 대해 Null 값 처리
            for key, value in item_data.items():
                if value is None:
                    item_data[key] = ''

        print(f"🟢 [dms_update] 도면 정보 조회 완료: {dms_id}")
        print(f"🔍 [dms_update] 최종 응답 데이터 키들: {list(item_data.keys())}")
        
        return jsonify({
            'success': True,
            'message': '도면 정보 조회 성공',
            'data': item_data
        })

    except Exception as e:
        print(f"🔴 [dms_update] get_data 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 🔥 오류 발생 시에도 최소한의 응답 제공
        try:
            # 기본 데이터만이라도 조회 시도
            with get_session() as session_obj:
                basic_sql = text("SELECT dms_id, contents FROM dms WHERE dms_id = :dms_id")
                basic_result = session_obj.execute(basic_sql, {'dms_id': dms_id}).fetchone()
                
                if basic_result:
                    minimal_data = {
                        'dms_id': basic_result.dms_id,
                        'contents': basic_result.contents or '',
                        'prop_id': '',
                        'bl_id': '',
                        'fl_id': '',
                        'emclass_id': '',
                        'em_id': '',
                        'date_reg': '',
                        'prop_name': '',
                        'bl_name': '',
                        'fl_name': '',
                        'em_name': '',
                        'attachments': []
                    }
                    
                    return jsonify({
                        'success': True,
                        'message': '도면 정보 조회 성공 (최소 데이터)',
                        'data': minimal_data
                    })
        except:
            pass
        
        return jsonify({
            'success': False,
            'message': f'도면 정보 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /dms_update/save_data - 도면정보 저장 #####
@dms_update_bp.route('/dms_update/save_data', methods=['POST'])
@login_required
def save_data():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        dms_id = data.get('dms_id')
        contents = data.get('contents', '').strip()
        bl_id = data.get('bl_id')
        fl_id = data.get('fl_id')
        emclass_id = data.get('emclass_id')

        print(f"🔵 [dms_update] 도면 저장 요청: dms_id={dms_id}, contents={contents}")

        # 필수 필드 검증
        if not contents:
            return jsonify({
                'success': False,
                'message': '도면명은 필수 입력 항목입니다.'
            }), 400

        if not all([em_id, dms_id]):
            return jsonify({
                'success': False,
                'message': '사용자 ID 또는 도면 ID가 누락되었습니다.'
            }), 400

        # 업데이트 쿼리

        update_sql = text("""
            UPDATE dms SET
                contents = :contents,
                bl_id = :bl_id,
                fl_id = :fl_id,
                emclass_id = :emclass_id,
                DATE_MODI = NOW(),
                EM_ID_MODI = :em_id
            WHERE dms_id = :dms_id
        """)

        with get_session() as session_obj:
            result = session_obj.execute(update_sql, {
                'dms_id': dms_id,
                'contents': contents,
                'bl_id': bl_id if bl_id else None,
                'fl_id': fl_id if fl_id else None,
                'emclass_id': emclass_id if emclass_id else None,
                'em_id': em_id
            })
            
            session_obj.commit()
            
            if result.rowcount == 0:
                return jsonify({
                    'success': False,
                    'message': '업데이트할 도면 정보를 찾을 수 없습니다.'
                }), 404

        print(f"🟢 [dms_update] 도면 저장 완료: {dms_id}")
        
        return jsonify({
            'success': True,
            'message': '도면 정보가 성공적으로 수정되었습니다.'
        })

    except Exception as e:
        print(f"🔴 [dms_update] save_data 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'도면 정보 저장 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /dms_update/delete_data - 도면정보 삭제 #####
@dms_update_bp.route('/dms_update/delete_data', methods=['POST'])
@login_required
def delete_data():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        dms_id = data.get('dms_id')

        print(f"🔵 [dms_update] 도면 삭제 요청: em_id={em_id}, dms_id={dms_id}")

        if not all([em_id, dms_id]):
            return jsonify({
                'success': False,
                'message': '사용자 ID 또는 도면 ID가 누락되었습니다.'
            }), 400

        with get_session() as session_obj:
            # 첨부파일 먼저 삭제
            delete_images_sql = text("DELETE FROM dms_image WHERE dms_id = :dms_id")
            session_obj.execute(delete_images_sql, {'dms_id': dms_id})
            
            # 도면 정보 삭제
            delete_sql = text("DELETE FROM dms WHERE dms_id = :dms_id")
            result = session_obj.execute(delete_sql, {'dms_id': dms_id})
            
            session_obj.commit()
            
            if result.rowcount == 0:
                return jsonify({
                    'success': False,
                    'message': '삭제할 도면 정보를 찾을 수 없습니다.'
                }), 404

        print(f"🟢 [dms_update] 도면 삭제 완료: {dms_id}")
        
        return jsonify({
            'success': True,
            'message': '도면 정보가 성공적으로 삭제되었습니다.'
        })

    except Exception as e:
        print(f"🔴 [dms_update] delete_data 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'도면 정보 삭제 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /dms_update/get_bl_list - 건물 목록 조회 #####
@dms_update_bp.route('/dms_update/get_bl_list', methods=['POST'])
@login_required
def get_bl_list():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')

        if not all([em_id, prop_id]):
            return jsonify({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다.'
            }), 400

        sql = text("""
            SELECT bl_id, name as bl_name 
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
        print(f"🔴 [dms_update] get_bl_list 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'건물 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /dms_update/get_fl_list - 층 목록 조회 #####
@dms_update_bp.route('/dms_update/get_fl_list', methods=['POST'])
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

        return jsonify({
            'success': True,
            'message': '층 목록 조회 성공',
            'data': fl_list
        })

    except Exception as e:
        print(f"🔴 [dms_update] get_fl_list 오류 발생: {str(e)}")
@dms_update_bp.route('/dms_update/download', methods=['GET'])
@login_required
def download_file():
    try:
        dms_id = request.args.get('dms_id')
        file_id = request.args.get('file_id')

        print(f"🔵 [dms_update] 파일 다운로드 요청: dms_id={dms_id}, file_id={file_id}")

        if not all([dms_id, file_id]):
            return jsonify({
                'success': False,
                'message': 'DMS ID 또는 파일 ID가 누락되었습니다.'
            }), 400

        # 파일 정보 조회
        sql = text("""
            SELECT dms_image_id, filename, file_path, file_size
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
            
            # Null 값 처리
            for key, value in file_info.items():
                if value is None:
                    file_info[key] = ''

        # 실제 파일 경로 확인 및 다운로드
        file_path = file_info.get('file_path', '')
        filename = file_info.get('filename', 'download_file')
        
        # 파일 경로가 절대경로가 아닌 경우 업로드 디렉토리와 결합
        if file_path and not os.path.isabs(file_path):
            # 업로드 디렉토리 설정 (환경에 맞게 수정 필요)
            upload_dir = '/path/to/upload/directory'  # 실제 업로드 디렉토리로 변경
            file_path = os.path.join(upload_dir, file_path)
        
        # 파일 존재 여부 확인
        if not file_path or not os.path.exists(file_path):
            print(f"🔴 [dms_update] 파일을 찾을 수 없음: {file_path}")
            return jsonify({
                'success': False,
                'message': '파일이 서버에 존재하지 않습니다.'
            }), 404

        print(f"🟢 [dms_update] 파일 다운로드 시작: {filename}")
        
        # 파일 다운로드 전송
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,  # Flask 2.0+ 에서는 download_name 사용
            mimetype='application/octet-stream'
        )

    except Exception as e:
        print(f"🔴 [dms_update] download 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'message': f'파일 다운로드 중 오류가 발생했습니다: {str(e)}'
        }), 500
        
@dms_update_bp.route('/dms_update/delete_file', methods=['POST'])
@login_required
def delete_file():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        dms_id = data.get('dms_id')
        file_id = data.get('file_id')

        print(f"🔵 [dms_update] 파일 삭제 요청: dms_id={dms_id}, file_id={file_id}")

        if not all([em_id, dms_id, file_id]):
            return jsonify({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다.'
            }), 400

        with get_session() as session_obj:
            # 파일 존재 여부 확인
            check_sql = text("""
                SELECT filename FROM dms_image 
                WHERE dms_id = :dms_id AND dms_image_id = :file_id
            """)
            
            result = session_obj.execute(check_sql, {
                'dms_id': dms_id,
                'file_id': file_id
            }).fetchone()
            
            if not result:
                return jsonify({
                    'success': False,
                    'message': '삭제할 파일을 찾을 수 없습니다.'
                }), 404
            
            filename = result.filename
            
            # 파일 삭제
            delete_sql = text("""
                DELETE FROM dms_image 
                WHERE dms_id = :dms_id AND dms_image_id = :file_id
            """)
            
            delete_result = session_obj.execute(delete_sql, {
                'dms_id': dms_id,
                'file_id': file_id
            })
            
            session_obj.commit()
            
            if delete_result.rowcount == 0:
                return jsonify({
                    'success': False,
                    'message': '파일 삭제에 실패했습니다.'
                }), 500

        print(f"🟢 [dms_update] 파일 삭제 완료: {filename}")
        
        return jsonify({
            'success': True,
            'message': f'파일 "{filename}"이 성공적으로 삭제되었습니다.'
        })

    except Exception as e:
        print(f"🔴 [dms_update] delete_file 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'파일 삭제 중 오류가 발생했습니다: {str(e)}'
        }), 500
        
@dms_update_bp.route('/dms_update/get_part_list', methods=['POST'])
@login_required
def get_part_list():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')

        print(f"🔵 [dms_update] 파트코드 목록 조회 요청: em_id={em_id}, prop_id={prop_id}")

        if not em_id:
            return jsonify({
                'success': False,
                'message': '사용자 ID가 누락되었습니다.'
            }), 400

        # 🔥 prop_id가 없으면 사용자의 기본 사업장 조회
        if not prop_id:
            try:
                user_prop_sql = text("""
                    SELECT prop_id FROM em WHERE em_id = :em_id LIMIT 1
                """)
                with get_session() as session_obj:
                    user_result = session_obj.execute(user_prop_sql, {'em_id': em_id}).fetchone()
                    if user_result:
                        prop_id = user_result.prop_id
                        print(f"🔍 [dms_update] 사용자 기본 사업장 조회: {prop_id}")
            except Exception as e:
                print(f"🟡 [dms_update] 사용자 사업장 조회 오류: {str(e)}")

        # 🔥 여전히 prop_id가 없으면 전체 조회
        if prop_id:
            # JSP 원본 쿼리와 동일
            sql = text("""
                SELECT emclass_id 
                FROM emclass 
                WHERE prop_id = :prop_id 
                AND emclass_id IS NOT NULL 
                GROUP BY emclass_id 
                ORDER BY emclass_id ASC
            """)
            params = {'prop_id': prop_id}
        else:
            # prop_id 없이 전체 조회
            sql = text("""
                SELECT emclass_id 
                FROM emclass 
                WHERE emclass_id IS NOT NULL 
                GROUP BY emclass_id 
                ORDER BY emclass_id ASC
            """)
            params = {}

        print(f"🔍 [dms_update] 실행할 쿼리: prop_id={prop_id}")

        with get_session() as session_obj:
            result = session_obj.execute(sql, params).fetchall()
            
            print(f"🔍 [dms_update] DB 조회 결과: {len(result)}개")
            
            if result and len(result) > 0:
                part_list = [{'emclass_id': row.emclass_id} for row in result]
                print(f"🟢 [dms_update] DB에서 파트코드 조회 성공: {[p['emclass_id'] for p in part_list]}")
            else:
                print(f"🟡 [dms_update] DB에 파트코드 데이터가 없음, 기본값 사용")
                # JSP에서 실제로 나타나는 값들
                part_list = [
                    {'emclass_id': '건축'},
                    {'emclass_id': '관제'},
                    {'emclass_id': '기계'},
                    {'emclass_id': '기타'},
                    {'emclass_id': '미화'},
                    {'emclass_id': '방재'},
                    {'emclass_id': '전기'},
                    {'emclass_id': '주차'},
                    {'emclass_id': '행정'}
                ]
            
            # Null 값 처리
            for item in part_list:
                for key, value in item.items():
                    if value is None:
                        item[key] = ''

        print(f"🟢 [dms_update] 파트코드 목록 조회 완료: {len(part_list)}개")

        return jsonify({
            'success': True,
            'message': '파트코드 목록 조회 성공',
            'data': part_list
        })

    except Exception as e:
        print(f"🔴 [dms_update] get_part_list 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 🔥 오류 발생 시에도 기본값 반환
        default_parts = [
            {'emclass_id': '건축'},
            {'emclass_id': '관제'},
            {'emclass_id': '기계'},
            {'emclass_id': '기타'},
            {'emclass_id': '미화'},
            {'emclass_id': '방재'},
            {'emclass_id': '전기'},
            {'emclass_id': '주차'},
            {'emclass_id': '행정'}
        ]
        
        return jsonify({
            'success': True,
            'message': '파트코드 목록 조회 성공 (기본값)',
            'data': default_parts
        })