sudo bpftrace -e '
kprobe:klp_try_switch_task { 
    @target[tid] = (struct task_struct *)arg0; 
}

kretprobe:klp_try_switch_task /@target[tid]/ { 
    $task = @target[tid];
    $tpid = $task->pid;

    if ($task->comm == "iperf3") {
        
        if (retval == 0) {
            if (!@blocked_start[$tpid]) {
                @blocked_start[$tpid] = nsecs;
                printf("[Start Blocking] Target PID: %d | Time: %llu\n", $tpid, nsecs);
            }
        } 
        else {
            if (@blocked_start[$tpid]) {
                $start_time = @blocked_start[$tpid];
                $duration = nsecs - $start_time;
                
                printf("[Unblocked!]     Target PID: %d | Time: %llu | Waited: %llu ns\n", 
                       $tpid, nsecs, $duration);
                
                delete(@blocked_start[$tpid]);
            }
        }
    }
    
    delete(@target[tid]); 
}
'