import subprocess
import sys
import os

# Install PIL (Pillow) in Blender's Python environment
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'Pillow'])
print("Pillow (PIL) has been installed in Blender's Python environment.") 