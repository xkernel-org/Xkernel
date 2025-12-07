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

print(f"ID,directory,file,function,offset,source start,source end")

with open('find-binary-addresses/addr.clean.log', 'r') as f:
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
            result = line.strip()
            result_parts = result.split(',')

            function = ''
            offset = ''

            source_start = ''
            source_end = ''

            if (len(result_parts) == 7) and (result_parts[2].startswith(' 0x') and result_parts[3].startswith(' 0x')):
                source_start = result_parts[0].strip().replace('->', '').strip()
                source_end = result_parts[1].strip()
                assembly_start = result_parts[2].strip()
                assembly_end = result_parts[3].strip()

                start_offset = result_parts[5].strip()
                end_offset = result_parts[6].strip()

                # In some stages of the script, these values showed up but
                # should not now.
                if start_offset.startswith('-') or end_offset.startswith('-'):
                    assert False
                if start_offset == 'None' or end_offset == 'None':
                    assert False

                function = result_parts[4].strip()
                offset = start_offset + ' - ' + end_offset

            print(f"{id_to_idx[perf_const_id]},{perf_const_id},{raw_output_file},{function},{offset},{source_start},{source_end}")
            perf_const_id = None
    assert perf_const_id is None
