PROGRAM_NAME=${1:-"prog\$"}
PRINTED_DELIMITER=0

while true; do
    RESULT=`bash numa-maps-monitor.sh $PROGRAM_NAME`
    RESULT2=`bash which-cpu-monitor.sh $PROGRAM_NAME`
    if [[ $RESULT2 == "" ]]; then RESULT2='?'; fi
    if [[ $RESULT == "" ]]; then
        if [[ $PRINTED_DELIMITER == 0 ]]; then
            echo --------
            PRINTED_DELIMITER=1
        fi
    else
        PRINTED_DELIMITER=0
        echo $RESULT2
        echo $RESULT
    fi
    sleep 1
done
