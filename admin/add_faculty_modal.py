import os

modal_html = """
  <!-- Faculty Details Modal -->
  <div class="modal-overlay" id="faculty-details-modal" style="display: none;">
    <div class="modal-card" style="max-width: 450px; padding: 24px; position: relative;">
      <button class="btn-icon" onclick="document.getElementById('faculty-details-modal').style.display='none'" style="position: absolute; top: 16px; right: 16px; z-index: 10;">✕</button>
      
      <div id="faculty-card-capture" style="background: var(--surface-1); border-radius: 12px; padding: 20px; text-align: center; border: 1px solid var(--border);">
        <div style="margin-bottom: 16px;">
          <img id="fd-photo" src="images/default-avatar.svg" alt="Faculty" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid var(--primary); padding: 2px;">
        </div>
        
        <h2 id="fd-name" style="font-size: 20px; font-weight: 700; margin-bottom: 4px; color: var(--text);">Name</h2>
        <div id="fd-reg" style="font-size: 14px; color: var(--primary); font-family: monospace; margin-bottom: 12px; font-weight: 600;">REG123</div>
        
        <div style="display: flex; flex-direction: column; gap: 8px; text-align: left; background: var(--surface-2); padding: 16px; border-radius: 8px; margin-bottom: 16px;">
          <div style="display: flex; justify-content: space-between;">
            <span style="color: var(--text-muted); font-size: 13px;">Department</span>
            <span id="fd-dept" style="font-size: 13px; font-weight: 500; color: var(--text);">CSE</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span style="color: var(--text-muted); font-size: 13px;">Email</span>
            <span id="fd-email" style="font-size: 13px; font-weight: 500; color: var(--text);">email@example.com</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span style="color: var(--text-muted); font-size: 13px;">Face Encoded</span>
            <span id="fd-face" style="font-size: 13px; font-weight: 600;">Yes</span>
          </div>
          <div style="display: flex; justify-content: space-between;">
            <span style="color: var(--text-muted); font-size: 13px;">Status</span>
            <span id="fd-status" style="font-size: 13px; font-weight: 600;">Active</span>
          </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2); padding: 12px; border-radius: 8px;">
            <div style="font-size: 24px; font-weight: 700; color: #10b981;" id="fd-leaves-taken">0</div>
            <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">Leaves Taken</div>
          </div>
          <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2); padding: 12px; border-radius: 8px;">
            <div style="font-size: 24px; font-weight: 700; color: #f59e0b;" id="fd-cut-pct">0%</div>
            <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">Salary Cut</div>
          </div>
        </div>
      </div>
      
      <button class="btn-primary btn-full" style="margin-top: 16px; display: flex; align-items: center; justify-content: center; gap: 8px;" onclick="shareFacultyCard()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path><polyline points="16 6 12 2 8 6"></polyline><line x1="12" y1="2" x2="12" y2="15"></line></svg>
        Share / Download Card
      </button>
    </div>
  </div>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
"""

filepath = r"C:\project\ALLBACKUP\GeoFense\admin\teachers.html"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Insert before <script src="js/api.js?v=1028"></script>
insertion_point = '<script src="js/api.js?v=1028"></script>'
if insertion_point in content and "id=\"faculty-details-modal\"" not in content:
    new_content = content.replace(insertion_point, modal_html + "\n  " + insertion_point)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Injected modal HTML into teachers.html")
else:
    print("Could not find insertion point or modal already exists")
