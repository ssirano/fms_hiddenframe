import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useApp } from '../../contexts/AppContext';

const Header = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { 
    menuData, 
    propList, 
    selectedPropId, 
    currentModule,
    setCurrentModule,
    changeProp,
    showStatus,
    formatCurrentTime
  } = useApp();

  const [currentTime, setCurrentTime] = useState(formatCurrentTime());

  // 시계 업데이트
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(formatCurrentTime());
    }, 1000);

    return () => clearInterval(interval);
  }, [formatCurrentTime]);

  // 사업소 변경 핸들러
  const handlePropChange = (e) => {
    const propId = e.target.value;
    changeProp(propId);
  };

  // 모듈 클릭 핸들러
  const handleModuleClick = (moduleId, moduleTitle) => {
    setCurrentModule(moduleId);
    showStatus(`${moduleTitle} 모듈이 선택되었습니다.`);
    
    // 해당 모듈의 첫 번째 메뉴로 네비게이션
    const module = menuData.find(m => m.menu_01_module_id === moduleId);
    if (module && module.menu_02_data && module.menu_02_data.length > 0) {
      const firstMenu = module.menu_02_data[0];
      let targetUrl = '';
      
      if (firstMenu.menu_03_data && firstMenu.menu_03_data.length > 0) {
        // 3단계 메뉴가 있는 경우
        targetUrl = firstMenu.menu_03_data[0].menu_03_url;
      } else if (firstMenu.menu_02_url) {
        // 2단계 메뉴로 직접 이동
        targetUrl = firstMenu.menu_02_url;
      }
      
      if (targetUrl) {
        // JSP를 React 라우트로 변환
        const reactPath = convertJspToReactPath(targetUrl);
        navigate(reactPath);
      }
    }
  };

  // JSP URL을 React 라우트로 변환
  const convertJspToReactPath = (jspUrl) => {
    const urlMap = {
      '/fm/em_list.html': '/fm/em_list',
      '/fm/prop_list.html': '/fm/prop_list',
      '/fm/prop_insert.html': '/fm/prop_insert',
      '/fm/prop_update.html': '/fm/prop_update',
    };
    
    return urlMap[jspUrl] || jspUrl.replace('.html', '').replace('.jsp', '');
  };

  // 로그아웃 핸들러
  const handleLogout = async () => {
    if (window.confirm('로그아웃 하시겠습니까?')) {
      try {
        await logout();
        navigate('/login');
        showStatus('로그아웃되었습니다.');
      } catch (error) {
        console.error('로그아웃 오류:', error);
        showStatus('로그아웃 처리 중 오류가 발생했습니다.');
      }
    }
  };

  return (
    <>
      <div className="topheader-left">
        <label htmlFor="sel_business_place"><b>사업소 선택:</b></label>
        <select 
          id="sel_business_place" 
          value={selectedPropId}
          onChange={handlePropChange}
        >
          {propList.length === 0 ? (
            <option value="">사업소 로딩 중...</option>
          ) : (
            <>
              <option value="">사업소 선택</option>
              {propList.map(prop => (
                <option key={prop.prop_id} value={prop.prop_id}>
                  {prop.prop_name} ({prop.prop_id})
                </option>
              ))}
            </>
          )}
        </select>
      </div>
      
      {/* 모듈 메뉴 */}
      <div className="module-menu">
        {menuData.length === 0 ? (
          <div style={{ color: '#666' }}>메뉴 로딩 중...</div>
        ) : (
          menuData.map(module => (
            <div
              key={module.menu_01_module_id}
              className={`module-item ${currentModule === module.menu_01_module_id ? 'active' : ''}`}
              onClick={() => handleModuleClick(module.menu_01_module_id, module.menu_01_title)}
            >
              {module.menu_01_title}
            </div>
          ))
        )}
      </div>
      
      <div className="user-info">
        <span id="current-datetime">{currentTime}</span>
        <span>
          <b>
            {user ? `사용자: ${user.name} 님 [${user.emclass_id}]` : '사용자: 로딩 중...'}
          </b>
        </span>
        <button 
          type="button" 
          className="toggle-btn" 
          onClick={handleLogout}
        >
          로그아웃
        </button>
      </div>
    </>
  );
};

export default Header;