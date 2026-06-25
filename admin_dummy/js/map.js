// ============================================================
// GeoFace Admin Panel — Map Logic
// ============================================================

const COLLEGE_CENTER = [31.2536, 75.7037]; // NIT Jalandhar Main Campus

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

  L.control.layers(baseMaps, null, { position: 'topleft' }).addTo(map);

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
  checkpointLayers.forEach(l => map.removeLayer(l));
  checkpointLayers = [];
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

  // 3. Draw Checkpoints
  if ((mode === 3 || editMode) && currentConfig.checkpoints) {
    currentConfig.checkpoints.forEach((cp, idx) => {
      if (!cp.lat || !cp.lng || !cp.radius) return;
      const layer = L.circle([cp.lat, cp.lng], {
        color: '#7c3aed',
        fillColor: '#7c3aed',
        fillOpacity: 0.15,
        radius: cp.radius,
        weight: 2
      }).addTo(map);
      checkpointLayers.push(layer);

      const pinIcon = L.divIcon({
        className: 'custom-pin-icon',
        html: `<svg viewBox="0 0 384 512" style="width:24px; height:32px; filter:drop-shadow(2px 4px 4px rgba(0,0,0,0.6));">
          <!-- Main body of pin -->
          <path fill="#7c3aed" d="M384 192c0 87.4-117 243-168.3 307.2c-12.3 15.3-35.1 15.3-47.4 0C117 435 0 279.4 0 192C0 86 86 0 192 0S384 86 384 192z"></path>
          <!-- Shading for 3D effect -->
          <path fill="#5b21b6" d="M192 0C86 0 0 86 0 192c0 87.4 117 243 168.3 307.2c3.1 3.8 7.3 6 11.7 6.8V0c4 0 8 0 12 0z" opacity="0.3"></path>
          <!-- Center white circle -->
          <circle cx="192" cy="192" r="75" fill="#ffffff"></circle>
          <!-- Number -->
          <text x="192" y="235" font-size="130" font-family="sans-serif" font-weight="bold" fill="#7c3aed" text-anchor="middle">${idx + 1}</text>
        </svg>`,
        iconSize: [24, 32],
        iconAnchor: [12, 32],
        popupAnchor: [0, -32]
      });

      const pinLayer = L.marker([cp.lat, cp.lng], { icon: pinIcon }).addTo(map);
      checkpointLayers.push(pinLayer);

      let popupContent = `<strong>Checkpoint</strong><br>Radius: ${cp.radius}m`;
      if (editMode) {
        popupContent += `<br><button class="btn-secondary" style="margin-top:8px; width:100%; color:red; border-color:red" onclick="deleteCheckpoint(${idx})">Delete Checkpoint</button>`;
      }
      pinLayer.bindPopup(popupContent);
      layer.bindPopup(popupContent);
    });
  }
}

window.deleteSubPolygon = async function(idx) {
  if (await uiConfirm("Delete Block?", "Are you sure you want to delete this department block?")) {
    currentConfig.sub_polygons.splice(idx, 1);
    drawAllGeofences();
  }
};

window.deleteCheckpoint = async function(idx) {
  if (await uiConfirm("Delete Checkpoint?", "Are you sure you want to delete this checkpoint?")) {
    currentConfig.checkpoints.splice(idx, 1);
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
  } else if (activeTool === 'cp') {
    document.getElementById('btn-save-geofence').innerText = "Finish Checkpoint";
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
  ['main', 'sub', 'cp'].forEach(t => {
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
  if (!editMode) return;
  
  if (activeTool === 'cp') {
    // Checkpoints only need 1 point
    draftPoints = [[e.latlng.lat, e.latlng.lng]];
  } else {
    draftPoints.push([e.latlng.lat, e.latlng.lng]);
  }
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

  if (activeTool === 'cp') {
    draftPoints = [[lat, lng]];
  } else {
    draftPoints.push([lat, lng]);
  }
  
  redrawDraft();
  map.setView([lat, lng], map.getZoom());
  latInput.value = '';
  lngInput.value = '';
}

function redrawDraft() {
  clearDraft();

  if (draftPoints.length > 0) {
    if (activeTool === 'cp') {
      const p = draftPoints[0];
      draftLayer = L.circle(p, { color: 'white', fillColor: 'white', fillOpacity: 0.5, radius: 20 }).addTo(map);
      
      const marker = L.circleMarker(p, { radius: 5, color: 'white', fillColor: '#fff', fillOpacity: 1 }).addTo(map);
      marker.on('click', (e) => {
        L.DomEvent.stopPropagation(e);
        draftPoints = [];
        redrawDraft();
      });
      draftMarkers.push(marker);

    } else {
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
    // If no draft points, fall through to save overall config (e.g., after deletion)
  }
  
  if (activeTool === 'cp') {
    if (draftPoints.length > 0) {
      if (draftPoints.length !== 1) {
        uiAlert("Error", "Click the map to place one checkpoint dot.");
        return;
      }
      document.getElementById('checkpoint-modal').style.display = 'flex';
      return;
    }
    // If no draft points, fall through to save overall config (e.g., after deletion)
  }
  
  // Main Geofence Save All
  if (activeTool === 'main') {
    currentConfig.main_polygon = [...draftPoints];
  }
  
  try {
    const payload = { geofence_config: currentConfig };
    console.log("PAYLOAD_MAIN:", JSON.stringify(payload));
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


// ── ATTENDANCE PLOTTING ──

async function loadMapData() {
  const data = await api('/admin/attendance?per_page=1000');
  if (!data) return;

  const urlParams = new URLSearchParams(window.location.search);
  const focusId = urlParams.get('focus');
  let focusedLog = null;
  let focusedMarker = null;

  const users = {};

  data.logs.forEach(log => {
    if (!log.latitude || !log.longitude) return;
    if (log.reason && log.reason.includes('Demo Mode')) return;

    if (focusId && log.id == focusId) {
      focusedLog = log;
      return; 
    }

    if (!users[log.teacher_id]) {
      users[log.teacher_id] = {
        name: log.teacher_name,
        success: null,
        failures: []
      };
    }

    if (log.status === 'success' || log.status === 'CHECK-IN SUCCESS' || log.status === 'CHECK-OUT SUCCESS') {
      if (!users[log.teacher_id].success) {
        users[log.teacher_id].success = log;
      }
    } else {
      users[log.teacher_id].failures.push(log);
    }
  });

  Object.values(users).forEach(user => {
    if (user.success) {
      const log = user.success;
      const isCheckOut = log.action_type === 'check_out';
      const actionText = isCheckOut ? 'Check Out' : 'Check In';
      const bgColor = isCheckOut ? '#8b5cf6' : '#7C3AED';

      const markerClass = isCheckOut ? 'premium-marker-checkout' : 'premium-marker-checkin';
      const successIcon = L.divIcon({
        className: 'custom-div-icon',
        html: `<div class="premium-marker ${markerClass}"><div class="marker-icon-inner" style="color:white">✓</div></div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });
      L.marker([log.latitude, log.longitude], { icon: successIcon }).addTo(map)
        .bindPopup(`<strong>${user.name}</strong><br><span class="badge" style="background-color:${bgColor}; color:white; padding:2px 6px;border-radius:4px">${actionText}</span><br>Time: ${formatDt(log.timestamp)}`);
    }

    if (user.failures.length > 0) {
      const log = user.failures[0];
      const failureIcon = L.divIcon({
        className: 'custom-div-icon',
        html: '<div class="premium-marker premium-marker-failure"><div class="marker-icon-inner">✕</div></div>',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });
      L.marker([log.latitude, log.longitude], { icon: failureIcon }).addTo(map)
        .bindPopup(`<strong>${user.name}</strong><br><span class="badge badge--failure" style="padding:2px 6px;border-radius:4px">Failed</span><br>Reason: ${log.reason}<br>Time: ${formatDt(log.timestamp)}`);
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
