import React, { useState, useEffect, useRef } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Login = () => {
  const { login, isAuthenticated } = useAuth();
  const [formData, setFormData] = useState({
    mem_id: '',
    mem_pwd: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [capsLockWarning, setCapsLockWarning] = useState(false);
  const [warningPosition, setWarningPosition] = useState({ left: 0, top: 0 });
  
  const memIdRef = useRef(null);
  const memPwdRef = useRef(null);

  // 이미 로그인된 경우 메인 페이지로 리다이렉트
  if (isAuthenticated) {
    return <Navigate to="/main" replace />;
  }

  // 컴포넌트 마운트 시 ID 입력 필드에 포커스
  useEffect(() => {
    if (memIdRef.current) {
      memIdRef.current.focus();
    }
  }, []);

  // 입력값 변경 핸들러
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // 에러 메시지 클리어
    if (error) setError('');
  };

  // Caps Lock 감지
  const checkCapsLock = (e) => {
    const capsLockOn = e.getModifierState && e.getModifierState('CapsLock');
    const input = e.target;
    
    if (capsLockOn && input.name === 'mem_pwd') {
      const rect = input.getBoundingClientRect();
      setWarningPosition({
        left: rect.left,
        top: rect.top - 80
      });
      setCapsLockWarning(true);
    } else {
      setCapsLockWarning(false);
    }
  };

  // 엔터키 핸들러
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      if (e.target.name === 'mem_id' && memPwdRef.current) {
        memPwdRef.current.focus();
      } else {
        handleSubmit(e);
      }
    }
  };

  // 폼 제출 핸들러
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.mem_id || !formData.mem_pwd) {
      setError('ID와 비밀번호를 입력해주세요.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const result = await login(formData);
      
      if (result.success) {
        // 로그인 성공 시 자동으로 메인 페이지로 이동 (Navigate 컴포넌트에서 처리)
      } else {
        setError(result.message || '로그인에 실패했습니다.');
        // 비밀번호 필드 초기화 및 포커스
        setFormData(prev => ({ ...prev, mem_pwd: '' }));
        if (memPwdRef.current) {
          memPwdRef.current.focus();
        }
      }
    } catch (error) {
      console.error('로그인 오류:', error);
      setError('서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ height: '100vh' }}>
      {/* Caps Lock 경고 */}
      {capsLockWarning && (
        <div 
          id="capsLockWarning"
          style={{
            position: 'fixed',
            left: `${warningPosition.left}px`,
            top: `${warningPosition.top}px`,
            display: 'block'
          }}
        >
          ⚠️ &lt;Caps Lock&gt;이 켜져 있습니다.<br/>
          &lt;Caps Lock&gt;이 켜져 있으면 암호를 올바르게 입력하지 못할 수 있습니다.
        </div>
      )}
      
      <form className="login-form" onSubmit={handleSubmit} tabIndex="-1">
        <div className="login-container">
          <div className="logo-container">
            {/* CSS 로고 */}
            <div className="logo-placeholder">
              <h1>FMS</h1>
              <p>시설관리시스템</p>
            </div>
          </div>
          
          <div className="login-box">
            <input
              ref={memIdRef}
              type="text"
              name="mem_id"
              value={formData.mem_id}
              onChange={handleInputChange}
              onKeyPress={handleKeyPress}
              placeholder="ID 입력"
              required
              autoComplete="username"
              disabled={loading}
            />
            
            <div className="password-container">
              <input
                ref={memPwdRef}
                type="password"
                name="mem_pwd"
                value={formData.mem_pwd}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                onKeyUp={checkCapsLock}
                onFocus={checkCapsLock}
                onBlur={() => setCapsLockWarning(false)}
                placeholder="Password 입력"
                required
                autoComplete="current-password"
                disabled={loading}
              />
            </div>
            
            {/* 에러 메시지 */}
            {error && (
              <div style={{
                color: '#dc3545',
                fontSize: '14px',
                textAlign: 'center',
                marginBottom: '10px',
                padding: '8px',
                backgroundColor: '#f8d7da',
                border: '1px solid #f1aeb5',
                borderRadius: '4px'
              }}>
                {error}
              </div>
            )}
            
            <button 
              type="submit" 
              id="btn_login"
              disabled={loading}
            >
              {loading ? '로그인 중...' : 'Log in'}
            </button>
            
            <div className="help-link">
              <a href="#">• 사용자등록</a>
            </div>
            
            <hr id="hr_login" />
          </div>
          
          <div className="footer">
            ※ 시스템 문의 : tel) 02-2664-5354 fax) 070-8299-1170 e-mail - help@afm.co.kr<br/>
            <br/>
            <b>create by ARCHISYSTEMS</b><br/>
            <u>Designed by JG</u>
          </div>
        </div>
      </form>
    </div>
  );
};

export default Login;