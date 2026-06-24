// ====================================================================
// 🌐 1. Global State
// ====================================================================
let rawData = {};
let codeBook = {};
let sheetData = {};
let currentFrequencies = [];
let currentColumnName = null;

// Cache DOM Elements for better performance
let frequenciesTableBody;
let responsesTableHeader
let responsesTableBody;
let top10ChartContainer;
let codeSearchInput;
let responsesSearchInput;
let ResponsesShowEmptyToggle;
let columnSelect;

// ====================================================================
// 2. Entry Point
// ====================================================================
document.addEventListener('DOMContentLoaded', function () {

    // Initialize DOM references
    frequenciesTableBody = document.getElementById('frequenciesTableBody');
    responsesTableHeader = document.getElementById('responsesTableHeader');
    responsesTableBody = document.getElementById('responsesTableBody');
    top10ChartContainer = document.getElementById('top10ChartContainer');
    codeSearchInput = document.getElementById('codeSearchInput');
    responsesSearchInput = document.getElementById('responsesSearchInput');
    ResponsesShowEmptyToggle = document.getElementById('showEmptyToggle');
    columnSelect = document.getElementById('columnSelect');

    // Focus Mode Toggle Logic
    const btnCodeList = document.getElementById('CodeListfullscreenToggleBtn');
    const cardList = document.querySelector('.full-codebook-box');
    const btnResponsesList = document.getElementById('ResponsesListfullscreenToggleBtn');
    const cardResponsesList = document.querySelector('.responses-section');
    const overlay = document.getElementById('focusOverlay');

    if (btnCodeList && cardList && overlay) {
        const icon = btnCodeList.querySelector('i');

        function toggleCodeFocus() {
            const isActive = cardList.classList.toggle('is-focus');
            overlay.classList.toggle('active', isActive);
            if (icon) {
                icon.classList.toggle('fa-expand', !isActive);
                icon.classList.toggle('fa-compress', isActive);
            }
        }
        btnCodeList.addEventListener('click', toggleCodeFocus);
    }

    if (btnResponsesList && cardResponsesList && overlay) {
        const icon = btnResponsesList.querySelector('i');

        function toggleResponsesFocus() {
            const isActive = cardResponsesList.classList.toggle('is-focus');
            overlay.classList.toggle('active', isActive);
            if (icon) {
                icon.classList.toggle('fa-expand', !isActive);
                icon.classList.toggle('fa-compress', isActive);
            }
        }
        btnResponsesList.addEventListener('click', toggleResponsesFocus);
    }

    if (overlay) {
        overlay.addEventListener('click', function () {
            // إغلاق كارت الأكواد لو مفتوح
            if (cardList && cardList.classList.contains('is-focus')) {
                btnCodeList.click();
            }
            if (cardResponsesList && cardResponsesList.classList.contains('is-focus')) {
                btnResponsesList.click();
            }
        });
    }

    // Get the initial data from the global variable injected by Django template
    rawData = window.projectAnalysisData || {};
    codeBook = rawData.CodeBook || {};
    sheetData = rawData.sheet_Data || {};

    // First column to display by default
    if (columnSelect) {
        currentColumnName = columnSelect.value;

        columnSelect.addEventListener('change', function () {
            currentColumnName = this.value;
            renderColumnData(currentColumnName);
        });
    }

    // Initial rendering of the page with the first column's data
    setupPageEvents();
    renderColumnData(currentColumnName);
});

// ====================================================================
// ⚡ 3. Setup Events (Inline Editing & Search)
// ====================================================================
function setupPageEvents() {

    // 
    if (frequenciesTableBody) {
        frequenciesTableBody.addEventListener('blur', function (e) {
            if (e.target.classList.contains('editable-code-name')) {
                const codeId = e.target.getAttribute('data-code-id');
                const newText = e.target.textContent.trim();

                if (!newText) {
                    showAlert('Code text cannot be empty.', "error");
                    e.target.textContent = codeBook[codeId] || '';
                    return;
                }

                if (codeBook[codeId] === newText) return;

                const jobId = window.currentJobId || "";

                fetch('/jobs/update-codebook/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie("csrftoken"),
                    },
                    body: JSON.stringify({
                        job_id: jobId,
                        action: 'update',
                        code_id: codeId,
                        new_text: newText
                    })
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            showAlert('Code updated successfully!', "success");

                            //  Update the local state with the fresh data from the backend to ensure consistency
                            codeBook = data.new_codebook || codeBook;
                            if (data.new_sheet_data) sheetData = data.new_sheet_data;

                            // Re-render the current column to reflect the updated code label
                            renderColumnData(currentColumnName);
                        } else {
                            showAlert('Error updating: ' + data.message, "error");
                            e.target.textContent = codeBook[codeId] || '';
                        }
                    })
                    .catch(error => {
                        console.error('Fetch Error:', error);
                        e.target.textContent = codeBook[codeId] || '';
                    });
            }
        }, true);

        frequenciesTableBody.addEventListener('keydown', function (e) {
            if (e.target.classList.contains('editable-code-name') && e.key === 'Enter') {
                e.preventDefault();
                e.target.blur();
            }
        });
    }

    // Search functionality for the full codebook table
    if (codeSearchInput) {
        codeSearchInput.addEventListener('input', function () {
            const searchText = this.value.toLowerCase().trim();
            const filtered = currentFrequencies.filter(f =>
                f.label.toLowerCase().includes(searchText)
            );
            renderFullCodebookTable(filtered);
        });
    }

    // Search functionality for the responses table (both Full View and Single Column)
    if (responsesSearchInput) {
        responsesSearchInput.addEventListener('input', applyResponsesFilter);
    }

    // الـ checkbox
    if (ResponsesShowEmptyToggle) {
        ResponsesShowEmptyToggle.addEventListener('change', applyResponsesFilter);
    }


}

// ====================================================================
// 🔄 4. Core Calculation Logic
// ====================================================================
function renderColumnData(columnName) {
    if (!columnName) return;

    let entries = [];
    let isFullView = (columnName === 'fullView');

    if (isFullView) {
        Object.keys(sheetData).forEach(col => {
            entries = entries.concat(sheetData[col] || []);
        });
    } else {
        entries = sheetData[columnName] || [];
    }

    let allFinalIds = [];
    entries.forEach(entry => {
        const finalIdsStr = entry['Final IDs'] || '';
        if (finalIdsStr) {
            const ids = finalIdsStr.toString().split(',').map(x => x.trim()).filter(Boolean);
            allFinalIds = allFinalIds.concat(ids);
        }
    });

    const totalAssignedCodes = allFinalIds.length;

    currentFrequencies = [];
    for (const [codeId, codeLabel] of Object.entries(codeBook)) {
        const count = allFinalIds.filter(id => id === codeId).length;
        const percentage = totalAssignedCodes > 0 ? Math.round((count / totalAssignedCodes) * 100) : 0;

        currentFrequencies.push({
            id: codeId,
            label: codeLabel,
            count: count,
            percentage: percentage
        });
    }

    currentFrequencies.sort((a, b) => b.count - a.count);

    renderTop10Chart(currentFrequencies.slice(0, 10));

    if (codeSearchInput) codeSearchInput.value = '';

    renderFullCodebookTable(currentFrequencies);

    if (isFullView) {
        renderResponsesTable(sheetData, true);
    } else {
        renderResponsesTable(entries, false);
    }
}

// ====================================================================
// 🎨 5. Render Functions
// ====================================================================
function renderTop10Chart(top10Data) {
    if (top10Data.length === 0) {
        top10ChartContainer.innerHTML = `<p class="empty-tag text-center py-4">Empty</p>`;
        return;
    }

    const activeTop10 = top10Data.filter(f => f.count > 0);
    if (activeTop10.length === 0) {
        top10ChartContainer.innerHTML = `<p class="empty-tag text-center py-4">Empty</p>`;
        return;
    }

    top10ChartContainer.innerHTML = activeTop10.map(f => `
        <div class="chart-row">
            <div class="chart-label" data-chart-code-id="${f.id}">${f.label}</div>
            <div class="chart-bar-wrapper">
                <div class="chart-bar-fill" style="width: ${f.percentage}%"></div>
                <div class="chart-count">${f.count} records (${f.percentage}%)</div>
            </div>
        </div>
    `).join('');
}

function renderFullCodebookTable(frequenciesData) {
    if (!frequenciesTableBody) return;
    if (frequenciesData.length === 0) {
        frequenciesTableBody.innerHTML = `<tr><td colspan="4" class="text-center empty-tag">Empty</td></tr>`;
        return;
    }

    frequenciesTableBody.innerHTML = frequenciesData.map(f => `
        <tr>
            <td>
                <span class="editable-code-name" 
                    data-code-id="${f.id}" 
                    contenteditable="true" 
                    spellcheck="false"
                    style="font-weight: 600; display: inline-block; width: 100%; min-width: 150px;">
                    ${f.label}
                </span>
            </td>
            <td class="text-center">
                <span style="background: #1A0F2E; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: 700; color: #C4B5D9;">
                    ${f.count}
                </span>
            </td>
            <td>
                <div class="progress-container">
                    <span class="progress-num">${f.percentage}%</span>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" style="width: ${f.percentage}%"></div>
                    </div>
                </div>
            </td>
            <td class="text-center" style="width: 100px;">
                <div style="display: flex; gap: 8px; justify-content: center; align-items: center;">
                    <button class="btn-merge-action" 
                            title="Merge this code into another" 
                            onclick="CodeBook_triggerMergeCode('${f.id}', '${f.label}')"
                            style="background: transparent; border: 1px solid #7B2CBF; color: #C4B5D9; padding: 5px 8px; border-radius: 6px; cursor: pointer; font-size: 0.85rem; transition: all 0.2s;">
                        <i class="fa-solid fa-code-merge"></i>
                    </button>
                    <button class="btn-delete-action" 
                            title="Delete this code completely" 
                            onclick="CodeBook_triggerDeleteCode('${f.id}')"
                            style="background: transparent; border: 1px solid #E63946; color: #E63946; padding: 5px 8px; border-radius: 6px; cursor: pointer; font-size: 0.85rem; transition: all 0.2s;">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function renderResponsesTable(data, isFullView = false) {
    if (!responsesTableBody) return;

    // 1️⃣ حالة إن الداتا فاضية أو مش موجودة
    if (!data || (isFullView ? Object.keys(data).length === 0 : data.length === 0)) {
        // الـ colspan بيبقى 3 في العرض العادي، وبيزيد ديناميكياً في الـ Full View حسب عدد الأعمدة
        const totalCols = isFullView ? (Object.keys(data).length * 2) + 1 : 3;
        responsesTableBody.innerHTML = `<tr><td colspan="${totalCols}" class="text-center empty-tag">Empty</td></tr>`;
        return;
    }

    let rowsHTML = '';

    if (isFullView) {
        // ==========================================
        // 🔹 وضع الـ Full View (أعمدة ديناميكية متعددة)
        // ==========================================
        const columns = Object.keys(data);

        // بناء الـ Header ديناميكياً بأسماء الأعمدة الحقيقية
        if (responsesTableHeader) {
            let headerHTML = '<tr><th style="width: 50px;">#</th>'; // عمود الـ Index
            columns.forEach((colName, index) => {
                const borderClass = index > 0 ? 'class="border-left-sep"' : '';
                headerHTML += `
                    <th ${borderClass}>${colName}</th>
                    <th style="width: 200px;">Codes (${colName})</th>
                `;
            });
            headerHTML += '</tr>';
            responsesTableHeader.innerHTML = headerHTML;
        }

        // حساب أطول عمود عشان الـ Loop
        const maxLength = Math.max(...columns.map(col => (data[col] || []).length));

        // بناء الـ Rows
        for (let i = 0; i < maxLength; i++) {
            rowsHTML += `<tr>`;
            // إضافة عمود الـ Index بنفس الستايل بتاعك
            rowsHTML += `<td class="text-center" style="font-weight: 700; color: #94a3b8;">${i + 1}</td>`;

            columns.forEach((colName, index) => {
                
                const colData = data[colName] || [];
                const entry = colData[i] || { Text: '', 'Final IDs': '' };
                const recordId = entry['id'];
                const borderClass = index > 0 ? 'border-left-sep' : '';

                const originalText = entry['Text'] || '';
                const finalIdsStr = entry['Final IDs'] || '';

                // بناء الـ Badges بنفس اللوجيك والكلاسات بتاعتك
                let badgesHtml = '';

                if (finalIdsStr) {
                    const ids = finalIdsStr.toString().split(',').map(x => x.trim()).filter(Boolean);
                    
                    badgesHtml = ids.map(id => {
                        const currentLabel = codeBook[id] || `Code ${id}`;
                        return ResponseTable_buildBadgeHTML(id, currentLabel, recordId, colName);
                    }).join('');
                } else {
                    badgesHtml = `<span class="empty-tag">Empty</span>`;
                }
                badgesHtml += ResponseTable_buildAddBtnHTML(recordId, colName);

                // حقن الخلايا مع الحفاظ على الكلاسات بتاعتك
                rowsHTML += `
                    <td class="${borderClass}"><p class="arabic-text">${originalText || '<span class="empty-tag">-</span>'}</p></td>
                    <td><div class="badges-container">${badgesHtml}</div></td>
                `;
            });

            rowsHTML += `</tr>`;
        }
    }
    else {
        // ==========================================
        // 🔹 الوضع العادي بتاعك بالظبط (Single Column)
        // ==========================================
        if (responsesTableHeader) {
            responsesTableHeader.innerHTML = `
                <tr>
                    <th style="width: 50px;">#</th>
                    <th>Response Text</th>
                    <th style="width: 200px;">Codes</th>
                </tr>
            `;
        }

        // الكود بتاعك القديم زي ما هو بالظبط بدون أي تعديل في الـ DOM structure
        rowsHTML = data.map((entry, index) => {
            const recordId = entry['id'];
            const originalText = entry['Text'] || '';
            const finalIdsStr = entry['Final IDs'] || '';

            let badgesHtml = '';
            if (finalIdsStr) {
                const ids = finalIdsStr.toString().split(',').map(x => x.trim()).filter(Boolean);
                badgesHtml = ids.map(id => {
                    const currentLabel = codeBook[id] || `Code ${id}`;
                    return ResponseTable_buildBadgeHTML(id, currentLabel, recordId, null);
                }).join('');
            } else {
                badgesHtml = `<span class="empty-tag">Empty</span>`;
            }
            badgesHtml += ResponseTable_buildAddBtnHTML(recordId, null);

            return `
                <tr>
                    <td class="text-center" style="font-weight: 700; color: #94a3b8;">${index + 1}</td>
                    <td><p class="arabic-text">${originalText}</p></td>
                    <td><div class="badges-container">${badgesHtml}</div></td>
                </tr>
            `;
        }).join('');
    }

    responsesTableBody.innerHTML = rowsHTML;
}

function updateDashboardCounters(totalCodes, avgCodes) {
    const totalCodesCard = document.getElementById('totalCodesCounter');
    const avgCodesCard = document.getElementById('avgCodesCounter');

    if (totalCodesCard && totalCodes !== undefined) {
        totalCodesCard.textContent = totalCodes;
    }
    if (avgCodesCard && avgCodes !== undefined) {
        avgCodesCard.textContent = avgCodes;
    }
}

function applyResponsesFilter() {
    const searchText  = responsesSearchInput?.value.toLowerCase().trim() || '';
    const showEmpty   = document.getElementById('showEmptyToggle')?.checked;
    const isFullView  = currentColumnName === 'fullView';

    if (isFullView) {
        const columns   = Object.keys(sheetData);
        const maxLength = Math.max(...columns.map(col => (sheetData[col] || []).length));

        let filteredSheetData = {};
        columns.forEach(col => { filteredSheetData[col] = []; });

        for (let i = 0; i < maxLength; i++) {
            let matchFound = false;

            for (let colName of columns) {
                const entry = sheetData[colName]?.[i];
                if (entry) {
                    const finalIdsStr = (entry['Final IDs'] || '').toString().trim();
                    const ids = finalIdsStr.split(',').map(x => x.trim()).filter(Boolean);

                    // فلتر الفاضية
                    if (showEmpty) {
                        if (finalIdsStr === '' || finalIdsStr === 'nan' || ids.length === 0) {
                            matchFound = true; break;
                        }
                        continue;
                    }

                    // فلتر الـ search
                    if (searchText) {
                        const hasMatchingLabel = ids.some(id => (codeBook[id] || '').toLowerCase().includes(searchText));
                        if (finalIdsStr.toLowerCase().includes(searchText) || hasMatchingLabel) {
                            matchFound = true; break;
                        }
                        continue;
                    }

                    // لو مفيش فلتر — اعرض الكل
                    matchFound = true; break;
                }
            }

            if (matchFound) {
                columns.forEach(colName => {
                    filteredSheetData[colName].push(sheetData[colName]?.[i] || { Text: '', 'Final IDs': '' });
                });
            }
        }

        renderResponsesTable(filteredSheetData, true);

    } else {
        let filtered = [...(sheetData[currentColumnName] || [])];

        // فلتر الفاضية
        if (showEmpty) {
            filtered = filtered.filter(entry => {
                const ids = (entry['Final IDs'] || '').toString().trim();
                return ids === '' || ids === 'nan' || ids.split(',').filter(x => x.trim()).length === 0;
            });
        }

        // فلتر الـ search
        if (searchText && !showEmpty) {
            filtered = filtered.filter(entry => {
                const finalIdsStr = (entry['Final IDs'] || '').toString().toLowerCase();
                const ids = finalIdsStr.split(',').map(x => x.trim()).filter(Boolean);
                const hasMatchingLabel = ids.some(id => (codeBook[id] || '').toLowerCase().includes(searchText));
                return finalIdsStr.includes(searchText) || hasMatchingLabel;
            });
        }

        renderResponsesTable(filtered, false);
    }
}

// ====================================================================
// 6. Backend-Driven Actions (Delete & Merge)
// ====================================================================
async function CodeBook_triggerAddNewCode() {
    newCodeText = await promptWindow('Add New Code', 'Enter the new code name...');
    if (!newCodeText) return;

    fetch('/jobs/update-codebook/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            job_id:   window.currentJobId,
            action:   'add_code',
            new_text: newCodeText.trim()
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            codeBook  = data.new_codebook;
            sheetData = data.new_sheet_data;
            updateDashboardCounters(data.current_codes_count, data.new_avg_codes);
            renderColumnData(currentColumnName);
            showAlert(`Code "${newCodeText}" added successfully!`, 'success');
        } else {
            showAlert('Error: ' + data.message, 'error');
        }
    });
}

async function CodeBook_triggerDeleteCode(codeId) {
    if (!await confirmWindow(`Are you sure you want to delete Code [${codeBook[codeId]}]? This will remove it from all sheets and verbatims. This action cannot be undone.`)) {
        return;
    }

    const jobId = window.currentJobId || "";

    fetch('/jobs/update-codebook/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie("csrftoken"),
        },
        body: JSON.stringify({
            job_id: jobId,
            action: 'delete',
            code_id: codeId
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showAlert(`Code deleted successfully!`, "success");

                // 🔄 تحديث الـ State ببيانات الباك-إند الفريش فوراً
                codeBook = data.new_codebook || codeBook;
                sheetData = data.new_sheet_data || sheetData;

                // تحديث عداد الكود بوك في الكارت العلوي لو موجود
                const totalCodesCard = document.getElementById('totalCodesCounter');
                if (totalCodesCard && data.current_codes_count !== undefined) {
                    totalCodesCard.textContent = data.current_codes_count;
                }

                updateDashboardCounters(data.current_codes_count, data.new_avg_codes);
                // إعادة الحسابات والرندرة اللحظية
                renderColumnData(currentColumnName);
            } else {
                showAlert('Error deleting code: ' + data.message, "error");
            }
        })
        .catch(error => console.error('Delete Fetch Error:', error));
}

async function CodeBook_triggerMergeCode(sourceId, sourceLabel) {
    const availableOptions = {};
    for (const [id, label] of Object.entries(codeBook)) {
        if (id !== sourceId) {
            availableOptions[id] = `[#${id}] ${label}`;
        }
    }

    // 2. استدعاء الـ Dropdown الـ ذكي بتاع Swal
    const targetId = await Select_DropdownWindow(
        `Merge: "${sourceLabel}" into...`,
        availableOptions
    );

    if (!targetId) return;

    const cleanTargetId = targetId.trim();

    if (!codeBook[cleanTargetId]) {
        showAlert(`Target Code ID [${cleanTargetId}] does not exist in the current CodeBook.`, "error");
        return;
    }

    if (!await confirmWindow(`Are you sure you want to merge all data from Code [${sourceLabel}] into Code [${codeBook[cleanTargetId]}]?\n\nCode [${sourceLabel}] will be permanently deleted.`)) {
        return;
    }

    const jobId = window.currentJobId || "";

    fetch('/jobs/update-codebook/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie("csrftoken"),
        },
        body: JSON.stringify({
            job_id: jobId,
            action: 'merge',
            source_code_id: sourceId,
            target_code_id: cleanTargetId
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {

                codeBook = data.new_codebook || codeBook;
                sheetData = data.new_sheet_data || sheetData;

                updateDashboardCounters(data.current_codes_count, data.new_avg_codes);
                renderColumnData(currentColumnName);
                showAlert(`Merged successfully!`, "success");
            } else {
                showAlert('Error merging codes: ' + data.message, "error");
            }
        })
        .catch(error => console.error('Merge Fetch Error:', error));
}

async function ResponseTable_triggerRemoveCode(btn, codeId, record_id, colName) {
    if (!await confirmWindow(`Remove code "${codeBook[codeId]}" from this response?`)) return;
    // backend call
    fetch('/jobs/update-dataset/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            job_id:     window.currentJobId,
            action:     'remove',
            column:     colName,
            record_id:  record_id,
            code_id:    codeId
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            sheetData = data.new_sheet_data;
            codeBook  = data.new_codebook;
            renderColumnData(currentColumnName);
            showAlert('Code removed successfully!', 'success');
        } else {
            showAlert('Error: ' + data.message, 'error');
        }
    });
}

async function ResponseTable_triggerReplaceCode(btn, codeId, record_id, colName) {
    const options = {};
    for (const [id, label] of Object.entries(codeBook)) {
        if (id !== codeId) options[id] = `[#${id}] ${label}`;
    }

    const newCodeId = await Select_DropdownWindow(
        `Replace "${codeBook[codeId]}" with...`,
        options
    );
    if (!newCodeId) return;

    fetch('/jobs/update-dataset/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            job_id:      window.currentJobId,
            action:      'replace',
            column:      colName,
            record_id:   record_id,
            old_code_id: codeId,
            new_code_id: newCodeId
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            sheetData = data.new_sheet_data;
            codeBook  = data.new_codebook;
            renderColumnData(currentColumnName);
            showAlert('Code replaced successfully!', 'success');
        } else {
            showAlert('Error: ' + data.message, 'error');
        }
    });
}

async function ResponseTable_triggerAddCode(btn, record_id, colName) {
    const options = {};
    for (const [id, label] of Object.entries(codeBook)) {
        options[id] = `[#${id}] ${label}`;
    }

    const newCodeId = await Select_DropdownWindow(
        `Select a code...`,
        options
    );
    if (!newCodeId) return;

    fetch('/jobs/update-dataset/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            job_id:    window.currentJobId,
            action:    'add',
            column:    colName,
            record_id: record_id,
            code_id:   newCodeId
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            sheetData = data.new_sheet_data;
            codeBook  = data.new_codebook;
            renderColumnData(currentColumnName);
            showAlert('Code added successfully!', 'success');
        } else {
            showAlert('Error: ' + data.message, 'error');
        }
    });
}

// ====================================================================
// Helper Functions for Modals
// ====================================================================

function ResponseTable_buildBadgeHTML(id, label, recordId, colName) {
    const col = colName ? `'${colName}'` : `currentColumnName`;
    return `
        <span class="custom-tag response-badge" data-badge-code-id="${id}">
            ${label}
            <button class="badge-replace-btn" title="Replace"
                onclick="ResponseTable_triggerReplaceCode(this, '${id}', ${recordId}, ${col})">✎</button>
            <button class="badge-remove-btn" title="Remove"
                onclick="ResponseTable_triggerRemoveCode(this, '${id}', ${recordId}, ${col})">✕</button>
        </span>
    `;
}

function ResponseTable_buildAddBtnHTML(recordId, colName) {
    const col = colName ? `'${colName}'` : `currentColumnName`;
    return `<button class="response-add-btn" onclick="ResponseTable_triggerAddCode(this, ${recordId}, ${col})">+ Add</button>`;
}


// ====================================================================
// 🍪 7. Utils
// ====================================================================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}