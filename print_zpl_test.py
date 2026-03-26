import sys
sys.path.insert(0, r'c:\agrosample')
from zebra_print_service import build_zpl_small_label_5x2
print(build_zpl_small_label_5x2("100", 731, 795, "PROPAL"))
