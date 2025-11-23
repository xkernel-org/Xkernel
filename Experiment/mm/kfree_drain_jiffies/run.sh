#!/bin/bash

for i in {1..1000}
do
    ./t -t 4 -I 2000 -r 32 -p 0
done

echo "Done!"