with open(r'admin/css/styles.css', 'a', encoding='utf-8') as f:
    f.write('''
/* Multi-select item layout for map sub-polygon */
.multi-select-item {
  display: flex;
  align-items: center;
  padding: 8px 10px;
  cursor: pointer;
  border-radius: 5px;
  transition: 300ms;
}

.multi-select-item:hover {
  background-color: var(--surface-3);
  color: white;
}

.multi-select-item label {
  cursor: pointer;
  margin: 0;
  padding: 0;
  width: auto;
  font-size: 14px;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.multi-select-item:hover label {
  color: white;
}
''')
print("Appended CSS successfully!")
