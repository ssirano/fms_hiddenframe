from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request, make_response, json
from controllers.auth import login_required
from sqlalchemy import text
from db import engine
from utils.common_functions import get_user_info

base_bp = Blueprint('base', __name__)

@base_bp.route('/main')
@login_required
def main():
    """메인 페이지 - HiddenFrame SPA 모드"""
    try:
        em_id = session.get('user')
        if not em_id:
            return redirect(url_for('index'))
        
        # 사용자 정보 조회
        user_info = get_user_info(em_id)
        if not user_info:
            return redirect(url_for('index'))
        
        # 메뉴 데이터 조회
        menu_data = get_user_menu_data(em_id)
        
        return render_template('base.html', 
                             user_info=user_info,
                             menu_data=menu_data,
                             current_module_title='시설관리시스템 (HiddenFrame)',
                             current_module_title_eng='Facility Management System with HiddenFrame')
    
    except Exception as e:
        print(f"메인 페이지 로드 중 오류: {str(e)}")
        return redirect(url_for('index'))

@base_bp.route('/dashboard')
@login_required
def dashboard():
    """대시보드 페이지 (HiddenFrame SPA 내에서 사용)"""
    return redirect(url_for('base.main'))

@base_bp.route('/common/get_user_info', methods=['POST'])
@login_required
def get_user_info_api():
    """사용자 정보 API - prop_id 포함"""
    try:
        em_id = session.get('user')
        if not em_id:
            return jsonify({'success': False, 'message': '로그인이 필요합니다.'})
        
        user_info = get_user_info(em_id)
        if not user_info:
            return jsonify({'success': False, 'message': '사용자 정보를 찾을 수 없습니다.'})
        
        print(f"🔐 사용자 정보 API 호출 (HiddenFrame):")
        print(f"   - em_id: {user_info.get('em_id')}")
        print(f"   - prop_id: {user_info.get('prop_id')}")
        print(f"   - name: {user_info.get('name')}")
        
        response_data = {
            'success': True,
            'name': user_info.get('name', ''),
            'em_id': user_info.get('em_id', ''),
            'prop_id': user_info.get('prop_id', ''),  # prop_id 포함
            'emclass_id': user_info.get('emclass_id', '정보없음'),
        }
        
        response = make_response(json.dumps(response_data, ensure_ascii=False))
        response.mimetype = 'application/json; charset=utf-8'
        return response
    
    except Exception as e:
        print(f"❌ 사용자 정보 API 오류: {str(e)}")  
        return jsonify({'success': False, 'message': '서버 오류가 발생했습니다.'})

@base_bp.route('/get_menu_data', methods=['POST'])
def get_menu_data():
    """메뉴 데이터 조회 - HiddenFrame 최적화"""
    try:
        em_id = request.json.get('em_id') or session.get('user')
        if not em_id:
            return jsonify({"success": False, "message": "em_id가 필요합니다."}), 400

        print(f"🔵 HiddenFrame 메뉴 데이터 조회: {em_id}")

        with engine.connect() as conn:
            # 1단계: emcontrol → menu_id 목록 조회
            sql1 = text("""SELECT DISTINCT menu_id FROM emcontrol WHERE em_id = :em_id""")
            menu_ids = [row['menu_id'] for row in conn.execute(sql1, {"em_id": em_id}).fetchall()]
            if not menu_ids:
                print(f"🟡 접근 가능한 메뉴가 없음: {em_id}")
                return jsonify([])

            # 2단계: menu → module_id 목록 조회
            sql2 = text("""SELECT DISTINCT module_id FROM menu WHERE menu_id IN :menu_ids""")
            module_ids = [row['module_id'] for row in conn.execute(sql2, {"menu_ids": tuple(menu_ids)}).fetchall()]
            if not module_ids:
                print(f"🟡 접근 가능한 모듈이 없음: {em_id}")
                return jsonify([])

            # 3단계: 전체 메뉴 정보
            sql3 = text("""
                SELECT module_id, menu_id, title, level1, level2, url
                FROM menu 
                WHERE module_id IN :module_ids
                AND title != 'TEST'
                ORDER BY level1, level2
            """)
            all_menus = [dict(row) for row in conn.execute(sql3, {"module_ids": tuple(module_ids)}).fetchall()]

            # 4단계: 모듈 정보
            sql4 = text("""
                SELECT module_id, sorting, title, title_eng
                FROM module
                WHERE module_id IN :module_ids
                ORDER BY sorting
            """)
            module_data = [dict(row) for row in conn.execute(sql4, {"module_ids": tuple(module_ids)}).fetchall()]

        # 5단계: HiddenFrame용 계층 구조 생성
        def get_menu_hierarchy_by_module(module_id, all_menus):
            module_menus = [m for m in all_menus if m['module_id'] == module_id]
            level2_menus = [m for m in module_menus if m['level2'] == 0]
            level3_menus = [m for m in module_menus if m['level2'] != 0]

            result = []
            for menu2 in sorted(level2_menus, key=lambda x: x['level1']):
                item = {
                    "menu_id": menu2["menu_id"],
                    "menu_02_name": menu2["title"],
                    "menu_03_data": []
                }
                # HiddenFrame: URL 변환 (.jsp → .html)
                if menu2.get("url"):
                    original_url = menu2["url"]
                    converted_url = original_url.replace(".jsp", ".html") if original_url else ""
                    item["menu_02_url"] = converted_url
                    print(f"🔄 URL 변환: {original_url} → {converted_url}")

                for menu3 in sorted(level3_menus, key=lambda x: x["level1"]):
                    if menu3["level2"] == menu2["level1"]:
                        sub_item = {
                            "menu_id": menu3["menu_id"],
                            "menu_03_name": menu3["title"],
                        }
                        # HiddenFrame: URL 변환 (.jsp → .html)
                        if menu3.get("url"):
                            original_url = menu3["url"]
                            converted_url = original_url.replace(".jsp", ".html") if original_url else ""
                            sub_item["menu_03_url"] = converted_url
                            print(f"🔄 URL 변환: {original_url} → {converted_url}")
                        item["menu_03_data"].append(sub_item)
                result.append(item) 
            return result

        result_data = []
        for module in module_data:
            hierarchy = get_menu_hierarchy_by_module(module["module_id"], all_menus)
            result_data.append({
                "menu_01_module_id": module["module_id"],
                "menu_01_title": module["title"],
                "menu_01_title_eng": module.get("title_eng", ""),
                "menu_01_sorting": module.get("sorting"),
                "menu_02_data": hierarchy
            })

        print(f"✅ HiddenFrame 메뉴 데이터 조회 완료: {len(result_data)}개 모듈")
        return make_response(json.dumps(result_data, ensure_ascii=False))

    except Exception as e:
        print(f"❌ HiddenFrame 메뉴 데이터 조회 오류: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@base_bp.route('/common/get_prop_list', methods=['POST'])
@login_required
def get_prop_list_api():
    """사업소 목록 API - HiddenFrame 최적화"""
    try:
        request_data = request.get_json()
        em_id = request_data.get('em_id') if request_data else session.get('user')
        
        if not em_id:
            return jsonify({'success': False, 'message': 'em_id가 필요합니다.'})
        
        print(f"🏢 HiddenFrame 사업소 목록 조회: {em_id}")
        
        with engine.connect() as conn:
            sql = text("""
                SELECT DISTINCT p.prop_id, p.name AS prop_name
                FROM emcontrol e
                JOIN prop p ON e.prop_id = p.prop_id
                WHERE e.em_id = :em_id AND e.prop_id IS NOT NULL
                ORDER BY p.prop_id ASC
            """)
            rows = conn.execute(sql, {"em_id": em_id}).fetchall()
            result_data = [{"prop_name": row['prop_name'], "prop_id": row['prop_id']} for row in rows]
        
        result = {
            'success': True,
            'data': result_data
        }
        
        print(f"✅ HiddenFrame 사업소 목록: {len(result_data)}개")
        
        response = make_response(json.dumps(result, ensure_ascii=False))
        response.mimetype = 'application/json; charset=utf-8'
        return response
    
    except Exception as e:
        print(f"❌ HiddenFrame 사업소 목록 API 오류: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@base_bp.route('/common/load_container', methods=['POST'])
@login_required
def load_container():
    """HiddenFrame 컨테이너 로드 - 최적화된 템플릿 처리"""
    try:
        menu_url = request.json.get('menuUrl', '').split('?')[0]
        original_url = menu_url
        
        print(f"🔵 HiddenFrame load_container 요청: {menu_url}")
        
        # JSP → HTML 변환
        if menu_url.endswith('.jsp'):
            menu_url = menu_url.replace('.jsp', '.html')
            print(f"🔄 JSP → HTML 변환: {original_url} → {menu_url}")

        print(f"🔵 HiddenFrame 템플릿 로드 시도: {menu_url}")
        
        try:
            # HiddenFrame: 템플릿 로드 시도
            template_content = render_template(menu_url)
            print(f"✅ HiddenFrame 템플릿 로드 성공: {menu_url}")
            print(f"📄 템플릿 내용 길이: {len(template_content)} 문자")
            
            # HiddenFrame: 성공 시 바로 반환
            return template_content
            
        except Exception as template_error:
            print(f"❌ HiddenFrame 템플릿 없음: {menu_url}, 오류: {str(template_error)}")
            
            # HiddenFrame: 템플릿이 없는 경우 구현 예정 페이지 반환
            page_title = get_menu_title_from_db(original_url) or extract_page_name(menu_url)
            coming_soon_page = create_hiddenframe_coming_soon_page(menu_url, page_title, original_url)
            print(f"📄 HiddenFrame 구현 예정 페이지 반환: {page_title}")
            return coming_soon_page

    except Exception as e:
        print(f"🔴 HiddenFrame load_container 오류: {str(e)}")
        return create_hiddenframe_error_page("오류", str(e))

def get_user_menu_data(em_id):
    """메뉴 데이터 조회 - HiddenFrame 최적화"""
    try:
        print(f"🔵 HiddenFrame 사용자 메뉴 데이터 조회: {em_id}")
        
        with engine.connect() as conn:
            # Step 1: emcontrol → menu_id 목록 조회
            sql1 = text("""
                SELECT DISTINCT menu_id 
                FROM emcontrol 
                WHERE em_id = :em_id
            """)
            menu_ids = [row['menu_id'] for row in conn.execute(sql1, {"em_id": em_id}).fetchall()]

            if not menu_ids:
                print(f"🟡 HiddenFrame 접근 가능한 메뉴 없음: {em_id}")
                return []

            # Step 2: menu → module_id 목록 조회
            sql2 = text("""
                SELECT DISTINCT module_id 
                FROM menu 
                WHERE menu_id IN :menu_ids
            """)
            module_ids = [row['module_id'] for row in conn.execute(sql2, {"menu_ids": tuple(menu_ids)}).fetchall()]

            if not module_ids:
                print(f"🟡 HiddenFrame 접근 가능한 모듈 없음: {em_id}")
                return []

            # Step 3: 전체 메뉴 정보 가져오기
            sql3 = text("""
                SELECT module_id, menu_id, title, level1, level2, url
                FROM menu
                WHERE module_id IN :module_ids
                AND title != 'TEST'
                ORDER BY level1, level2
            """)
            all_menus = [
                dict(row) for row in conn.execute(sql3, {"module_ids": tuple(module_ids)}).fetchall()
            ]

            # Step 4: module 테이블 정보 가져오기
            sql4 = text("""
                SELECT module_id, sorting, title, title_eng
                FROM module
                WHERE module_id IN :module_ids
                ORDER BY sorting
            """)
            module_data = [
                dict(row) for row in conn.execute(sql4, {"module_ids": tuple(module_ids)}).fetchall()
            ]

            # Step 5: HiddenFrame용 메뉴 계층 구성
            result_data = []
            for module in module_data:
                menu_hierarchy = get_hiddenframe_menu_hierarchy_by_module(module["module_id"], all_menus)
                
                modified_module = {
                    "menu_01_module_id": module["module_id"],
                    "menu_01_title": module["title"],
                    "menu_01_title_eng": module.get("title_eng", ""),
                    "menu_01_sorting": module.get("sorting"),
                    "menu_02_data": menu_hierarchy or []
                }
                result_data.append(modified_module)

            print(f"✅ HiddenFrame 사용자 메뉴 데이터 조회 완료: {len(result_data)}개 모듈")
            return result_data

    except Exception as e:
        print(f"❌ HiddenFrame 메뉴 데이터 조회 중 오류 발생: {str(e)}")
        return []

def get_hiddenframe_menu_hierarchy_by_module(module_id, all_menus):
    """HiddenFrame용 모듈별 메뉴 계층 구조 생성"""
    module_menus = [menu for menu in all_menus if menu["module_id"] == module_id]
    level2_menus = [menu for menu in module_menus if menu["level2"] == 0]
    level3_menus = [menu for menu in module_menus if menu["level2"] != 0]

    menu_02_data = []

    for menu2 in sorted(level2_menus, key=lambda x: x["level1"]):
        menu2_item = {
            "menu_id": menu2["menu_id"],
            "menu_02_name": menu2["title"],
            "menu_03_data": []
        }
        
        # HiddenFrame: URL 처리 시 JSP → HTML 변환
        menu2_url = menu2.get("url", "")
        if menu2_url and menu2_url.strip():
            converted_url = menu2_url.replace('.jsp', '.html')
            menu2_item["menu_02_url"] = converted_url
            print(f"🔄 Level2 URL 변환: {menu2_url} → {converted_url}")

        for menu3 in sorted(level3_menus, key=lambda x: x["level1"]):
            if menu3["level2"] == menu2["level1"]:
                menu3_item = {
                    "menu_id": menu3["menu_id"],
                    "menu_03_name": menu3["title"],
                }
                
                # HiddenFrame: URL 처리 시 JSP → HTML 변환
                menu3_url = menu3.get("url", "")
                if menu3_url and menu3_url.strip():
                    converted_url = menu3_url.replace('.jsp', '.html')
                    menu3_item["menu_03_url"] = converted_url
                    print(f"🔄 Level3 URL 변환: {menu3_url} → {converted_url}")
                    
                menu2_item["menu_03_data"].append(menu3_item)

        menu_02_data.append(menu2_item)

    return menu_02_data if menu_02_data else []

def get_menu_title_from_db(url):
    """DB에서 URL에 해당하는 메뉴 제목 조회 - HiddenFrame 최적화"""
    try:
        with engine.connect() as conn:
            # HiddenFrame: .html을 .jsp로 되돌려서 DB에서 검색
            search_url = url.replace('.html', '.jsp') if url.endswith('.html') else url
            
            sql = text("""
                SELECT title 
                FROM menu 
                WHERE url = :url 
                LIMIT 1
            """)
            result = conn.execute(sql, {"url": search_url}).fetchone()
            
            if result:
                print(f"🟢 HiddenFrame DB에서 메뉴 제목 찾음: {search_url} → {result['title']}")
                return result['title']
            else:
                print(f"🟡 HiddenFrame DB에서 메뉴 제목 못찾음: {search_url}")
                return None
                
    except Exception as e:
        print(f"🔴 HiddenFrame DB 메뉴 제목 조회 오류: {str(e)}")
        return None

def extract_page_name(url):
    """URL에서 페이지 이름 추출 - HiddenFrame 최적화"""
    # URL에서 파일명 추출하고 의미있는 이름으로 변환
    file_name = url.split('/')[-1].replace('.html', '').replace('.jsp', '')
    
    # HiddenFrame: 일반적인 페이지 이름 매핑 확장
    name_mappings = {
        'em_list': '📝 직원목록',
        'dept_list': '🏢 부서목록', 
        'prop_list': '🏢 사업장목록',
        'prop_update': '🏢 사업장수정',
        'prop_insert': '🏢 사업장등록',
        'bl_list': '🏗️ 건물목록',
        'pwr_chart': '👮 순찰현황',
        'pwr_list': '👮 순찰목록',
        'docu_per_list': '📋 문서관리',
        'sms_manual_list': '📱 SMS관리',
        'mytb_list': '⏰ 근태관리',
        'myinfo_list': '👤 개인정보',
        'elec_save2': '⚡ 전력관리',
        'gas_list2': '🔥 가스관리',
        'com_list': '🏢 업체관리',
        'cooperate_code': '🏷️ 업체분류',
        'licenceem_list_em': '🎓 자격증현황', 
    }
    
    return name_mappings.get(file_name, f"📄 {file_name.replace('_', ' ').title()}")

def create_hiddenframe_coming_soon_page(menu_url, page_title, original_url):
    """HiddenFrame용 구현 예정 페이지 생성"""
    html_content = f"""
    <div style="padding: 40px; text-align: center; min-height: 400px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 12px; margin-bottom: 30px;">
            <h2 style="margin: 0 0 10px 0; font-size: 28px;">🚧 {page_title}</h2>
            <p style="margin: 0; font-size: 16px; opacity: 0.9;">HiddenFrame 탭에서 구현 중입니다</p>
        </div>
        
        <div style="background: white; border-radius: 8px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <div style="margin-bottom: 25px;">
                <h3 style="color: #333; margin-bottom: 15px;">🎯 HiddenFrame 구현 계획</h3>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 6px; text-align: left;">
                    <ul style="margin: 0; padding-left: 20px; color: #495057;">
                        <li>✅ 폼 데이터 완전 보존 (작성 중인 글 유지)</li>
                        <li>✅ 스크롤 위치 자동 복원</li>
                        <li>✅ 빠른 탭 전환 (DOM 재생성 없음)</li>
                        <li>✅ 메모리 자동 관리 (LRU 방식)</li>
                        <li>🔄 비즈니스 로직 구현</li>
                        <li>🔄 AJAX API 연동</li>
                        <li>🔄 실시간 데이터 업데이트</li>
                        <li>🔄 사용자 경험 최적화</li>
                    </ul>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px;">
                <div>
                    <h4 style="color: #666; margin-bottom: 10px;">📍 원본 URL (DB)</h4>
                    <code style="background: #e9ecef; padding: 8px 12px; border-radius: 4px; color: #495057; font-family: monospace; display: block;">{original_url}</code>
                </div>
                <div>
                    <h4 style="color: #666; margin-bottom: 10px;">🔄 HiddenFrame URL</h4>
                    <code style="background: #d4edda; padding: 8px 12px; border-radius: 4px; color: #155724; font-family: monospace; display: block;">{menu_url}</code>
                </div>
            </div>
            
            <div style="border-top: 1px solid #dee2e6; padding-top: 20px;">
                <p style="color: #6c757d; margin: 0; font-size: 14px;">
                    🎪 <strong>HiddenFrame 탭 시스템의 장점</strong><br>
                    • 작성 중인 폼이 절대 사라지지 않음<br>
                    • 탭 간 이동이 즉시 이루어짐<br>
                    • 메모리 효율성으로 최대 15개 탭 관리<br>
                    • 사용자 경험이 네이티브 앱 수준으로 향상됨
                </p>
            </div>
        </div>
    </div>
    """
    return html_content

def create_hiddenframe_error_page(page_title, error_message):
    """HiddenFrame용 오류 페이지 생성"""
    html_content = f"""
    <div style="padding: 40px; text-align: center; min-height: 400px;">
        <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 40px; border-radius: 12px; margin-bottom: 30px;">
            <h2 style="margin: 0 0 10px 0; font-size: 28px;">❌ HiddenFrame 오류 발생</h2>
            <p style="margin: 0; font-size: 16px; opacity: 0.9;">{page_title} 탭 로드 중 문제가 발생했습니다</p>
        </div>
        
        <div style="background: white; border-radius: 8px; padding: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h3 style="color: #dc3545; margin-bottom: 15px;">오류 내용</h3>
            <div style="background: #f8d7da; padding: 15px; border-radius: 6px; border-left: 4px solid #dc3545; text-align: left; margin-bottom: 20px;">
                <code style="color: #721c24; font-family: monospace; word-break: break-all;">{error_message}</code>
            </div>
            
            <div style="display: flex; gap: 10px; justify-content: center;">
                <button class="btn btn-primary" onclick="window.tabManager.reloadTab(window.tabManager.activeTabId)" 
                        style="background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">
                    🔄 다시 시도
                </button>
                <button class="btn btn-secondary" onclick="window.tabManager.showDashboard()" 
                        style="background: #6c757d; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">
                    🏠 대시보드로
                </button>
            </div>
            
            <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 6px;">
                <p style="color: #6c757d; margin: 0; font-size: 12px;">
                    💡 <strong>HiddenFrame 오류 복구 팁</strong><br>
                    다시 시도해도 문제가 지속되면 브라우저를 새로고침해주세요.<br>
                    기존에 작성 중이던 다른 탭의 데이터는 보존됩니다.
                </p>
            </div>
        </div>
    </div>
    """
    return html_content