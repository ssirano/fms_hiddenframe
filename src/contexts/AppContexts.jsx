import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { useAuth } from './AuthContext';

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [headerPinned, setHeaderPinned] = useState(true);
  const [sidebarPinned, setSidebarPinned] = useState(true);
  const [currentModule, setCurrentModule] = useState(null);
  const [menuData, setMenuData] = useState([]);
  const [propList, setPropList] = useState([]);
  const [selectedPropId, setSelectedPropId] = useState('');
  const [statusMessage, setStatusMessage] = useState('');

  // 메뉴 데이터 로드
  useEffect(() => {
    if (isAuthenticated && user?.em_id) {
      loadMenuData();
      loadPropList();
    }
  }, [isAuthenticated, user]);

  // 메뉴 데이터 로드
  const loadMenuData = async () => {
    try {
      const response = await apiService.post('/get_menu_data', {
        em_id: user.em_id
      });
      
      if (Array.isArray(response.data)) {
        setMenuData(response.data);
        // 첫 번째 모듈을 기본 선택
        if (response.data.length > 0) {
          setCurrentModule(response.data[0].menu_01_module_id);
        }
      }
    } catch (error) {
      console.error('메뉴 데이터 로드 오류:', error);
      showStatus('메뉴 데이터 로드에 실패했습니다.');
    }
  };

  // 사업소 목록 로드
  const loadPropList = async () => {
    try {
      const response = await apiService.post('/common/get_prop_list', {
        em_id: user.em_id
      });
      
      if (response.data.success && Array.isArray(response.data.data)) {
        setPropList(response.data.data);
        // 첫 번째 사업소를 기본 선택
        if (response.data.data.length > 0) {
          setSelectedPropId(response.data.data[0].prop_id);
        }
      }
    } catch (error) {
      console.error('사업소 목록 로드 오류:', error);
      showStatus('사업소 목록 로드에 실패했습니다.');
    }
  };

  // 상태 메시지 표시
  const showStatus = (message, duration = 3000) => {
    setStatusMessage(message);
    setTimeout(() => {
      setStatusMessage('');
    }, duration);
  };

  // 헤더 핀 토글
  const toggleHeaderPin = () => {
    setHeaderPinned(prev => {
      const newState = !prev;
      showStatus(newState ? '헤더가 고정되었습니다.' : '헤더가 비고정되었습니다.');
      return newState;
    });
  };

  // 사이드바 핀 토글
  const toggleSidebarPin = () => {
    setSidebarPinned(prev => {
      const newState = !prev;
      showStatus(newState ? '사이드바가 고정되었습니다.' : '사이드바가 비고정되었습니다.');
      return newState;
    });
  };

  // 사업소 변경
  const changeProp = (propId) => {
    setSelectedPropId(propId);
    const selectedProp = propList.find(prop => prop.prop_id === propId);
    if (selectedProp) {
      showStatus(`선택된 사업소: ${selectedProp.prop_name}`);
    }
  };

  // 현재 시간 포맷팅
  const formatCurrentTime = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const weekdays = ['일', '월', '화', '수', '목', '금', '토'];
    const weekday = weekdays[now.getDay()];
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    
    return `${year}-${month}-${day} (${weekday}) ${hours}:${minutes}:${seconds}`;
  };

  const value = {
    // 상태
    headerPinned,
    sidebarPinned,
    currentModule,
    menuData,
    propList,
    selectedPropId,
    statusMessage,
    
    // 액션
    setCurrentModule,
    toggleHeaderPin,
    toggleSidebarPin,
    changeProp,
    showStatus,
    loadMenuData,
    loadPropList,
    formatCurrentTime
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};