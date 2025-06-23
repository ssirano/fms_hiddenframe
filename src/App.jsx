import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { AppProvider } from './contexts/AppContext';
import Layout from './components/layout/Layout';
import Login from './components/pages/Login';
import Dashboard from './components/pages/Dashboard';
import EmployeeList from './components/pages/EmployeeList';
import PropList from './components/pages/PropList';
import PropInsert from './components/pages/PropInsert';
import PropUpdate from './components/pages/PropUpdate';
import ProtectedRoute from './components/common/ProtectedRoute';

// CSS 임포트 (기존 스타일 유지)
import './styles/base.css';
import './styles/common.css';
import './styles/login.css';

function App() {
  return (
    <AuthProvider>
      <AppProvider>
        <Router>
          <div className="App">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }>
                <Route index element={<Navigate to="/main" replace />} />
                <Route path="main" element={<Dashboard />} />
                <Route path="fm/em_list" element={<EmployeeList />} />
                <Route path="fm/prop_list" element={<PropList />} />
                <Route path="fm/prop_insert" element={<PropInsert />} />
                <Route path="fm/prop_update/:propId?" element={<PropUpdate />} />
              </Route>
              <Route path="*" element={<Navigate to="/main" replace />} />
            </Routes>
          </div>
        </Router>
      </AppProvider>
    </AuthProvider>
  );
}

export default App;