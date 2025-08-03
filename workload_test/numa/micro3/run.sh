THIS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# 20 threads, 500 MB per thread, 5000 rounds
$THIS_DIR/benchmark 20 500 5000
