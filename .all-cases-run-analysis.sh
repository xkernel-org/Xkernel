### 1. DFR_MAX (1,2)

# %163 = icmp slt i32 %162, 301, !dbg !17437
# Conclusion: [LOCAL]

# SOURCE_FILE=net/sunrpc/cache.c
# FUNCTION_NAME=cache_check_rcu
# SOURCE_OP=icmp
# CONSTANT_VALUE=301
# OCCURENCE=1

# # %166 = icmp sgt i32 %165, 300, !dbg !17442
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/sunrpc/cache.c
# FUNCTION_NAME=cache_check_rcu
# SOURCE_OP=icmp
# CONSTANT_VALUE=300
# OCCURENCE=1

### 2. GSSD_MIN_TIMEOUT

# # %15 = select i1 %14, i32 3600, i32 %13, !dbg !18545
# # Conclusion: [INTERPROC, EXTERNAL]
#
# SOURCE_FILE=net/sunrpc/auth_gss/auth_gss.c
# FUNCTION_NAME=gss_fill_context
# SOURCE_OP=select
# CONSTANT_VALUE=3600
# OCCURENCE=1

### 3. SMC_TX_WORK_DELAY (1,2)

# Kconfig:
# - CONFIG_INFINIBAND
# - CONFIG_SMC

# # %144 = call zeroext i1 @mod_delayed_work_on(i32 noundef 64, ptr noundef %142, ptr noundef nonnull %143, i64 noundef 0) #8, !dbg !17462
# # Conclusion: [INTERPROC]
#
# SOURCE_FILE=net/smc/smc_tx.c
# FUNCTION_NAME=smc_tx_sndbuf_nonempty
# SOURCE_OP=call
# CONSTANT_VALUE=0
# OCCURENCE=2 # <--- the combination of "call" and "0" is too common, double
#             #      check we are starting at the right instruction

# # %103 = tail call zeroext i1 @queue_delayed_work_on(i32 noundef 64, ptr noundef %101, ptr noundef nonnull %102, i64 noundef 0) #8, !dbg !18394
# # Conclusion: [INTERPROC]
#
# SOURCE_FILE=net/smc/smc_tx.c
# FUNCTION_NAME=smc_tx_consumer_update
# SOURCE_OP=call
# CONSTANT_VALUE=0
# OCCURENCE=3 # <--- the combination of "call" and "0" is too common, double
#             #      check we are starting at the right instruction

### 4. SMC_LGR_NUM_INCR

# # %326 = add i32 %325, 256, !dbg !22204
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/smc/smc_core.c
# FUNCTION_NAME=smc_conn_create
# SOURCE_OP=add
# CONSTANT_VALUE=256
# OCCURENCE=1

### 5. RDS_IB_RECYCLE_BATCH_COUNT

# Kconfig:
# - CONFIG_RDS
# - CONFIG_RDS_RDMA

# # %23 = icmp ult i64 %22, 32, !dbg !15799
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/rds/ib_recv
# FUNCTION_NAME=rds_ib_recv_cache_put
# SOURCE_OP=icmp
# CONSTANT_VALUE=32
# OCCURENCE=1

### 6. QUEUE_THRESHOLD (1,2,3)

# Kconfig:
# - CONFIG_NET_SCH_PIE

# # %25 = icmp ugt i32 %3, 16383, !dbg !12932
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/sched/sch_pie.c
# FUNCTION_NAME=pie_process_dequeue
# SOURCE_OP=icmp
# CONSTANT_VALUE=16383
# OCCURENCE=1

# # %42 = icmp ugt i64 %41, 16383, !dbg !12949
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/sched/sch_pie.c
# FUNCTION_NAME=pie_process_dequeue
# SOURCE_OP=icmp
# CONSTANT_VALUE=16383
# OCCURENCE=2

# # %61 = icmp ult i32 %3, 16381, !dbg !12962
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/sched/sch_pie.c
# FUNCTION_NAME=pie_process_dequeue
# SOURCE_OP=icmp
# CONSTANT_VALUE=16384
# OCCURENCE=1

### 7. PIE_SCALE (1,2,3)

# # %39 = lshr i64 %38, 8, !dbg !12658
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/sched/sch_pie.c
# FUNCTION_NAME=pie_dump_stats
# SOURCE_OP=lshr
# CONSTANT_VALUE=8
# OCCURENCE=1

# # %14 = shl i32 %2, 8, !dbg !12786
# # Conclusion: [INTERPROC, EXTERNAL]
#
# SOURCE_FILE=net/sched/sch_pie.c
# FUNCTION_NAME=pie_calculate_probability
# SOURCE_OP=shl
# CONSTANT_VALUE=8
# OCCURENCE=1

# # %51 = shl i32 %50, 8, !dbg !12956
# # Conclusion: [LOCAL]
#
# SOURCE_FILE=net/sched/sch_pie.c
# FUNCTION_NAME=pie_process_dequeue
# SOURCE_OP=shl
# CONSTANT_VALUE=8
# OCCURENCE=1

### 8. BUSY_POLL_BUDGET (1,2,3,4,5)

# # tail call void @napi_busy_loop_rcu(i32 noundef %61, ptr noundef %46, ptr noundef %45, i1 noundef zeroext %63, i16 noundef zeroext 8) #7, !dbg !13037
# # Conclusion: [INTERPROC, EXTERNAL]
#
# SOURCE_FILE=io_uring/napi.c
# FUNCTION_NAME=__io_napi_busy_loop
# SOURCE_OP="call"
# CONSTANT_VALUE=8
# OCCURENCE=1

# # tail call void @napi_busy_loop_rcu(i32 noundef %71, ptr noundef %46, ptr noundef %45, i1 noundef zeroext %73, i16 noundef zeroext 8) #7, !dbg !13060
# # Conclusion: [INTERPROC, EXTERNAL]
#
# SOURCE_FILE=io_uring/napi.c
# FUNCTION_NAME=__io_napi_busy_loop
# SOURCE_OP="call"
# CONSTANT_VALUE=8
# OCCURENCE=2

# # tail call void @napi_busy_loop_rcu(i32 noundef %25, ptr noundef null, ptr noundef null, i1 noundef zeroext %27, i16 noundef zeroext 8) #7, !dbg !13518
# # Conclusion: [INTERPROC, EXTERNAL]
#
# SOURCE_FILE=io_uring/napi.c
# FUNCTION_NAME=io_napi_sqpoll_busy_poll
# SOURCE_OP="call"
# CONSTANT_VALUE=8
# OCCURENCE=1

# # tail call void @napi_busy_loop_rcu(i32 noundef %37, ptr noundef null, ptr noundef null, i1 noundef zeroext %39, i16 noundef zeroext 8) #7, !dbg !13527
# # Conclusion: [INTERPROC, EXTERNAL]
#
# SOURCE_FILE=io_uring/napi.c
# FUNCTION_NAME=io_napi_sqpoll_busy_poll
# SOURCE_OP="call"
# CONSTANT_VALUE=8
# OCCURENCE=2

# # %227 = select i1 %226, i16 8, i16 %223, !dbg !16238
# # Conclusion: [INTERPROC, EXTERNAL]
#
# SOURCE_FILE=fs/eventpoll.c
# FUNCTION_NAME=do_epoll_wait
# SOURCE_OP="select"
# CONSTANT_VALUE=8
# OCCURENCE=1

### 15. TCP_ATO_MIN

# # %19 = or disjoint i32 %18, 40, !dbg !13077
# # Conclusion: []
#
# SOURCE_FILE=net/dccp/output.c
# FUNCTION_NAME=dccp_send_ack
# SOURCE_OP="or"
# CONSTANT_VALUE=40
# OCCURENCE=1

# # %58 = or disjoint i32 %57, 40, !dbg !12925
# # Conclusion: []
#
# SOURCE_FILE=net/dccp/timer.c
# FUNCTION_NAME=dccp_delack_timer
# SOURCE_OP="or"
# CONSTANT_VALUE=40
# OCCURENCE=1

# # %260 = or disjoint i32 %259, 40, !dbg !14536
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_rcv_state_process
# SOURCE_OP="or"
# CONSTANT_VALUE=40
# OCCURENCE=1

# # %530 = or disjoint i32 %529, 40, !dbg !20138
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_data_queue
# SOURCE_OP="or"
# CONSTANT_VALUE=40
# OCCURENCE=1

# # %176 = or disjoint i32 %156, 40, !dbg !22150
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_event_data_recv
# SOURCE_OP="or"
# CONSTANT_VALUE=40
# OCCURENCE=1

# # %181 = icmp ult i32 %180, 21, !dbg !22155
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_event_data_recv
# SOURCE_OP="icmp"
# CONSTANT_VALUE=21
# OCCURENCE=1

# # %184 = add nuw nsw i32 %183, 20, !dbg !22159
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_event_data_recv
# SOURCE_OP="add"
# CONSTANT_VALUE=20
# OCCURENCE=1

# # %36 = or disjoint i32 %35, 40, !dbg !22517
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_ecn_check_ce
# SOURCE_OP="or"
# CONSTANT_VALUE=40
# OCCURENCE=1

# # %76 = or disjoint i32 %75, 40, !dbg !22577
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_ecn_check_ce
# SOURCE_OP="or"
# CONSTANT_VALUE=40
# OCCURENCE=2

# # %40 = or disjoint i32 %39, 40, !dbg !24216
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_send_dupack
# SOURCE_OP="or"
# CONSTANT_VALUE=40
# OCCURENCE=1

# # %28 = or disjoint i32 %27, 40, !dbg !14261
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_output.c
# FUNCTION_NAME=__tcp_send_ack
# SOURCE_OP="or"
# CONSTANT_VALUE=40
# OCCURENCE=1

# # %532 = or disjoint i32 %531, 40, !dbg !15353
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_output.c
# FUNCTION_NAME=__tcp_transmit_skb
# SOURCE_OP="or"
# CONSTANT_VALUE=40
# OCCURENCE=1

# # %53 = or disjoint i32 %52, 40, !dbg !12849
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_timer.c
# FUNCTION_NAME=tcp_delack_timer_handler
# SOURCE_OP="or"
# CONSTANT_VALUE=40
# OCCURENCE=1

### 16. TCP_TIMEOUT_MIN

# # %29 = icmp ult i64 %28, -199, !dbg !17271
# # Conclusion: []
#
# SOURCE_FILE=net/core/filter.c
# FUNCTION_NAME=bpf_sol_tcp_setsockopt
# SOURCE_OP="icmp"
# CONSTANT_VALUE=-199
# OCCURENCE=1

# # %36 = icmp ult i64 %35, -199, !dbg !17280
# # Conclusion: []
#
# SOURCE_FILE=net/core/filter.c
# FUNCTION_NAME=bpf_sol_tcp_setsockopt
# SOURCE_OP="icmp"
# CONSTANT_VALUE=-199
# OCCURENCE=2

# # %76 = add i64 %75, 2, !dbg !14179
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_rcv_state_process
# SOURCE_OP="add"
# CONSTANT_VALUE=2
# OCCURENCE=1

# # %21 = tail call i32 @llvm.umax.i32(i32 %20, i32 2), !dbg !12753
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_timer.c
# FUNCTION_NAME=tcp_clamp_probe0_to_user_timeout
# SOURCE_OP="call"
# CONSTANT_VALUE=2
# OCCURENCE=1

### 17. TCP_TIMEOUT_MIN_US

# # %36 = phi i32 [ %34, %33 ], [ 2000, %30 ]
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_output.c
# FUNCTION_NAME=tcp_schedule_loss_probe
# SOURCE_OP="phi"
# CONSTANT_VALUE=2000
# OCCURENCE=1

# # %12 = add i32 %9, 2000, !dbg !12402
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_recovery.c
# FUNCTION_NAME=tcp_rack_mark_lost
# SOURCE_OP="add"
# CONSTANT_VALUE=2000
# OCCURENCE=1

### 18. MAX_GRO_SKBS

# # %357 = icmp sgt i32 %356, 7, !dbg !13079
# # Conclusion: []
#
# SOURCE_FILE=net/core/gro.c
# FUNCTION_NAME=dev_gro_receive
# SOURCE_OP="icmp"
# CONSTANT_VALUE=7
# OCCURENCE=1
