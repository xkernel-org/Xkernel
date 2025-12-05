# Index: number in the original GitHub gist file
# ID: a name suitable for creating directories. If it's a macro, the ID should
#     be the macro name; if it's "const TYPE" or hardcoded numbers, the ID may be
#     made up by adding prefixes__ and __suffixes to be identifiable.
#     E.g., "p->node_stamp += 2 * TICK_NSEC" -> "node_stamp__2__TICK_NSEC"

id_to_idx = {}
idx_to_addr = {}

with open('dataset/source-occurrence-and-mutation.sh', 'r') as f:
    for line in f:
        if line.startswith('### '):
            perf_const_id = line.strip().split('. ')[1].split(' ')[0]
            perf_const_idx = line.strip().split('. ')[0].split(' ')[1]
            # print(f"ID: {perf_const_id}, Index: {perf_const_idx}")
            id_to_idx[perf_const_id] = perf_const_idx

# Expect input like
#   ...
#   --
#   [10/400] kernel-results/AMT_SECRET_TIMEOUT/1.output.txt
#     -> 0xffffffff814d2081 - 0xffffffff814d2081
#   --
#   [11/400] kernel-results/AMT_SECRET_TIMEOUT/2.output.txt
#     -> ERROR: Could not find earliest instruction
#   --
#   ...
with open('addr.clean.log', 'r') as f:
    perf_const_id = None
    for line in f:
        if line.startswith('['):
            raw_output_file = line.strip().split(' ')[1]
            perf_const_id = line.strip().split('/')[2]
            assert perf_const_id in id_to_idx
        elif line.startswith('--'):
            continue
        else:
            assert perf_const_id is not None
            assembly_address = line.strip()
            print(f"{id_to_idx[perf_const_id]},{perf_const_id},{raw_output_file},\"{assembly_address}\"")
            perf_const_id = None
    assert perf_const_id is None
