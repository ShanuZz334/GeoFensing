import re

with open(r'admin/map.html', 'r', encoding='utf-8') as f:
    html = f.read()

target = """              <div class="uiverse-options">
                <div title="Select School / Department"><input id="sd-none" value="" name="sub-dept-checkbox" type="checkbox" style="display:none;"><label class="uiverse-option" for="sd-none">Select School / Department</label></div>
                <div title="School of Computer Science &amp; Engineering (CSE)"><input id="sd-cse" value="School of Computer Science &amp; Engineering (CSE)" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-cse">School of Computer Science &amp; Engineering (CSE)</label></div>
                <div title="School of Engineering"><input id="sd-eng" value="School of Engineering" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-eng">School of Engineering</label></div>
                <div title="Mittal School of Business / Management &amp; Commerce"><input id="sd-biz" value="Mittal School of Business / Management &amp; Commerce" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-biz">Mittal School of Business / Management &amp; Commerce</label></div>
                <div title="School of Agriculture"><input id="sd-agr" value="School of Agriculture" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-agr">School of Agriculture</label></div>
                <div title="School of Pharmacy / Pharmaceutical Sciences"><input id="sd-phm" value="School of Pharmacy / Pharmaceutical Sciences" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-phm">School of Pharmacy / Pharmaceutical Sciences</label></div>
                <div title="School of Law"><input id="sd-law" value="School of Law" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-law">School of Law</label></div>
                <div title="School of Architecture &amp; Design"><input id="sd-arc" value="School of Architecture &amp; Design" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-arc">School of Architecture &amp; Design</label></div>
                <div title="School of Hotel Management &amp; Tourism"><input id="sd-hot" value="School of Hotel Management &amp; Tourism" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-hot">School of Hotel Management &amp; Tourism</label></div>
                <div title="School of Humanities &amp; Social Sciences"><input id="sd-hum" value="School of Humanities &amp; Social Sciences" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-hum">School of Humanities &amp; Social Sciences</label></div>
                <div title="School of Sciences"><input id="sd-sci" value="School of Sciences" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-sci">School of Sciences</label></div>
                <div title="School of Media, Animation &amp; Multimedia"><input id="sd-med" value="School of Media, Animation &amp; Multimedia" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-med">School of Media, Animation &amp; Multimedia</label></div>
                <div title="School of Education &amp; Physical Education"><input id="sd-edu" value="School of Education &amp; Physical Education" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-edu">School of Education &amp; Physical Education</label></div>
                <div title="School of Allied Medical Sciences / Physiotherapy"><input id="sd-meds" value="School of Allied Medical Sciences / Physiotherapy" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-meds">School of Allied Medical Sciences / Physiotherapy</label></div>
                <div title="School of Computer Applications &amp; IT"><input id="sd-it" value="School of Computer Applications &amp; IT" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-it">School of Computer Applications &amp; IT</label></div>
              </div>"""

replacement = """              <div class="uiverse-options">
                <div title="Select School / Department"><input id="sd-none" value="" name="sub-dept-checkbox" type="checkbox" style="display:none;"><label class="uiverse-option" for="sd-none">Select School / Department</label></div>
                <div title="School of Computer Science &amp; Engineering (CSE)"><input id="sd-cse" value="CSE" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-cse">CSE</label></div>
                <div title="School of Engineering"><input id="sd-eng" value="Engineering" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-eng">Engineering</label></div>
                <div title="Mittal School of Business / Management &amp; Commerce"><input id="sd-biz" value="Business" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-biz">Business</label></div>
                <div title="School of Agriculture"><input id="sd-agr" value="Agriculture" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-agr">Agriculture</label></div>
                <div title="School of Pharmacy / Pharmaceutical Sciences"><input id="sd-phm" value="Pharmacy" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-phm">Pharmacy</label></div>
                <div title="School of Law"><input id="sd-law" value="Law" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-law">Law</label></div>
                <div title="School of Architecture &amp; Design"><input id="sd-arc" value="Architecture" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-arc">Architecture</label></div>
                <div title="School of Hotel Management &amp; Tourism"><input id="sd-hot" value="Hotel Management" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-hot">Hotel Management</label></div>
                <div title="School of Humanities &amp; Social Sciences"><input id="sd-hum" value="Humanities" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-hum">Humanities</label></div>
                <div title="School of Sciences"><input id="sd-sci" value="Sciences" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-sci">Sciences</label></div>
                <div title="School of Media, Animation &amp; Multimedia"><input id="sd-med" value="Media" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-med">Media</label></div>
                <div title="School of Education &amp; Physical Education"><input id="sd-edu" value="Education" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-edu">Education</label></div>
                <div title="School of Allied Medical Sciences / Physiotherapy"><input id="sd-meds" value="Medical Sciences" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-meds">Medical Sciences</label></div>
                <div title="School of Computer Applications &amp; IT"><input id="sd-it" value="IT" name="sub-dept-checkbox" type="checkbox"><label class="uiverse-option" for="sd-it">IT</label></div>
              </div>"""

if target in html:
    html = html.replace(target, replacement)
    with open(r'admin/map.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Replaced dropdown successfully!")
else:
    print("Target not found.")
