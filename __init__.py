import os
import sys

module_path = os.path.dirname(os.path.realpath(__file__))
if module_path not in sys.path:
    sys.path.append(module_path)
