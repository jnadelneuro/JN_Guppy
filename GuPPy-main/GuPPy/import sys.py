import sys
import numpy
print(f"NumPy version: {numpy.__version__}")
print(f"NumPy location: {numpy.__file__}")
print("Python path:")
for p in sys.path:
    print(f" - {p}")