
PROGRAM_NAME=${1:-"2-threads"}
PRINTED_DELIMITER=0

while true; do
    RESULT=`bash numa-maps-monitor.sh $PROGRAM_NAME`
    if [[ $RESULT == "" ]]; then
        if [[ $PRINTED_DELIMITER == 0 ]]; then
            echo --------
            PRINTED_DELIMITER=1
        fi
    else
        PRINTED_DELIMITER=0
        echo $RESULT
    fi
    sleep 1
done
