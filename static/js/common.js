// 공통 AJAX 처리 함수
function handleSelectOptions({url, postData, selectorID, defaultOption, option_val, option_text, option_textFormat}) {
    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(postData)
    })
    .then(response => response.json())
    .then(data => {
        if (data && data.success) {
            const $select = document.querySelector(selectorID);
            if (!$select) {
                console.error('셀렉터를 찾을 수 없습니다:', selectorID);
                return;
            }
            
            $select.innerHTML = ''; // 기존 옵션 제거

            // 기본 옵션 추가
            const defaultOpt = document.createElement('option');
            defaultOpt.value = '';
            defaultOpt.textContent = defaultOption;
            $select.appendChild(defaultOpt);

            // 데이터로 옵션 생성
            data.data.forEach(function(item) {
                let displayText;
                if (option_textFormat === 'option_text(option_val)') {
                    displayText = `${item[option_text] || ''} (${item[option_val] || ''})`;
                } else {
                    displayText = item[option_text] || '';
                }

                const option = document.createElement('option');
                option.value = option_val ? (item[option_val] || '') : (item[option_text] || '');
                option.textContent = displayText;
                $select.appendChild(option);
            });
        } else {
            console.error('데이터 로드 실패:', data?.message || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('AJAX 오류:', error);
    });
}

// 기존 getValue 함수들을 새로운 API 구조에 맞게 리팩토링
function getValue({url, collection, option_val, option_text, option_textFormat, selectorID, defaultOption, sort_field, findKey_01, findVal_01, findKey_02, findVal_02}) {
    const postData = {
        collection: collection,
        id_field: option_val || option_text,
        text_field: option_text,
        sort_field: sort_field,
        findKey_01: findKey_01,
        findVal_01: findVal_01,
        findKey_02: findKey_02,
        findVal_02: findVal_02
    };

    handleSelectOptions({url, postData, selectorID, defaultOption, option_val, option_text, option_textFormat});
}

function getValueDistinct({url, collection, option_val, option_text, option_textFormat, selectorID, defaultOption, sort_field, findKey_01, findVal_01, findKey_02, findVal_02}) {
    const postData = {
        collection: collection,
        id_field: option_val || option_text,
        text_field: option_text,
        sort_field: sort_field,
        findKey_01: findKey_01,
        findVal_01: findVal_01,
        findKey_02: findKey_02,
        findVal_02: findVal_02
    };

    handleSelectOptions({url, postData, selectorID, defaultOption, option_val, option_text, option_textFormat});
}

// 미완료건 수를 조회하는 함수
function getUncompletedCount({url, collection, selectorID, findKey_01, findVal_01, findKey_02, findVal_02}) {
    const postData = {
        collection: collection,
        findKey_01: findKey_01,
        findVal_01: findVal_01,
        findKey_02: findKey_02,
        findVal_02: findVal_02
    };

    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(postData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('getUncompletedCount response:', data);
        if (data && data.success) {
            const $selector = document.querySelector(selectorID + ' strong');
            if ($selector) {
                $selector.textContent = data.uncompleted_count + '건';
            }
        } else {
            console.error('데이터 로드 실패:', data?.message || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('getUncompletedCount 오류:', error);
    });
}

// 폼 데이터를 객체로 변환하는 유틸리티 함수
function formToObject(form) {
    const formData = new FormData(form);
    const obj = {};
    for (let [key, value] of formData.entries()) {
        obj[key] = value;
    }
    return obj;
}

// 쿼리 스트링을 객체로 변환하는 함수
function queryStringToObject(queryString) {
    const params = new URLSearchParams(queryString);
    const obj = {};
    for (let [key, value] of params.entries()) {
        obj[key] = value;
    }
    return obj;
}

// 객체를 쿼리 스트링으로 변환하는 함수
function objectToQueryString(obj) {
    const params = new URLSearchParams();
    for (let [key, value] of Object.entries(obj)) {
        if (value !== null && value !== undefined && value !== '') {
            params.append(key, value);
        }
    }
    return params.toString();
}

// 날짜 포맷팅 함수
function formatDate(date, format = 'YYYY-MM-DD') {
    if (!date) return '';
    
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const seconds = String(d.getSeconds()).padStart(2, '0');
    
    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes)
        .replace('ss', seconds);
}

// 숫자 포맷팅 함수 (천단위 콤마)
function formatNumber(num) {
    if (num === null || num === undefined || num === '') return '';
    return Number(num).toLocaleString();
}

// 안전한 HTML 이스케이프 함수
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 로딩 스피너 표시/숨김
function showLoading(selector = 'body') {
    const target = document.querySelector(selector);
    if (!target) return;
    
    // 기존 로딩 제거
    const existingLoader = target.querySelector('.loading-overlay');
    if (existingLoader) {
        existingLoader.remove();
    }
    
    const loader = document.createElement('div');
    loader.className = 'loading-overlay';
    loader.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <div>로딩 중...</div>
        </div>
    `;
    loader.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    `;
    
    target.style.position = 'relative';
    target.appendChild(loader);
}

function hideLoading(selector = 'body') {
    const target = document.querySelector(selector);
    if (!target) return;
    
    const loader = target.querySelector('.loading-overlay');
    if (loader) {
        loader.remove();
    }
}

// 알림 메시지 표시
function showAlert(message, type = 'info', duration = 3000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 4px;
        z-index: 10000;
        min-width: 250px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    `;
    
    // 타입별 스타일
    const styles = {
        success: 'background: #d4edda; color: #155724; border: 1px solid #c3e6cb;',
        error: 'background: #f8d7da; color: #721c24; border: 1px solid #f1aeb5;',
        warning: 'background: #fff3cd; color: #856404; border: 1px solid #ffeaa7;',
        info: 'background: #d1ecf1; color: #0c5460; border: 1px solid #b8daff;'
    };
    
    alertDiv.style.cssText += styles[type] || styles.info;
    
    document.body.appendChild(alertDiv);
    
    // 자동 제거
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, duration);
}

// 확인 다이얼로그
function showConfirm(message, callback) {
    if (confirm(message)) {
        if (typeof callback === 'function') {
            callback();
        }
        return true;
    }
    return false;
}

// 페이지 새로고침 없이 URL 업데이트 (MPA에서도 히스토리 관리용)
function updateURL(params) {
    const url = new URL(window.location);
    
    for (let [key, value] of Object.entries(params)) {
        if (value !== null && value !== undefined && value !== '') {
            url.searchParams.set(key, value);
        } else {
            url.searchParams.delete(key);
        }
    }
    
    window.history.replaceState({}, '', url);
}

// 간단한 디바운스 함수
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 전역 에러 핸들러
window.addEventListener('error', function(e) {
    console.error('전역 오류:', e.error);
    // 필요시 서버로 오류 로그 전송
});

// 전역 AJAX 에러 핸들러
window.addEventListener('unhandledrejection', function(e) {
    console.error('처리되지 않은 Promise 거부:', e.reason);
    // 필요시 서버로 오류 로그 전송
});