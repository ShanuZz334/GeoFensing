import os
import re

NAVBAR_HTML = """  <!-- -- Navbar ------------------------------------------------------- -->
  <nav class="navbar" id="navbar">
    <div class="navbar-left">
      <div class="navbar-logo">
        <div class="logo-icon">
          <img src="images/logo.png?v=6" alt="GeoFace Logo">
        </div>
        <span>Geo<span class="face-text">Face</span></span>
      </div>
      <div class="navbar-nav">
        <a href="index.html" class="nav-item{index_active}" id="nav-dashboard">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"/></svg>
          Dashboard
        </a>
        <a href="teachers.html" class="nav-item{teachers_active}" id="nav-teachers">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"/></svg>
          Teachers
        </a>
        <a href="logs.html" class="nav-item{logs_active}" id="nav-logs">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z"/></svg>
          Scans
        </a>
        <a href="audit.html" class="nav-item{audit_active}" id="nav-audit">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/></svg>
          Reports
        </a>
        <a href="map.html" class="nav-item{map_active}" id="nav-map">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 6.75V15m6-6v8.25m.503-3.46c.453-.172.806-.5 1.026-.915a2.25 2.25 0 00-.834-2.923c-.426-.258-.87-.492-1.32-.7l-.156-.07a2.25 2.25 0 01-1.055-1.94V4.5c0-.621-.504-1.125-1.125-1.125h-3c-.621 0-1.125.504-1.125 1.125v1.233c0 .822-.443 1.577-1.157 1.986l-.117.067a2.25 2.25 0 01-1.2 2.01c-.266.136-.534.275-.802.417a2.25 2.25 0 00-.81 3.01c.25.438.613.79 1.06 1.02a2.25 2.25 0 011.023 1.94V19.5c0 .621.504 1.125 1.125 1.125h3c.621 0 1.125-.504 1.125-1.125v-1.233c0-.822.443-1.577 1.157-1.986l.117-.067a2.25 2.25 0 011.2-2.01z"/></svg>
          Map
        </a>
        <a href="settings.html" class="nav-item{settings_active}" id="nav-settings">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
          Settings
        </a>
      </div>
    </div>
    
    <div class="navbar-right">
      <div class="nav-bell" onclick="window.location.href='alerts.html'">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
        </svg>
        <span class="nav-bell-badge" id="navbar-alert-badge" style="display:none;">0</span>
      </div>
      
      <div class="nav-profile">
        <img src="images/default-avatar.png" alt="Admin" class="nav-profile-pic" id="nav-profile-pic" onerror="this.src='data:image/svg+xml;charset=UTF-8,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' viewBox=\\'0 0 24 24\\' fill=\\'none\\' stroke=\\'currentColor\\' stroke-width=\\'2\\' stroke-linecap=\\'round\\' stroke-linejoin=\\'round\\'%3E%3Cpath d=\\'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2\\'/%3E%3Ccircle cx=\\'12\\' cy=\\'7\\' r=\\'4\\'/%3E%3C/svg%3E'">
        <div class="nav-profile-info">
          <span class="nav-profile-name" id="nav-profile-name">Admin</span>
          <span class="nav-profile-role" id="nav-profile-role">Administrator</span>
        </div>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg>
        
        <div class="nav-dropdown">
          <a href="admins.html" class="nav-dropdown-item" id="nav-manage-admins" style="display:none;">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0z" /></svg>
            Manage Admins
          </a>
          <div class="nav-dropdown-divider" id="nav-manage-admins-divider" style="display:none;"></div>
          <a href="#" class="nav-dropdown-item" onclick="adminSignOut()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" /></svg>
            Sign Out
          </a>
        </div>
      </div>
    </div>
  </nav>"""

# Files to update
files = ['index.html', 'alerts.html', 'teachers.html', 'logs.html', 'map.html', 'admins.html', 'audit.html', 'settings.html']
base_dir = r"c:\\project\\ALLBACKUP\\GeoFense\\admin"

for f in files:
    filepath = os.path.join(base_dir, f)
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # We use a pattern that strictly finds <aside class="sidebar" id="sidebar"> ... </aside>
    pattern = re.compile(r'<aside class="sidebar" id="sidebar">.*?</aside>', re.DOTALL)
    
    # Generate the navbar string with the correct active class
    nav_str = NAVBAR_HTML.format(
        index_active='',
        teachers_active=' active' if f == 'teachers.html' else '',
        logs_active=' active' if f == 'logs.html' else '',
        audit_active=' active' if f == 'audit.html' else '',
        map_active=' active' if f == 'map.html' else '',
        settings_active=' active' if f == 'settings.html' else ''
    )
    
    new_content = pattern.sub(nav_str, content)
    
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(new_content)
        
print("Updated all html files successfully.")
