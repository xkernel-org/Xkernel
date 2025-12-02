echo Started:
ls kernel-results/*/*.output.txt | wc -l

echo Completed:
for f in kernel-results/*/*.output.txt; do
    if grep 'Taint Analysis Complete' $f >& /dev/null; then
        echo $f
    fi
done | wc -l

echo

bash utils/time_stats.sh

echo

# Watch for potential empty analysis output

for f in kernel-results/*/*.output.txt; do
    if grep 'Taint Analysis Complete' $f >& /dev/null; then
        echo "`wc -l < $f`,$f"
    fi
done | sort -nr | tail
