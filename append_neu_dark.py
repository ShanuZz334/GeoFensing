css = """
.neu-button-dark {
  width: 100%;
  background: #212121 !important;
  border: 2px solid #212121 !important;
  border-radius: 6px !important;
  color: #fff !important;
  padding: 16px !important;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 6px 6px 10px rgba(0,0,0,1), 1px 1px 10px rgba(255, 255, 255, 0.15) !important;
  transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.neu-button-dark:active {
  transform: scale(0.98);
  box-shadow: 2px 2px 5px rgba(0,0,0,1), 0px 0px 5px rgba(255, 255, 255, 0.15) !important;
}
"""

with open('admin/css/styles.css', 'a', encoding='utf-8') as f:
    f.write(css)
print('Appended neu-button-dark successfully.')
