while true; do
  sudo grep -E 'kmalloc-64|kmalloc-cg-64' /proc/slabinfo | head 
  sleep 0.1
done
