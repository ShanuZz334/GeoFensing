import sys

code = """
// ── FACULTY AUTOCOMPLETE FOR EVENT CHECKPOINTS ──
let selectedFacultyPills = [];

window.handleTeacherInput = async function(val) {
  const dropdown = document.getElementById('cp-teacher-dropdown');
  if (val.length < 2) {
    dropdown.style.display = 'none';
    return;
  }
  
  try {
    const res = await api('/admin/teachers?search=' + encodeURIComponent(val) + '&per_page=10');
    if (!res || !res.teachers || res.teachers.length === 0) {
      dropdown.innerHTML = '<div style="padding:8px 12px; color:var(--text-muted); font-size:13px;">No faculty found</div>';
      dropdown.style.display = 'block';
      return;
    }
    
    dropdown.innerHTML = '';
    res.teachers.forEach(t => {
      // Don't show if already selected
      if (selectedFacultyPills.find(p => p.reg_no === t.reg_no)) return;
      
      const item = document.createElement('div');
      item.className = 'multi-select-item';
      item.style.cssText = 'padding:8px 12px; cursor:pointer; font-size:13px; color:var(--text); border-bottom:1px solid rgba(255,255,255,0.05);';
      item.innerHTML = `<strong>${t.reg_no}</strong> - ${t.full_name}`;
      item.onclick = () => addTeacherPill(t.reg_no, t.full_name);
      
      item.onmouseenter = () => item.style.background = 'rgba(255,255,255,0.1)';
      item.onmouseleave = () => item.style.background = 'transparent';
      
      dropdown.appendChild(item);
    });
    
    dropdown.style.display = dropdown.children.length > 0 ? 'block' : 'none';
  } catch (e) {
    console.error('Search failed', e);
  }
};

window.addTeacherPill = function(regNo, name) {
  if (!selectedFacultyPills.find(p => p.reg_no === regNo)) {
    selectedFacultyPills.push({reg_no: regNo, name: name});
  }
  document.getElementById('cp-teacher-input').value = '';
  document.getElementById('cp-teacher-dropdown').style.display = 'none';
  renderTeacherPills();
};

window.removeTeacherPill = function(regNo) {
  selectedFacultyPills = selectedFacultyPills.filter(p => p.reg_no !== regNo);
  renderTeacherPills();
};

function renderTeacherPills() {
  const container = document.getElementById('cp-teacher-pills');
  container.innerHTML = '';
  
  selectedFacultyPills.forEach(p => {
    const pill = document.createElement('div');
    pill.style.cssText = 'background:rgba(124, 58, 237, 0.2); color:#c084fc; border:1px solid rgba(124, 58, 237, 0.4); border-radius:16px; padding:2px 8px; font-size:12px; display:flex; align-items:center; gap:6px;';
    pill.innerHTML = `
      <span>${p.reg_no}</span>
      <button style="background:none;border:none;color:#c084fc;cursor:pointer;padding:0;font-size:14px;line-height:1;" onclick="removeTeacherPill('${p.reg_no}')">&times;</button>
    `;
    container.appendChild(pill);
  });
  
  document.getElementById('cp-teacher-value').value = selectedFacultyPills.map(p => p.reg_no).join(',');
}

// Reset pills when opening modal
const originalStartPlacing = window.startPlacingEventCp;
window.startPlacingEventCp = function() {
  selectedFacultyPills = [];
  renderTeacherPills();
  document.getElementById('cp-teacher-input').value = '';
  document.getElementById('cp-teacher-dropdown').style.display = 'none';
  if(originalStartPlacing) originalStartPlacing();
};
"""

with open('js/map.js', 'a', encoding='utf-8') as f:
    f.write(code)
print("Done")
