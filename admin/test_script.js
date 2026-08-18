
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
      const emergencyTbody = document.getElementById('emergency-leaves-tbody');
      const normalTbody = document.getElementById('normal-leaves-tbody');
      
      emergencyTbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 30px; color: var(--text-muted);">Loading...</td></tr>';
      normalTbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 30px; color: var(--text-muted);">Loading...</td></tr>';
      
      try {
        const data = await api('/admin/leaves?status=pending');
        if (!data) return;
        
        emergencyTbody.innerHTML = '';
        normalTbody.innerHTML = '';
        
        const leaves = data.leaves || [];
        const emergencyLeaves = leaves.filter(l => l.leave_type === 'emergency');
        const normalLeaves = leaves.filter(l => l.leave_type === 'normal');

        if (emergencyLeaves.length === 0) {
          emergencyTbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: var(--text-muted);">No pending emergency leave requests.</td></tr>';
        }
        
        if (normalLeaves.length === 0) {
          normalTbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px; color: var(--text-muted);">No pending normal leave requests.</td></tr>';
        }
        
        function createLeaveRow(leave) {
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
              <div style="margin-top:6px; font-size:12px; color:var(--text-muted); display:flex; gap:12px;">
                <span title="Approved leaves taken this month"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-2px; margin-right:4px;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>${leave.leaves_this_month || 0} taken</span>
                <span title="Current deduction percentage" style="${leave.current_cut_percent > 0 ? 'color:#ef4444' : ''}"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-2px; margin-right:4px;"><line x1="19" y1="5" x2="5" y2="19"></line><circle cx="6.5" cy="6.5" r="2.5"></circle><circle cx="17.5" cy="17.5" r="2.5"></circle></svg>${leave.current_cut_percent || 0}% cut</span>
              </div>
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
          return tr;
        }

        emergencyLeaves.forEach(leave => {
          emergencyTbody.appendChild(createLeaveRow(leave));
        });
        
        normalLeaves.forEach(leave => {
          normalTbody.appendChild(createLeaveRow(leave));
        });
        
      } catch (err) {
        emergencyTbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 30px; color: #ef4444;">Error: ${err.message}</td></tr>`;
        normalTbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 30px; color: #ef4444;">Error: ${err.message}</td></tr>`;
      }
    }

    async function updateLeaveStatus(id, status) {
      if (!confirm(`Are you sure you want to ${status} this leave request?`)) return;
      try {
        const res = await api(`/admin/leaves/${id}`, {
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
