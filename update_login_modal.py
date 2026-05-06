import os, re

NEW_LOGIN = '''  <!-- Admin Login Modal (Neumorphic) -->
  <div class="modal-overlay" id="login-modal">
    <div style="
      width: 380px;
      padding: 40px 32px;
      border-radius: 24px;
      background: #1a1a2e;
      box-shadow: 12px 12px 24px #0d0d1a, -12px -12px 24px #272742, inset 0 0 0 1px rgba(255,255,255,0.04);
      text-align: center;
    ">
      <h2 style="font-size: 26px; font-weight: 700; color: #fff; margin-bottom: 32px; letter-spacing: 0.5px;">Login</h2>
      <div id="login-error" class="error-banner" style="display:none; margin-bottom:16px;"></div>

      <div style="margin-bottom: 20px;">
        <input type="text" id="admin-reg-no" placeholder="Registration Number" style="
          width: 100%; padding: 14px 18px; border: none; border-radius: 12px;
          background: #12121f;
          box-shadow: inset 4px 4px 8px #0a0a15, inset -4px -4px 8px #1e1e33;
          color: #e0e0e0; font-size: 14px; outline: none;
          box-sizing: border-box;
        " />
      </div>

      <div style="margin-bottom: 28px; position: relative;">
        <input type="password" id="admin-password" placeholder="Password" style="
          width: 100%; padding: 14px 48px 14px 18px; border: none; border-radius: 12px;
          background: #12121f;
          box-shadow: inset 4px 4px 8px #0a0a15, inset -4px -4px 8px #1e1e33;
          color: #e0e0e0; font-size: 14px; outline: none;
          box-sizing: border-box;
        " />
        <button type="button" onclick="togglePasswordVisibility()" style="
          position: absolute; right: 14px; top: 50%; transform: translateY(-50%);
          background: none; border: none; cursor: pointer; color: #666; padding: 4px;
        ">
          <svg id="eye-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </button>
      </div>

      <button id="btn-login" onclick="adminLogin()" style="
        width: 100%; padding: 14px; border: none; border-radius: 12px; cursor: pointer;
        background: #1a1a2e;
        box-shadow: 6px 6px 12px #0d0d1a, -6px -6px 12px #272742;
        color: #fff; font-size: 15px; font-weight: 700; letter-spacing: 0.5px;
        transition: all 0.2s;
      " onmouseover="this.style.boxShadow='inset 4px 4px 8px #0d0d1a, inset -4px -4px 8px #272742'" onmouseout="this.style.boxShadow='6px 6px 12px #0d0d1a, -6px -6px 12px #272742'">
        Login
      </button>
    </div>
  </div>

  <script>
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

admin_dir = 'admin'
for fn in os.listdir(admin_dir):
    if not fn.endswith('.html'):
        continue
    fp = os.path.join(admin_dir, fn)
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Match the old login modal block
    pattern = r'  <!-- (?:Admin )?Login Modal[^>]*-->.*?</div>\s*</div>'
    # Need to be more specific - find modal with id="login-modal"
    pattern = r'  <(?:!-- (?:Admin )?Login Modal.*?-->)\s*<div class="modal-overlay" id="login-modal">.*?</div>\s*</div>\s*</div>'
    
    match = re.search(pattern, content, re.DOTALL)
    if match:
        content = content[:match.start()] + NEW_LOGIN + content[match.end():]
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {fn}")
    else:
        # Try alternate pattern
        pattern2 = r'<div class="modal-overlay" id="login-modal">.*?</div>\s*</div>\s*</div>'
        match2 = re.search(pattern2, content, re.DOTALL)
        if match2:
            # Check if there's a comment before it
            start = match2.start()
            before = content[max(0,start-80):start]
            comment_match = re.search(r'  <!-- .*?Login.*?-->\s*$', before)
            if comment_match:
                start = start - len(before) + comment_match.start()
            content = content[:start] + NEW_LOGIN + content[match2.end():]
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {fn} (alt)")
        else:
            print(f"SKIP {fn} - no login modal found")
