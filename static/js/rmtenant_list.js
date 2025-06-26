
// 🛡️ 완전한 스코프 분리 및 고급 모듈 패턴
(function() {
    'use strict';
    
    console.log('📋 rmtenant_list.html 고급 스크립트 시작!');
    
    // 🔥 기존 모듈 완전 정리
    if (typeof window.RmtenantListModule !== 'undefined') {
        console.log('📋 기존 RmtenantListModule 완전 제거');
        if (window.RmtenantListModule.cleanup && typeof window.RmtenantListModule.cleanup === 'function') {
            window.RmtenantListModule.cleanup();
        }
        delete window.RmtenantListModule;
    }
    
    // 고급 모듈 생성
    window.RmtenantListModule = {
        // 📊 데이터 저장소
        data: {
            isInitialized: false,
            moduleId: 'rmtenant_list_' + Date.now(),
            currentPage: 1,
            totalPages: 1,
            totalCount: 0,
            pageSize: 10,
            sortField: '',
            sortDirection: 'ASC',
            searchConditions: {},
            selectedRows: new Set(),
            lastUpdated: null
        },
        
        // 🔧 고급 DOM 접근 헬퍼
        safeGetElement: function(id) {
            try {
                const element = document.getElementById(id);
                if (!element) {
                    console.warn('📋 [RMTENANT] DOM 요소를 찾을 수 없음:', id);
                }
                return element;
            } catch (error) {
                console.error('📋 [RMTENANT] DOM 접근 오류:', error);
                return null;
            }
        },

        // 🚀 초기화
        init: function() {
            console.log('📋 [RMTENANT] 고급 페이지 초기화 시작');
            
            this.data.isInitialized = true;
            this.data.lastUpdated = new Date();
            
            // 이벤트 리스너 등록
            this.bindEvents();
            
            // 키보드 단축키 등록
            this.bindKeyboardShortcuts();
            
            // 초기 데이터 로드
            this.loadData();
            
            console.log('📋 [RMTENANT] 초기화 완료');
        },
        
        // 🎯 이벤트 리스너 등록
        bindEvents: function() {
            
            // ')" value="검색"><%=Search_Room_t%> 버튼
            const btn_search = this.safeGetElement('btn_search');
            if (btn_search) {
                btn_search.onclick = (e) => {
                    e.preventDefault();
                    this.search();
                };
                
                // 툴팁 추가
                const tooltip = '조건에 맞는 데이터를 검색합니다';
                if (tooltip) {
                    btn_search.title = tooltip;
                }
            }

            // <%=Registered_Occupants_t%> 버튼
            const btn_register = this.safeGetElement('btn_register');
            if (btn_register) {
                btn_register.onclick = (e) => {
                    e.preventDefault();
                    this.register();
                };
                
                // 툴팁 추가
                const tooltip = '새 항목을 등록합니다';
                if (tooltip) {
                    btn_register.title = tooltip;
                }
            }

            // ');"><%=list_t%> 버튼
            const btn_list = this.safeGetElement('btn_list');
            if (btn_list) {
                btn_list.onclick = (e) => {
                    e.preventDefault();
                    this.list();
                };
                
                // 툴팁 추가
                const tooltip = '목록 페이지로 이동합니다';
                if (tooltip) {
                    btn_list.title = tooltip;
                }
            }

            // 목록보기 버튼
            const btn_list = this.safeGetElement('btn_list');
            if (btn_list) {
                btn_list.onclick = (e) => {
                    e.preventDefault();
                    this.list();
                };
                
                // 툴팁 추가
                const tooltip = '목록 페이지로 이동합니다';
                if (tooltip) {
                    btn_list.title = tooltip;
                }
            }

            // reset 버튼
            const btn_reset = this.safeGetElement('btn_reset');
            if (btn_reset) {
                btn_reset.onclick = (e) => {
                    e.preventDefault();
                    this.reset();
                };
            }

            // excel 버튼
            const btn_excel = this.safeGetElement('btn_excel');
            if (btn_excel) {
                btn_excel.onclick = (e) => {
                    e.preventDefault();
                    this.excel();
                };
            }
            
            // 페이지 크기 변경 이벤트
            const pageSizeSelect = this.safeGetElement('page_size');
            if (pageSizeSelect) {
                pageSizeSelect.onchange = () => {
                    this.data.pageSize = parseInt(pageSizeSelect.value);
                    this.data.currentPage = 1;
                    this.loadData();
                };
            }
            
            // 검색 입력 실시간 필터링 (디바운스)
            this.bindSearchInputs();
            
            console.log('📋 [RMTENANT] 이벤트 리스너 등록 완료');
        },
        
        // ⌨️ 키보드 단축키
        bindKeyboardShortcuts: function() {
            document.addEventListener('keydown', (e) => {
                // Ctrl+S: 저장
                if (e.ctrlKey && e.key === 's') {
                    e.preventDefault();
                    if (this.save && typeof this.save === 'function') {
                        this.save();
                    }
                }
                
                // F5: 새로고침/조회
                if (e.key === 'F5') {
                    e.preventDefault();
                    if (this.search && typeof this.search === 'function') {
                        this.search();
                    } else if (this.loadData && typeof this.loadData === 'function') {
                        this.loadData();
                    }
                }
                
                // ESC: 취소/닫기
                if (e.key === 'Escape') {
                    if (this.cancel && typeof this.cancel === 'function') {
                        this.cancel();
                    }
                }
            });
        },
        
        // 🔍 검색 입력 디바운스
        bindSearchInputs: function() {
            const searchInputs = document.querySelectorAll('[id^="search_"]');
            searchInputs.forEach(input => {
                let timeout;
                input.addEventListener('input', () => {
                    clearTimeout(timeout);
                    timeout = setTimeout(() => {
                        if (this.autoSearch && typeof this.autoSearch === 'function') {
                            this.autoSearch();
                        }
                    }, 500);
                });
            });
        },
        
        
        // 📊 데이터 로드 (고급)
        loadData: function(action = 'read') {
            const requestData = {
                em_id: window.currentEmId || (window.userInfo && window.userInfo.em_id),
                page_size: this.data.pageSize,
                page_number: this.data.currentPage,
                action: action,
                sort_field: this.data.sortField,
                sort_direction: this.data.sortDirection
            };
            
            // 검색 조건 추가
            this.addSearchConditions(requestData);
            
            console.log('🔍 [RMTENANT] 데이터 요청:', requestData);
            
            this.showLoading();
            
            fetch('rmtenant_list/get_data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('🔍 [RMTENANT] 데이터 응답:', data);
                if (data && data.success) {
                    this.data.totalCount = data.total_count || 0;
                    this.data.totalPages = data.total_pages || 1;
                    this.data.currentPage = data.current_page || 1;
                    
                    this.renderTable(data.result_data || []);
                    this.renderPagination();
                    this.updateDataInfo();
                    
                    // 검색 조건 저장
                    this.saveToStorage('lastSearch', requestData);
                    
                } else {
                    console.error('데이터 로드 실패:', data ? data.message : 'Unknown error');
                    this.renderTable([]);
                    this.showError('데이터를 불러올 수 없습니다: ' + (data ? data.message : 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('데이터 로드 오류:', error);
                this.renderTable([]);
                this.showError('데이터를 불러오는 중 오류가 발생했습니다: ' + error.message);
            });
        },
        
        // 🔍 검색 조건 추가 (고급)
        addSearchConditions: function(requestData) {
            const searchElements = document.querySelectorAll('[id^="search_"]');
            searchElements.forEach(element => {
                const fieldName = element.id.replace('search_', '');
                const value = element.value ? element.value.trim() : '';
                
                if (value) {
                    requestData[`search_${fieldName}`] = value;
                    this.data.searchConditions[fieldName] = value;
                }
            });
        },
        
        // 📋 테이블 렌더링 (고급)
        renderTable: function(data) {
            const tableContent = this.safeGetElement('rmtenant_list_table_content');
            if (!tableContent) return;
            
            if (!data || data.length === 0) {
                tableContent.innerHTML = `
                    <div class="empty-message">
                        <i class="fas fa-inbox" style="font-size: 48px; color: #dee2e6; margin-bottom: 16px;"></i>
                        <div>검색 결과가 없습니다.</div>
                        <div style="font-size: 11px; color: #6c757d; margin-top: 8px;">검색 조건을 확인해주세요.</div>
                    </div>
                `;
                return;
            }
            
            let html = '';
            data.forEach((item, index) => {
                html += this.renderTableRow(item, index);
            });
            
            tableContent.innerHTML = html;
            
            // 애니메이션 적용
            const rows = tableContent.querySelectorAll('.table-row');
            rows.forEach((row, index) => {
                row.style.animationDelay = `${index * 0.05}s`;
            });
        },
        
        // 📄 테이블 행 렌더링 (고급)
        renderTableRow: function(item, index) {
            const rowClass = index % 2 === 0 ? 'table-row' : 'table-row table-row-alt';
            const rowId = `row_${item.rmtenant_id || index}`;
            
            return `
                <div class="${rowClass}" id="${rowId}" 
                     onclick="RmtenantListModule.selectRow(${JSON.stringify(item).replace(/"/g, '&quot;')})">
                    <div class="table-cell col-default text-left">${item.tb_rmtenant_table || ""}</div>
                    <div class="table-cell col-default text-left">${item.random || ""}</div>
                    <div class="table-cell col-date text-center">${item.sb_move_date ? new Date(item.sb_move_date).toLocaleDateString() : ""}</div>
                </div>
            `;
        },
        
        // 🎯 행 선택 처리 (고급)
        selectRow: function(item) {
            console.log('📋 [RMTENANT] 행 선택됨:', item);
            
            // 선택 효과
            const rowElement = document.getElementById(`row_${item.rmtenant_id}`);
            if (rowElement) {
                // 기존 선택 제거
                document.querySelectorAll('.table-row.selected').forEach(row => {
                    row.classList.remove('selected');
                });
                
                // 새 선택 추가
                rowElement.classList.add('selected');
            }
            
            // 수정 페이지로 이동
            this.goToUpdate(item);
        },
        
        // 📝 수정 페이지로 이동
        goToUpdate: function(item) {
            const updateUrl = `rmtenant_update.html`;
            const title = `<%=title_t%> 수정`;
            this.openTab(updateUrl, title, item);
        },
        
        // ➕ 등록 페이지로 이동
        goToRegister: function() {
            const insertUrl = `rmtenant_insert.html`;
            const title = `<%=title_t%> 등록`;
            this.openTab(insertUrl, title);
        },
        
        // 🔍 검색 실행
        search: function() {
            this.data.currentPage = 1;
            this.loadData('search');
        },
        
        // 🔄 자동 검색 (디바운스)
        autoSearch: function() {
            if (this.searchTimeout) {
                clearTimeout(this.searchTimeout);
            }
            
            this.searchTimeout = setTimeout(() => {
                this.search();
            }, 300);
        },
        
        // 🧹 초기화
        reset: function() {
            // 검색 필드 초기화
            document.querySelectorAll('[id^="search_"]').forEach(element => {
                if (element.tagName === 'SELECT') {
                    element.selectedIndex = 0;
                } else {
                    element.value = '';
                }
            });
            
            // 데이터 초기화
            this.data.searchConditions = {};
            this.data.currentPage = 1;
            this.data.sortField = '';
            this.data.sortDirection = 'ASC';
            
            // 검색 조건 스토리지에서 제거
            this.saveToStorage('lastSearch', {});
            
            this.loadData('read');
        },
        
        // 📊 정렬 처리
        sortBy: function(field) {
            if (this.data.sortField === field) {
                // 같은 필드면 방향 변경
                this.data.sortDirection = this.data.sortDirection === 'ASC' ? 'DESC' : 'ASC';
            } else {
                // 다른 필드면 새로 설정
                this.data.sortField = field;
                this.data.sortDirection = 'ASC';
            }
            
            // 정렬 아이콘 업데이트
            this.updateSortIcons();
            
            // 데이터 재로드
            this.data.currentPage = 1;
            this.loadData('search');
        },
        
        // 🔄 정렬 아이콘 업데이트
        updateSortIcons: function() {
            // 모든 정렬 아이콘 초기화
            document.querySelectorAll('.sort-icon').forEach(icon => {
                icon.className = 'sort-icon fas fa-sort';
            });
            
            // 현재 정렬 필드 아이콘 업데이트
            if (this.data.sortField) {
                const headerCell = document.querySelector(`[data-field="${this.data.sortField}"] .sort-icon`);
                if (headerCell) {
                    const iconClass = this.data.sortDirection === 'ASC' ? 'fa-sort-up' : 'fa-sort-down';
                    headerCell.className = `sort-icon fas ${iconClass}`;
                }
            }
        },
        
        // 📄 페이지네이션 렌더링
        renderPagination: function() {
            const paginationArea = this.safeGetElement('rmtenant_list_pagination');
            if (!paginationArea) return;
            
            const totalPages = this.data.totalPages;
            const currentPage = this.data.currentPage;
            
            if (totalPages <= 1) {
                paginationArea.innerHTML = '';
                return;
            }
            
            let html = '<div class="pagination">';
            
            // 이전 페이지
            if (currentPage > 1) {
                html += `<button onclick="RmtenantListModule.goToPage(1)">«</button>`;
                html += `<button onclick="RmtenantListModule.goToPage(${currentPage - 1})">‹</button>`;
            }
            
            // 페이지 번호들
            const startPage = Math.max(1, currentPage - 2);
            const endPage = Math.min(totalPages, currentPage + 2);
            
            for (let i = startPage; i <= endPage; i++) {
                const activeClass = i === currentPage ? 'active' : '';
                html += `<button class="${activeClass}" onclick="RmtenantListModule.goToPage(${i})">${i}</button>`;
            }
            
            // 다음 페이지
            if (currentPage < totalPages) {
                html += `<button onclick="RmtenantListModule.goToPage(${currentPage + 1})">›</button>`;
                html += `<button onclick="RmtenantListModule.goToPage(${totalPages})">»</button>`;
            }
            
            html += '</div>';
            
            // 페이지 정보
            html += `
                <div class="page-info">
                    ${currentPage} / ${totalPages} 페이지 (총 ${this.data.totalCount}건)
                </div>
            `;
            
            paginationArea.innerHTML = html;
        },
        
        // 📄 페이지 이동
        goToPage: function(page) {
            if (page >= 1 && page <= this.data.totalPages && page !== this.data.currentPage) {
                this.data.currentPage = page;
                this.loadData('read');
            }
        },
        
        // 📊 데이터 정보 업데이트
        updateDataInfo: function() {
            const totalCountElement = this.safeGetElement('total_count');
            if (totalCountElement) {
                totalCountElement.textContent = this.data.totalCount.toLocaleString();
            }
        },
        
        // 📊 엑셀 다운로드
        excel: function() {
            const searchConditions = this.data.searchConditions;
            
            const requestData = {
                em_id: window.currentEmId || (window.userInfo && window.userInfo.em_id),
                action: 'excel',
                ...searchConditions
            };
            
            console.log('📊 [RMTENANT] 엑셀 다운로드 요청:', requestData);
            
            // 엑셀 다운로드 처리
            fetch('rmtenant_list/excel', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.blob();
            })
            .then(blob => {
                // 파일 다운로드
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `<%=title_t%>_${new Date().toISOString().slice(0, 10)}.xlsx`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showSuccess('엑셀 파일이 다운로드되었습니다.');
            })
            .catch(error => {
                console.error('엑셀 다운로드 오류:', error);
                this.showError('엑셀 다운로드 중 오류가 발생했습니다: ' + error.message);
            });
        }
        
        // 🌐 URL 파라미터 고급 처리
        getUrlParams: function() {
            const urlParams = new URLSearchParams(window.location.search);
            const params = {};
            for (const [key, value] of urlParams) {
                // 타입 추론
                if (value === 'true' || value === 'false') {
                    params[key] = value === 'true';
                } else if (!isNaN(value) && value !== '') {
                    params[key] = Number(value);
                } else {
                    params[key] = value;
                }
            }
            return params;
        },
        
        // 🔗 고급 탭 관리
        openTab: function(url, title, data = null) {
            try {
                if (window.tabManager && typeof window.tabManager.addTab === 'function') {
                    // 데이터가 있으면 URL 파라미터로 추가
                    if (data) {
                        const params = new URLSearchParams();
                        for (const [key, value] of Object.entries(data)) {
                            if (value !== null && value !== undefined && value !== '') {
                                params.append(key, value);
                            }
                        }
                        if (params.toString()) {
                            url += (url.includes('?') ? '&' : '?') + params.toString();
                        }
                    }
                    
                    window.tabManager.addTab(url, title);
                } else {
                    window.location.href = url;
                }
            } catch (error) {
                console.error('📋 [RMTENANT] 탭 열기 오류:', error);
                window.location.href = url;
            }
        },
        
        // 📋 목록으로 이동 (고급 탭 연동)
        goToList: function() {
            try {
                if (window.tabManager && window.tabManager.tabs) {
                    let listTabId = null;
                    
                    if (window.tabManager.tabs instanceof Map) {
                        for (const [tabId, tab] of window.tabManager.tabs.entries()) {
                            if (tabId.includes('rmtenant_list') || 
                                (tab.url && tab.url.includes('rmtenant_list.html'))) {
                                listTabId = tabId;
                                console.log('🟢 [RMTENANT] 기존 목록 탭 발견:', listTabId);
                                break;
                            }
                        }
                    }
                    
                    if (listTabId && typeof window.tabManager.switchToTab === 'function') {
                        window.tabManager.switchToTab(listTabId);
                        
                        setTimeout(() => {
                            if (typeof window.tabManager.removeCurrentTab === 'function') {
                                window.tabManager.removeCurrentTab();
                            }
                        }, 100);
                        
                        setTimeout(() => {
                            const listModuleName = 'RmtenantListModule';
                            if (window[listModuleName] && typeof window[listModuleName].refreshData === 'function') {
                                window[listModuleName].refreshData();
                            }
                        }, 300);
                        
                        return;
                    }
                    
                    if (typeof window.tabManager.addTab === 'function') {
                        window.tabManager.addTab('rmtenant_list.html', '<%=title_t%> 목록');
                        
                        setTimeout(() => {
                            if (typeof window.tabManager.removeCurrentTab === 'function') {
                                window.tabManager.removeCurrentTab();
                            }
                        }, 200);
                        
                        return;
                    }
                }
                
                window.location.href = 'rmtenant_list.html';
                
            } catch (error) {
                console.error('🔴 [RMTENANT] 목록 이동 중 오류:', error);
                window.location.href = 'rmtenant_list.html';
            }
        },
        
        // 💾 로컬 스토리지 관리
        saveToStorage: function(key, data) {
            try {
                localStorage.setItem(`rmtenant_list_${key}`, JSON.stringify(data));
            } catch (error) {
                console.warn('로컬 스토리지 저장 실패:', error);
            }
        },
        
        loadFromStorage: function(key) {
            try {
                const data = localStorage.getItem(`rmtenant_list_${key}`);
                return data ? JSON.parse(data) : null;
            } catch (error) {
                console.warn('로컬 스토리지 로드 실패:', error);
                return null;
            }
        },
        
        // 🎨 UI 상태 관리
        showLoading: function() {
            const content = this.safeGetElement('rmtenant_list_table_content') || 
                           this.safeGetElement('rmtenant_list_content');
            if (content) {
                content.innerHTML = `
                    <div class="loading">
                        <div class="spinner"></div>
                        데이터를 불러오는 중...
                    </div>
                `;
            }
        },
        
        hideLoading: function() {
            // 로딩이 완료되면 자동으로 콘텐츠로 대체됨
        },
        
        showMessage: function(message, type = 'info') {
            const messageHtml = `
                <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
            
            const container = this.safeGetElement('rmtenant_list_outer');
            if (container) {
                const existingAlert = container.querySelector('.alert');
                if (existingAlert) {
                    existingAlert.remove();
                }
                container.insertAdjacentHTML('afterbegin', messageHtml);
                
                // 3초 후 자동 제거
                setTimeout(() => {
                    const alert = container.querySelector('.alert');
                    if (alert) alert.remove();
                }, 3000);
            }
        },
        
        // ❌ 오류 처리
        showError: function(message) {
            console.error('🔴 [RMTENANT] 오류:', message);
            this.showMessage(message, 'danger');
        },
        
        // ✅ 성공 메시지
        showSuccess: function(message) {
            console.log('✅ [RMTENANT] 성공:', message);
            this.showMessage(message, 'success');
        },
        
        // ⚠️ 경고 메시지
        showWarning: function(message) {
            console.warn('⚠️ [RMTENANT] 경고:', message);
            this.showMessage(message, 'warning');
        },
        
        // 🔄 새로고침
        refreshData: function() {
            this.data.currentPage = 1;
            this.loadData();
        },
        
        // 🧹 정리 함수
        cleanup: function() {
            console.log('📋 [RMTENANT] RmtenantListModule 정리 중...');
            this.data.isInitialized = false;
            
            // 이벤트 리스너 제거
            document.removeEventListener('keydown', this.keydownHandler);
            
            // 타이머 정리
            if (this.searchTimeout) {
                clearTimeout(this.searchTimeout);
            }
        }
    };
    
    // 전역 함수 등록
    window.initializeRmtenantListModule = function() {
        window.RmtenantListModule.init();
    };
    
    // 새로고침 함수
    window.refreshRmtenantListModuleData = function() {
        if (window.RmtenantListModule && typeof window.RmtenantListModule.refreshData === 'function') {
            window.RmtenantListModule.refreshData();
        }
    };
    
    // 자동 초기화
    setTimeout(() => {
        console.log('📋 [RMTENANT] RmtenantListModule 자동 초기화 시작');
        window.RmtenantListModule.init();
    }, 100);
    
    console.log('📋 [RMTENANT] RmtenantListModule 로드 완료');
    
})(); // 즉시 실행 함수 끝