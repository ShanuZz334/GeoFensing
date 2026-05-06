// ============================================================
// GeoFace Admin Panel — Map Logic
// ============================================================

const COLLEGE_CENTER = [31.2536, 75.7037];

let map = null;
let currentPolygon = [];
let mainPolygonLayer = null;
let bufferPolygonLayer = null;

// Editor state
let editMode = false;
let draftPoints = [];
let draftLayer = null;
let draftMarkers = [];

async function initMap() {
  const darkMap = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
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
    layers: [satelliteMap]
  });

  const baseMaps = {
    "Satellite Mode": satelliteMap,
    "Normal Mode": normalMap,
    "Dark Mode": darkMap
  };

  L.control.layers(baseMaps).addTo(map);

  map.on('click', onMapClick);

  await fetchGeofence();
  loadMapData();
}

async function fetchGeofence() {
  try {
    const res = await api('/admin/geofence');
    if (res && res.polygon) {
      currentPolygon = res.polygon;
      drawGeofence(currentPolygon);
    }
  } catch (e) {
    console.error("Failed to load geofence", e);
  }
}

function drawGeofence(coords) {
  if (mainPolygonLayer) map.removeLayer(mainPolygonLayer);
  if (bufferPolygonLayer) map.removeLayer(bufferPolygonLayer);

  if (!coords || coords.length === 0) return;

  mainPolygonLayer = L.polygon(coords, {
    color: '#3b82f6',
    fillColor: '#3b82f6',
    fillOpacity: 0.2,
    weight: 2
  }).addTo(map);

  try {
    const turfCoords = coords.map(p => [p[1], p[0]]);
    turfCoords.push(turfCoords[0]); // Close polygon
    const turfPolygon = turf.polygon([turfCoords]);
    const buffered = turf.buffer(turfPolygon, 15, { units: 'meters' });

    const bufferCoords = buffered.geometry.coordinates[0].map(p => [p[1], p[0]]);
    bufferPolygonLayer = L.polygon(bufferCoords, {
      color: '#f59e0b',
      fillColor: '#f59e0b',
      fillOpacity: 0.1,
      weight: 1,
      dashArray: '5, 5'
    }).addTo(map);
  } catch (e) {
    console.error('Turf buffer error:', e);
  }
}

function toggleEditMode() {
  editMode = true;
  draftPoints = [...currentPolygon];

  document.getElementById('btn-edit-geofence').style.display = 'none';
  document.getElementById('btn-save-geofence').style.display = 'inline-block';
  document.getElementById('btn-cancel-edit').style.display = 'inline-block';
  document.getElementById('btn-clear-geofence').style.display = 'inline-block';
  document.getElementById('edit-instructions').style.display = 'block';
  document.getElementById('manual-coord-panel').style.display = 'block';

  if (mainPolygonLayer) map.removeLayer(mainPolygonLayer);
  if (bufferPolygonLayer) map.removeLayer(bufferPolygonLayer);

  redrawDraft();
}

function cancelEditMode() {
  editMode = false;
  clearDraft();

  document.getElementById('btn-edit-geofence').style.display = 'inline-block';
  document.getElementById('btn-save-geofence').style.display = 'none';
  document.getElementById('btn-cancel-edit').style.display = 'none';
  document.getElementById('btn-clear-geofence').style.display = 'none';
  document.getElementById('edit-instructions').style.display = 'none';
  document.getElementById('manual-coord-panel').style.display = 'none';

  drawGeofence(currentPolygon);
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
  
  // Center map on the newly added manual point
  map.setView([lat, lng], map.getZoom());

  // Clear inputs
  latInput.value = '';
  lngInput.value = '';
}

function redrawDraft() {
  clearDraft();

  if (draftPoints.length > 0) {
    if (draftPoints.length >= 3) {
      draftLayer = L.polygon(draftPoints, { color: 'red', weight: 2, fillOpacity: 0.2 }).addTo(map);
    } else {
      draftLayer = L.polyline(draftPoints, { color: 'red', weight: 2 }).addTo(map);
    }

    draftPoints.forEach((p, idx) => {
      const marker = L.circleMarker(p, { radius: 5, color: 'red', fillColor: '#fff', fillOpacity: 1 }).addTo(map);
      marker.on('click', (e) => {
        L.DomEvent.stopPropagation(e);
        draftPoints.splice(idx, 1);
        redrawDraft();
      });
      draftMarkers.push(marker);
    });
  }
}

async function saveGeofence() {
  if (draftPoints.length < 3) {
    await uiAlert("Error", "Please draw a polygon with at least 3 points.");
    return;
  }

  try {
    const res = await api('/admin/geofence', 'PUT', { polygon: draftPoints });

    if (res && res.polygon) {
      currentPolygon = res.polygon;
      await uiAlert("Success", "Geofence saved successfully!");
      cancelEditMode();
    } else {
      await uiAlert("Error", "Failed to save geofence.");
    }
  } catch (e) {
    console.error(e);
    await uiAlert("Error", "Error saving geofence.");
  }
}

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
      return; // Handled separately
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

  // Plot markers
  Object.values(users).forEach(user => {
    // 1. Plot success (latest)
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

    // 2. Plot LAST failure
    if (user.failures.length > 0) {
      const log = user.failures[0]; // First in desc order is latest
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

document.addEventListener('DOMContentLoaded', initMap);
