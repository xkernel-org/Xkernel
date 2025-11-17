### 1. DFR_MAX (1,2)

# # %163 = icmp slt i32 %162, 301, !dbg !17437
# # Conclusion: [LOCAL]

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

### 9. MLD_MAX_QUEUE

# FIXME there was a huge diff during IR localization

### 10. MLD_MAX_SKBS

# # %15 = icmp ult i32 %14, 32, !dbg !18374
# # Conclusion: []
#
# SOURCE_FILE=net/ipv6/mcast.c
# FUNCTION_NAME=igmp6_event_query
# SOURCE_OP="icmp"
# CONSTANT_VALUE=32
# OCCURENCE=1

# # %15 = icmp ult i32 %14, 32, !dbg !18493
# # Conclusion: []
#
# SOURCE_FILE=net/ipv6/mcast.c
# FUNCTION_NAME=igmp6_event_report
# SOURCE_OP="icmp"
# CONSTANT_VALUE=32
# OCCURENCE=1

### 11. TCP_MAX_QUICKACKS

# # %247 = call i32 @llvm.umin.i32(i32 %245, i32 range(i32 2, 17) 16), !dbg !14518
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_rcv_state_process
# SOURCE_OP="call"
# CONSTANT_VALUE=16
# OCCURENCE=1

# # %517 = tail call i32 @llvm.umin.i32(i32 %515, i32 range(i32 2, 17) 16), !dbg !20126
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_data_queue
# SOURCE_OP="call"
# CONSTANT_VALUE=16
# OCCURENCE=1

# # %167 = tail call i32 @llvm.umin.i32(i32 %165, i32 16), !dbg !22143
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_event_data_recv
# SOURCE_OP="call"
# CONSTANT_VALUE=16
# OCCURENCE=1

# # %212 = tail call i32 @llvm.umin.i32(i32 %210, i32 16), !dbg !22186
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_event_data_recv
# SOURCE_OP="call"
# CONSTANT_VALUE=16
# OCCURENCE=2

# # %27 = tail call i32 @llvm.umin.i32(i32 %25, i32 range(i32 2, 17) 16), !dbg !24204
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_send_dupack
# SOURCE_OP="call"
# CONSTANT_VALUE=16
# OCCURENCE=1

### 12. TCP_MAX_WSCALE

# # %61 = icmp ugt i8 %60, 14, !dbg !32910
# # Conclusion: []
#
# SOURCE_FILE=net/core/filter.c
# FUNCTION_NAME=bpf_sk_assign_tcp_reqsk
# SOURCE_OP="icmp"
# CONSTANT_VALUE=14
# OCCURENCE=1

# # %65 = icmp ugt i8 %64, 14, !dbg !32913
# # Conclusion: []
#
# SOURCE_FILE=net/core/filter.c
# FUNCTION_NAME=bpf_sk_assign_tcp_reqsk
# SOURCE_OP="icmp"
# CONSTANT_VALUE=14
# OCCURENCE=2

# # %34 = and i32 %33, 65535, !dbg !16421
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp.c
# FUNCTION_NAME=tcp_repair_options_est
# SOURCE_OP="and"
# CONSTANT_VALUE=65535
# OCCURENCE=1

# # %35 = icmp samesign ult i32 %34, 15, !dbg !16423
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp.c
# FUNCTION_NAME=tcp_repair_options_est
# SOURCE_OP="icmp"
# CONSTANT_VALUE=15
# OCCURENCE=1

# # %36 = icmp ult i32 %33, 983040
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp.c
# FUNCTION_NAME=tcp_repair_options_est
# SOURCE_OP="icmp"
# CONSTANT_VALUE=983040
# OCCURENCE=1

# # %90 = icmp ugt i8 %86, 14, !dbg !15205
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_parse_options
# SOURCE_OP="icmp"
# CONSTANT_VALUE=14
# OCCURENCE=1

# # %95 = tail call i32 (ptr, ...) @_printk(ptr noundef nonnull @.str.1, ptr noundef nonnull @__func__.tcp_parse_options, i32 noundef %89, i32 noundef 14) #27, !dbg !15210
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_parse_options
# SOURCE_OP="call"
# CONSTANT_VALUE=14
# OCCURENCE=1

# # %97 = phi i8 [ %86, %85 ], [ 14, %94 ], [ 14, %91 ], !dbg !15201
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_parse_options
# SOURCE_OP="phi"
# CONSTANT_VALUE=14
# OCCURENCE=1

# # %12 = select i1 %11, i32 1073725440, i32 %10, !dbg !13613
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_output.c
# FUNCTION_NAME=tcp_select_initial_window
# SOURCE_OP="select"
# CONSTANT_VALUE=1073725440
# OCCURENCE=1

# # %42 = icmp sgt i32 %41, 13, !dbg !13667
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_output.c
# FUNCTION_NAME=tcp_select_initial_window
# SOURCE_OP="icmp"
# CONSTANT_VALUE=13
# OCCURENCE=1

# # %45 = select i1 %42, i8 14, i8 %44, !dbg !13667
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_output.c
# FUNCTION_NAME=tcp_select_initial_window
# SOURCE_OP="select"
# CONSTANT_VALUE=14
# OCCURENCE=1

# # %255 = select i1 %254, i32 1073725440, i32 %253, !dbg !23001
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_output.c
# FUNCTION_NAME=tcp_connect
# SOURCE_OP="select"
# CONSTANT_VALUE=1073725440
# OCCURENCE=1

# # %282 = icmp sgt i32 %281, 13, !dbg !23033
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_output.c
# FUNCTION_NAME=tcp_connect
# SOURCE_OP="icmp"
# CONSTANT_VALUE=13
# OCCURENCE=1

# # %285 = select i1 %282, i8 14, i8 %284, !dbg !23033
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_output.c
# FUNCTION_NAME=tcp_connect
# SOURCE_OP="select"
# CONSTANT_VALUE=14
# OCCURENCE=1

# # %68 = call i8 @llvm.umin.i8(i8 %67, i8 14), !dbg !14069
# # Conclusion: []
#
# SOURCE_FILE=net/netfilter/nf_conntrack_proto_tcp.c
# FUNCTION_NAME=tcp_options
# SOURCE_OP="call"
# CONSTANT_VALUE=14
# OCCURENCE=1

# # %69 = call i8 @llvm.umin.i8(i8 %68, i8 14), !dbg !14125
# # Conclusion: []
#
# SOURCE_FILE=net/netfilter/nf_synproxy_core.c
# FUNCTION_NAME=synproxy_parse_options
# SOURCE_OP="call"
# CONSTANT_VALUE=14
# OCCURENCE=1

### 13. TCP_DELACK_MAX

# # %28 = add i64 %27, -201, !dbg !17271
# # Conclusion: []
#
# SOURCE_FILE=net/core/filter.c
# FUNCTION_NAME=bpf_sol_tcp_setsockopt
# SOURCE_OP="add"
# CONSTANT_VALUE=-201
# OCCURENCE=1

# # %29 = icmp ult i64 %28, -199, !dbg !17271
# # Conclusion: []
#
# SOURCE_FILE=net/core/filter.c
# FUNCTION_NAME=bpf_sol_tcp_setsockopt
# SOURCE_OP="icmp"
# CONSTANT_VALUE=-199
# OCCURENCE=1

# # %23 = add i64 %22, 200, !dbg !13091
# # Conclusion: []
#
# SOURCE_FILE=net/dccp/output.c
# FUNCTION_NAME=dccp_send_ack
# SOURCE_OP="add"
# CONSTANT_VALUE=200
# OCCURENCE=1

# # store i32 200, ptr %16, align 8, !dbg !22232
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp.c
# FUNCTION_NAME=tcp_init_sock
# SOURCE_OP="store"
# CONSTANT_VALUE=200
# OCCURENCE=1

# # store i32 200, ptr %147, align 8, !dbg !26222
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp.c
# FUNCTION_NAME=tcp_disconnect
# SOURCE_OP="store"
# CONSTANT_VALUE=200
# OCCURENCE=2

# # %264 = add i64 %263, 200, !dbg !14548
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_rcv_state_process
# SOURCE_OP="add"
# CONSTANT_VALUE=200
# OCCURENCE=1

# FIXME there was a huge diff during IR localization

### 14. TCP_DELACK_MIN

# # %14 = add i64 %13, 40, !dbg !12866
# # Conclusion: []
#
# SOURCE_FILE=net/dccp/timer.c
# FUNCTION_NAME=dccp_delack_timer
# SOURCE_OP="add"
# CONSTANT_VALUE=40
# OCCURENCE=1

# # %6 = icmp samesign ugt i32 %5, 40, !dbg !25718
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_output.c
# FUNCTION_NAME=tcp_send_delayed_ack
# SOURCE_OP="icmp"
# CONSTANT_VALUE=40
# OCCURENCE=1

# # %30 = tail call i32 @llvm.smax.i32(i32 %28, i32 40), !dbg !25750
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_output.c
# FUNCTION_NAME=tcp_send_delayed_ack
# SOURCE_OP="call"
# CONSTANT_VALUE=40
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

### 19. BLK_MQ_CPU_WORK_BATCH

# # store i32 8, ptr %251, align 4, !dbg !10731
# # Conclusion: []
#
# SOURCE_FILE=block/blk-mq.c
# FUNCTION_NAME=blk_mq_map_swqueue
# SOURCE_OP="store"
# CONSTANT_VALUE=8
# OCCURENCE=1

# # store i32 8, ptr %23, align 4, !dbg !11737
# # Conclusion: []
#
# SOURCE_FILE=block/blk-mq.c
# FUNCTION_NAME=blk_mq_delay_run_hw_queue
# SOURCE_OP="store"
# CONSTANT_VALUE=8
# OCCURENCE=1

### 20. TCP_THIN_LINEAR_RETRIES

# # %572 = icmp ult i8 %571, 7, !dbg !13927
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_timer.c
# FUNCTION_NAME=tcp_retransmit_timer
# SOURCE_OP="icmp"
# CONSTANT_VALUE=7
# OCCURENCE=1

### 21. TCP_INIT_CWND

# # store i32 10, ptr %26, align 4, !dbg !22266
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp.c
# FUNCTION_NAME=tcp_init_sock
# SOURCE_OP="store"
# CONSTANT_VALUE=10
# OCCURENCE=1

# # store i32 10, ptr %149, align 4, !dbg !26228
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp.c
# FUNCTION_NAME=tcp_disconnect
# SOURCE_OP="store"
# CONSTANT_VALUE=10
# OCCURENCE=1

# # %213 = phi i32 [ %211, %201 ], [ 11, %198 ], !dbg !13118
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_bbr.c
# FUNCTION_NAME=bbr_main
# SOURCE_OP="phi"
# CONSTANT_VALUE=11
# OCCURENCE=1

# # %258 = phi i32 [ %256, %247 ], [ 11, %244 ], !dbg !13167
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_bbr.c
# FUNCTION_NAME=bbr_main
# SOURCE_OP="phi"
# CONSTANT_VALUE=11
# OCCURENCE=2

# # %355 = phi i32 [ %353, %342 ], [ 11, %338 ], !dbg !13285
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_bbr.c
# FUNCTION_NAME=bbr_main
# SOURCE_OP="phi"
# CONSTANT_VALUE=11
# OCCURENCE=3

# # %452 = phi i32 [ %450, %439 ], [ 11, %428 ], !dbg !13386
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_bbr.c
# FUNCTION_NAME=bbr_main
# SOURCE_OP="phi"
# CONSTANT_VALUE=11
# OCCURENCE=4

# # %753 = phi i32 [ %751, %742 ], [ 11, %739 ], !dbg !13780
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_bbr.c
# FUNCTION_NAME=bbr_main
# SOURCE_OP="phi"
# CONSTANT_VALUE=11
# OCCURENCE=5

# # %808 = icmp ult i32 %807, 10, !dbg !13867
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_bbr.c
# FUNCTION_NAME=bbr_main
# SOURCE_OP="icmp"
# CONSTANT_VALUE=10
# OCCURENCE=1

# # %80 = tail call i32 @llvm.umax.i32(i32 %79, i32 10), !dbg !18178
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_check_space
# SOURCE_OP="call"
# CONSTANT_VALUE=10
# OCCURENCE=1

# # %31 = phi i32 [ 10, %29 ], [ %27, %20 ], !dbg !19003
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_init_transfer
# SOURCE_OP="phi"
# CONSTANT_VALUE=10
# OCCURENCE=1

# # %82 = tail call i32 @llvm.umax.i32(i32 %81, i32 10), !dbg !19108
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_init_transfer
# SOURCE_OP="call"
# CONSTANT_VALUE=10
# OCCURENCE=1

# # %160 = mul nuw nsw i32 %159, 10, !dbg !19197
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_init_transfer
# SOURCE_OP="mul"
# CONSTANT_VALUE=10
# OCCURENCE=1

# # %15 = phi i32 [ 10, %13 ], [ %11, %4 ], !dbg !31092
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_init_cwnd
# SOURCE_OP="phi"
# CONSTANT_VALUE=10
# OCCURENCE=1

# # %26 = shl i32 %19, 8, !dbg !12774
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_dctcp.c
# FUNCTION_NAME=dctcp_update_alpha
# SOURCE_OP="shl"
# CONSTANT_VALUE=8
# OCCURENCE=1

### 22. TCP_PLB_SCALE

# # %26 = shl i32 %19, 8, !dbg !12774
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_dctcp.c
# FUNCTION_NAME=dctcp_update_alpha
# SOURCE_OP="shl"
# CONSTANT_VALUE=8
# OCCURENCE=1

# # store i32 128, ptr %98, align 4, !dbg !24126
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_ipv4.c
# FUNCTION_NAME=tcp_sk_init
# SOURCE_OP="store"
# CONSTANT_VALUE=128
# OCCURENCE=1

### 23. AMT_DISCOVERY_TIMEOUT

# # %23 = tail call zeroext i1 @mod_delayed_work_on(i32 noundef 64, ptr noundef %22, ptr noundef %0, i64 noundef 5000) #15, !dbg !13691
# # Conclusion: []
#
# SOURCE_FILE=drivers/net/amt.c
# FUNCTION_NAME=amt_discovery_work
# SOURCE_OP="call"
# CONSTANT_VALUE=64
# OCCURENCE=2

# # %540 = call zeroext i1 @mod_delayed_work_on(i32 noundef 64, ptr noundef %539, ptr noundef nonnull %38, i64 noundef 5000) #15, !dbg !15018
# # Conclusion: []
#
# SOURCE_FILE=drivers/net/amt.c
# FUNCTION_NAME=amt_event_work
# SOURCE_OP="call"
# CONSTANT_VALUE=64
# OCCURENCE=2
