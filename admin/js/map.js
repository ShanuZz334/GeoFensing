// ============================================================
// GeoFace Admin Panel — Map Logic
// ============================================================

const GEOFENCE_POLYGON = [[31.26046,75.70661],[31.26022,75.70624],[31.25947,75.70714],[31.25988,75.70582],[31.25911,75.70590],[31.25907,75.70719],[31.25853,75.70667],[31.25865,75.70809],[31.25884,75.70872],[31.25910,75.70908],[31.25847,75.70913],[31.25846,75.70829],[31.25794,75.70774],[31.25784,75.70857],[31.25753,75.70798],[31.25669,75.70755],[31.25654,75.70706],[31.25615,75.70633],[31.25386,75.70518],[31.25382,75.70624],[31.25061,75.70628],[31.24977,75.70930],[31.24798,75.70931],[31.24807,75.70442],[31.24582,75.70456],[31.24363,75.70081],[31.24700,75.69853],[31.24904,75.69870],[31.24902,75.69918],[31.24887,75.69947],[31.25078,75.69965],[31.25114,75.69954],[31.25230,75.70014],[31.25257,75.70212],[31.25550,75.70113],[31.25564,75.70382],[31.25714,75.70448],[31.25729,75.70638]];
const COLLEGE_CENTER = [31.2536, 75.7037];

let map = null;

function initMap() {
  // Initialize Leaflet map
  map = L.map('map').setView(COLLEGE_CENTER, 15);

  // OpenStreetMap Tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  // 1. Draw Main Polygon (Green/Blue)
  L.polygon(GEOFENCE_POLYGON, {
    color: '#3b82f6',
    fillColor: '#3b82f6',
    fillOpacity: 0.2,
    weight: 2
  }).addTo(map);

  // 2. Draw Buffer Zone (Orange/Yellow) using Turf.js
  try {
    const turfCoords = GEOFENCE_POLYGON.map(p => [p[1], p[0]]);
    turfCoords.push(turfCoords[0]); // Close polygon
    const turfPolygon = turf.polygon([turfCoords]);
    const buffered = turf.buffer(turfPolygon, 15, {units: 'meters'});
    
    const bufferCoords = buffered.geometry.coordinates[0].map(p => [p[1], p[0]]);
    L.polygon(bufferCoords, {
      color: '#f59e0b',
      fillColor: '#f59e0b',
      fillOpacity: 0.1,
      weight: 1,
      dashArray: '5, 5'
    }).addTo(map);
  } catch (e) {
    console.error('Turf buffer error:', e);
  }

  loadMapData();
}

async function loadMapData() {
  const data = await api('/admin/attendance?per_page=1000');
  if (!data) return;

  const users = {};
  
  data.logs.forEach(log => {
    if (!log.latitude || !log.longitude) return;
    
    if (!users[log.teacher_id]) {
      users[log.teacher_id] = {
        name: log.teacher_name,
        success: null,
        failures: []
      };
    }
    
    if (log.status === 'success') {
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
      L.circleMarker([log.latitude, log.longitude], {
        color: '#10b981',
        fillColor: '#10b981',
        fillOpacity: 0.9,
        radius: 8,
        weight: 2
      }).addTo(map)
        .bindPopup(`<strong>${user.name}</strong><br><span class="badge badge--success" style="padding:2px 6px;border-radius:4px">Present</span><br>Time: ${formatDt(log.timestamp)}`);
    }

    // 2. Plot LAST failure
    if (user.failures.length > 0) {
      const log = user.failures[0]; // First in desc order is latest
      L.circleMarker([log.latitude, log.longitude], {
        color: '#ef4444',
        fillColor: '#ef4444',
        fillOpacity: 0.9,
        radius: 8,
        weight: 2
      }).addTo(map)
        .bindPopup(`<strong>${user.name}</strong><br><span class="badge badge--failure" style="padding:2px 6px;border-radius:4px">Failed</span><br>Reason: ${log.reason}<br>Time: ${formatDt(log.timestamp)}`);
    }
  });
}

document.addEventListener('DOMContentLoaded', initMap);
