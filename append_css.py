css = """
/* ── Custom Toggle Switch ────────────────────────────────────────── */
.switch {
  font-size: 14px;
  position: relative;
  display: inline-block;
  width: 3.5em;
  height: 2em;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.1);
  transition: .4s;
  border-radius: 10px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 1.4em;
  width: 1.4em;
  border-radius: 8px;
  left: 0.3em;
  bottom: 0.3em;
  transform: rotate(270deg);
  background-color: rgb(255, 255, 255);
  transition: .4s;
}

.switch input:checked + .slider {
  background-color: var(--primary);
}

.switch input:focus + .slider {
  box-shadow: 0 0 1px var(--primary);
}

.switch input:checked + .slider:before {
  transform: translateX(1.5em);
}
"""

with open('admin/css/styles.css', 'a', encoding='utf-8') as f:
    f.write(css)
print('Appended CSS successfully.')
