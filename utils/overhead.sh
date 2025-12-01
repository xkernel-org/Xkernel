for f in kernel-results/*/*.input.txt; do
    time=$(grep Elapsed $(dirname $f)/$(basename $f .input.txt).time.txt | awk '{print $8}' | python utils/to-min.py)
    size=$(wc -l < $(dirname $f)/$(basename $f .input.txt).output.txt)
    echo $f,$time,$size
done | tee kernel-results/overhead.csv

python utils/plot-overhead.py
