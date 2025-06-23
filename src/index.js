import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// 개발 환경에서의 성능 측정
import reportWebVitals from './reportWebVitals';

// React 18의 새로운 root API 사용
const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// 성능 측정 시작 (개발 환경에서만)
if (process.env.NODE_ENV === 'development') {
  reportWebVitals(console.log);
}

// 전역 에러 핸들러
window.addEventListener('error', function(e) {
  console.error('전역 오류:', e.error);
  // 필요시 에러 로깅 서비스로 전송
});

// 처리되지 않은 Promise 거부 핸들러
window.addEventListener('unhandledrejection', function(e) {
  console.error('처리되지 않은 Promise 거부:', e.reason);
  // 필요시 에러 로깅 서비스로 전송
});

// 개발 환경에서 Hot Module Replacement 지원
if (module.hot) {
  module.hot.accept();
}