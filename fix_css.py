import re
with open(r'admin/css/styles.css', 'r', encoding='utf-8') as f:
    css = f.read()

broken_css = """  display: inline-block;
  width: 3.5em;
  height: 2em;
}

.uiverse-switch input {"""

fixed_css = """  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.uiverse-option:hover {
  background-color: var(--surface-3);
  color: white;
}

.uiverse-options input[type="radio"] {
  display: none;
}

.uiverse-options input[type="checkbox"] {
  appearance: none;
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid #8e8e93;
  outline: none;
  cursor: pointer;
  margin-right: 8px;
  vertical-align: middle;
  background-color: transparent;
  display: inline-block;
  position: relative;
  top: 3px;
}

.uiverse-options input[type="checkbox"]:checked {
  background-color: #8b5cf6;
  border-color: #8b5cf6;
  box-shadow: inset 0 0 0 3px #1c1c1e;
}

.uiverse-options label {
  display: inline-block;
  vertical-align: middle;
}

/* Hide the option label if it is checked (optional, but requested by Uiverse CSS originally) */
.uiverse-options input[type="radio"]:checked+label {
  display: none;
}

/* Custom Uiverse Toggle Switch */
.uiverse-switch {
  font-size: 10px;
  position: relative;
  display: inline-block;
  width: 3.5em;
  height: 2em;
}

.uiverse-switch input {"""

if broken_css in css:
    css = css.replace(broken_css, fixed_css)
    with open(r'admin/css/styles.css', 'w', encoding='utf-8') as f:
        f.write(css)
    print("Fixed CSS!")
else:
    print("Broken CSS not found.")
