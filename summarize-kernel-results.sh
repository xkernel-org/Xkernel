DOWNWARD_LIST=(
    "CHILD FUNCTION"
    "INDIRECT CALL"
)

UPWARD_LIST=(
    "RETURN"
    "POINTER PARAMETER"
)

CNT_DOWNWARD=0
CNT_UPWARD=0
CNT_NOT_HANDLED=0
CNT_INTRAPROC=0
CNT_INTERPROC=0
CNT_TOTAL=0

for OUTPUT_FILE in $(ls kernel-results/*/*.output.txt); do
    CNT_TOTAL=$((CNT_TOTAL + 1))

    if grep "GLOBAL" $OUTPUT_FILE > /dev/null; then
        CNT_NOT_HANDLED=$((CNT_NOT_HANDLED + 1))
        # echo $OUTPUT_FILE
        continue
    fi

    INTERPROC=false

    for HEADER in "${DOWNWARD_LIST[@]}"; do
        if grep "$HEADER" $OUTPUT_FILE > /dev/null; then
            CNT_DOWNWARD=$((CNT_DOWNWARD + 1))
            INTERPROC=true
            break
        fi
    done

    for HEADER in "${UPWARD_LIST[@]}"; do
        if grep "$HEADER" $OUTPUT_FILE > /dev/null; then
            CNT_UPWARD=$((CNT_UPWARD + 1))
            INTERPROC=true
            break
        fi
    done

    if [[ $INTERPROC == "false" ]]; then
        CNT_INTRAPROC=$((CNT_INTRAPROC + 1))
    else
        CNT_INTERPROC=$((CNT_INTERPROC + 1))
    fi
done

echo "TOTAL: $CNT_TOTAL"
echo "NOT HANDLED: $CNT_NOT_HANDLED"
echo "INTRAPROC: $CNT_INTRAPROC"
echo "INTERPROC: $CNT_INTERPROC"
echo "  DOWNWARD: $CNT_DOWNWARD"
echo "  UPWARD: $CNT_UPWARD"
