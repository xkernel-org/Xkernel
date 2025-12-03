for f in kernel-results/*/*.output.txt; do
    grep -E "Total: [0-9]+ instructions" $f
done | awk '{ print $2 }' | tee kernel-results/occurrence-size.txt

python utils/plot_cdf.py kernel-results/occurrence-size.txt
