import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useApp } from '../../contexts/AppContext';

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { menuData, currentModule, showStatus } = useApp();
  
  const [expandedMenus, setExpandedMenus] = useState(new Set());
  const [currentModuleData, setCurrentModuleData] = useState(null);

  // 현재 모듈 데이터 업데이트
  useEffect(() => {
    if (currentModule && menuData.length > 0) {
      const moduleData = menuData.find(m => m.menu_01_module_id === currentModule);
      setCurrentModuleData(moduleData);
    } else if (menuData.length > 0) {
      // 첫 번째 모듈을 기본으로 설정
      setCurrentModuleData(menuData[0]);
    }
  }, [currentModule, menuData]);

  // 하위 메뉴 토글
  const toggleSubMenu = (menuId) => {
    setExpandedMenus(prev => {
      const newSet = new Set(prev);
      if (newSet.has(menuId)) {
        newSet.delete(menuId);
      } else {
        newSet.add(menuId);
      }
      return newSet;
    });
  };

  // 메뉴 클릭 핸들러
  const handleMenuClick = (url, title) => {
    if (!url) {
      showStatus('메뉴 URL이 설정되지 않았습니다.');
      return;
    }
    
    // JSP URL을 React 라우트로 변환
    const reactPath = convertJspToReactPath(url);
    navigate(reactPath);
    showStatus(`${title} 페이지로 이동했습니다.`);
  };

  // JSP URL을 React 라우트로 변환
  const convertJspToReactPath = (jspUrl) => {
    // URL 정규화
    let url = jspUrl;
    if (url.startsWith('/')) {
      url = url.substring(1);
    }
    
    const urlMap = {
      'fm/em_list.html': '/fm/em_list',
      'fm/prop_list.html': '/fm/prop_list',
      'fm/prop_insert.html': '/fm/prop_insert',
      'fm/prop_update.html': '/fm/prop_update',
    };
    
    return urlMap[url] || ('/' + url.replace('.html', '').replace('.jsp', ''));
  };

  // 현재 경로와 메뉴 URL 비교해서 활성 상태 확인
  const isActiveMenu = (url) => {
    if (!url) return false;
    const reactPath = convertJspToReactPath(url);
    return location.pathname === reactPath;
  };

  if (!currentModuleData) {
    return (
      <div className="sidebar-content">
        <h3>시스템관리</h3>
        <p>System Management</p>
        <hr style={{ margin: '15px 0', borderColor: '#6c757d' }} />
        <div style={{ textAlign: 'center', padding: '20px', color: '#6c757d' }}>
          메뉴를 로딩 중입니다...
        </div>
      </div>
    );
  }

  return (
    <div className="sidebar-content">
      <h3 id="sidebarTitle">{currentModuleData.menu_01_title}</h3>
      <p id="sidebarSubtitle">{currentModuleData.menu_01_title_eng || 'Management'}</p>
      <hr style={{ margin: '15px 0', borderColor: '#6c757d' }} />
      
      <div id="menuContainer">
        {currentModuleData.menu_02_data && currentModuleData.menu_02_data.length > 0 ? (
          currentModuleData.menu_02_data.map(menu2 => {
            const hasSubMenus = menu2.menu_03_data && menu2.menu_03_data.length > 0;
            const isExpanded = expandedMenus.has(menu2.menu_id);
            
            if (hasSubMenus) {
              // 하위 메뉴가 있는 경우
              return (
                <div key={menu2.menu_id} className="menu-group">
                  <div 
                    className="menu-item-parent" 
                    onClick={() => toggleSubMenu(menu2.menu_id)}
                  >
                    <span>{menu2.menu_02_name}</span>
                    <span className="menu-arrow">
                      {isExpanded ? '▼' : '▶'}
                    </span>
                  </div>
                  <div 
                    className="sub-menu-container" 
                    style={{ display: isExpanded ? 'block' : 'none' }}
                  >
                    {menu2.menu_03_data.map(menu3 => (
                      <div
                        key={menu3.menu_id}
                        className={`menu-item sub-menu ${isActiveMenu(menu3.menu_03_url) ? 'active' : ''}`}
                        onClick={() => handleMenuClick(menu3.menu_03_url, menu3.menu_03_name)}
                      >
                        {menu3.menu_03_name}
                      </div>
                    ))}
                  </div>
                </div>
              );
            } else {
              // 하위 메뉴가 없는 경우
              return (
                <div
                  key={menu2.menu_id}
                  className={`menu-item ${isActiveMenu(menu2.menu_02_url) ? 'active' : ''}`}
                  onClick={() => handleMenuClick(menu2.menu_02_url, menu2.menu_02_name)}
                >
                  {menu2.menu_02_name}
                </div>
              );
            }
          })
        ) : (
          <div style={{ textAlign: 'center', padding: '20px', color: '#6c757d' }}>
            접근 가능한 메뉴가 없습니다.
          </div>
        )}
      </div>
    </div>
  );
};

export default Sidebar;