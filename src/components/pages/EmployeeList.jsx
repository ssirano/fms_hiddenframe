import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useApp } from '../../contexts/AppContext';
import { employeeAPI, commonAPI } from '../../services/api';

const EmployeeList = () => {
  const { user } = useAuth();
  const { selectedPropId, showStatus } = useApp();
  
  // 상태 관리
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('info');
  
  // 검색 조건
  const [searchParams, setSearchParams] = useState({
    prop_id_chk: '',
    emclass_id: '',
    emstd_id: '',
    status: '',
    name_sch: '',
    order: 'basic',
    desc: 'asc',
    page_no: 1
  });
  
  // 페이징 정보
  const [pagination, setPagination] = useState({
    totalCount: 0,
    totalPages: 1,
    currentPage: 1
  });
  
  // 필터 옵션
  const [filterOptions, setFilterOptions] = useState({
    emclassOptions: [],
    emstdOptions: []
  });
  
  // 상세 정보
  const [employeeDetail, setEmployeeDetail] = useState(null);
  const [employeeHistory, setEmployeeHistory] = useState([]);
  const [employeeLicense, setEmployeeLicense] = useState([]);

  // 컴포넌트 마운트 시 초기화
  useEffect(() => {
    if (user?.em_id && selectedPropId) {
      setSearchParams(prev => ({ ...prev, prop_id_chk: selectedPropId }));
      loadFilterOptions();
      searchEmployees();
    }
  }, [user, selectedPropId]);

  // 사업소 변경 시 검색 조건 업데이트
  useEffect(() => {
    if (selectedPropId) {
      setSearchParams(prev => ({ ...prev, prop_id_chk: selectedPropId, page_no: 1 }));
      setSelectedEmployee(null);
      loadFilterOptions();
      searchEmployees();
    }
  }, [selectedPropId]);

  // 필터 옵션 로드
  const loadFilterOptions = async () => {
    if (!selectedPropId) return;

    try {
      // 파트 목록
      const emclassResponse = await commonAPI.getSelectOptions({
        table: 'emclass',
        id_field: 'emclass_id',
        text_field: 'emclass_id',
        conditions: { prop_id: selectedPropId },
        order_by: 'vieworder ASC'
      });

      // 직급 목록
      const emstdResponse = await commonAPI.getSelectOptions({
        table: 'emstd',
        id_field: 'emstd_id',
        text_field: 'emstd_id',
        conditions: { prop_id: selectedPropId },
        order_by: 'vieworder ASC'
      });

      setFilterOptions({
        emclassOptions: emclassResponse.data.success ? emclassResponse.data.data : [],
        emstdOptions: emstdResponse.data.success ? emstdResponse.data.data : []
      });
    } catch (error) {
      console.error('필터 옵션 로드 오류:', error);
    }
  };

  // 직원 검색
  const searchEmployees = async () => {
    if (!user?.em_id || !searchParams.prop_id_chk) {
      showStatus('사업소를 선택해주세요.');
      return;
    }

    setLoading(true);
    try {
      const response = await employeeAPI.getEmployeeList(searchParams);
      
      if (response.data.success) {
        setEmployees(response.data.data);
        setPagination({
          totalCount: response.data.total_count,
          totalPages: response.data.total_pages,
          currentPage: response.data.current_page
        });
      } else {
        showStatus('검색 실패: ' + response.data.message);
        setEmployees([]);
      }
    } catch (error) {
      console.error('직원 검색 오류:', error);
      showStatus('검색 중 오류가 발생했습니다.');
      setEmployees([]);
    } finally {
      setLoading(false);
    }
  };

  // 검색 조건 변경
  const handleSearchChange = (field, value) => {
    setSearchParams(prev => ({ ...prev, [field]: value, page_no: 1 }));
  };

  // 검색 실행
  const handleSearch = () => {
    searchEmployees();
  };

  // 정렬
  const handleSort = (field) => {
    setSearchParams(prev => ({
      ...prev,
      order: field,
      desc: prev.order === field && prev.desc === 'asc' ? 'desc' : 'asc',
      page_no: 1
    }));
    searchEmployees();
  };

  // 페이지 변경
  const handlePageChange = (pageNo) => {
    if (pageNo < 1 || pageNo > pagination.totalPages) return;
    setSearchParams(prev => ({ ...prev, page_no: pageNo }));
    searchEmployees();
  };

  // 직원 선택
  const handleEmployeeSelect = async (employee) => {
    setSelectedEmployee(employee);
    setActiveTab('info');
    
    // 직원 상세 정보 로드
    try {
      const response = await employeeAPI.getEmployeeDetail(employee.em_id);
      if (response.data.success) {
        setEmployeeDetail(response.data.data);
      }
    } catch (error) {
      console.error('직원 상세 정보 로드 오류:', error);
      showStatus('직원 정보를 불러올 수 없습니다.');
    }
  };

  // 탭 변경
  const handleTabChange = async (tab) => {
    setActiveTab(tab);
    
    if (!selectedEmployee) return;
    
    try {
      if (tab === 'history') {
        const response = await employeeAPI.getEmployeeHistory(selectedEmployee.em_id);
        if (response.data.success) {
          setEmployeeHistory(response.data.data);
        }
      } else if (tab === 'license') {
        const response = await employeeAPI.getEmployeeLicense(selectedEmployee.em_id);
        if (response.data.success) {
          setEmployeeLicense(response.data.data);
        }
      }
    } catch (error) {
      console.error('탭 데이터 로드 오류:', error);
      showStatus('데이터를 불러올 수 없습니다.');
    }
  };

  // 엑셀 다운로드
  const handleExcelDownload = () => {
    if (!searchParams.prop_id_chk) {
      showStatus('사업소를 선택해주세요.');
      return;
    }
    
    const downloadUrl = employeeAPI.downloadExcel(searchParams);
    window.open(downloadUrl, '_blank');
    showStatus('엑셀 파일을 다운로드합니다.');
  };

  // 직원 등록
  const handleEmployeeInsert = () => {
    showStatus('직원 등록 기능을 구현 중입니다.');
  };

  // 직원 수정
  const handleEmployeeEdit = (emId) => {
    showStatus(`직원 수정 기능을 구현 중입니다. 직원 ID: ${emId}`);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>📝 직원정보 관리</h2>

      {/* 검색 폼 */}
      <div className="search-form">
        <div className="form-row">
          <div className="form-group col-2">
            <label>파트:</label>
            <select 
              className="form-control" 
              value={searchParams.emclass_id}
              onChange={(e) => handleSearchChange('emclass_id', e.target.value)}
            >
              <option value="">-전체-</option>
              {filterOptions.emclassOptions.map(option => (
                <option key={option.id} value={option.id}>{option.text}</option>
              ))}
            </select>
          </div>
          <div className="form-group col-2">
            <label>직급:</label>
            <select 
              className="form-control"
              value={searchParams.emstd_id}
              onChange={(e) => handleSearchChange('emstd_id', e.target.value)}
            >
              <option value="">-전체-</option>
              {filterOptions.emstdOptions.map(option => (
                <option key={option.id} value={option.id}>{option.text}</option>
              ))}
            </select>
          </div>
          <div className="form-group col-2">
            <label>상태:</label>
            <select 
              className="form-control"
              value={searchParams.status}
              onChange={(e) => handleSearchChange('status', e.target.value)}
            >
              <option value="">-전체-</option>
              <option value="재직중">재직중</option>
              <option value="신청중">신청자</option>
              <option value="퇴직자">퇴직자</option>
              <option value="관리자">관리자</option>
            </select>
          </div>
          <div className="form-group col-3">
            <label>이름:</label>
            <input 
              type="text" 
              className="form-control" 
              value={searchParams.name_sch}
              onChange={(e) => handleSearchChange('name_sch', e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="이름 검색"
            />
          </div>
          <div className="form-group col-3" style={{ textAlign: 'right', display: 'flex', alignItems: 'end', gap: '5px' }}>
            <button type="button" className="btn btn-primary" onClick={handleSearch}>검색</button>
            <button type="button" className="btn btn-success" onClick={handleEmployeeInsert}>등록</button>
            <button type="button" className="btn btn-info" onClick={handleExcelDownload}>엑셀저장</button>
          </div>
        </div>
      </div>

      <div className="employee-layout">
        {/* 직원 목록 */}
        <div className="employee-list-container">
          <div className="employee-count-info">
            <span>총 {pagination.totalCount}명</span>
            <span>{pagination.currentPage} / {pagination.totalPages} 페이지</span>
          </div>

          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th onClick={() => handleSort('name')} style={{ cursor: 'pointer' }}>이름 ↕</th>
                  <th onClick={() => handleSort('emstd_id')} style={{ cursor: 'pointer' }}>직급 ↕</th>
                  <th onClick={() => handleSort('emclass_id')} style={{ cursor: 'pointer' }}>파트 ↕</th>
                  <th onClick={() => handleSort('status')} style={{ cursor: 'pointer' }}>상태 ↕</th>
                  <th onClick={() => handleSort('mobile_phone')} style={{ cursor: 'pointer' }}>핸드폰 ↕</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan="5" className="text-center">로딩 중...</td></tr>
                ) : employees.length === 0 ? (
                  <tr><td colSpan="5" className="text-center">검색 결과가 없습니다.</td></tr>
                ) : (
                  employees.map(emp => (
                    <tr 
                      key={emp.em_id} 
                      className={`employee-row ${selectedEmployee?.em_id === emp.em_id ? 'selected' : ''}`}
                      onClick={() => handleEmployeeSelect(emp)}
                    >
                      <td>{emp.name || ''}</td>
                      <td>{emp.emstd_id || ''}</td>
                      <td>{emp.emclass_id || ''}</td>
                      <td>{emp.status || ''}</td>
                      <td>{emp.mobile_phone || ''}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* 페이징 */}
          <div className="pagination">
            <button onClick={() => handlePageChange(1)} disabled={pagination.currentPage <= 1}>처음</button>
            <button onClick={() => handlePageChange(pagination.currentPage - 1)} disabled={pagination.currentPage <= 1}>◀ 이전</button>
            <span>{pagination.currentPage} / {pagination.totalPages}</span>
            <button onClick={() => handlePageChange(pagination.currentPage + 1)} disabled={pagination.currentPage >= pagination.totalPages}>다음 ▶</button>
            <button onClick={() => handlePageChange(pagination.totalPages)} disabled={pagination.currentPage >= pagination.totalPages}>마지막</button>
          </div>
        </div>

        {/* 직원 상세 정보 */}
        <div className="detail-section">
          {!selectedEmployee ? (
            <div className="employee-detail-placeholder">
              직원을 선택하면 상세 정보가 표시됩니다
            </div>
          ) : (
            <>
              {/* 탭 메뉴 */}
              <div className="nav-tabs">
                <div 
                  className={`nav-tab ${activeTab === 'info' ? 'active' : ''}`}
                  onClick={() => handleTabChange('info')}
                >
                  직원정보
                </div>
                <div 
                  className={`nav-tab ${activeTab === 'history' ? 'active' : ''}`}
                  onClick={() => handleTabChange('history')}
                >
                  이력관리
                </div>
                <div 
                  className={`nav-tab ${activeTab === 'license' ? 'active' : ''}`}
                  onClick={() => handleTabChange('license')}
                >
                  자격증
                </div>
              </div>
              
              {/* 탭 내용 */}
              <div className="tab-content">
                {activeTab === 'info' && employeeDetail && (
                  <EmployeeDetailTab 
                    employee={employeeDetail} 
                    onEdit={handleEmployeeEdit}
                  />
                )}
                {activeTab === 'history' && (
                  <EmployeeHistoryTab history={employeeHistory} />
                )}
                {activeTab === 'license' && (
                  <EmployeeLicenseTab licenses={employeeLicense} />
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// 직원 상세 정보 탭
const EmployeeDetailTab = ({ employee, onEdit }) => (
  <table className="detail-table" style={{ width: '100%', borderCollapse: 'collapse', tableLayout: 'fixed', fontSize: '12px' }}>
    <tbody>
      <tr>
        <td className="detail-label">이름</td>
        <td className="detail-value">
          {employee.name || ''}
          <button 
            type="button" 
            className="btn btn-warning" 
            style={{ float: 'right', padding: '4px 8px', fontSize: '11px' }}
            onClick={() => onEdit(employee.em_id)}
          >
            수정
          </button>
        </td>
        <td className="detail-label" rowSpan="5" style={{ textAlign: 'center', verticalAlign: 'middle' }}>사진</td>
        <td className="detail-value" rowSpan="5" style={{ textAlign: 'center', verticalAlign: 'middle' }}>
          <img 
            src={employee.maskname ? `/static/images/employees/${employee.maskname}` : '/static/images/common/noimg.gif'}
            className="employee-photo" 
            alt="직원사진" 
            onError={(e) => { e.target.src = '/static/images/common/noimg.gif'; }}
            style={{ maxWidth: '100px', maxHeight: '100px', objectFit: 'cover' }}
          />
        </td>
      </tr>
      <tr>
        <td className="detail-label">생일</td>
        <td className="detail-value">{employee.birthday || ''}</td>
      </tr>
      <tr>
        <td className="detail-label">전화번호</td>
        <td className="detail-value">{employee.phone || ''}</td>
      </tr>
      <tr>
        <td className="detail-label">핸드폰</td>
        <td className="detail-value">{employee.mobile_phone || ''}</td>
      </tr>
      <tr>
        <td className="detail-label">이메일</td>
        <td className="detail-value">{employee.email || ''}</td>
      </tr>
      <tr>
        <td className="detail-label">주소</td>
        <td className="detail-value" colSpan="3">{employee.address || ''}</td>
      </tr>
      <tr>
        <td className="detail-label">소속</td>
        <td className="detail-value">{employee.prop_name || ''}</td>
        <td className="detail-label">근무지</td>
        <td className="detail-value">{employee.work_address || ''}</td>
      </tr>
      <tr>
        <td className="detail-label">성별</td>
        <td className="detail-value">{employee.sex || ''}</td>
        <td className="detail-label">파트</td>
        <td className="detail-value">{employee.emclass_id || ''}</td>
      </tr>
      <tr>
        <td className="detail-label">회사명</td>
        <td className="detail-value">{employee.com_id || ''}</td>
        <td className="detail-label">직급</td>
        <td className="detail-value">{employee.emstd_id || ''}</td>
      </tr>
    </tbody>
  </table>
);

// 직원 이력 탭
const EmployeeHistoryTab = ({ history }) => (
  <>
    <div style={{ marginBottom: '15px' }}>
      <button className="btn btn-primary">이력 등록</button>
    </div>
    <table className="data-table">
      <thead>
        <tr>
          <th>번호</th>
          <th>설명</th>
          <th>파일</th>
          <th>등록일</th>
        </tr>
      </thead>
      <tbody>
        {history.length === 0 ? (
          <tr><td colSpan="4" className="text-center">등록된 이력이 없습니다.</td></tr>
        ) : (
          history.map(item => (
            <tr key={item.auto_number}>
              <td>{item.auto_number || ''}</td>
              <td>{(item.filetype || '') + ' ' + (item.comments || '')}</td>
              <td>{item.filename || ''}</td>
              <td>{item.reg_date || ''}</td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  </>
);

// 직원 자격증 탭
const EmployeeLicenseTab = ({ licenses }) => (
  <table className="data-table">
    <thead>
      <tr>
        <th>번호</th>
        <th>직원ID</th>
        <th>자격증명</th>
        <th>취득일자</th>
        <th>비고</th>
      </tr>
    </thead>
    <tbody>
      {licenses.length === 0 ? (
        <tr><td colSpan="5" className="text-center">등록된 자격증이 없습니다.</td></tr>
      ) : (
        licenses.map(item => (
          <tr key={item.licenceem_id}>
            <td>{item.licenceem_id || ''}</td>
            <td>{item.em_id || ''}</td>
            <td>{item.licence_id || ''}</td>
            <td>{item.certici_date || ''}</td>
            <td>{item.description || ''}</td>
          </tr>
        ))
      )}
    </tbody>
  </table>
);

export default EmployeeList;