import re

# Read the file
with open('e:\\YORK.A\\Python codes2\\Antigrav\\geotutor\\client\\src\\components\\Sidebar.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the JSX comment on line 209
content = content.replace('{/* Teacher Access Code Dialog */ }', '{/* Teacher Access Code Dialog */}')

# Fix indentation - Dialog should be indented like other top-level JSX
content = content.replace('    <Dialog open={showCodeDialog}', '        <Dialog open={showCodeDialog}')
content = content.replace('    </Dialog>', '        </Dialog>')

# Write back
with open('e:\\YORK.A\\Python codes2\\Antigrav\\geotutor\\client\\src\\components\\Sidebar.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed Sidebar.tsx JSX comment syntax")
