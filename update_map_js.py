import re

with open(r'admin/js/map.js', 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Update sub-polygon rendering to look much better
target1 = """    currentConfig.sub_polygons.forEach((sp, idx) => {
      if (!sp.polygon || sp.polygon.length < 3) return;
      const layer = L.polygon(sp.polygon, {
        color: sp.color || '#ef4444',
        fillColor: sp.color || '#ef4444',
        fillOpacity: 0.35,
        weight: 2
      }).addTo(map);
      
      const depts = Array.isArray(sp.departments) ? sp.departments.join(', ') : sp.departments;
      let popupContent = `<strong>${depts} Block</strong>`;
      if (editMode) {
        popupContent += `<br><button class="btn-secondary" style="margin-top:8px; width:100%; color:red; border-color:red" onclick="deleteSubPolygon(${idx})">Delete Block</button>`;
      }
      layer.bindPopup(popupContent);"""

replacement1 = """    currentConfig.sub_polygons.forEach((sp, idx) => {
      if (!sp.polygon || sp.polygon.length < 3) return;
      
      // Draw outer glow layer
      L.polygon(sp.polygon, {
        color: sp.color || '#ef4444',
        fill: false,
        weight: 6,
        opacity: 0.3,
        lineJoin: 'round'
      }).addTo(map);

      // Draw main layer
      const layer = L.polygon(sp.polygon, {
        color: sp.color || '#ef4444',
        fillColor: sp.color || '#ef4444',
        fillOpacity: 0.25,
        weight: 2,
        dashArray: '6, 6',
        lineJoin: 'round'
      }).addTo(map);
      
      const depts = Array.isArray(sp.departments) ? sp.departments.join(', ') : sp.departments;
      let popupContent = `<div style="font-size: 14px; margin-bottom: 8px;"><strong>${depts} Block</strong></div>`;
      if (editMode) {
        popupContent += `<div style="display:flex; gap: 8px; margin-top:8px;">
          <button class="btn-primary" style="flex:1; padding:6px;" onclick="editSubPolygon(${idx})">Edit</button>
          <button class="btn-secondary" style="flex:1; color:#ff4d4d; border-color:#ff4d4d; padding:6px;" onclick="deleteSubPolygon(${idx})">Delete</button>
        </div>`;
      }
      layer.bindPopup(popupContent);"""

if target1 in js:
    js = js.replace(target1, replacement1)
    print("Replaced sub-polygon rendering!")
else:
    print("Failed to find target1")

# 2. Add editSubPolygon and modify commitSubPolygon
target2 = """window.commitSubPolygon = async function() {
  const deptCheckboxes = document.querySelectorAll('input[name="sub-dept-checkbox"]:checked');
  const depts = Array.from(deptCheckboxes).map(cb => cb.value.trim()).filter(val => val);
  const color = document.getElementById('sub-color').value;
  
  if (depts.length === 0) {
    await uiAlert("Error", "Please select at least one department.");
    return;
  }
  
  if (!currentConfig.sub_polygons) currentConfig.sub_polygons = [];
  
  currentConfig.sub_polygons.push({
    id: 'sub_' + Date.now(),
    departments: depts,
    polygon: [...draftPoints],
    color: color
  });
  
  document.getElementById('sub-polygon-modal').style.display = 'none';
  draftPoints = [];
  redrawDraft();
  drawAllGeofences();
};"""

replacement2 = """window.editingSubPolygonIndex = null;

window.editSubPolygon = function(idx) {
  const poly = currentConfig.sub_polygons[idx];
  window.editingSubPolygonIndex = idx;
  
  // Setup Color
  const color = poly.color || '#ff4d4d';
  document.getElementById('sub-color').value = color;
  const swatches = document.querySelectorAll('.color-swatch');
  swatches.forEach(s => s.classList.remove('selected'));
  let found = false;
  swatches.forEach(s => {
    if (s.dataset.color.toLowerCase() === color.toLowerCase()) {
      s.classList.add('selected');
      found = true;
    }
  });
  if(!found && swatches.length > 0) swatches[0].classList.add('selected');
  
  // Uncheck all depts
  document.querySelectorAll('input[name="sub-dept-checkbox"]').forEach(cb => cb.checked = false);
  
  // Check assigned depts
  if (poly.departments) {
    poly.departments.forEach(dept => {
      const cb = document.querySelector(`input[name="sub-dept-checkbox"][value="${dept}"]`);
      if (cb) cb.checked = true;
    });
  }
  
  // Update uiverse-select text (trigger custom change)
  const firstCb = document.querySelector('input[name="sub-dept-checkbox"]');
  if (firstCb) firstCb.dispatchEvent(new Event('change', { bubbles: true }));

  document.getElementById('sub-polygon-modal').style.display = 'flex';
};

window.commitSubPolygon = async function() {
  const deptCheckboxes = document.querySelectorAll('input[name="sub-dept-checkbox"]:checked');
  const depts = Array.from(deptCheckboxes).map(cb => cb.value.trim()).filter(val => val);
  const color = document.getElementById('sub-color').value;
  
  if (depts.length === 0) {
    await uiAlert("Error", "Please select at least one department.");
    return;
  }
  
  if (!currentConfig.sub_polygons) currentConfig.sub_polygons = [];
  
  if (window.editingSubPolygonIndex !== null && window.editingSubPolygonIndex !== undefined) {
    currentConfig.sub_polygons[window.editingSubPolygonIndex].departments = depts;
    currentConfig.sub_polygons[window.editingSubPolygonIndex].color = color;
    window.editingSubPolygonIndex = null;
  } else {
    currentConfig.sub_polygons.push({
      id: 'sub_' + Date.now(),
      departments: depts,
      polygon: [...draftPoints],
      color: color
    });
  }
  
  document.getElementById('sub-polygon-modal').style.display = 'none';
  draftPoints = [];
  redrawDraft();
  drawAllGeofences();
};"""

if target2 in js:
    js = js.replace(target2, replacement2)
    print("Replaced commitSubPolygon!")
else:
    print("Failed to find target2")

# 3. Add window.selectColor to global scope
if "window.selectColor" not in js:
    js += """\n
window.selectColor = function(el) {
  document.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('selected'));
  el.classList.add('selected');
  document.getElementById('sub-color').value = el.dataset.color;
};
"""
    print("Added selectColor!")

# 4. Handle cancelEditSubPolygon
js = js.replace("document.getElementById('sub-polygon-modal').style.display = 'none';", "document.getElementById('sub-polygon-modal').style.display = 'none';\n  window.editingSubPolygonIndex = null;")

with open(r'admin/js/map.js', 'w', encoding='utf-8') as f:
    f.write(js)
