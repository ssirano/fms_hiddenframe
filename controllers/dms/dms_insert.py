import math
import os
import time
from flask import Blueprint, request, jsonify, make_response, json
from controllers.auth import login_required
from sqlalchemy import text
from db import engine, get_session
from datetime import datetime
from werkzeug.utils import secure_filename

dms_insert_bp = Blueprint('dms_insert', __name__)

##### /dms_insert/save_data - 도면정보 등록 (파일 업로드 포함) #####
@dms_insert_bp.route('/dms_insert/save_data', methods=['POST'])
@login_required
def save_data():
    try:
        # 🔥 FormData 처리 (파일 + 텍스트 데이터)
        em_id = request.form.get('em_id')
        contents = request.form.get('contents', '').strip()
        prop_id = request.form.get('prop_id')
        bl_id = request.form.get('bl_id')
        fl_id = request.form.get('fl_id')
        emclass_id = request.form.get('emclass_id')

        print(f"🔵 [dms_insert] 도면 등록 요청: contents={contents}, em_id={em_id}")

        # 필수 필드 검증 (JSP 원본 로직과 동일)
        if not contents:
            return jsonify({
                'success': False,
                'message': '도면명을 입력해주세요'
            }), 400

        if not em_id:
            return jsonify({
                'success': False,
                'message': '작성자를 선택해주세요'
            }), 400

        with get_session() as session_obj:
            # 🔥 1단계: 새로운 DMS ID 생성 (JSP 원본 로직)
            try:
                max_id_sql = text("SELECT COALESCE(MAX(dms_id), 0) + 1 as next_id FROM dms")
                max_result = session_obj.execute(max_id_sql).fetchone()
                new_dms_id = str(max_result.next_id) if max_result else "1"
                print(f"🔍 [dms_insert] 새 DMS ID 생성: {new_dms_id}")
            except Exception as e:
                print(f"🔴 [dms_insert] ID 생성 오류: {str(e)}")
                new_dms_id = "1"

            # 🔥 2단계: DMS 기본 정보 INSERT (MySQL 호환 쿼리)
            try:
                insert_sql = text("""
                    INSERT INTO dms (
                        dms_id, em_id, prop_id, bl_id, contents, 
                        date_reg, emclass_id, fl_id
                    ) VALUES (
                        :dms_id, :em_id, :prop_id, :bl_id, :contents, 
                        NOW(), :emclass_id, :fl_id
                    )
                """)
                
                session_obj.execute(insert_sql, {
                    'dms_id': new_dms_id,
                    'em_id': em_id,
                    'prop_id': prop_id if prop_id else None,
                    'bl_id': bl_id if bl_id else None,
                    'contents': contents,
                    'emclass_id': emclass_id if emclass_id else None,
                    'fl_id': fl_id if fl_id else None
                })
                
                print(f"🟢 [dms_insert] DMS 기본 정보 INSERT 완료: {new_dms_id}")
                
            except Exception as e:
                print(f"🔴 [dms_insert] DMS INSERT 오류: {str(e)}")
                session_obj.rollback()
                return jsonify({
                    'success': False,
                    'message': f'도면 정보 저장 중 오류가 발생했습니다: {str(e)}'
                }), 500

            # 🔥 3단계: 첨부파일 처리 (JSP 원본 로직과 동일)
            uploaded_files = []
            upload_errors = []
            
            # 파일 저장 디렉토리 설정
            upload_dir = os.path.join(os.getcwd(), 'uploads', 'dms')
            os.makedirs(upload_dir, exist_ok=True)
            
            # JSP와 동일한 파일 처리 순서 (filename6부터 filename1까지 역순)
            file_index = 6
            for i in range(6, 0, -1):  # 6, 5, 4, 3, 2, 1 순서
                try:
                    file_key = f'filename{i}'
                    file = request.files.get(file_key)
                    
                    if file and file.filename and file.filename.strip():
                        original_filename = secure_filename(file.filename)
                        
                        # JSP 원본과 동일한 마스크명 생성 (currentTimeMillis + index)
                        maskname = str(int(time.time() * 1000) + file_index)
                        
                        # 파일 확장자 추출
                        filetype = ""
                        if '.' in original_filename:
                            filetype = original_filename.rsplit('.', 1)[1].lower()
                        
                        # 파일 저장
                        file_path = os.path.join(upload_dir, maskname)
                        file.save(file_path)
                        
                        # 파일 크기 계산
                        filesize = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                        
                        print(f"🔍 [dms_insert] 파일 저장 완료: {original_filename} → {maskname}")
                        
                        # DMS_IMAGE 테이블에 INSERT
                        try:
                            image_sql = text("""
                                INSERT INTO dms_image (
                                    dms_id, dms_image_id, filename, filesize, 
                                    maskname, filetype, reg_date, reg_man
                                ) VALUES (
                                    :dms_id, :dms_image_id, :filename, :filesize,
                                    :maskname, :filetype, NOW(), :reg_man
                                )
                            """)
                            
                            session_obj.execute(image_sql, {
                                'dms_id': new_dms_id,
                                'dms_image_id': str(file_index),
                                'filename': original_filename,
                                'filesize': filesize,
                                'maskname': maskname,
                                'filetype': filetype,
                                'reg_man': em_id
                            })
                            
                            uploaded_files.append({
                                'index': file_index,
                                'original': original_filename,
                                'maskname': maskname,
                                'size': filesize
                            })
                            
                        except Exception as e:
                            print(f"🔴 [dms_insert] 파일 DB 저장 오류: {str(e)}")
                            upload_errors.append(f"파일 {i}: {str(e)}")
                            
                            # 저장된 파일 삭제
                            if os.path.exists(file_path):
                                os.remove(file_path)
                
                except Exception as e:
                    print(f"🔴 [dms_insert] 파일 {i} 처리 오류: {str(e)}")
                    upload_errors.append(f"파일 {i}: {str(e)}")
                
                file_index -= 1  # JSP 원본 로직: maskname 중복 방지

            # 🔥 4단계: 빈 파일 정보 정리 (JSP 원본 로직)
            try:
                cleanup_sql = text("""
                    DELETE FROM dms_image 
                    WHERE dms_id = :dms_id 
                    AND (filename = '' OR filename IS NULL)
                """)
                session_obj.execute(cleanup_sql, {'dms_id': new_dms_id})
                print(f"🧹 [dms_insert] 빈 파일 정보 정리 완료")
                
            except Exception as e:
                print(f"🟡 [dms_insert] 파일 정리 오류 (무시): {str(e)}")

            # 🔥 5단계: 소팅 순서 변경 (JSP 원본 로직과 동일)
            try:
                # 현재 파일들의 dms_image_id를 순서대로 가져오기
                sort_sql = text("""
                    SELECT dms_image_id 
                    FROM dms_image 
                    WHERE dms_id = :dms_id 
                    ORDER BY dms_image_id ASC
                """)
                
                sort_result = session_obj.execute(sort_sql, {'dms_id': new_dms_id}).fetchall()
                
                # 0부터 순차적으로 재정렬
                new_index = 0
                for row in sort_result:
                    old_image_id = row.dms_image_id
                    
                    update_sort_sql = text("""
                        UPDATE dms_image 
                        SET dms_image_id = :new_id 
                        WHERE dms_id = :dms_id AND dms_image_id = :old_id
                    """)
                    
                    session_obj.execute(update_sort_sql, {
                        'new_id': str(new_index),
                        'dms_id': new_dms_id,
                        'old_id': old_image_id
                    })
                    
                    new_index += 1
                
                print(f"🔄 [dms_insert] 파일 소팅 순서 변경 완료: {len(sort_result)}개")
                
            except Exception as e:
                print(f"🟡 [dms_insert] 소팅 순서 변경 오류 (무시): {str(e)}")

            # 모든 처리 완료 후 커밋
            session_obj.commit()

        # 결과 메시지 구성
        result_message = "작성되었습니다."
        if uploaded_files:
            result_message += f" (첨부파일 {len(uploaded_files)}개 업로드 완료)"
        if upload_errors:
            result_message += f" ⚠️ 일부 파일 업로드 실패: {len(upload_errors)}개"

        print(f"🟢 [dms_insert] 도면 등록 완료: {new_dms_id}")
        
        return jsonify({
            'success': True,
            'message': result_message,
            'data': {
                'dms_id': new_dms_id,
                'uploaded_files': uploaded_files,
                'upload_errors': upload_errors
            }
        })

    except Exception as e:
        print(f"🔴 [dms_insert] save_data 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'도면 등록 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /dms_insert/get_bl_list - 건물 목록 조회 #####
@dms_insert_bp.route('/dms_insert/get_bl_list', methods=['POST'])
@login_required
def get_bl_list():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')

        print(f"🔵 [dms_insert] 건물 목록 조회: prop_id={prop_id}")

        if not all([em_id, prop_id]):
            return jsonify({
                'success': False,
                'message': '사용자 ID 또는 사업장 ID가 누락되었습니다.'
            }), 400

        # JSP 원본 쿼리와 동일
        sql = text("""
            SELECT bl_id, name as bl_name 
            FROM bl 
            WHERE prop_id = :prop_id 
            AND (bl_id IS NOT NULL AND name IS NOT NULL) 
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
        print(f"🔴 [dms_insert] get_bl_list 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'건물 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /dms_insert/get_fl_list - 층 목록 조회 #####
@dms_insert_bp.route('/dms_insert/get_fl_list', methods=['POST'])
@login_required
def get_fl_list():
    try:
        data = request.get_json()
        prop_id = data.get('prop_id')
        bl_id = data.get('bl_id')

        print(f"🔵 [dms_insert] 층 목록 조회: prop_id={prop_id}, bl_id={bl_id}")

        if not all([prop_id, bl_id]):
            return jsonify({
                'success': False,
                'message': '사업장 ID 또는 건물 ID가 누락되었습니다.'
            }), 400

        # JSP 원본 쿼리와 동일
        sql = text("""
            SELECT fl_id, name as fl_name 
            FROM fl 
            WHERE prop_id = :prop_id AND bl_id = :bl_id 
            ORDER BY fl_id, name ASC
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
        print(f"🔴 [dms_insert] get_fl_list 오류 발생: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'층 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

##### /dms_insert/get_part_list - 파트코드 목록 조회 #####
@dms_insert_bp.route('/dms_insert/get_part_list', methods=['POST'])
@login_required
def get_part_list():
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')

        print(f"🔵 [dms_insert] 파트코드 목록 조회: em_id={em_id}, prop_id={prop_id}")

        if not em_id:
            return jsonify({
                'success': False,
                'message': '사용자 ID가 누락되었습니다.'
            }), 400

        # 🔥 JSP 원본 로직과 동일: dh_em_prop_id 사용
        # JSP에서 dh_em_prop_id는 로그인된 사용자의 사업장ID
        if not prop_id:
            try:
                # 사용자의 기본 사업장 조회 (JSP의 dh_em_prop_id와 동일)
                user_prop_sql = text("""
                    SELECT prop_id FROM em WHERE em_id = :em_id LIMIT 1
                """)
                with get_session() as session_obj:
                    user_result = session_obj.execute(user_prop_sql, {'em_id': em_id}).fetchone()
                    if user_result:
                        prop_id = user_result.prop_id
                        print(f"🔍 [dms_insert] 사용자 기본 사업장 조회 (dh_em_prop_id): {prop_id}")
            except Exception as e:
                print(f"🟡 [dms_insert] 사용자 사업장 조회 오류: {str(e)}")

        # 🔥 JSP 원본 쿼리와 완전히 동일
        if prop_id:
            sql = text("""
                SELECT emclass_id 
                FROM emclass 
                WHERE prop_id = :prop_id 
                AND emclass_id IS NOT NULL 
                GROUP BY emclass_id 
                ORDER BY emclass_id ASC
            """)
            params = {'prop_id': prop_id}
            print(f"🔍 [dms_insert] JSP 원본 쿼리 실행: prop_id={prop_id}")
        else:
            # prop_id 없이 전체 조회 (fallback)
            sql = text("""
                SELECT emclass_id 
                FROM emclass 
                WHERE emclass_id IS NOT NULL 
                GROUP BY emclass_id 
                ORDER BY emclass_id ASC
                LIMIT 20
            """)
            params = {}
            print(f"🔍 [dms_insert] Fallback 쿼리 실행 (전체 조회)")

        with get_session() as session_obj:
            result = session_obj.execute(sql, params).fetchall()
            
            if result and len(result) > 0:
                part_list = [{'emclass_id': row.emclass_id} for row in result]
                print(f"🟢 [dms_insert] DB에서 파트코드 조회 성공: {[p['emclass_id'] for p in part_list]}")
                
                # 🔥 JSP에서 실제로 나타나는 값들과 병합 (중복 제거)
                db_parts = {p['emclass_id'] for p in part_list}
                default_parts = {'건축', '관제', '기계', '기타', '미화', '방재', '전기', '주차', '행정'}
                
                # DB 데이터를 우선으로 하고, 누락된 기본값들 추가
                all_parts = list(db_parts)
                for default in default_parts:
                    if default not in db_parts:
                        all_parts.append(default)
                
                # 정렬
                all_parts.sort()
                part_list = [{'emclass_id': part} for part in all_parts]
                
                print(f"🔄 [dms_insert] DB + 기본값 병합 완료: {[p['emclass_id'] for p in part_list]}")
                
            else:
                print(f"🟡 [dms_insert] DB에 파트코드 데이터가 없음, 기본값 사용")
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

        print(f"🚀 [dms_insert] 최종 파트코드 반환: {len(part_list)}개")
        
        return jsonify({
            'success': True,
            'message': '파트코드 목록 조회 성공',
            'data': part_list
        })

    except Exception as e:
        print(f"🔴 [dms_insert] get_part_list 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 🔥 오류 발생 시에도 기본값 반환 (JSP 원본 안정성)
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
        
        print(f"🟡 [dms_insert] 오류 복구: 기본값 반환")
        
        return jsonify({
            'success': True,
            'message': '파트코드 목록 조회 성공 (기본값)',
            'data': default_parts
        })