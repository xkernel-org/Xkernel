python utils/analyze_disjoint_chunks.py |\
    grep -v '^999,' |\
    grep -v '^9,' |\
    grep -v '^43,' |\
    grep -v '^91,' |\
    grep -v '^13,' | cut -d, -f2 > find-binary-addresses/disjoint_sses_asm.txt
