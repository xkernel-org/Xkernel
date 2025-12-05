grep -e 'kernel-results/' -e '^  ->' addr.log > addr.clean.log

python utils/process-addr.py | sort -n > addr.csv
