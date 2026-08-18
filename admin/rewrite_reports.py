import re

with open('reports.html', 'r', encoding='utf-8') as f:
    html = f.read()

main_content = """
  <main class="main-content">
    <header class="page-header" style="margin-bottom: 28px; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <h1 class="page-title" style="font-size: 24px; font-weight: 700; background: linear-gradient(135deg, #c084fc 0%, #6366f1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">Monthly Attendance Report</h1>
        <p style="font-size: 13px; color: var(--text-muted); margin-top: 4px; margin-bottom: 0;">Institutional overview of faculty attendance.</p>
      </div>
      <div style="display: flex; align-items: center; gap: 12px;">
        <select id="report-month" class="filter-input" style="height:38px; border-radius:8px; padding: 0 12px;" onchange="loadReport()">
            <option value="1">January</option><option value="2">February</option><option value="3">March</option>
            <option value="4">April</option><option value="5">May</option><option value="6">June</option>
            <option value="7">July</option><option value="8">August</option><option value="9">September</option>
            <option value="10">October</option><option value="11">November</option><option value="12">December</option>
        </select>
        <input type="number" id="report-year" class="filter-input" style="height:38px; border-radius:8px; width:80px; padding: 0 12px;" value="2026" onchange="loadReport()">
        <button class="btn-primary" onclick="window.print()" style="margin: 0;">Print</button>
      </div>
    </header>

    <div class="table-wrapper" style="overflow-x: auto;">
      <table class="data-table" id="report-table">
        <thead id="report-thead">
          <tr><th>Teacher</th></tr>
        </thead>
        <tbody id="report-tbody">
          <tr><td class="td-loading"><div class="gear-loader"></div></td></tr>
        </tbody>
      </table>
    </div>
  </main>
"""

script_content = """
  <script src="js/app.js"></script>
  <script>
    async function loadReport() {
        const tbody = document.getElementById('report-tbody');
        const thead = document.getElementById('report-thead');
        tbody.innerHTML = '<tr><td class="td-loading" colspan="35"><div class="gear-loader"></div></td></tr>';
        
        const year = document.getElementById('report-year').value;
        const month = document.getElementById('report-month').value;
        
        const data = await api(`/admin/reports/monthly?year=${year}&month=${month}`);
        if (!data) return;
        
        // Build Header
        let theadHtml = '<tr><th style="min-width: 200px; position: sticky; left: 0; background: var(--surface-1); z-index: 2;">Teacher</th>';
        for(let d=1; d<=data.num_days; d++) {
            theadHtml += `<th style="min-width: 30px; text-align: center; padding: 8px 4px;">${d}</th>`;
        }
        theadHtml += '<th style="text-align:center;">Total P</th><th style="text-align:center;">Total A</th></tr>';
        thead.innerHTML = theadHtml;
        
        if (data.report.length === 0) {
            tbody.innerHTML = `<tr><td colspan="${data.num_days + 3}" style="text-align:center; color:var(--text-muted);">No data available</td></tr>`;
            return;
        }
        
        let tbodyHtml = '';
        data.report.forEach(row => {
            tbodyHtml += `<tr>`;
            tbodyHtml += `<td style="position: sticky; left: 0; background: var(--surface-1); z-index: 1;"><div style="font-weight:600;">${row.full_name}</div><div style="font-size:11px; color:var(--text-muted);">${row.reg_no}</div></td>`;
            for(let d=1; d<=data.num_days; d++) {
                const mark = row.days[d];
                let color = 'var(--text-muted)';
                if (mark === 'P') color = 'var(--primary)';
                if (mark === 'A') color = '#ef4444';
                if (mark === 'HD') color = '#f59e0b';
                tbodyHtml += `<td style="text-align: center; font-weight: 600; color: ${color}; padding: 8px 4px;">${mark}</td>`;
            }
            tbodyHtml += `<td style="text-align:center; font-weight:bold;">${row.present}</td><td style="text-align:center; font-weight:bold; color:#ef4444;">${row.absent}</td>`;
            tbodyHtml += `</tr>`;
        });
        tbody.innerHTML = tbodyHtml;
    }
    
    // Set current month/year
    const now = new Date();
    document.getElementById('report-month').value = now.getMonth() + 1;
    document.getElementById('report-year').value = now.getFullYear();

    initApp('reports', loadReport);
  </script>
</body>
</html>
"""

# Replace <main class="main-content">...</main>
html = re.sub(r'<main class="main-content">.*?</main>', main_content, html, flags=re.DOTALL)
# Replace <script src="js/app.js"></script>...</body></html>
html = re.sub(r'<script src="js/app.js"></script>.*</html>', script_content, html, flags=re.DOTALL)

with open('reports.html', 'w', encoding='utf-8') as f:
    f.write(html)
