grep -e 'kernel-results/' -e '^  ->' find-binary-addresses/addr.log > find-binary-addresses/addr.clean.log

python utils/process-addr.py | sort -n > find-binary-addresses/addr.csv
