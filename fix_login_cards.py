import os, re

CLEAN_CARD_INNER = '''    <div style="
      width: 360px;
      padding: 40px 28px;
      border-radius: 20px;
      background: #1c1c1c;
      border: 1px solid rgba(255,255,255,0.07);
      box-shadow: 0 32px 64px rgba(0,0,0,0.7);
      text-align: center;
    ">
      <h2 style="font-size: 24px; font-weight: 700; color: #fff; margin-bottom: 28px;">Login</h2>
      <div id="login-error" class="error-banner" style="display:none; margin-bottom:16px;"></div>

      <div style="margin-bottom: 16px;">
        <input type="text" id="admin-reg-no" placeholder="Registration Number" style="
          width: 100%; padding: 13px 16px; border: none; border-radius: 10px;
          background: #2a2a2a;
          color: #e0e0e0; font-size: 14px; outline: none;
          box-sizing: border-box; font-family: inherit;
        " />
      </div>

      <div style="margin-bottom: 24px; position: relative;">
        <input type="password" id="admin-password" placeholder="Password" style="
          width: 100%; padding: 13px 46px 13px 16px; border: none; border-radius: 10px;
          background: #2a2a2a;
          color: #e0e0e0; font-size: 14px; outline: none;
          box-sizing: border-box; font-family: inherit;
        " />
        <button type="button" onclick="togglePasswordVisibility()" style="
          position: absolute; right: 13px; top: 50%; transform: translateY(-50%);
          background: none; border: none; cursor: pointer; color: #777; padding: 4px;
        ">
          <svg id="eye-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </button>
      </div>

      <button id="btn-login" onclick="adminLogin()" style="
        width: 100%; padding: 13px; border: none; border-radius: 10px; cursor: pointer;
        background: #2a2a2a;
        border: 1px solid rgba(255,255,255,0.06);
        color: #fff; font-size: 15px; font-weight: 700;
        transition: background 0.2s;
      " onmouseover="this.style.background='#333'" onmouseout="this.style.background='#2a2a2a'">
        Login
      </button>
    </div>'''

TOGGLE_SCRIPT = '''  <script>
  function togglePasswordVisibility() {
    const pw = document.getElementById('admin-password');
    const icon = document.getElementById('eye-icon');
    if (pw.type === 'password') {
      pw.type = 'text';
      icon.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';
    } else {
      pw.type = 'password';
      icon.innerHTML = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
    }
  }
  </script>'''

for fn in ['admin/index.html', 'admin/logs.html']:
    with open(fn, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find id="login-modal" and replace inner content of its child div
    # Strategy: find the modal overlay, then replace what's inside it
    # Replace everything between <div class="modal-overlay" id="login-modal"> ... </div>\n</div>
    
    # First, remove any old togglePasswordVisibility script block
    content = re.sub(
        r'\s*<script>\s*function togglePasswordVisibility\(\).*?</script>',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Now find and replace the inner content of login-modal
    def replace_modal(m):
        return f'  <div class="modal-overlay" id="login-modal">\n{CLEAN_CARD_INNER}\n  </div>\n{TOGGLE_SCRIPT}'
    
    content = re.sub(
        r'<div class="modal-overlay" id="login-modal">.*?</div>\s*</div>',
        replace_modal,
        content,
        flags=re.DOTALL
    )
    
    with open(fn, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Fixed {fn}")
