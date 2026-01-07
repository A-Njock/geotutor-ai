import re

# Read the file
with open(r'e:\YORK.A\Python codes2\Antigrav\geotutor\client\src\components\Sidebar.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the Dialog section (around line 209-255) and fix indentation
new_lines = []
in_dialog = False
for i, line in enumerate(lines):
    line_num = i + 1
    
    # Fix the comment on line 209
    if line_num == 209:
        new_lines.append('        {/* Teacher Access Code Dialog */}\r\n')
        in_dialog = True
    # Fix Dialog opening tag (line 210) - should be 8 spaces
    elif line_num == 210 and line.strip().startswith('<Dialog'):
        new_lines.append('        <Dialog open={showCodeDialog} onOpenChange={setShowCodeDialog}>\r\n')
    # Fix Dialog children - they should maintain relative indentation but Dialog itself is at 8 spaces
    elif 210 < line_num < 255:
        # These lines had 4-space base indent, change to 8-space
        if line.startswith('    ') and not line.startswith('        '):
            new_lines.append('    ' + line)  # Add 4 more spaces
        else:
            new_lines.append(line)
    # Fix Dialog closing tag (line 255)
    elif line_num == 255 and line.strip() == '</Dialog>':
        new_lines.append('        </Dialog>\r\n')
    else:
        new_lines.append(line)

# Write back
with open(r'e:\YORK.A\Python codes2\Antigrav\geotutor\client\src\components\Sidebar.tsx', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Fixed Sidebar.tsx indentation for Dialog component (lines 209-255)")
print("Dialog is now properly indented as part of the return statement")
