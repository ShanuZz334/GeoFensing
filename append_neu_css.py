css = """
/* ── Neumorphic Login Modal ───────────────────────────────────────────────── */
.neu-login-card {
  background: #1e1e1e !important;
  border: none !important;
  border-radius: 15px !important;
  padding: 48px 32px !important;
  box-shadow: 2px 2px 10px rgba(0,0,0,1), -1px -1px 5px rgba(255, 255, 255, 0.1) !important;
  max-width: 400px;
  width: 100%;
}

.neu-input-wrapper {
  margin-bottom: 24px;
}

.neu-input-wrapper label {
  display: block;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 8px;
}

.neu-input {
  width: 100%;
  background: #212121 !important;
  border: 2px solid #212121 !important;
  border-radius: 6px !important;
  color: #fff !important;
  padding: 16px !important;
  font-size: 14px;
  box-shadow: 6px 6px 10px rgba(0,0,0,1), 1px 1px 10px rgba(255, 255, 255, 0.15) !important;
  outline: none;
  transition: border-color 0.2s ease;
}

.neu-input::placeholder {
  color: #999 !important;
}

.neu-input:focus {
  border-color: var(--primary) !important;
}

.neu-button {
  width: 100%;
  background: var(--primary) !important;
  border: none !important;
  border-radius: 6px !important;
  color: #fff !important;
  padding: 16px !important;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 6px 6px 10px rgba(0,0,0,0.5), 1px 1px 10px rgba(124, 58, 237, 0.3) !important;
  transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.neu-button:active {
  transform: scale(0.98);
  box-shadow: 2px 2px 5px rgba(0,0,0,0.5), 0px 0px 5px rgba(124, 58, 237, 0.3) !important;
}
"""

with open('admin/css/styles.css', 'a', encoding='utf-8') as f:
    f.write(css)
print('Appended Neumorphic CSS successfully.')
