import math
from flask import Blueprint, request, jsonify, make_response, json
from controllers.auth import login_required
from sqlalchemy import text
from db import engine, get_session
from datetime import datetime

rm_tenant_bp = Blueprint('rm_tenant', __name__)

@rm_tenant_bp.route('/rm_tenant/test', methods=['GET', 'POST'])
def test_route():
    """테스트용 라우트"""
    return jsonify({
        'success': True,
        'message': 'rm_tenant Blueprint가 정상 작동합니다!'
    })

@rm_tenant_bp.route('/rm_tenant/get_tenant_info', methods=['POST'])
@login_required
def get_tenant_info():
    """입주사 정보 조회 (수정 모달용)"""
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        rmtenant_id = data.get('rmtenant_id')
        
        # 파라미터 검증
        if not all([em_id, rmtenant_id]):
            return jsonify({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다.'
            }), 400
        
        # 입주사 정보 조회 SQL
        sql = text("""
            SELECT 
                rmtenant_id,
                prop_id,
                bl_id,
                fl_id,
                rm_id,
                tenant_name,
                move_in,
                move_out,
                comments
            FROM rmtenant
            WHERE rmtenant_id = :rmtenant_id
        """)
        
        with get_session() as session_obj:
            result = session_obj.execute(sql, {
                'rmtenant_id': rmtenant_id
            }).fetchone()
            
            if not result:
                return jsonify({
                    'success': False,
                    'message': '입주사 정보를 찾을 수 없습니다.'
                }), 404
            
            tenant_data = dict(result)
            
            # Null 값 처리
            for key, value in tenant_data.items():
                if value is None:
                    tenant_data[key] = ''
        
        return jsonify({
            'success': True,
            'message': '조회 성공',
            'data': tenant_data
        })
        
    except Exception as e:
        print(f"🔴 입주사 정보 조회 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'처리 중 오류가 발생했습니다: {str(e)}'
        }), 500

@rm_tenant_bp.route('/rm_tenant/save_tenant', methods=['POST'])
@login_required
def save_tenant():
    """입주사 저장 (신규 등록)"""
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        prop_id = data.get('prop_id')
        bl_id = data.get('bl_id')
        fl_id = data.get('fl_id')
        rm_id = data.get('rm_id')
        tenant_name = data.get('tenant_name', '').strip()
        move_in = data.get('move_in')
        move_out = data.get('move_out')
        comments = data.get('comments', '').strip()
        
        # 파라미터 검증
        if not all([em_id, prop_id, bl_id, fl_id, rm_id, tenant_name]):
            return jsonify({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다.'
            }), 400
        
        # 날짜 유효성 검사
        if move_in and move_out and move_in > move_out:
            return jsonify({
                'success': False,
                'message': '퇴점일이 입점일보다 빠를 수 없습니다.'
            }), 400
        
        with get_session() as session_obj:
            # 중복 체크 (같은 실에 같은 입주사명이 있는지)
            check_sql = text("""
                SELECT COUNT(*) as cnt 
                FROM rmtenant 
                WHERE prop_id = :prop_id AND bl_id = :bl_id AND fl_id = :fl_id AND rm_id = :rm_id 
                    AND tenant_name = :tenant_name
                    AND (move_out IS NULL OR move_out = '')
            """)
            
            duplicate_count = session_obj.execute(check_sql, {
                'prop_id': prop_id,
                'bl_id': bl_id,
                'fl_id': fl_id,
                'rm_id': rm_id,
                'tenant_name': tenant_name
            }).fetchone()
            
            if duplicate_count and duplicate_count.cnt > 0:
                return jsonify({
                    'success': False,
                    'message': '해당 실에 동일한 입주사가 이미 등록되어 있습니다.'
                }), 400
            
            # rmtenant_id 생성 (MariaDB 방식)
            try:
                # COALESCE(MAX + 1, 1) 방식 사용 (오라클 nvl과 동일)
                id_sql = text("SELECT COALESCE(MAX(rmtenant_id) + 1, 1) as new_id FROM rmtenant")
                new_id = session_obj.execute(id_sql).fetchone().new_id
            except:
                new_id = 1
            
            # 건물, 층, 실 이름 조회 (JSP와 동일하게)
            building_sql = text("SELECT name FROM bl WHERE bl_id = :bl_id")
            building_result = session_obj.execute(building_sql, {'bl_id': bl_id}).fetchone()
            bl_name = building_result.name if building_result else ''
            
            floor_sql = text("SELECT name FROM fl WHERE fl_id = :fl_id") 
            floor_result = session_obj.execute(floor_sql, {'fl_id': fl_id}).fetchone() 
            fl_name = floor_result.name if floor_result else ''
            
            room_sql = text("SELECT name FROM rm WHERE rm_id = :rm_id")
            room_result = session_obj.execute(room_sql, {'rm_id': rm_id}).fetchone()
            rm_name = room_result.name if room_result else ''
            
            # 입주사 등록 (JSP와 동일한 컬럼 구조)
            insert_sql = text("""
                INSERT INTO rmtenant (
                    rmtenant_id, tenant_name, prop_id, bl_id, bl_name, fl_id, fl_name, rm_id, rm_name,
                    move_in, move_out, em_reg, date_reg, comments
                ) VALUES (
                    :rmtenant_id, :tenant_name, :prop_id, :bl_id, :bl_name, :fl_id, :fl_name, :rm_id, :rm_name,
                    :move_in, :move_out, :em_id, NOW(), :comments
                )
            """)
            
            session_obj.execute(insert_sql, {
                'rmtenant_id': new_id,
                'tenant_name': tenant_name,
                'prop_id': prop_id,
                'bl_id': bl_id,
                'bl_name': bl_name,
                'fl_id': fl_id,
                'fl_name': fl_name,
                'rm_id': rm_id,
                'rm_name': rm_name,
                'move_in': move_in if move_in else None,
                'move_out': move_out if move_out else None,
                'em_id': em_id,
                'comments': comments
            })
            
            session_obj.commit()
        
        return jsonify({
            'success': True,
            'message': '저장되었습니다.',
            'data': {'rmtenant_id': new_id}
        })
        
    except Exception as e:
        print(f"🔴 입주사 저장 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'처리 중 오류가 발생했습니다: {str(e)}'
        }), 500

@rm_tenant_bp.route('/rm_tenant/update_tenant', methods=['POST'])
@login_required
def update_tenant():
    """입주사 수정"""
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        rmtenant_id = data.get('rmtenant_id')
        tenant_name = data.get('tenant_name', '').strip()
        move_in = data.get('move_in')
        move_out = data.get('move_out')
        comments = data.get('comments', '').strip()
        
        # 파라미터 검증
        if not all([em_id, rmtenant_id, tenant_name]):
            return jsonify({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다.'
            }), 400
        
        # 날짜 유효성 검사
        if move_in and move_out and move_in > move_out:
            return jsonify({
                'success': False,
                'message': '퇴점일이 입점일보다 빠를 수 없습니다.'
            }), 400
        
        with get_session() as session_obj:
            # 기존 정보 조회
            check_sql = text("""
                SELECT prop_id, bl_id, fl_id, rm_id, tenant_name as old_tenant_name 
                FROM rmtenant 
                WHERE rmtenant_id = :rmtenant_id
            """)
            
            existing = session_obj.execute(check_sql, {
                'rmtenant_id': rmtenant_id
            }).fetchone()
            
            if not existing:
                return jsonify({
                    'success': False,
                    'message': '수정할 입주사 정보를 찾을 수 없습니다.'
                }), 404
            
            # 입주사명이 변경된 경우 중복 체크
            if existing.old_tenant_name != tenant_name:
                duplicate_sql = text("""
                    SELECT COUNT(*) as cnt 
                    FROM rmtenant 
                    WHERE prop_id = :prop_id AND bl_id = :bl_id AND fl_id = :fl_id AND rm_id = :rm_id 
                        AND tenant_name = :tenant_name
                        AND rmtenant_id != :rmtenant_id
                        AND (move_out IS NULL OR move_out = '')
                """)
                
                duplicate_count = session_obj.execute(duplicate_sql, {
                    'prop_id': existing.prop_id,
                    'bl_id': existing.bl_id,
                    'fl_id': existing.fl_id,
                    'rm_id': existing.rm_id,
                    'tenant_name': tenant_name,
                    'rmtenant_id': rmtenant_id
                }).fetchone()
                
                if duplicate_count and duplicate_count.cnt > 0:
                    return jsonify({
                        'success': False,
                        'message': '해당 실에 동일한 입주사가 이미 등록되어 있습니다.'
                    }), 400
            
            # 입주사 정보 업데이트 (JSP와 동일)
            update_sql = text("""
                UPDATE rmtenant 
                SET tenant_name = :tenant_name,
                    move_in = :move_in,
                    move_out = :move_out,
                    comments = :comments
                WHERE rmtenant_id = :rmtenant_id
            """)
            
            result = session_obj.execute(update_sql, {
                'tenant_name': tenant_name,
                'move_in': move_in if move_in else None,
                'move_out': move_out if move_out else None,
                'comments': comments,
                'rmtenant_id': rmtenant_id
            })
            
            session_obj.commit()
            
            if result.rowcount == 0:
                return jsonify({
                    'success': False,
                    'message': '수정할 입주사 정보를 찾을 수 없습니다.'
                }), 404
        
        return jsonify({
            'success': True,
            'message': '수정되었습니다.'
        })
        
    except Exception as e:
        print(f"🔴 입주사 수정 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'처리 중 오류가 발생했습니다: {str(e)}'
        }), 500

@rm_tenant_bp.route('/rm_tenant/delete_tenant', methods=['POST'])
@login_required
def delete_tenant():
    """입주사 삭제"""
    try:
        data = request.get_json()
        em_id = data.get('em_id')
        rmtenant_id = data.get('rmtenant_id')
        
        # 파라미터 검증
        if not all([em_id, rmtenant_id]):
            return jsonify({
                'success': False,
                'message': '필수 파라미터가 누락되었습니다.'
            }), 400
        
        with get_session() as session_obj:
            # 입주사 정보 존재 확인
            check_sql = text("""
                SELECT tenant_name 
                FROM rmtenant 
                WHERE rmtenant_id = :rmtenant_id
            """)
            
            existing = session_obj.execute(check_sql, {
                'rmtenant_id': rmtenant_id
            }).fetchone()
            
            if not existing:
                return jsonify({
                    'success': False,
                    'message': '삭제할 입주사 정보를 찾을 수 없습니다.'
                }), 404
            
            # 입주사 정보 삭제 (JSP와 동일)
            delete_sql = text("""
                DELETE FROM rmtenant 
                WHERE rmtenant_id = :rmtenant_id
            """)
            
            result = session_obj.execute(delete_sql, {
                'rmtenant_id': rmtenant_id
            })
            
            session_obj.commit()
            
            if result.rowcount == 0:
                return jsonify({
                    'success': False,
                    'message': '삭제할 입주사 정보를 찾을 수 없습니다.'
                }), 404
        
        return jsonify({
            'success': True,
            'message': '삭제되었습니다.'
        })
        
    except Exception as e:
        print(f"🔴 입주사 삭제 오류: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'처리 중 오류가 발생했습니다: {str(e)}'
        }), 500