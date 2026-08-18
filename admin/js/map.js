// ============================================================
// GeoFace Admin Panel — Map Logic
// ============================================================

const COLLEGE_CENTER = [31.2536, 75.7037];

let map = null;
let currentConfig = {
  mode: 1,
  main_polygon: [],
  sub_polygons: [],
  checkpoints: []
};

// Layers
let mainPolygonLayer = null;
let bufferPolygonLayer = null;
let subPolygonLayers = [];
let checkpointLayers = [];
let attendanceLatestLayer;
let attendanceAllLayer;

// Editor state
let editMode = false;
let activeTool = 'main'; // 'main', 'sub', 'cp'
let draftPoints = [];
let draftLayer = null;
let draftMarkers = [];

async function initMap() {
  const darkMap = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    subdomains: 'abcd',
    maxZoom: 20
  });

  const normalMap = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 19
  });

  const satelliteMap = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri',
    maxZoom: 19
  });

  map = L.map('map', {
    center: COLLEGE_CENTER,
    zoom: 15,
    layers: [satelliteMap],
    zoomControl: false
  });

  const baseMaps = {
    "Satellite Mode": satelliteMap,
    "Normal Mode": normalMap,
    "Dark Mode": darkMap
  };

  attendanceLatestLayer = L.layerGroup().addTo(map);
  attendanceAllLayer = L.layerGroup(); // Not added to map by default

  const overlayMaps = {
    "Attendance (Latest Only)": attendanceLatestLayer,
    "Attendance (All History)": attendanceAllLayer
  };

  L.control.layers(baseMaps, overlayMaps, { position: 'topleft' }).addTo(map);

  // Make the two attendance layers mutually exclusive (like radio buttons)
  map.on('overlayadd', function(e) {
    setTimeout(() => {
      if (e.name === "Attendance (Latest Only)") {
        if (map.hasLayer(attendanceAllLayer)) map.removeLayer(attendanceAllLayer);
      } else if (e.name === "Attendance (All History)") {
        if (map.hasLayer(attendanceLatestLayer)) map.removeLayer(attendanceLatestLayer);
      }
    }, 10);
  });

  map.on('click', onMapClick);

  await fetchGeofence();
  loadMapData();
}

async function fetchGeofence() {
  try {
    const res = await api('/admin/geofence');
    if (res && res.geofence_config) {
      currentConfig = res.geofence_config;
      drawAllGeofences();
    } else if (res && res.polygon) {
      currentConfig.main_polygon = res.polygon;
      drawAllGeofences();
    }
  } catch (e) {
    console.error("Failed to load geofence", e);
  }
}

function clearAllLayers() {
  if (mainPolygonLayer) map.removeLayer(mainPolygonLayer);
  if (bufferPolygonLayer) map.removeLayer(bufferPolygonLayer);
  subPolygonLayers.forEach(l => map.removeLayer(l));
  subPolygonLayers = [];
}

function drawAllGeofences() {
  clearAllLayers();

  const mode = currentConfig.mode || 1;

  // 1. Draw Main Polygon
  const mainCoords = currentConfig.main_polygon || [];
  if (mainCoords.length > 0) {
    mainPolygonLayer = L.polygon(mainCoords, {
      color: '#7c3aed',
      fillColor: '#7c3aed',
      fillOpacity: editMode || mode === 1 || mode === 2 ? 0.08 : 0.02,
      weight: 2
    }).addTo(map);

    // Draw buffer only if mode 1, or in edit mode
    if ((mode === 1 || editMode) && typeof turf !== 'undefined') {
      try {
        const turfCoords = mainCoords.map(p => [p[1], p[0]]);
        turfCoords.push(turfCoords[0]); 
        const turfPolygon = turf.polygon([turfCoords]);
        const buffered = turf.buffer(turfPolygon, 15, { units: 'meters' });
        const bufferCoords = buffered.geometry.coordinates[0].map(p => [p[1], p[0]]);
        bufferPolygonLayer = L.polygon(bufferCoords, {
          color: '#8b5cf6',
          fillColor: '#8b5cf6',
          fillOpacity: 0.1,
          weight: 1,
          dashArray: '5, 5'
        }).addTo(map);
      } catch (e) {
        console.error('Turf buffer error:', e);
      }
    }
  }

  // 2. Draw Sub Polygons
  if ((mode === 2 || editMode) && currentConfig.sub_polygons) {
    currentConfig.sub_polygons.forEach((sp, idx) => {
      if (!sp.polygon || sp.polygon.length < 3) return;
      // Draw main layer
      const layer = L.polygon(sp.polygon, {
        color: sp.color || '#ef4444',
        fillColor: '#000000',
        fillOpacity: 0.35,
        weight: 1.5,
        dashArray: '4, 4',
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
      layer.bindPopup(popupContent);
      subPolygonLayers.push(layer);
    });
  }

}

window.deleteSubPolygon = async function(idx) {
  if (await uiConfirm("Delete Block?", "Are you sure you want to delete this department block?")) {
    currentConfig.sub_polygons.splice(idx, 1);
    drawAllGeofences();
  }
};




// ── EDITOR CONTROLS ──

function toggleManualPanel(show) {
  if (show) {
    document.getElementById('manual-coord-panel').style.display = 'block';
    document.getElementById('btn-show-manual').style.display = 'none';
  } else {
    document.getElementById('manual-coord-panel').style.display = 'none';
    document.getElementById('btn-show-manual').style.display = 'flex';
  }
}

function toggleEditMode() {
  editMode = true;
  activeTool = 'main';
  
  // Set draft points to current main polygon so user can edit it
  draftPoints = currentConfig.main_polygon ? [...currentConfig.main_polygon] : [];

  document.getElementById('btn-edit-geofence').style.display = 'none';
  document.getElementById('editor-tools').style.display = 'flex';
  document.getElementById('btn-save-geofence').style.display = 'inline-block';
  document.getElementById('btn-cancel-edit').style.display = 'inline-block';
  document.getElementById('btn-clear-geofence').style.display = 'inline-block';
  
  // Default hide panel
  toggleManualPanel(false);

  // We temporarily remove the main polygon since it is now in the draftLayer
  if (mainPolygonLayer) map.removeLayer(mainPolygonLayer);
  if (bufferPolygonLayer) map.removeLayer(bufferPolygonLayer);

  updateToolUI();
  drawAllGeofences(); // will redraw sub & cp with delete buttons
  redrawDraft();
}

function cancelEditMode() {
  editMode = false;
  clearDraft();

  document.getElementById('btn-edit-geofence').style.display = 'inline-block';
  document.getElementById('editor-tools').style.display = 'none';
  document.getElementById('btn-save-geofence').style.display = 'none';
  document.getElementById('btn-cancel-edit').style.display = 'none';
  document.getElementById('btn-clear-geofence').style.display = 'none';
  document.getElementById('manual-coord-panel').style.display = 'none';
  document.getElementById('btn-show-manual').style.display = 'none';

  // Restore main polygon visually
  drawAllGeofences();
}

window.setEditorTool = function(tool) {
  // If we were on Main, save the draft back to config before switching
  if (activeTool === 'main') {
    currentConfig.main_polygon = [...draftPoints];
  }
  
  activeTool = tool;
  
  // Clear draft
  draftPoints = [];
  if (activeTool === 'main') {
    draftPoints = [...(currentConfig.main_polygon || [])];
    document.getElementById('btn-save-geofence').innerText = "Save All Changes";
  } else if (activeTool === 'sub') {
    document.getElementById('btn-save-geofence').innerText = "Finish Sub-Polygon";
  }
  
  updateToolUI();
  drawAllGeofences();
  if (activeTool === 'main') {
    if (mainPolygonLayer) map.removeLayer(mainPolygonLayer);
    if (bufferPolygonLayer) map.removeLayer(bufferPolygonLayer);
  }
  redrawDraft();
};

function updateToolUI() {
  ['main', 'sub'].forEach(t => {
    const btn = document.getElementById(`tool-${t}`);
    if(btn) {
      if (activeTool === t) {
        btn.style.background = 'var(--primary)';
        btn.style.color = 'white';
        btn.style.borderColor = 'var(--primary)';
      } else {
        btn.style.background = '';
        btn.style.color = '';
        btn.style.borderColor = '';
      }
    }
  });
}

function clearDraft() {
  if (draftLayer) map.removeLayer(draftLayer);
  draftMarkers.forEach(m => map.removeLayer(m));
  draftMarkers = [];
}

function clearGeofence() {
  draftPoints = [];
  redrawDraft();
}

function onMapClick(e) {
  if (isPlacingEventCp) {
    eventCpCoords = [e.latlng.lat, e.latlng.lng];
    if (eventCpMarker) map.removeLayer(eventCpMarker);
    eventCpMarker = L.circleMarker(eventCpCoords, { radius: 6, color: '#10b981', fillColor: '#fff', fillOpacity: 1 }).addTo(map);
    document.getElementById('checkpoint-modal').style.display = 'flex';
    return;
  }

  if (!editMode) return;
  
  draftPoints.push([e.latlng.lat, e.latlng.lng]);
  redrawDraft();
}

function addManualPoint() {
  if (!editMode) return;
  
  const latInput = document.getElementById('manual-lat');
  const lngInput = document.getElementById('manual-lng');
  const lat = parseFloat(latInput.value);
  const lng = parseFloat(lngInput.value);

  if (isNaN(lat) || isNaN(lng)) {
    uiAlert("Error", "Please enter valid numeric latitude and longitude values.");
    return;
  }

  draftPoints.push([lat, lng]);
  
  redrawDraft();
  map.setView([lat, lng], map.getZoom());
  latInput.value = '';
  lngInput.value = '';
}

function redrawDraft() {
  clearDraft();

  if (draftPoints.length > 0) {
    // Polygon drawing (Main or Sub)
    let drawColor = activeTool === 'main' ? 'red' : 'magenta';
    
    if (draftPoints.length >= 3) {
      draftLayer = L.polygon(draftPoints, { color: drawColor, weight: 2, fillOpacity: 0.2 }).addTo(map);
    } else {
      draftLayer = L.polyline(draftPoints, { color: drawColor, weight: 2 }).addTo(map);
    }

    draftPoints.forEach((p, idx) => {
      const marker = L.circleMarker(p, { radius: 5, color: drawColor, fillColor: '#fff', fillOpacity: 1 }).addTo(map);
      marker.on('click', (e) => {
        L.DomEvent.stopPropagation(e);
        draftPoints.splice(idx, 1);
        redrawDraft();
      });
      draftMarkers.push(marker);
    });
  }
}

// ── SAVING ──

async function saveGeofence() {
  if (activeTool === 'sub') {
    if (draftPoints.length > 0) {
      if (draftPoints.length < 3) {
        uiAlert("Error", "Draw at least 3 points for a department block.");
        return;
      }
        // Clear previous selection for new sub-polygon
        window.editingSubPolygonIndex = null;
        document.querySelectorAll('input[name="sub-dept-checkbox"]').forEach(cb => cb.checked = false);
        const firstCb = document.querySelector('input[name="sub-dept-checkbox"]');
        if (firstCb) firstCb.dispatchEvent(new Event('change', { bubbles: true }));
        
        document.getElementById('sub-polygon-modal').style.display = 'flex';
        return;
    }
  }
  
  // Main Geofence Save All
  if (activeTool === 'main') {
    currentConfig.main_polygon = [...draftPoints];
  }
  
  try {
    const payload = { geofence_config: currentConfig };
    const res = await api('/admin/geofence', 'PUT', payload);
    if (res && res.geofence_config) {
      currentConfig = res.geofence_config;
      await uiAlert("Success", "Geofence settings saved successfully!");
      cancelEditMode();
    } else {
      await uiAlert("Error", "Failed to save geofence.");
    }
  } catch (e) {
    console.error(e);
    await uiAlert("Error", "Error saving geofence.");
  }
}

// ── SUB-POLYGON MODAL ──
window.editingSubPolygonIndex = null;

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
  
  saveFullConfigToBackend();
};

window.cancelSubPolygon = function() {
  document.getElementById('sub-polygon-modal').style.display = 'none';
  window.editingSubPolygonIndex = null;
};

// ── CHECKPOINT MODAL ──
window.commitCheckpoint = async function() {
  const radius = parseFloat(document.getElementById('cp-radius').value);
  if (isNaN(radius) || radius < 5) {
    await uiAlert("Error", "Invalid radius. Minimum is 5 meters.");
    return;
  }
  
  if (!currentConfig.checkpoints) currentConfig.checkpoints = [];
  
  currentConfig.checkpoints.push({
    id: 'cp_' + Date.now(),
    lat: draftPoints[0][0],
    lng: draftPoints[0][1],
    radius: radius
  });
  
  document.getElementById('checkpoint-modal').style.display = 'none';
  draftPoints = [];
  redrawDraft();
  drawAllGeofences();
  
  saveFullConfigToBackend();
};

window.cancelCheckpoint = function() {
  document.getElementById('checkpoint-modal').style.display = 'none';
};

async function saveFullConfigToBackend() {
  try {
    const payload = { geofence_config: currentConfig };
    console.log("PAYLOAD:", JSON.stringify(payload));
    const res = await api('/admin/geofence', 'PUT', payload);
    if (res && res.geofence_config) {
      currentConfig = res.geofence_config;

      // uiAlert("Success", "Added successfully!");
      // Switch back to main tool automatically
      setEditorTool('main');
    }
  } catch (e) {
    console.error(e);
  }
}

// -- ATTENDANCE PLOTTING --

async function loadMapData() {
  const data = await api('/admin/attendance?per_page=1000');
  if (!data) return;

  const urlParams = new URLSearchParams(window.location.search);
  const focusId = urlParams.get('focus');
  let focusedLog = null;
  let focusedMarker = null;

  if (attendanceLatestLayer) attendanceLatestLayer.clearLayers();
  if (attendanceAllLayer) attendanceAllLayer.clearLayers();

  const latestLogs = {};

  data.logs.forEach(log => {
    if (!log.latitude || !log.longitude) return;
    if (log.reason && log.reason.includes('Demo Mode')) return;

    if (focusId && log.id == focusId) {
      focusedLog = log;
      return; 
    }

    // Compute consistent jitter once per log so pins don't jump when toggling layers
    if (!log.jitterLat) {
      log.jitterLat = parseFloat(log.latitude) + (Math.random() - 0.5) * 0.0001;
      log.jitterLng = parseFloat(log.longitude) + (Math.random() - 0.5) * 0.0001;
    }

    // Always track the absolute latest for the "Latest" layer
    if (!latestLogs[log.teacher_id]) {
      latestLogs[log.teacher_id] = log;
    } else {
      if (new Date(log.timestamp) > new Date(latestLogs[log.teacher_id].timestamp)) {
        latestLogs[log.teacher_id] = log;
      }
    }

    // Helper to generate a marker
    const createMarker = (isLatest) => {
      const isCheckOut = log.action_type === 'check_out';
      const actionText = isCheckOut ? 'Check Out' : 'Check In';
      const bgColor = isCheckOut ? '#8b5cf6' : '#7C3AED';

      const layerToUse = isLatest ? attendanceLatestLayer : attendanceAllLayer;

      if (log.status === 'success' || log.status === 'CHECK-IN SUCCESS' || log.status === 'CHECK-OUT SUCCESS') {
        const markerClass = isCheckOut ? 'premium-marker-checkout' : 'premium-marker-checkin';
        const successIcon = L.divIcon({
          className: 'custom-div-icon',
          html: `<div class="premium-marker ${markerClass}"><div class="marker-icon-inner" style="color:white">✓</div></div>`,
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        });
        L.marker([log.jitterLat, log.jitterLng], { icon: successIcon }).addTo(layerToUse)
          .bindPopup(`<strong>${log.teacher_name}</strong><br><span class="badge" style="background-color:${bgColor}; color:white; padding:2px 6px;border-radius:4px">${actionText}</span><br>Time: ${formatDt(log.timestamp)}`);
      } else {
        const failureIcon = L.divIcon({
          className: 'custom-div-icon',
          html: '<div class="premium-marker premium-marker-failure"><div class="marker-icon-inner">✕</div></div>',
          iconSize: [24, 24],
          iconAnchor: [12, 12]
        });
        L.marker([log.jitterLat, log.jitterLng], { icon: failureIcon }).addTo(layerToUse)
          .bindPopup(`<strong>${log.teacher_name}</strong><br><span class="badge badge--failure" style="padding:2px 6px;border-radius:4px">Failed</span><br>Reason: ${log.reason}<br>Time: ${formatDt(log.timestamp)}`);
      }
    };

    // Add ALL valid logs to the 'All' layer
    createMarker(false);
  });

  // Add only the latest logs to the 'Latest' layer
  Object.values(latestLogs).forEach(log => {
    const isCheckOut = log.action_type === 'check_out';
    const actionText = isCheckOut ? 'Check Out' : 'Check In';
    const bgColor = isCheckOut ? '#8b5cf6' : '#7C3AED';

    if (log.status === 'success' || log.status === 'CHECK-IN SUCCESS' || log.status === 'CHECK-OUT SUCCESS') {
      const markerClass = isCheckOut ? 'premium-marker-checkout' : 'premium-marker-checkin';
      const successIcon = L.divIcon({
        className: 'custom-div-icon',
        html: `<div class="premium-marker ${markerClass}"><div class="marker-icon-inner" style="color:white">✓</div></div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });
      L.marker([log.jitterLat, log.jitterLng], { icon: successIcon }).addTo(attendanceLatestLayer)
        .bindPopup(`<strong>${log.teacher_name}</strong><br><span class="badge" style="background-color:${bgColor}; color:white; padding:2px 6px;border-radius:4px">${actionText}</span><br>Time: ${formatDt(log.timestamp)}`);
    } else {
      const failureIcon = L.divIcon({
        className: 'custom-div-icon',
        html: '<div class="premium-marker premium-marker-failure"><div class="marker-icon-inner">✕</div></div>',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });
      L.marker([log.jitterLat, log.jitterLng], { icon: failureIcon }).addTo(attendanceLatestLayer)
        .bindPopup(`<strong>${log.teacher_name}</strong><br><span class="badge badge--failure" style="padding:2px 6px;border-radius:4px">Failed</span><br>Reason: ${log.reason}<br>Time: ${formatDt(log.timestamp)}`);
    }
  });

  if (focusedLog) {
    const focusColor = '#9c27b0';
    const focusIcon = L.divIcon({
      className: 'custom-div-icon',
      html: `<div class="premium-marker" style="background-color: ${focusColor}; box-shadow: 0 0 10px ${focusColor}; border: 3px solid #121212;"><div class="marker-icon-inner" style="color:white; display:flex; align-items:center; justify-content:center;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="3"></circle></svg></div></div>`,
      iconSize: [28, 28],
      iconAnchor: [14, 14]
    });
    focusedMarker = L.marker([focusedLog.latitude, focusedLog.longitude], { icon: focusIcon, zIndexOffset: 1000 }).addTo(map)
      .bindPopup(`<strong>${focusedLog.teacher_name}</strong><br><span class="badge badge--${focusedLog.status}" style="padding:2px 6px;border-radius:4px">${focusedLog.status.toUpperCase()}</span><br>Reason: ${focusedLog.reason}<br>Time: ${formatDt(focusedLog.timestamp)}`);

    map.setView([focusedLog.latitude, focusedLog.longitude], 18);
    focusedMarker.openPopup();
  }
}

initApp('map', initMap);
window.selectColor = function(el) {
  document.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('selected'));
  el.classList.add('selected');
  document.getElementById('sub-color').value = el.dataset.color;
};

// ── EVENT CHECKPOINTS (New Standalone System) ──
let isPlacingEventCp = false;
let eventCpCoords = null;
let eventCpMarker = null;
let activeEventCheckpoints = [];
let eventCpMapLayers = [];

window.startPlacingEventCp = function() {
  if (editMode) cancelEditMode();
  isPlacingEventCp = true;
  uiAlert('Click anywhere on the map to place the event checkpoint.', { type: 'info' });
};

window.cancelEventCheckpoint = function() {
  isPlacingEventCp = false;
  eventCpCoords = null;
  if (eventCpMarker) {
    map.removeLayer(eventCpMarker);
    eventCpMarker = null;
  }
  document.getElementById('checkpoint-modal').style.display = 'none';
};

window.submitEventCheckpoint = async function() {
  const name = document.getElementById('cp-name').value.trim();
  const radius = parseFloat(document.getElementById('cp-radius').value);
  const duration = parseFloat(document.getElementById('cp-duration').value);
  
  if (!name || isNaN(radius) || isNaN(duration)) {
    uiAlert('Please fill all required fields correctly.', { type: 'error' });
    return;
  }
  
  const typeRadio = document.querySelector('input[name="cp-restriction-type"]:checked');
  const restrictionType = typeRadio ? typeRadio.value : 'none';
  
  let departments = [];
  if (restrictionType === 'department') {
    const deptCheckboxes = document.querySelectorAll('input[name="cp-dept-value"]:checked');
    deptCheckboxes.forEach(cb => departments.push(cb.value));
    if (departments.length === 0) {
      uiAlert('Please select at least one department.', { type: 'error' });
      return;
    }
  }
  
  let facultyRegNos = [];
  if (restrictionType === 'faculty') {
    const rawVal = document.getElementById('cp-teacher-value').value;
    facultyRegNos = rawVal ? rawVal.split(',').map(s => s.trim()) : [];
  }
  
  // Calculate expiry
  const startsAt = new Date();
  const expiresAt = new Date(startsAt.getTime() + duration * 60 * 60 * 1000);
  
  const payload = {
    name: name,
    lat: eventCpCoords[0],
    lng: eventCpCoords[1],
    radius: radius,
    restriction_type: restrictionType === 'none' ? 'all' : restrictionType,
    departments: departments,
    faculty_reg_nos: facultyRegNos,
    is_compulsory: document.getElementById('cp-compulsory').checked,
    starts_at: startsAt.toISOString(),
    expires_at: expiresAt.toISOString()
  };
  
  try {
    const res = await api('/admin/checkpoints', 'POST', payload);
    if (!res) return; // API function already showed an error toast
    
    if (res.status === 'success') {
      uiAlert('Event Checkpoint Created!', { type: 'success' });
      cancelEventCheckpoint();
      loadEventCheckpoints();
    } else {
      uiAlert(res.reason || 'Failed to create', { type: 'error' });
    }
  } catch (e) {
    uiAlert('Server error while creating checkpoint', { type: 'error' });
  }
};

window.loadEventCheckpoints = async function() {
  try {
    const res = await api('/admin/checkpoints');
    if (res && res.checkpoints) {
      activeEventCheckpoints = res.checkpoints;
      renderEventCheckpoints();
    }
  } catch (e) {
    console.error('Failed to load event checkpoints');
  }
};

window.deleteEventCheckpoint = async function(id) {
  if (!(await uiConfirm('Delete Checkpoint', 'Are you sure you want to delete this event checkpoint?'))) return;
  try {
    const res = await api('/admin/checkpoints/' + id, 'DELETE');
    if (res.status === 'success') {
      loadEventCheckpoints();
    } else {
      uiAlert('Failed to delete', { type: 'error' });
    }
  } catch (e) {
    uiAlert('Failed to delete', { type: 'error' });
  }
};

function renderEventCheckpoints() {
  const listEl = document.getElementById('event-cp-list');
  listEl.innerHTML = '';
  
  // Clear map layers
  eventCpMapLayers.forEach(l => map.removeLayer(l));
  eventCpMapLayers = [];
  
  const panelEl = document.getElementById('event-cp-panel');
  
  if (activeEventCheckpoints.length === 0) {
    panelEl.style.display = 'none';
    return;
  }
  
  panelEl.style.display = 'flex';
  activeEventCheckpoints.forEach((cp, idx) => {
    // 1. Add to sidebar list
    const div = document.createElement('div');
    div.style.cssText = 'background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 12px; position: relative;';
    
    const titleRow = document.createElement('div');
    titleRow.style.cssText = 'display: flex; justify-content: space-between; align-items: center;';
    titleRow.innerHTML = `<strong style="color:var(--text); font-size:13px;"><span style="display:inline-block; background:#7c3aed; color:white; border-radius:50%; width:18px; height:18px; text-align:center; line-height:18px; font-size:10px; margin-right:6px;">${idx + 1}</span>${cp.name}</strong>
      <button style="background:none; border:none; color:var(--error); cursor:pointer; font-size:16px; padding:0; line-height: 1;" onclick="deleteEventCheckpoint('${cp.id}')">&times;</button>`;
    
    const infoRow = document.createElement('div');
    infoRow.style.cssText = 'font-size: 11px; color: var(--text-muted); display:flex; flex-direction:column; gap:2px; margin-top: 6px;';
    
    let restr = 'All Faculty';
    if (cp.restriction_type === 'department') restr = 'Dept: ' + (cp.departments.join(', ') || 'None');
    if (cp.restriction_type === 'faculty') restr = 'Faculty: ' + (cp.faculty_reg_nos.join(', ') || 'None');
    
    if (cp.is_compulsory) {
      restr += ' <span style="color:var(--error); font-weight:600;">(Compulsory)</span>';
    } else {
      restr += ' <span style="color:var(--text-muted);">(Optional)</span>';
    }
    
    const expiry = new Date(cp.expires_at).toLocaleString('en-US', {month: 'short', day: 'numeric', hour: 'numeric', minute:'2-digit', hour12: true});
    const coordHtml = `<span style="display:flex; align-items:center; gap:4px; margin-top:2px;"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg> ${cp.lat.toFixed(5)}, ${cp.lng.toFixed(5)}</span>`;
    infoRow.innerHTML = `<span style="display:flex; align-items:center; gap:4px;"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/></svg> Radius: ${cp.radius}m | Expires: ${expiry}</span><span style="display:flex; align-items:center; gap:4px; margin-top:2px;"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg> ${restr}</span>${coordHtml}`;
    
    div.appendChild(titleRow);
    div.appendChild(infoRow);
    listEl.appendChild(div);
    
    // 2. Add to Map
    const circle = L.circle([cp.lat, cp.lng], { color: '#7c3aed', fillColor: '#7c3aed', fillOpacity: 0.3, radius: cp.radius, dashArray: '10, 10' }).addTo(map);
    
    const pinIcon = L.divIcon({
      className: 'custom-pin-icon',
      html: `<svg viewBox="0 0 384 512" style="width:28px; height:36px; filter:drop-shadow(2px 4px 4px rgba(0,0,0,0.6));">
        <path fill="#7c3aed" d="M384 192c0 87.4-117 243-168.3 307.2c-12.3 15.3-35.1 15.3-47.4 0C117 435 0 279.4 0 192C0 86 86 0 192 0S384 86 384 192z"></path>
        <path fill="#5b21b6" d="M192 0C86 0 0 86 0 192c0 87.4 117 243 168.3 307.2c3.1 3.8 7.3 6 11.7 6.8V0c4 0 8 0 12 0z" opacity="0.3"></path>
        <circle cx="192" cy="192" r="75" fill="#ffffff"></circle>
        <text x="192" y="235" font-size="130" font-family="sans-serif" font-weight="bold" fill="#7c3aed" text-anchor="middle">${idx + 1}</text>
      </svg>`,
      iconSize: [28, 36],
      iconAnchor: [14, 36]
    });
    
    const marker = L.marker([cp.lat, cp.lng], { icon: pinIcon }).addTo(map);
    marker.bindPopup(`<strong>${cp.name}</strong>`);
    eventCpMapLayers.push(circle, marker);
  });
}

// Automatically load them on startup
document.addEventListener("DOMContentLoaded", () => {
  setTimeout(loadEventCheckpoints, 1000); // Give auth a second to initialize
});


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
