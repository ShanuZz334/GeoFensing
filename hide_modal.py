import glob

for f in glob.glob('admin/*.html'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Add display:none to the login-modal so it doesn't flash on screen while JS loads
    content = content.replace('<div class="modal-overlay" id="login-modal">', '<div class="modal-overlay" id="login-modal" style="display: none;">')
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
