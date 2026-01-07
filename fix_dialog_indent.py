import re

# Read the file
with open(r'e:\YORK.A\Python codes2\Antigrav\geotutor\client\src\components\Sidebar.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the incorrect indentation pattern
# Line 210 should have 8 spaces before <Dialog, not 4
content = content.replace('    <Dialog open={showCodeDialog}', '        <Dialog open={showCodeDialog}')

# Also fix closing tag
content = content.replace('    </Dialog>', '        </Dialog>')

# Write back
with open(r'e:\YORK.A\Python codes2\Antigrav\geotutor\client\src\components\Sidebar.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed Dialog indentation from 4 spaces to 8 spaces")
