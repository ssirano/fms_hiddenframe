import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../../contexts/AppContext';

const Dashboard = () => {
  const navigate = useNavigate();
  const { showStatus } = useApp();

  const handleQuickAction = (path, title) => {
    navigate(path);
    showStatus(`${title} 페이지로 이동했습니다.`);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>📊 대시보드</h2>
      
      <div style={{
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '20px', 
        marginBottom: '30px'
      }}>
        <div style={{
          background: '#e8f5e8', 
          padding: '20px', 
          borderRadius: '8px', 
          borderLeft: '4px solid #28a745'
        }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#155724' }}>React 시스템</h4>
          <p style={{ fontSize: '24px', fontWeight: 'bold', margin: '0', color: '#155724' }}>가동 중</p>
        </div>
        
        <div style={{
          background: '#e3f2fd', 
          padding: '20px', 
          borderRadius: '8px', 
          borderLeft: '4px solid #007bff'
        }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#004085' }}>직원 관리</h4>
          <p style={{ fontSize: '24px', fontWeight: 'bold', margin: '0', color: '#004085' }}>시스템</p>
        </div>
        
        <div style={{
          background: '#fff3cd', 
          padding: '20px', 
          borderRadius: '8px', 
          borderLeft: '4px solid #ffc107'
        }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#856404' }}>SPA 모드</h4>
          <p style={{ fontSize: '24px', fontWeight: 'bold', margin: '0', color: '#856404' }}>React Router</p>
        </div>
        
        <div style={{
          background: '#f8d7da', 
          padding: '20px', 
          borderRadius: '8px', 
          borderLeft: '4px solid #dc3545'
        }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#721c24' }}>상태 관리</h4>
          <p style={{ fontSize: '24px', fontWeight: 'bold', margin: '0', color: '#721c24' }}>Context API</p>
        </div>
      </div>
      
      <div style={{
        background: 'white', 
        borderRadius: '8px', 
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)', 
        padding: '20px'
      }}>
        <h3 style={{ margin: '0 0 20px 0' }}>⚡ 빠른 작업</h3>
        <div style={{
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
          gap: '15px'
        }}>
          <button 
            style={{
              padding: '15px', 
              background: '#007bff', 
              color: 'white', 
              border: 'none', 
              borderRadius: '6px', 
              cursor: 'pointer', 
              textAlign: 'left',
              transition: 'all 0.15s ease-in-out'
            }}
            onClick={() => handleQuickAction('/fm/em_list', '📝 직원정보')}
            onMouseOver={(e) => e.target.style.background = '#0056b3'}
            onMouseOut={(e) => e.target.style.background = '#007bff'}
          >
            📝 직원 정보 관리
          </button>
          
          <button 
            style={{
              padding: '15px', 
              background: '#28a745', 
              color: 'white', 
              border: 'none', 
              borderRadius: '6px', 
              cursor: 'pointer', 
              textAlign: 'left',
              transition: 'all 0.15s ease-in-out'
            }}
            onClick={() => handleQuickAction('/fm/prop_list', '🏢 사업장정보')}
            onMouseOver={(e) => e.target.style.background = '#1e7e34'}
            onMouseOut={(e) => e.target.style.background = '#28a745'}
          >
            🏢 사업장 정보 관리
          </button>
          
          <button 
            style={{
              padding: '15px', 
              background: '#17a2b8', 
              color: 'white', 
              border: 'none', 
              borderRadius: '6px', 
              cursor: 'pointer', 
              textAlign: 'left',
              transition: 'all 0.15s ease-in-out'
            }}
            onClick={() => handleQuickAction('/fm/prop_insert', '🏢 사업장등록')}
            onMouseOver={(e) => e.target.style.background = '#117a8b'}
            onMouseOut={(e) => e.target.style.background = '#17a2b8'}
          >
            🏢 사업장 등록
          </button>
        </div>
      </div>
      
      <div style={{
        background: 'white', 
        borderRadius: '8px', 
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)', 
        padding: '20px',
        marginTop: '20px'
      }}>
        <h3 style={{ margin: '0 0 20px 0' }}>🔧 시스템 정보</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div>
            <h5 style={{ color: '#495057', marginBottom: '10px' }}>프론트엔드</h5>
            <ul style={{ margin: 0, paddingLeft: '20px', color: '#6c757d' }}>
              <li>React 18.2.0</li>
              <li>React Router 6.8.0</li>
              <li>Axios for API calls</li>
              <li>Context API for state</li>
            </ul>
          </div>
          <div>
            <h5 style={{ color: '#495057', marginBottom: '10px' }}>백엔드</h5>
            <ul style={{ margin: 0, paddingLeft: '20px', color: '#6c757d' }}>
              <li>Flask API Server</li>
              <li>SQLAlchemy ORM</li>
              <li>Session-based Auth</li>
              <li>MySQL Database</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;