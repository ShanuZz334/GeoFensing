import re

with open("admin/alerts.html", "r", encoding="utf-8") as f:
    html = f.read()

# Add a tabs toggle right after the header
header_pattern = r'</header>\s*<div class="table-wrapper">'
tabs_html = '''</header>

    <div style="display: flex; gap: 16px; margin-bottom: 24px; border-bottom: 1px solid var(--border);">
      <button id="tab-alerts" onclick="switchTab('alerts')" style="padding: 12px 16px; background: transparent; border: none; border-bottom: 2px solid var(--primary); color: var(--text); font-weight: 600; cursor: pointer; transition: all 0.2s;">Security Alerts</button>
      <button id="tab-leaves" onclick="switchTab('leaves')" style="padding: 12px 16px; background: transparent; border: none; border-bottom: 2px solid transparent; color: var(--text-muted); font-weight: 500; cursor: pointer; transition: all 0.2s;">Leave Requests</button>
    </div>

    <!-- Security Alerts Table -->
    <div id="section-alerts" class="table-wrapper">'''
html = re.sub(header_pattern, tabs_html, html, flags=re.DOTALL, count=1)

# Add Leave Requests Table right after the alerts table wrapper
table_end_pattern = r'</table>\s*</div>\s*</main>'
leaves_table_html = '''</table>
    </div>

    <!-- Leave Requests Table -->
    <div id="section-leaves" class="table-wrapper" style="display: none;">
      <table class="data-table" id="leaves-table">
        <thead>
          <tr>
            <th>Applied At</th>
            <th>Teacher</th>
            <th>Type</th>
            <th>Dates</th>
            <th>Reason</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody id="leaves-tbody">
          <tr><td colspan="6" style="text-align: center; padding: 30px; color: var(--text-muted);">Loading leave requests...</td></tr>
        </tbody>
      </table>
    </div>
  </main>'''
html = re.sub(table_end_pattern, leaves_table_html, html, flags=re.DOTALL, count=1)

# Add JavaScript to handle tabs and leave requests
js_addition = '''
    // Tab Switching
    function switchTab(tabId) {
      if (tabId === 'alerts') {
        document.getElementById('tab-alerts').style.borderColor = 'var(--primary)';
        document.getElementById('tab-alerts').style.color = 'var(--text)';
        document.getElementById('tab-alerts').style.fontWeight = '600';
        
        document.getElementById('tab-leaves').style.borderColor = 'transparent';
        document.getElementById('tab-leaves').style.color = 'var(--text-muted)';
        document.getElementById('tab-leaves').style.fontWeight = '500';
        
        document.getElementById('section-alerts').style.display = 'block';
        document.getElementById('section-leaves').style.display = 'none';
        
        loadAlerts();
      } else {
        document.getElementById('tab-leaves').style.borderColor = 'var(--primary)';
        document.getElementById('tab-leaves').style.color = 'var(--text)';
        document.getElementById('tab-leaves').style.fontWeight = '600';
        
        document.getElementById('tab-alerts').style.borderColor = 'transparent';
        document.getElementById('tab-alerts').style.color = 'var(--text-muted)';
        document.getElementById('tab-alerts').style.fontWeight = '500';
        
        document.getElementById('section-leaves').style.display = 'block';
        document.getElementById('section-alerts').style.display = 'none';
        
        loadLeaves();
      }
    }

    // Load Leave Requests
    async function loadLeaves() {
      const tbody = document.getElementById('leaves-tbody');
      tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 30px; color: var(--text-muted);">Loading...</td></tr>';
      
      try {
        const res = await apiFetch('/admin/leaves?status=pending');
        if (!res.ok) throw new Error('Failed to load leaves');
        const data = await res.json();
        
        if (!data.leaves || data.leaves.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: var(--text-muted);">No pending leave requests.</td></tr>';
          return;
        }
        
        tbody.innerHTML = '';
        data.leaves.forEach(leave => {
          const appliedDate = new Date(leave.applied_at).toLocaleString();
          const start = new Date(leave.start_date).toLocaleDateString();
          const end = new Date(leave.end_date).toLocaleDateString();
          const dateStr = start === end ? start : `${start} to ${end}`;
          
          const typeLabel = leave.leave_type === 'emergency' 
            ? '<span style="color:#ef4444; background:rgba(239,68,68,0.1); padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600;">Emergency</span>'
            : '<span style="color:#3b82f6; background:rgba(59,130,246,0.1); padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600;">Normal</span>';
            
          const dayTypeLabel = leave.is_half_day 
            ? '<span style="color:#f59e0b; background:rgba(245,158,11,0.1); padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600; margin-left:4px;">Half Day</span>'
            : '<span style="color:#10b981; background:rgba(16,185,129,0.1); padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600; margin-left:4px;">Full Day</span>';
            
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td><div class="timestamp-code">${appliedDate}</div></td>
            <td>
              <div style="font-weight:600; color:var(--text);">${leave.teacher_name}</div>
              <div class="reg-id-code" style="margin-top:4px; display:inline-block;">${leave.teacher_reg_no}</div>
            </td>
            <td>${typeLabel}${dayTypeLabel}</td>
            <td><div style="font-weight:500;">${dateStr}</div></td>
            <td><div style="font-size:13px; color:var(--text-muted); max-width:200px; white-space:normal;">${leave.reason || '-'}</div></td>
            <td>
              <div class="alert-actions">
                <button class="btn-resolve primary" onclick="updateLeaveStatus('${leave.id}', 'approved')">Approve</button>
                <button class="btn-resolve danger" onclick="updateLeaveStatus('${leave.id}', 'rejected')">Reject</button>
              </div>
            </td>
          `;
          tbody.appendChild(tr);
        });
        
      } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 30px; color: #ef4444;">Error: ${err.message}</td></tr>`;
      }
    }

    async function updateLeaveStatus(id, status) {
      if (!confirm(`Are you sure you want to ${status} this leave request?`)) return;
      try {
        const res = await apiFetch(`/admin/leaves/${id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ status })
        });
        const data = await res.json();
        if (res.ok) {
          alert(`Leave request ${status} successfully.`);
          loadLeaves();
        } else {
          alert(data.error || 'Failed to update leave request');
        }
      } catch (err) {
        alert('Error: ' + err.message);
      }
    }
</script>'''

html = html.replace('</script>', js_addition, 1)

with open("admin/alerts.html", "w", encoding="utf-8") as f:
    f.write(html)
