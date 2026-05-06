css = """
/* ── Custom iOS Checkbox ─────────────────────────────────────────── */
.checkbox-container {
  display: flex;
  gap: 20px;
  padding: 10px;
  background: var(--surface);
  border-radius: 12px;
}

.ios-checkbox {
  --checkbox-size: 24px;
  --checkbox-color: var(--primary);
  --checkbox-bg: rgba(124, 58, 237, 0.1);
  --checkbox-border: var(--border);

  position: relative;
  display: inline-block;
  cursor: pointer;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.ios-checkbox input {
  display: none;
}

.checkbox-wrapper {
  position: relative;
  width: var(--checkbox-size);
  height: var(--checkbox-size);
  border-radius: 6px;
  transition: transform 0.2s ease;
}

.checkbox-bg {
  position: absolute;
  inset: 0;
  border-radius: 6px;
  border: 2px solid var(--checkbox-border);
  background: transparent;
  transition: all 0.2s ease;
}

.checkbox-icon {
  position: absolute;
  inset: 0;
  margin: auto;
  width: 80%;
  height: 80%;
  color: white;
  transform: scale(0);
  transition: all 0.2s ease;
}

.check-path {
  stroke-dasharray: 40;
  stroke-dashoffset: 40;
  transition: stroke-dashoffset 0.3s ease 0.1s;
}

/* Checked State */
.ios-checkbox input:checked + .checkbox-wrapper .checkbox-bg {
  background: var(--checkbox-color);
  border-color: var(--checkbox-color);
}

.ios-checkbox input:checked + .checkbox-wrapper .checkbox-icon {
  transform: scale(1);
}

.ios-checkbox input:checked + .checkbox-wrapper .check-path {
  stroke-dashoffset: 0;
}

/* Hover Effects */
.ios-checkbox:hover .checkbox-wrapper {
  transform: scale(1.05);
}

/* Active Animation */
.ios-checkbox:active .checkbox-wrapper {
  transform: scale(0.95);
}

/* Focus Styles */
.ios-checkbox input:focus + .checkbox-wrapper .checkbox-bg {
  box-shadow: 0 0 0 4px var(--checkbox-bg);
}

/* Animation */
@keyframes bounce-checkbox {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.ios-checkbox input:checked + .checkbox-wrapper {
  animation: bounce-checkbox 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
"""

with open('admin/css/styles.css', 'a', encoding='utf-8') as f:
    f.write(css)
print('Appended CSS successfully.')
