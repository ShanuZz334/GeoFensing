import re
import glob

css_to_append = """
/* ===== Uiverse Login (Rohankumar620) - Project Standard ===== */
.new-login-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.new-login-form {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 20px;
  padding: 65px 45px;
  border-radius: 15px;
  background-color: #212121;
  box-shadow: inset 2px 2px 10px rgba(0,0,0,1),
              inset -1px -1px 5px rgba(255, 255, 255, 0.08);
}

.new-login-form_details {
  font-size: 25px;
  font-weight: 600;
  padding-bottom: 10px;
  color: white;
  letter-spacing: 1px;
}

.new-login-input {
  width: 245px;
  min-height: 45px;
  color: #fff;
  outline: none;
  transition: 0.35s;
  padding: 0px 15px;
  background-color: #212121;
  border-radius: 6px;
  border: 2px solid #212121;
  font-size: 14px;
  box-shadow: 6px 6px 10px rgba(0,0,0,1),
              -1px -1px 10px rgba(255, 255, 255, 0.08);
}

.new-login-input::placeholder {
  color: #999;
}

.new-login-input:focus::placeholder {
  transition: 0.3s;
  opacity: 0;
}

.new-login-input:focus {
  transform: scale(1.05);
  border-color: var(--primary);
  box-shadow: 6px 6px 10px rgba(0,0,0,1),
              -1px -1px 10px rgba(255, 255, 255, 0.08),
              inset 2px 2px 10px rgba(0,0,0,1),
              inset -1px -1px 5px rgba(255, 255, 255, 0.08);
}

.new-login-btn {
  padding: 10px 35px;
  cursor: pointer;
  background-color: #212121;
  border-radius: 6px;
  border: 2px solid var(--primary);
  box-shadow: 6px 6px 10px rgba(0,0,0,1),
              -1px -1px 10px rgba(255, 255, 255, 0.08);
  color: #fff;
  font-size: 15px;
  font-weight: bold;
  transition: 0.35s;
  width: 100%;
  letter-spacing: 1px;
}

.new-login-btn:hover {
  transform: scale(1.05);
  background-color: var(--primary);
  box-shadow: 6px 6px 10px rgba(0,0,0,1),
              -1px -1px 10px rgba(255, 255, 255, 0.08),
              inset 2px 2px 10px rgba(0,0,0,1),
              inset -1px -1px 5px rgba(255, 255, 255, 0.08);
}

.new-login-btn:focus {
  transform: scale(1.05);
  background-color: var(--primary);
}
"""

html_replacement = """  <div class="modal-overlay" id="login-modal">
    <div class="new-login-container">
      <div class="new-login-form">
        <div class="new-login-form_details">Login</div>
        <div id="login-error" class="error-banner" style="display:none; width: 100%; margin: 0;"></div>
        <input type="text" id="admin-reg-no" class="new-login-input" placeholder="Reg No" required>
        <input type="password" id="admin-password" class="new-login-input" placeholder="Password" required>
        <button id="btn-login" class="new-login-btn" onclick="adminLogin()">Login</button>
      </div>
    </div>
  </div>"""

# Append CSS if not already present
css_file = 'admin/css/styles.css'
with open(css_file, 'r', encoding='utf-8') as f:
    css_content = f.read()

if '.new-login-container' not in css_content:
    with open(css_file, 'a', encoding='utf-8') as f:
        f.write(css_to_append)
    print("Appended new login CSS to styles.css")
else:
    print("CSS already present, skipping.")

# Update all HTML files
for html_file in glob.glob('admin/*.html'):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = re.compile(
        r'<div class="modal-overlay" id="login-modal">.*?</div>\s*</div>',
        re.DOTALL
    )
    if pattern.search(content):
        new_content = pattern.sub(html_replacement, content)
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated: {html_file}")
    else:
        print(f"No login-modal found in: {html_file}")
