import axios from 'axios';

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:5000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // 세션 쿠키 포함
});

// 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    // 요청 로깅
    console.log(`🔗 API 요청: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API 요청 오류:', error);
    return Promise.reject(error);
  }
);

// 응답 인터셉터
api.interceptors.response.use(
  (response) => {
    // 성공 응답 로깅
    console.log(`✅ API 응답: ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data);
    return response;
  },
  (error) => {
    // 오류 응답 처리
    console.error('API 응답 오류:', error);
    
    if (error.response?.status === 401) {
      // 인증 오류 시 로그인 페이지로 리다이렉트
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

// API 서비스 객체
export const apiService = {
  // GET 요청
  get: (url, params = {}) => {
    return api.get(url, { params });
  },

  // POST 요청
  post: (url, data = {}) => {
    return api.post(url, data);
  },

  // PUT 요청
  put: (url, data = {}) => {
    return api.put(url, data);
  },

  // DELETE 요청
  delete: (url) => {
    return api.delete(url);
  },

  // 파일 업로드
  upload: (url, formData) => {
    return api.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }
};

// 특화된 API 호출 함수들
export const authAPI = {
  // 로그인
  login: (credentials) => {
    return apiService.post('/login/login_check', credentials);
  },

  // 로그아웃
  logout: () => {
    return apiService.post('/login/logout');
  },

  // 사용자 정보 조회
  getUserInfo: () => {
    return apiService.post('/common/get_user_info');
  }
};

export const commonAPI = {
  // 사업소 목록 조회
  getPropList: (emId) => {
    return apiService.post('/common/get_prop_list', { em_id: emId });
  },

  // 메뉴 데이터 조회
  getMenuData: (emId) => {
    return apiService.post('/get_menu_data', { em_id: emId });
  },

  // 건물 목록 조회
  getBuildingList: (emId, propId, blId = null) => {
    return apiService.post('/common/get_bl_list', { 
      em_id: emId, 
      prop_id: propId,
      ...(blId && { bl_id: blId })
    });
  },

  // 셀렉트 옵션 조회
  getSelectOptions: (params) => {
    return apiService.post('/common/get_select_options', params);
  }
};

export const employeeAPI = {
  // 직원 목록 조회
  getEmployeeList: (params) => {
    return apiService.post('/fm/em_entry', {
      c_type: 'list',
      ...params
    });
  },

  // 직원 상세 정보 조회
  getEmployeeDetail: (emId) => {
    return apiService.post('/fm/em_entry', {
      c_type: 'detail',
      em_id: emId
    });
  },

  // 직원 이력 조회
  getEmployeeHistory: (emId) => {
    return apiService.post('/fm/em_entry', {
      c_type: 'history',
      em_id: emId
    });
  },

  // 직원 자격증 조회
  getEmployeeLicense: (emId) => {
    return apiService.post('/fm/em_entry', {
      c_type: 'license',
      em_id: emId
    });
  },

  // 직원 목록 엑셀 다운로드
  downloadExcel: (params) => {
    const queryString = new URLSearchParams(params).toString();
    return `${api.defaults.baseURL}/fm/em_list_excel?${queryString}`;
  }
};

export const propAPI = {
  // 사업장 목록 조회
  getPropList: (params) => {
    return apiService.post('/fm/prop_entry', {
      c_type: 'list',
      ...params
    });
  },

  // 사업장 상세 정보 조회
  getPropDetail: (propId) => {
    return apiService.post('/fm/prop_entry', {
      c_type: 'detail',
      prop_id: propId
    });
  },

  // 사업장 등록
  insertProp: (data) => {
    return apiService.post('/fm/prop_entry', {
      c_type: 'insert',
      ...data
    });
  },

  // 사업장 수정
  updateProp: (data) => {
    return apiService.post('/fm/prop_entry', {
      c_type: 'update',
      ...data
    });
  },

  // 사업장 코드 중복 체크
  checkDuplicate: (propId) => {
    return apiService.post('/fm/prop_entry', {
      c_type: 'check_duplicate',
      prop_id: propId
    });
  }
};

export const propUpdateAPI = {
  // 사업장 수정 상세 정보 조회
  getPropUpdateDetail: (propId) => {
    return apiService.post('/fm/prop_update_entry', {
      c_type: 'detail',
      prop_id: propId
    });
  },

  // 사업장 수정 이력 조회
  getPropUpdateHistory: (params) => {
    return apiService.post('/fm/prop_update_entry', {
      c_type: 'history',
      ...params
    });
  },

  // 사업장 정보 저장
  savePropUpdate: (data) => {
    return apiService.post('/fm/prop_update_entry', {
      c_type: 'save',
      ...data
    });
  },

  // 이미지 업로드
  uploadImages: (propId, files, overwrite = false) => {
    const formData = new FormData();
    formData.append('prop_id', propId);
    formData.append('overwrite', overwrite);
    
    if (files && files.length > 0) {
      Array.from(files).forEach(file => {
        formData.append('images[]', file);
      });
    }
    
    return apiService.upload('/fm/upload_images', formData);
  }
};

export default api;