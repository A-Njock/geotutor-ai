import sys

# Read the file
with open('e:\\YORK.A\\Python codes2\\Antigrav\\geotutor\\server\\routers.ts', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Delete lines 151-170 (0-indexed: 150-169)
new_lines = lines[:150] + lines[170:]

# Write back
with open('e:\\YORK.A\\Python codes2\\Antigrav\\geotutor\\server\\routers.ts', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Deleted duplicate systemPrompt declaration (lines 151-170)")
print(f"File now has {len(new_lines)} lines (was {len(lines)} lines)")
