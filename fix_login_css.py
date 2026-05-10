import re

css_file = 'admin/css/styles.css'
with open(css_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace everything from .new-login-form to the end of .new-login-btn:focus
pattern = re.compile(r'\.new-login-form \{.*?\.new-login-btn:focus \{.*?\}', re.DOTALL)

new_css = """.new-login-form {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
  padding: 48px 40px 40px;
  border-radius: 18px;
  background: #1a1a1a;
  border: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.8),
              inset 0 1px 0 rgba(255, 255, 255, 0.06);
  min-width: 320px;
}

.new-login-form_details {
  font-size: 26px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.5px;
  margin-bottom: 6px;
}

.new-login-input {
  width: 100%;
  min-height: 46px;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  outline: none;
  transition: border-color 0.25s, box-shadow 0.25s;
  padding: 0 14px;
  background: #242424 !important;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 14px;
  font-family: inherit;
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.5);
}

/* Kill browser autofill white/blue override */
.new-login-input:-webkit-autofill,
.new-login-input:-webkit-autofill:hover,
.new-login-input:-webkit-autofill:focus {
  -webkit-box-shadow: 0 0 0px 1000px #242424 inset !important;
  -webkit-text-fill-color: #ffffff !important;
  caret-color: #ffffff;
  border-color: rgba(255, 255, 255, 0.1);
  transition: background-color 5000s ease-in-out 0s;
}

.new-login-input::placeholder {
  color: #555;
}

.new-login-input:focus::placeholder {
  opacity: 0;
  transition: opacity 0.2s;
}

.new-login-input:focus {
  border-color: var(--primary);
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.5),
              0 0 0 3px rgba(124, 58, 237, 0.2);
}

.new-login-btn {
  width: 100%;
  padding: 12px;
  cursor: pointer;
  background: transparent;
  border-radius: 8px;
  border: 2px solid var(--primary);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  letter-spacing: 0.5px;
  transition: background 0.25s, box-shadow 0.25s, transform 0.15s;
  margin-top: 4px;
}

.new-login-btn:hover {
  background: var(--primary);
  box-shadow: 0 4px 20px rgba(124, 58, 237, 0.4);
  transform: translateY(-1px);
}

.new-login-btn:active {
  transform: translateY(0);
}

.new-login-btn:focus {
  background: var(--primary);
  outline: none;
}"""

if pattern.search(content):
    new_content = pattern.sub(new_css, content)
    with open(css_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS: Login CSS replaced cleanly")
else:
    print("Pattern not found, trying manual approach...")
    # Try a simpler approach - find the start and end line numbers
    lines = content.split('\n')
    start_idx = None
    end_idx = None
    brace_depth = 0
    in_block = False
    
    for i, line in enumerate(lines):
        if '.new-login-form {' in line and start_idx is None:
            start_idx = i
            print(f"Found start at line {i+1}: {line.strip()}")
        if '.new-login-btn:focus {' in line:
            in_block = True
        if in_block:
            if '{' in line:
                brace_depth += line.count('{')
            if '}' in line:
                brace_depth -= line.count('}')
                if brace_depth <= 0:
                    end_idx = i
                    print(f"Found end at line {i+1}")
                    break
    
    if start_idx and end_idx:
        lines[start_idx:end_idx+1] = new_css.split('\n')
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print("SUCCESS via manual approach")
    else:
        print(f"Failed: start_idx={start_idx}, end_idx={end_idx}")

# Also inject the #login-modal override if not present
with open(css_file, 'r', encoding='utf-8') as f:
    content2 = f.read()

if '#login-modal {' not in content2:
    modal_override = """
/* Override backdrop blur for login modal */
#login-modal {
  backdrop-filter: none;
  background: rgba(0, 0, 0, 0.88);
}

.new-login-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

"""
    # Insert before .new-login-form
    content2 = content2.replace('.new-login-form {', modal_override + '.new-login-form {', 1)
    with open(css_file, 'w', encoding='utf-8') as f:
        f.write(content2)
    print("Added #login-modal override")
