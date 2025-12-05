grep -A1 'kernel-results/' addr.log > addr.clean.log

python utils/process-addr.py | sort -n > addr.csv
