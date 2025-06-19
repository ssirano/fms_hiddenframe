from sqlalchemy import text
from db import engine

def get_user_info(em_id):
    """사용자 정보 조회"""
    try:
        with engine.connect() as conn:
            sql = text("""
                SELECT e.em_id, e.name, e.emclass_id, e.prop_id
                FROM em e
                WHERE e.em_id = :em_id
            """)
            result = conn.execute(sql, {"em_id": em_id}).fetchone()
            
            if result:
                return {
                    'em_id': result['em_id'],
                    'name': result['name'],
                    'emclass_id': result['emclass_id'] or '정보없음',
                    'prop_id': result['prop_id']
                }
            return None
    except Exception as e:
        print(f"사용자 정보 조회 오류: {str(e)}")
        return None

def build_query_conditions(conditions):
    """동적 쿼리 조건 구성"""
    where_conditions = []
    params = {}
    
    for key, value in conditions.items():
        if value and key.startswith('findKey_'):
            # findKey_01 -> findVal_01 매핑
            val_key = key.replace('findKey_', 'findVal_')
            if val_key in conditions and conditions[val_key]:
                where_conditions.append(f"{value} = :{key}")
                params[key] = conditions[val_key]
    
    return where_conditions, params

def get_user_menu_data(em_id):
    """DB 기반 사용자별 메뉴 조회"""
    try:
        with engine.connect() as conn:
            # 사용자가 접근 가능한 메뉴 ID 조회
            sql1 = text("""SELECT DISTINCT menu_id FROM emcontrol WHERE em_id = :em_id""")
            menu_ids = [row['menu_id'] for row in conn.execute(sql1, {"em_id": em_id}).fetchall()]
            if not menu_ids:
                return []

            # 메뉴 상세 정보 조회
            sql2 = text("""
                SELECT module_id, menu_id, title, level1, level2, url
                FROM menu
                WHERE menu_id IN :menu_ids
                ORDER BY level1, level2
            """)
            menus = [dict(row) for row in conn.execute(sql2, {"menu_ids": tuple(menu_ids)}).fetchall()]

            # 모듈 정보 조회
            module_ids = list(set(m['module_id'] for m in menus))
            sql3 = text("""
                SELECT module_id, title
                FROM module
                WHERE module_id IN :module_ids
                ORDER BY module_id
            """)
            modules = [dict(row) for row in conn.execute(sql3, {"module_ids": tuple(module_ids)}).fetchall()]

        # 계층 구조 생성
        result = []
        for module in modules:
            module_id = module['module_id']
            module_menus = [m for m in menus if m['module_id'] == module_id]

            level2_menus = [m for m in module_menus if m['level2'] == 0]
            level3_menus = [m for m in module_menus if m['level2'] != 0]

            menu_02_list = []
            for m2 in sorted(level2_menus, key=lambda x: x['level1']):
                menu_item = {
                    'menu_02_title': m2['title'],
                    'menu_02_url': m2['url'].replace('.jsp', '.html') if m2['url'] else ''
                }

                # 하위 메뉴 붙이기
                children = []
                for m3 in sorted(level3_menus, key=lambda x: x['level1']):
                    if m3['level2'] == m2['level1']:
                        children.append({
                            'menu_03_title': m3['title'],
                            'menu_03_url': m3['url'].replace('.jsp', '.html') if m3['url'] else ''
                        })
                if children:
                    menu_item['menu_03_list'] = children

                menu_02_list.append(menu_item)

            result.append({
                'menu_01_title': module['title'],
                'menu_01_module_id': module_id,
                'menu_02_list': menu_02_list
            })

        return result

    except Exception as e:
        print(f"[ERROR] 메뉴 데이터 조회 실패: {str(e)}")
        return []

def build_query_conditions(conditions):
    """동적 쿼리 조건 구성"""
    where_conditions = []
    params = {}
    
    for key, value in conditions.items():
        if value and key.startswith('findKey_'):
            # findKey_01 -> findVal_01 매핑
            val_key = key.replace('findKey_', 'findVal_')
            if val_key in conditions and conditions[val_key]:
                where_conditions.append(f"{value} = :{key}")
                params[key] = conditions[val_key]
    
    return where_conditions, params