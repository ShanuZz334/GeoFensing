let filterTimeout;

function applyFilters() { loadLeaves(); }
function debounceApplyFilters() {
    clearTimeout(filterTimeout);
    filterTimeout = setTimeout(applyFilters, 300);
}

function resetFilters() {
    setUiverseSelectValue('filter-status', 'all');
    setUiverseSelectValue('filter-type', 'all');
    document.getElementById('filter-reg-no').value = '';
    applyFilters();
}

async function loadLeaves() {
    const status = getUiverseSelectValue('filter-status');
    const type = getUiverseSelectValue('filter-type');
    const regNo = document.getElementById('filter-reg-no').value.trim();

    const params = new URLSearchParams();
    if (status && status !== 'all') params.set('status', status);
    if (type && type !== 'all') params.set('type', type);
    if (regNo) params.set('reg_no', regNo);

    const response = await api(`/admin/leaves?${params}`);
    if (!response) return;

    const data = response.leaves || [];
    
    const tbody = document.getElementById('leaves-tbody');
    if (!data.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="td-loading">No leave applications found</td></tr>';
        return;
    }

    tbody.innerHTML = data.map(leave => {
        // Faculty column
        const avatarUrl = leave.teacher_profile_pic ? 
            (leave.teacher_profile_pic.startsWith('data:') ? leave.teacher_profile_pic : 'data:image/jpeg;base64,' + leave.teacher_profile_pic) 
            : 'images/default-avatar.svg';
            
        const nameDisplay = `
            <div style="display:flex; align-items:center; gap:10px;">
                <img src="${avatarUrl}" alt="${escHtml(leave.teacher_name || 'Faculty')}" style="width:28px; height:28px; border-radius:50%; object-fit:cover; background:var(--surface-2); border:1px solid rgba(124, 58, 237, 0.2);" onerror="this.src='images/default-avatar.svg'" />
                <div style="display:flex; flex-direction:column; gap:1px;">
                    <strong>${escHtml(leave.teacher_name || 'Unknown')}</strong>
                </div>
            </div>
        `;

        // Leave Dates
        const startDate = formatDt(leave.start_date, true);
        const endDate = formatDt(leave.end_date, true);
        const dateDisplay = startDate === endDate ? startDate : `${startDate} - ${endDate}`;

        // Status Badge
        let statusBadge;
        if (leave.status === 'approved') {
            statusBadge = `<span class="badge badge--success">Approved</span>`;
        } else if (leave.status === 'rejected') {
            statusBadge = `<span class="badge badge--error">Rejected</span>`;
        } else {
            statusBadge = `<span class="badge badge--warning">Pending</span>`;
        }
        
        // Type Badge
        let typeBadge = leave.leave_type === 'emergency' 
            ? `<span class="badge badge--error">Emergency${leave.is_half_day ? ' (Half)' : ''}</span>`
            : `<span class="badge badge--check_in">Normal${leave.is_half_day ? ' (Half)' : ''}</span>`;

        return `
        <tr class="log-row">
            <td>${nameDisplay}</td>
            <td style="color:var(--text-muted);font-weight:500">${escHtml(leave.teacher_reg_no || 'N/A')}</td>
            <td style="font-weight: 500;">${dateDisplay}</td>
            <td>${typeBadge}</td>
            <td class="reason-cell" style="color:var(--text-muted)">${escHtml(leave.reason)}</td>
            <td>${statusBadge}</td>
            <td style="color: var(--text-muted); font-size: 12px;">${formatDt(leave.applied_at)}</td>
        </tr>
        `;
    }).join('');
}

initApp('leaves', loadLeaves);
