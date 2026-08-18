import os

filepath = r"C:\project\ALLBACKUP\GeoFense\admin\teachers.html"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

js_code = """
    // Faculty Details Modal Logic
    let currentFacultyData = [];
    
    // Override loadFaculty to store current data
    const originalLoadFaculty = loadFaculty;
    loadFaculty = async function(page = 1) {
      await originalLoadFaculty(page);
      // Wait a moment for DOM to update
      setTimeout(() => {
        // Add row clicks
        const tbody = document.getElementById('teachers-tbody');
        if (tbody) {
          const rows = tbody.querySelectorAll('tr');
          rows.forEach((row, index) => {
            if (row.querySelector('.td-loading')) return;
            const actionTd = row.querySelector('td:last-child');
            if (actionTd) {
              actionTd.onclick = (e) => e.stopPropagation();
            }
            row.style.cursor = 'pointer';
            row.classList.add('hover-row');
            // Extract reg_no from the first column code tag to find the faculty
            const codeTag = row.querySelector('.reg-id-code');
            if (codeTag) {
              const regNo = codeTag.textContent.trim();
              row.onclick = () => openFacultyDetailsByReg(regNo);
            }
          });
        }
      }, 100);
    };

    async function openFacultyDetailsByReg(regNo) {
      // Find faculty by regNo in the current table data
      // We don't have currentFacultyData saved easily because displayFaculty doesn't store it.
      // So we fetch it from the API again, or we can just fetch the specific faculty stats and use DOM for name.
      // Actually, let's fetch the list again or just find it if we can.
      // Better yet, modify displayFaculty to set an onclick directly!
    }

    async function openFacultyDetails(facultyId) {
      const modal = document.getElementById('faculty-details-modal');
      const nameEl = document.getElementById('fd-name');
      const regEl = document.getElementById('fd-reg');
      const deptEl = document.getElementById('fd-dept');
      const emailEl = document.getElementById('fd-email');
      const faceEl = document.getElementById('fd-face');
      const statusEl = document.getElementById('fd-status');
      const photoEl = document.getElementById('fd-photo');
      const leavesTakenEl = document.getElementById('fd-leaves-taken');
      const cutPctEl = document.getElementById('fd-cut-pct');
      
      // Reset values
      leavesTakenEl.textContent = '...';
      cutPctEl.textContent = '...';
      
      // Get basic details from the API
      // Wait, we need to fetch the faculty list or get it from global state
      const url = `/admin/teachers?page=1&per_page=1000`; // Hacky way to find them
      try {
        // Find the specific faculty from the DOM
        const btn = document.querySelector(`button[onclick*="showEditModal('${facultyId}')"]`);
        if (btn) {
           const tr = btn.closest('tr');
           if (tr) {
              const cells = tr.querySelectorAll('td');
              regEl.textContent = cells[0].textContent.trim();
              const nameContainer = cells[1].querySelector('strong');
              nameEl.textContent = nameContainer ? nameContainer.textContent : 'Unknown';
              const img = cells[1].querySelector('img');
              photoEl.src = img ? img.src : 'images/default-avatar.svg';
              emailEl.textContent = cells[2].textContent.trim();
              deptEl.textContent = cells[3].textContent.trim();
              faceEl.textContent = cells[4].textContent.includes('Yes') ? 'Yes' : 'No';
              statusEl.textContent = cells[5].textContent.includes('Active') ? 'Active' : 'Inactive';
           }
        }
        
        modal.style.display = 'flex';
        
        // Fetch stats
        const res = await api(`/admin/teachers/${facultyId}/stats`);
        if (res) {
          leavesTakenEl.textContent = res.leaves_taken || 0;
          cutPctEl.textContent = (res.cut_pct || 0) + '%';
        }
      } catch (e) {
        console.error("Error opening faculty details", e);
      }
    }

    async function shareFacultyCard() {
      const card = document.getElementById('faculty-card-capture');
      if (!card) return;
      
      try {
        const canvas = await html2canvas(card, {
          backgroundColor: '#0f172a', // var(--bg)
          scale: 2, // High res
          useCORS: true
        });
        
        canvas.toBlob(async (blob) => {
          if (!blob) {
            showToast('Failed to generate image', 'error');
            return;
          }
          
          const name = document.getElementById('fd-name').textContent.replace(/\\s+/g, '_');
          const file = new File([blob], `Faculty_${name}.png`, { type: 'image/png' });
          
          if (navigator.canShare && navigator.canShare({ files: [file] })) {
            try {
              await navigator.share({
                title: 'Faculty Details',
                text: 'Here are the details for ' + name,
                files: [file]
              });
            } catch (err) {
              console.log('Share cancelled or failed', err);
              downloadCard(blob, name);
            }
          } else {
            downloadCard(blob, name);
          }
        }, 'image/png');
      } catch (err) {
        console.error('Error creating image', err);
        showToast('Failed to create image', 'error');
      }
    }
    
    function downloadCard(blob, name) {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Faculty_${name}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
"""

# Modify displayFaculty to add the onclick directly to the TR
old_tr = "<tr>\n            <td><code class=\"reg-id-code\">${escHtml(t.reg_no || '—')}</code></td>"
new_tr = "<tr onclick=\"openFacultyDetails('${t.teacher_id}')\" style=\"cursor:pointer\" class=\"hover-row\">\n            <td><code class=\"reg-id-code\">${escHtml(t.reg_no || '—')}</code></td>"

old_td = "<td>\n              <div style=\"display:flex; gap:6px;\">"
new_td = "<td onclick=\"event.stopPropagation()\">\n              <div style=\"display:flex; gap:6px;\">"

if old_tr in content:
    content = content.replace(old_tr, new_tr)
    content = content.replace(old_td, new_td)
    print("Injected onclick into displayFaculty")
else:
    print("Could not find displayFaculty TR to replace")

if "async function openFacultyDetails" not in content:
    # Inject before </script>
    content = content.replace("</script>\n</body>", js_code + "\n</script>\n</body>")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Injected JS logic into teachers.html")
else:
    print("JS logic already exists")

