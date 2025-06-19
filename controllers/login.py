from flask import Blueprint, render_template, request, url_for, session, jsonify, redirect
from sqlalchemy import text
from db import engine

login_bp = Blueprint('login', __name__)

@login_bp.route('/login_check', methods=['POST'])
def login_check():
    """로그인 인증 처리"""
    try:
        request_data = request.get_json()
        mem_id = request_data.get('mem_id')
        mem_pwd = request_data.get('mem_pwd')

        if not mem_id or not mem_pwd:
            return jsonify({'success': False, 'message': 'ID와 비밀번호를 입력해주세요.'})

        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT em_id, mem_pwd FROM em WHERE mem_id=:mem_id"),
                {"mem_id": mem_id}
            ).fetchone()

        if result is None:
            return jsonify({'success': False, 'message': '존재하지 않는 ID 입니다.'})

        if str(result.mem_pwd) == str(mem_pwd):
            session.permanent = True
            session['user'] = result.em_id
            return jsonify({'success': True, 'redirect': url_for('base.main')})

        return jsonify({'success': False, 'message': '비밀번호가 올바르지 않습니다.'})

    except Exception as e:
        print(f"로그인 처리 중 오류 발생: {str(e)}")
        return jsonify({'success': False, 'message': '로그인 처리 중 오류가 발생했습니다.'})

@login_bp.route('/logout', methods=['POST'])
def logout():
    """로그아웃 처리"""
    try:
        if 'user' in session:
            session.clear()

        return jsonify({'success': True, 'redirect': url_for('index')})
    
    except Exception as e:
        print(f"로그아웃 처리 중 오류 발생: {str(e)}")
        return jsonify({'success': False, 'message': '로그아웃 처리 중 오류가 발생했습니다.'})