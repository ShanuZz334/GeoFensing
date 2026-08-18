with open(r'admin/css/styles.css', 'a', encoding='utf-8') as f:
    f.write('''
/* --- Dark Mode Leaflet Popups --- */
.leaflet-popup-content-wrapper {
  background: var(--surface) !important;
  color: var(--text) !important;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  border: 1px solid var(--surface-2);
}
.leaflet-popup-tip {
  background: var(--surface) !important;
}
.leaflet-popup-close-button {
  color: var(--text-muted) !important;
}
.leaflet-popup-close-button:hover {
  color: var(--text) !important;
}
.leaflet-popup-content {
  margin: 16px;
  line-height: 1.5;
}

/* --- Color Swatches --- */
.color-swatch-container {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 8px;
}
.color-swatch {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: transform 0.2s, border-color 0.2s;
  position: relative;
}
.color-swatch:hover {
  transform: scale(1.1);
}
.color-swatch.selected {
  border-color: white;
  box-shadow: 0 0 0 2px var(--surface);
}
.color-swatch.selected::after {
  content: "\\2713"; /* Checkmark */
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 14px;
  text-shadow: 0px 1px 2px rgba(0,0,0,0.5);
}

/* --- Fix Oval Checkbox --- */
.uiverse-options input[type="checkbox"] {
  min-width: 16px !important;
  min-height: 16px !important;
  flex-shrink: 0;
  flex-grow: 0;
  box-sizing: border-box;
}
''')
print("Added Leaflet Popup & Color Swatch CSS, and fixed Oval checkboxes!")
