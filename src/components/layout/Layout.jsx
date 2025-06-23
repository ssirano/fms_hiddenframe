import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import StatusIndicator from '../common/StatusIndicator';
import { useApp } from '../../contexts/AppContext';

const Layout = () => {
  const { 
    headerPinned, 
    sidebarPinned, 
    statusMessage,
    toggleHeaderPin,
    toggleSidebarPin
  } = useApp();

  const [headerHover, setHeaderHover] = useState(false);
  const [sidebarHover, setSidebarHover] = useState(false);

  // 호버 타이머 관리
  const [headerTimer, setHeaderTimer] = useState(null);
  const [sidebarTimer, setSidebarTimer] = useState(null);

  // 헤더 호버 이벤트
  const handleHeaderHover = () => {
    if (!headerPinned) {
      if (headerTimer) clearTimeout(headerTimer);
      setHeaderHover(true);
    }
  };

  const handleHeaderLeave = () => {
    if (!headerPinned) {
      const timer = setTimeout(() => {
        setHeaderHover(false);
      }, 300);
      setHeaderTimer(timer);
    }
  };

  // 사이드바 호버 이벤트
  const handleSidebarHover = () => {
    if (!sidebarPinned) {
      if (sidebarTimer) clearTimeout(sidebarTimer);
      setSidebarHover(true);
    }
  };

  const handleSidebarLeave = () => {
    if (!sidebarPinned) {
      const timer = setTimeout(() => {
        setSidebarHover(false);
      }, 300);
      setSidebarTimer(timer);
    }
  };

  // 컴포넌트 언마운트 시 타이머 정리
  useEffect(() => {
    return () => {
      if (headerTimer) clearTimeout(headerTimer);
      if (sidebarTimer) clearTimeout(sidebarTimer);
    };
  }, [headerTimer, sidebarTimer]);

  // 헤더와 사이드바 표시 여부 계산
  const showHeader = headerPinned || headerHover;
  const showSidebar = sidebarPinned || sidebarHover;

  return (
    <div className="main-container">
      {/* 헤더 호버 트리거 */}
      <div 
        className="header-hover-trigger" 
        onMouseEnter={handleHeaderHover}
        title="헤더 호버 영역"
      />
      
      {/* 사이드바 호버 트리거 */}
      <div 
        className="sidebar-hover-trigger" 
        onMouseEnter={handleSidebarHover}
        title="사이드바 호버 영역"
      />
      
      {/* 헤더 프레임 */}
      <div 
        className={`header-frame ${!showHeader ? 'hidden' : ''} ${headerHover ? 'hover-show' : ''}`}
        onMouseLeave={handleHeaderLeave}
      >
        <button 
          className={`pin-button header-pin ${headerPinned ? 'pinned' : ''}`}
          onClick={toggleHeaderPin}
          title="헤더 고정/해제"
        >
          {headerPinned ? '📌' : '📍'}
        </button>
        
        <Header />
      </div>

      {/* 사이드바 프레임 */}
      <div 
        className={`sidebar-frame ${!showSidebar ? 'hidden' : ''} ${sidebarHover ? 'hover-show' : ''}`}
        onMouseLeave={handleSidebarLeave}
        style={{
          top: showHeader ? '80px' : '0'
        }}
      >
        <button 
          className={`pin-button sidebar-pin ${sidebarPinned ? 'pinned' : ''}`}
          onClick={toggleSidebarPin}
          title="사이드바 고정/해제"
        >
          {sidebarPinned ? '📌' : '📍'}
        </button>
        
        <Sidebar />
      </div>

      {/* 콘텐츠 프레임 */}
      <div 
        className="content-frame"
        style={{
          top: showHeader ? '80px' : '0',
          left: showSidebar ? '280px' : '0'
        }}
      >
        <div className="content-area">
          <Outlet />
        </div>
      </div>

      {/* 상태 인디케이터 */}
      <StatusIndicator message={statusMessage} />
    </div>
  );
};

export default Layout;