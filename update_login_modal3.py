import os
import re
import glob

css_to_append = """
/* Custom Uiverse Login Styles */
.custom-login-title {
  color: #fff;
  text-transform: uppercase;
  letter-spacing: 2px;
  display: block;
  font-weight: bold;
  font-size: x-large;
}

.custom-login-card {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 350px;
  width: 320px;
  flex-direction: column;
  gap: 35px;
  background: #1c1c1c;
  box-shadow: 16px 16px 32px #121212, -16px -16px 32px #262626;
  border-radius: 8px;
  padding-top: 30px;
}

.custom-inputBox {
  position: relative;
  width: 250px;
}

.custom-inputBox input {
  width: 100%;
  padding: 10px;
  outline: none;
  border: none;
  color: #fff;
  font-size: 1em;
  background: transparent;
  border-left: 2px solid #fff;
  border-bottom: 2px solid #fff;
  transition: 0.1s;
  border-bottom-left-radius: 8px;
}

.custom-inputBox span {
  margin-top: 5px;
  position: absolute;
  left: 0;
  transform: translateY(-4px);
  margin-left: 10px;
  padding: 10px;
  pointer-events: none;
  font-size: 12px;
  color: #fff;
  text-transform: uppercase;
  transition: 0.5s;
  letter-spacing: 3px;
  border-radius: 8px;
}

.custom-inputBox input:valid~span,
.custom-inputBox input:focus~span {
  transform: translateX(113px) translateY(-15px);
  font-size: 0.8em;
  padding: 5px 10px;
  background: var(--primary);
  letter-spacing: 0.2em;
  color: #fff;
  border: none;
}

.custom-inputBox input:valid,
.custom-inputBox input:focus {
  border: 2px solid var(--primary);
  border-radius: 8px;
}

.custom-enter {
  height: 45px;
  width: 120px;
  border-radius: 5px;
  border: 2px solid var(--primary);
  cursor: pointer;
  background-color: transparent;
  transition: 0.5s;
  text-transform: uppercase;
  font-size: 12px;
  letter-spacing: 2px;
  margin-bottom: 1em;
  color: var(--primary);
  font-weight: bold;
}

.custom-enter:hover {
  background-color: var(--primary);
  color: white;
}
"""

html_replacement = """  <!-- Admin Login Modal -->
  <div class="modal-overlay" id="login-modal">
    <div class="custom-login-card">
      <a class="custom-login-title">Log in</a>
      <div id="login-error" class="error-banner" style="display:none; width: 85%; margin-bottom: 0;"></div>
      
      <div class="custom-inputBox">
        <input type="text" id="admin-reg-no" required="required">
        <span class="user">Reg No</span>
      </div>

      <div class="custom-inputBox">
        <input type="password" id="admin-password" required="required">
        <span>Password</span>
      </div>

      <button id="btn-login" class="custom-enter" onclick="adminLogin()">Enter</button>
    </div>
  </div>"""

# Ensure CSS is appended if not already there
css_file = 'admin/css/styles.css'
with open(css_file, 'r', encoding='utf-8') as f:
    css_content = f.read()

if '.custom-login-card' not in css_content:
    with open(css_file, 'a', encoding='utf-8') as f:
        f.write(css_to_append)
    print("Appended custom login CSS to styles.css")

# Update all HTML files
for html_file in glob.glob('admin/*.html'):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Use regex to find and replace the entire login-modal div
    pattern = re.compile(r'<!-- Admin Login Modal -->.*?<div class="modal-overlay" id="login-modal">.*?</div>\s*</div>', re.DOTALL)
    
    if pattern.search(content):
        new_content = pattern.sub(html_replacement, content)
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated login modal in {html_file}")
    else:
        # Some files might not have the comment exactly, search loosely
        pattern2 = re.compile(r'<div class="modal-overlay" id="login-modal">.*?</div>\s*</div>', re.DOTALL)
        if pattern2.search(content):
            new_content = pattern2.sub(html_replacement.replace('<!-- Admin Login Modal -->\n  ', ''), content)
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated login modal loosely in {html_file}")
        else:
            print(f"login-modal not found in {html_file}")
