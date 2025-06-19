window.headerPinned = true;
window.sidebarPinned = true;
window.userInfo = null;
window.propList = [];
window.menuData = [];

// 사용자 정보 로드
window.loadUserInfo = function() {
    return fetch('/common/get_user_info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.userInfo = data;
            const userInfoElement = document.getElementById('user-info-text');
            if (userInfoElement) {
                userInfoElement.innerHTML = `사용자: ${data.name} 님 [${data.emclass_id}]`;
            }
            return data;
        } else {
            window.showStatus('사용자 정보 로드 실패: ' + data.message);
            return null;
        }
    })
    .catch(error => {
        window.showStatus('사용자 정보 로드 중 오류');
        return null;
    });
};

// 사업소 목록 로드
window.loadPropList = function(em_id) {
    return fetch('/common/get_prop_list', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ em_id: em_id })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && Array.isArray(data.data)) {
            window.propList = data.data;
            window.renderPropList();
            return data.data;
        } else {
            window.showStatus('사업소 목록 로드 실패');
            return [];
        }
    })
    .catch(error => {
        window.showStatus('사업소 목록 로드 중 오류');
        return [];
    });
};

window.renderPropList = function() {
    const propSelect = document.getElementById('sel_business_place');
    if (!propSelect) return;

    propSelect.innerHTML = '';
    if (!window.propList || window.propList.length === 0) {
        propSelect.innerHTML = '<option value="">사업소 없음</option>';
        return;
    }

    propSelect.innerHTML = '<option value="">사업소 선택</option>';
    window.propList.forEach(prop => {
        const option = document.createElement('option');
        option.value = prop.prop_id;
        option.textContent = `${prop.prop_name} (${prop.prop_id})`;
        propSelect.appendChild(option);
    });

    if (window.propList.length > 0) {
        propSelect.value = window.propList[0].prop_id;
    }
};

// 메뉴 데이터 로드 (DB 기반)
window.loadMenuData = function() {
    if (!window.userInfo || !window.userInfo.em_id) return Promise.resolve([]);

    return fetch('/get_menu_data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ em_id: window.userInfo.em_id })
    })
    .then(response => response.json())
    .then(data => {
        if (Array.isArray(data)) {
            window.menuData = data;
            window.renderModuleMenu();
            window.renderSidebarMenu();
            return data;
        } else {
            window.showStatus('메뉴 데이터 로드 실패');
            return [];
        }
    })
    .catch(() => []);
};

window.renderModuleMenu = function() {
    const moduleMenu = document.getElementById('moduleMenu');
    if (!moduleMenu) return;

    moduleMenu.innerHTML = window.menuData.map(module => `
        <a href="#" class="module-item" data-module-id="${module.menu_01_module_id}">
            ${module.menu_01_title}
        </a>
    `).join('');
};

window.renderSidebarMenu = function() {
    const menuContainer = document.getElementById('menuContainer');
    if (!menuContainer) return;

    if (!window.menuData || window.menuData.length === 0) {
        menuContainer.innerHTML = '<div style="text-align: center; padding: 20px; color: #6c757d;">접근 가능한 메뉴가 없습니다.</div>';
        return;
    }

    let menuHtml = '';
    window.menuData.forEach(module => {
        menuHtml += `
            <div class="menu-group">
                <div class="menu-item-parent" onclick="toggleSubMenu(this)">
                    <span>${module.menu_01_title}</span>
                    <span class="menu-arrow">▶</span>
                </div>
                <div class="sub-menu-container" style="display: none;">
        `;
        (module.menu_02_data || []).forEach(menu2 => {
            if (menu2.menu_03_data.length > 0) {
                menuHtml += `
                    <div class="menu-subgroup">
                        <div class="menu-sub-title">${menu2.menu_02_name}</div>
                `;
                menu2.menu_03_data.forEach(menu3 => {
                    menuHtml += `<a href="${menu3.menu_03_url || '#'}" class="sub-menu">${menu3.menu_03_name}</a>`;
                });
                menuHtml += `</div>`;
            } else {
                menuHtml += `<a href="${menu2.menu_02_url || '#'}" class="sub-menu">${menu2.menu_02_name}</a>`;
            }
        });
        menuHtml += '</div></div>';
    });

    menuContainer.innerHTML = menuHtml;
};
// 하위 메뉴 토글 함수
window.toggleSubMenu = function(element) {
    const container = element.nextElementSibling;
    const arrow = element.querySelector('.menu-arrow');
    
    if (!container || !arrow) return;
    
    if (container.style.display === 'none' || container.style.display === '') {
        container.style.display = 'block';
        arrow.textContent = '▼';
    } else {
        container.style.display = 'none';
        arrow.textContent = '▶';
    }
};

// 사업소 변경 이벤트
window.onBusinessPlaceChange = function() {
    const propSelect = document.getElementById('sel_business_place');
    const selectedPropId = propSelect.value;
    const selectedPropName = propSelect.options[propSelect.selectedIndex].text;
    console.log('BASE: 사업소 변경됨:', selectedPropId, selectedPropName);
    
    if (selectedPropId && window.userInfo) {
        window.showStatus('선택된 사업소: ' + selectedPropName);
        
        // 메인 페이지에서 직원정보가 표시되고 있다면 자동 검색
        if (window.location.pathname === '/main' && typeof searchEmployees === 'function') {
            setTimeout(() => {
                searchEmployees();
            }, 500);
        }
    }
};

// 상태 메시지 표시
window.showStatus = function(message) {
    const statusIndicator = document.getElementById('statusIndicator');
    if (statusIndicator) {
        statusIndicator.textContent = message;
        statusIndicator.classList.add('show');
        setTimeout(() => {
            statusIndicator.classList.remove('show');
        }, 2000);
    }
};

// 헤더 핀 토글 함수
window.toggleHeaderPin = function(button) {
    console.log('헤더 핀 클릭됨!', window.headerPinned);
    
    window.headerPinned = !window.headerPinned;
    const headerFrame = document.getElementById('headerFrame');
    
    if (window.headerPinned) {
        button.classList.add('pinned');
        button.textContent = '📌';
        if (headerFrame) headerFrame.classList.remove('hidden');
        window.showStatus('헤더가 고정되었습니다.');
    } else {
        button.classList.remove('pinned');
        button.textContent = '📍';
        if (headerFrame) headerFrame.classList.add('hidden');
        window.showStatus('헤더가 비고정되었습니다. 상단에 마우스를 대면 나타납니다.');
    }
    
    console.log('헤더 핀 상태 변경됨:', window.headerPinned);
};

// 사이드바 핀 토글 함수
window.toggleSidebarPin = function(button) {
    console.log('사이드바 핀 클릭됨!', window.sidebarPinned);
    
    window.sidebarPinned = !window.sidebarPinned;
    const sidebarFrame = document.getElementById('sidebarFrame');
    
    if (window.sidebarPinned) {
        button.classList.add('pinned');
        button.textContent = '📌';
        if (sidebarFrame) sidebarFrame.classList.remove('hidden');
        window.showStatus('사이드바가 고정되었습니다.');
    } else {
        button.classList.remove('pinned');
        button.textContent = '📍';
        if (sidebarFrame) sidebarFrame.classList.add('hidden');
        window.showStatus('사이드바가 비고정되었습니다. 좌측에 마우스를 대면 나타납니다.');
    }
    
    console.log('사이드바 핀 상태 변경됨:', window.sidebarPinned);
};

// 시계 업데이트
window.updateClock = function() {
    const now = new Date();
    const timeStr = now.getFullYear() + '-' +
                   String(now.getMonth() + 1).padStart(2, '0') + '-' +
                   String(now.getDate()).padStart(2, '0') + ' (' +
                   ['일','월','화','수','목','금','토'][now.getDay()] + ') ' +
                   String(now.getHours()).padStart(2, '0') + ':' +
                   String(now.getMinutes()).padStart(2, '0') + ':' +
                   String(now.getSeconds()).padStart(2, '0');
    const clockElement = document.getElementById('current-datetime');
    if (clockElement) {
        clockElement.textContent = timeStr;
    }
};

// 호버 이벤트 함수들
window.onHeaderHover = function() {
    console.log('헤더 호버 트리거!', window.headerPinned);
    if (!window.headerPinned) {
        const headerFrame = document.getElementById('headerFrame');
        if (headerFrame) {
            headerFrame.classList.add('hover-show');
            console.log('헤더 표시됨');
        }
    }
};

window.onHeaderLeave = function() {
    console.log('헤더 떠남');
    if (!window.headerPinned) {
        const headerFrame = document.getElementById('headerFrame');
        setTimeout(() => {
            if (headerFrame && !headerFrame.matches(':hover')) {
                headerFrame.classList.remove('hover-show');
                console.log('헤더 숨겨짐');
            }
        }, 300);
    }
};

window.onSidebarHover = function() {
    console.log('사이드바 호버 트리거!', window.sidebarPinned);
    if (!window.sidebarPinned) {
        const sidebarFrame = document.getElementById('sidebarFrame');
        if (sidebarFrame) {
            sidebarFrame.classList.add('hover-show');
            console.log('사이드바 표시됨');
        }
    }
};

window.onSidebarLeave = function() {
    console.log('사이드바 떠남');
    if (!window.sidebarPinned) {
        const sidebarFrame = document.getElementById('sidebarFrame');
        setTimeout(() => {
            if (sidebarFrame && !sidebarFrame.matches(':hover')) {
                sidebarFrame.classList.remove('hover-show');
                console.log('사이드바 숨겨짐');
            }
        }, 300);
    }
};

// 로그아웃 함수
window.logout = function() {
    if (confirm('로그아웃 하시겠습니까?')) {
        fetch('/login/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = data.redirect;
            }
        })
        .catch(error => {
            console.error('로그아웃 오류:', error);
            alert('로그아웃 처리 중 오류가 발생했습니다.');
        });
    }
};

// 초기화 함수
window.initialize = function() {
    console.log('=== BASE 시스템 초기화 시작 ===');
    
    // 시계 시작
    window.updateClock();
    setInterval(window.updateClock, 1000);
    
    console.log('BASE: 1단계 - 사용자 정보 로드 시작');
    
    window.loadUserInfo()
        .then(userInfo => {
            console.log('BASE: 2단계 - 사용자 정보 로드 완료', userInfo);
            if (userInfo && userInfo.em_id) {
                console.log('BASE: 3단계 - 사업소 목록 로드 시작');
                return window.loadPropList(userInfo.em_id)
                    .then(propList => {
                        console.log('BASE: 4단계 - 사업소 목록 로드 완료', propList ? propList.length : 0, '개');
                        console.log('BASE: 5단계 - 메뉴 데이터 로드 시작');
                        return window.loadMenuData();
                    });
            }
            throw new Error('사용자 정보 로드 실패');
        })
        .then(menuData => {
            console.log('BASE: 6단계 - 메뉴 데이터 로드 완료', menuData ? menuData.length : 0, '개');
            console.log('=== BASE 시스템 초기화 완료 ===');
            window.showStatus('시스템이 준비되었습니다.');
        })
        .catch(error => {
            console.error('=== BASE 초기화 오류 ===', error);
            window.showStatus('시스템 초기화 중 오류가 발생했습니다: ' + error.message);
        });
};

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded 이벤트 발생');
    if (typeof window.initialize === 'function') {
        window.initialize();
    } else {
        console.error('initialize 함수를 찾을 수 없습니다.');
    }
});

// 이미 로드된 경우를 위한 백업
if (document.readyState === 'loading') {
    console.log('문서 로딩 중 - DOMContentLoaded 대기');
} else {
    console.log('문서 이미 로드됨 - 즉시 초기화');
    setTimeout(function() {
        if (typeof window.initialize === 'function') {
            window.initialize();
        } else {
            console.error('initialize 함수를 찾을 수 없습니다.');
        }
    }, 100);
}