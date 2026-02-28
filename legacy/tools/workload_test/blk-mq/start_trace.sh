sudo sh -c 'echo > /sys/kernel/tracing/trace'
sudo sh -c 'echo 1 > /sys/kernel/tracing/events/block/block_plug/enable'
sudo sh -c 'echo 1 > /sys/kernel/tracing/events/block/block_unplug/enable'
sudo sh -c 'echo 1 > /sys/kernel/tracing/tracing_on'
