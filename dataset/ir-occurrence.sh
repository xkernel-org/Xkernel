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

### 24. AMT_INIT_REQ_TIMEOUT

# # store i8 1, ptr %13, align 1, !dbg !15035
# # Conclusion: []
#
# SOURCE_FILE=drivers/net/amt.c
# FUNCTION_NAME=amt_event_work
# SOURCE_OP="store"
# CONSTANT_VALUE=1
# OCCURENCE=8

### 25. AMT_MAX_REQ_TIMEOUT

# # %563 = call i32 @llvm.umin.i32(i32 %562, i32 120), !dbg !15073
# # Conclusion: []
#
# SOURCE_FILE=drivers/net/amt.c
# FUNCTION_NAME=amt_event_work
# SOURCE_OP="call"
# CONSTANT_VALUE=120
# OCCURENCE=1

### 26. AMT_MAX_REQ_COUNT

# # %546 = icmp ugt i8 %544, 3, !dbg !15033
# # Conclusion: []
#
# SOURCE_FILE=drivers/net/amt.c
# FUNCTION_NAME=amt_event_work
# SOURCE_OP="icmp"
# CONSTANT_VALUE=3
# OCCURENCE=1

### 27. AMT_SECRET_TIMEOUT

# # %5 = tail call zeroext i1 @mod_delayed_work_on(i32 noundef 64, ptr noundef %4, ptr noundef %0, i64 noundef 60000) #15, !dbg !13761
# # Conclusion: []
#
# SOURCE_FILE=drivers/net/amt.c
# FUNCTION_NAME=amt_secret_work
# SOURCE_OP="call"
# CONSTANT_VALUE=64
# OCCURENCE=1

# # %46 = phi i64 [ 0, %40 ], [ 60000, %32 ]
# # Conclusion: []
#
# SOURCE_FILE=drivers/net/amt.c
# FUNCTION_NAME=amt_dev_open
# SOURCE_OP="phi"
# CONSTANT_VALUE=0
# OCCURENCE=1

### 28. IPVS_SYNC_WAKEUP_RATE

# # %32 = icmp eq i32 %31, 8, !dbg !13215
# # Conclusion: []
#
# SOURCE_FILE=net/netfilter/ipvs/ip_vs_sync.c
# FUNCTION_NAME=sb_queue_tail
# SOURCE_OP="icmp"
# CONSTANT_VALUE=8
# OCCURENCE=1

# # %12 = icmp ult i32 %11, 8, !dbg !14991
# # Conclusion: []
#
# SOURCE_FILE=net/netfilter/ipvs/ip_vs_sync.c
# FUNCTION_NAME=master_wakeup_work_handler
# SOURCE_OP="icmp"
# CONSTANT_VALUE=8
# OCCURENCE=1

# # store i32 8, ptr %10, align 8, !dbg !14995
# # Conclusion: []
#
# SOURCE_FILE=net/netfilter/ipvs/ip_vs_sync.c
# FUNCTION_NAME=master_wakeup_work_handler
# SOURCE_OP="store"
# CONSTANT_VALUE=8
# OCCURENCE=1

### 29. IPVS_SYNC_SEND_DELAY

# # %21 = tail call zeroext i1 @queue_delayed_work_on(i32 noundef 64, ptr noundef %20, ptr noundef nonnull %19, i64 noundef 20) #14, !dbg !13184
# # Conclusion: []
#
# SOURCE_FILE=net/netfilter/ipvs/ip_vs_sync.c
# FUNCTION_NAME=sb_queue_tail
# SOURCE_OP="call"
# CONSTANT_VALUE=64
# OCCURENCE=1

### 30. IPVS_SYNC_CHECK_PERIOD

# # %73 = call i64 @schedule_timeout(i64 noundef 1000) #14, !dbg !14783
# # Conclusion: []
#
# SOURCE_FILE=net/netfilter/ipvs/ip_vs_sync.c
# FUNCTION_NAME=sync_thread_master
# SOURCE_OP="call"
# CONSTANT_VALUE=1000
# OCCURENCE=1

### 31. IPVS_SYNC_FLUSH_TIME

# # %56 = add i64 %53, -2000, !dbg !14761
# # Conclusion: []
#
# SOURCE_FILE=net/netfilter/ipvs/ip_vs_sync.c
# FUNCTION_NAME=sync_thread_master
# SOURCE_OP="add"
# CONSTANT_VALUE=-2000
# OCCURENCE=1

### 32. TCP_RACK_RECOVERY_THRESH

# # %381 = tail call i8 @llvm.umin.i8(i8 %380, i8 15), !dbg !26375
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_fastretrans_alert
# SOURCE_OP="call"
# CONSTANT_VALUE=15
# OCCURENCE=1

# # %713 = tail call i8 @llvm.umin.i8(i8 %712, i8 15), !dbg !26841
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_input.c
# FUNCTION_NAME=tcp_fastretrans_alert
# SOURCE_OP="call"
# CONSTANT_VALUE=15
# OCCURENCE=2

# # %34 = or disjoint i8 %33, 16, !dbg !12830
# # Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp_recovery.c
# FUNCTION_NAME=tcp_rack_update_reo_wnd
# SOURCE_OP="or"
# CONSTANT_VALUE=16
# OCCURENCE=1

### 33. SBQ_WAKE_BATCH

# # %15 = icmp ugt i32 %14, 63, !dbg !4367
# # Conclusion: []
#
# SOURCE_FILE=lib/sbitmap.c
# FUNCTION_NAME=sbitmap_queue_resize
# SOURCE_OP="icmp"
# CONSTANT_VALUE=63
# OCCURENCE=1

# # %18 = select i1 %15, i32 8, i32 %17, !dbg !4367
# # Conclusion: []
#
# SOURCE_FILE=lib/sbitmap.c
# FUNCTION_NAME=sbitmap_queue_resize
# SOURCE_OP="select"
# CONSTANT_VALUE=8
# OCCURENCE=1

# # %7 = icmp ugt i32 %6, 63, !dbg !4433
# # Conclusion: []
#
# SOURCE_FILE=lib/sbitmap.c
# FUNCTION_NAME=sbitmap_queue_recalculate_wake_batch
# SOURCE_OP="icmp"
# CONSTANT_VALUE=63
# OCCURENCE=1

# # %10 = select i1 %7, i32 8, i32 %9, !dbg !4433
# # Conclusion: []
#
# SOURCE_FILE=lib/sbitmap.c
# FUNCTION_NAME=sbitmap_queue_recalculate_wake_batch
# SOURCE_OP="select"
# CONSTANT_VALUE=8
# OCCURENCE=1

# # %15 = icmp ugt i32 %14, 63, !dbg !4458
# # Conclusion: []
#
# SOURCE_FILE=lib/sbitmap.c
# FUNCTION_NAME=sbitmap_queue_min_shallow_depth
# SOURCE_OP="icmp"
# CONSTANT_VALUE=63
# OCCURENCE=1

# # %18 = select i1 %15, i32 8, i32 %17, !dbg !4458
# # Conclusion: []
#
# SOURCE_FILE=lib/sbitmap.c
# FUNCTION_NAME=sbitmap_queue_min_shallow_depth
# SOURCE_OP="select"
# CONSTANT_VALUE=8
# OCCURENCE=1

# # %20 = icmp ugt i32 %19, 63, !dbg !4479
# # Conclusion: []
#
# SOURCE_FILE=lib/sbitmap.c
# FUNCTION_NAME=sbitmap_queue_init_node
# SOURCE_OP="icmp"
# CONSTANT_VALUE=63
# OCCURENCE=1

# # %23 = select i1 %20, i32 8, i32 %22, !dbg !4479
# # Conclusion: []
#
# SOURCE_FILE=lib/sbitmap.c
# FUNCTION_NAME=sbitmap_queue_init_node
# SOURCE_OP="select"
# CONSTANT_VALUE=8
# OCCURENCE=1

### 34. BLK_MQ_MAX_DEPTH

# # %27 = icmp ugt i32 %7, 10240, !dbg !16457
# # Conclusion: []
#
# SOURCE_FILE=block/blk-mq.c
# FUNCTION_NAME=blk_mq_alloc_tag_set
# SOURCE_OP="icmp"
# CONSTANT_VALUE=10240
# OCCURENCE=1

# # %29 = tail call i32 (ptr, ...) @_printk(ptr noundef nonnull @.str.9, i32 noundef 10240) #26, !dbg !16459
# # Conclusion: []
#
# SOURCE_FILE=block/blk-mq.c
# FUNCTION_NAME=blk_mq_alloc_tag_set
# SOURCE_OP="call"
# CONSTANT_VALUE=10240
# OCCURENCE=1

# # store i32 10240, ptr %6, align 8, !dbg !16462
# # Conclusion: []
#
# SOURCE_FILE=block/blk-mq.c
# FUNCTION_NAME=blk_mq_alloc_tag_set
# SOURCE_OP="store"
# CONSTANT_VALUE=10240
# OCCURENCE=1

# # %31 = phi i32 [ 10240, %28 ], [ %7, %26 ]
# # Conclusion: []
#
# SOURCE_FILE=block/blk-mq.c
# FUNCTION_NAME=blk_mq_alloc_tag_set
# SOURCE_OP="phi"
# CONSTANT_VALUE=10240
# OCCURENCE=1

# # %10 = tail call i32 @__dm_get_module_param(ptr noundef nonnull @dm_mq_queue_depth, i32 noundef 2048, i32 noundef 10240) #14, !dbg !6487
# # Conclusion: []
#
# SOURCE_FILE=drivers/md/dm-rq.c
# FUNCTION_NAME=dm_mq_init_request_queue
# SOURCE_OP="call"
# CONSTANT_VALUE=2048
# OCCURENCE=1

# # %10 = tail call i16 @llvm.umin.i16(i16 %9, i16 10239), !dbg !23446
# # Conclusion: []
#
# SOURCE_FILE=drivers/nvme/host/core.c
# FUNCTION_NAME=nvme_alloc_io_tag_set
# SOURCE_OP="call"
# CONSTANT_VALUE=10239
# OCCURENCE=1

### 35. BLK_MIN_SG_TIMEOUT

# # %146 = call range(i32 7000, 0) i32 @llvm.umax.i32(i32 %145, i32 7000), !dbg !5814
# # Conclusion: []
#
# SOURCE_FILE=block/bsg.c
# FUNCTION_NAME=bsg_ioctl
# SOURCE_OP="call"
# CONSTANT_VALUE=7000
# OCCURENCE=1

# # %63 = icmp ult i32 %62, 7000, !dbg !7759
# # Conclusion: []
#
# SOURCE_FILE=drivers/scsi/scsi_ioctl.c
# FUNCTION_NAME=sg_io
# SOURCE_OP="icmp"
# CONSTANT_VALUE=7000
# OCCURENCE=1

# # %65 = phi i32 [ 60000, %57 ], [ 7000, %61 ]
# # Conclusion: []
#
# SOURCE_FILE=drivers/scsi/scsi_ioctl.c
# FUNCTION_NAME=sg_io
# SOURCE_OP="phi"
# CONSTANT_VALUE=60000
# OCCURENCE=1

### 36. NFS_JUKEBOX_RETRY_TIME

# # tail call void @rpc_delay(ptr noundef %0, i64 noundef 5000) #22, !dbg !18881
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/flexfilelayout/flexfilelayout.c
# FUNCTION_NAME=ff_layout_async_handle_error
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # %27 = call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !12672
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_proc_getattr
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # %45 = call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !12871
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_proc_setattr
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # %32 = call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !13063
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_proc_access
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # %32 = call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !13170
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_proc_readlink
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # %31 = call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !13638
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_proc_remove
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # tail call void @rpc_delay(ptr noundef %0, i64 noundef 5000) #12, !dbg !13743
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_proc_unlink_done
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # tail call void @rpc_delay(ptr noundef %0, i64 noundef 5000) #12, !dbg !13792
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_proc_rename_done
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # %42 = call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !13876
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_proc_link
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # %33 = call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !14195
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_proc_rmdir
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # %59 = call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !14327
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_proc_readdir
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # %19 = call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !14544
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_proc_statfs
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # %19 = call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !14618
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_proc_pathconf
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # tail call void @rpc_delay(ptr noundef %0, i64 noundef 5000) #12, !dbg !14719
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_read_done
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # tail call void @rpc_delay(ptr noundef %0, i64 noundef 5000) #12, !dbg !14774
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_write_done
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # tail call void @rpc_delay(ptr noundef %0, i64 noundef 5000) #12, !dbg !14831
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_commit_done
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # %17 = call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !14970
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=do_proc_fsinfo
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # %18 = tail call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !15031
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=nfs3_do_create
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # %38 = call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !15168
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=__nfs3_proc_lookup
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # %75 = call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !15225
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=__nfs3_proc_lookup
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=2

# # %17 = call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !15286
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=do_proc_get_root
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=1

# # %45 = call i64 @schedule_timeout(i64 noundef 5000) #12, !dbg !15331
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs3proc.c
# FUNCTION_NAME=do_proc_get_root
# SOURCE_OP="call"
# CONSTANT_VALUE=5000
# OCCURENCE=2

### 37. MAX_NR_FOLIOS_PER_FREE

# # %76 = tail call i32 @llvm.umin.i32(i32 %75, i32 512), !dbg !6877
# # Conclusion: []
#
# SOURCE_FILE=mm/mmu_gather.c
# FUNCTION_NAME=tlb_flush_mmu
# SOURCE_OP="call"
# CONSTANT_VALUE=512
# OCCURENCE=1

# # %109 = icmp ult i32 %106, 512, !dbg !6904
# # Conclusion: []
#
# SOURCE_FILE=mm/mmu_gather.c
# FUNCTION_NAME=tlb_flush_mmu
# SOURCE_OP="icmp"
# CONSTANT_VALUE=512
# OCCURENCE=1

### 38. PCPU_SLOT_FAIL_THRESHOLD

# # %101 = icmp sgt i32 %95, 2
# # Conclusion: []
#
# SOURCE_FILE=mm/percpu.c
# FUNCTION_NAME=pcpu_alloc_noprof
# SOURCE_OP="icmp"
# CONSTANT_VALUE=2
# OCCURENCE=1

### 39. NR_MAX_MIGRATE_PAGES_RETRY

# # %243 = icmp samesign ult i32 %49, 9, !dbg !12963
# # Conclusion: []
#
# SOURCE_FILE=mm/migrate.c
# FUNCTION_NAME=migrate_pages
# SOURCE_OP="icmp"
# CONSTANT_VALUE=9
# OCCURENCE=1

# # %324 = call fastcc i32 @migrate_pages_batch(ptr noundef nonnull %12, ptr noundef %1, ptr noundef %2, i64 noundef %3, i32 noundef 0, i32 noundef %5, ptr noundef nonnull %13, ptr noundef nonnull %14, ptr noundef nonnull %15, i32 noundef 10) #11, !dbg !13112
# # Conclusion: []
#
# SOURCE_FILE=mm/migrate.c
# FUNCTION_NAME=migrate_pages
# SOURCE_OP="call"
# CONSTANT_VALUE=10
# OCCURENCE=1

# # %374 = call fastcc i32 @migrate_pages_batch(ptr noundef nonnull %8, ptr noundef readonly %1, ptr noundef %2, i64 noundef %3, i32 noundef range(i32 1, 0) %4, i32 noundef %5, ptr noundef nonnull %13, ptr noundef nonnull %14, ptr noundef nonnull %15, i32 noundef 7) #11, !dbg !13230
# # Conclusion: []
#
# SOURCE_FILE=mm/migrate.c
# FUNCTION_NAME=migrate_pages
# SOURCE_OP="call"
# CONSTANT_VALUE=7
# OCCURENCE=1

### 40. SHRINK_BATCH

# # %43 = select i1 %42, i64 128, i64 %41, !dbg !6489
# # Conclusion: []
#
# SOURCE_FILE=mm/shrinker.c
# FUNCTION_NAME=shrink_slab
# SOURCE_OP="select"
# CONSTANT_VALUE=128
# OCCURENCE=1

### 41.MMAP_LOTSAMISS

# # %33 = icmp ult i32 %32, 1000, !dbg !12770
# # Conclusion: []
#
# SOURCE_FILE=mm/filemap.c
# FUNCTION_NAME=do_sync_mmap_readahead
# SOURCE_OP="icmp"
# CONSTANT_VALUE=1000
# OCCURENCE=1

# # %36 = icmp samesign ugt i32 %32, 99, !dbg !12775
# # Conclusion: []
#
# SOURCE_FILE=mm/filemap.c
# FUNCTION_NAME=do_sync_mmap_readahead
# SOURCE_OP="icmp"
# CONSTANT_VALUE=99
# OCCURENCE=1

### 42. GET_PAGE_MAX_RETRY_NUM

# # %385 = icmp samesign ult i32 %142, 3, !dbg !8370
# # Conclusion: []
#
# SOURCE_FILE=mm/memory-failure.c
# FUNCTION_NAME=get_hwpoison_page
# SOURCE_OP="icmp"
# CONSTANT_VALUE=3
# OCCURENCE=1

# # %415 = icmp samesign ult i32 %142, 3, !dbg !8414
# # Conclusion: []
#
# SOURCE_FILE=mm/memory-failure.c
# FUNCTION_NAME=get_hwpoison_page
# SOURCE_OP="icmp"
# CONSTANT_VALUE=3
# OCCURENCE=2

# # %532 = icmp samesign ult i32 %142, 3, !dbg !8592
# # Conclusion: []
#
# SOURCE_FILE=mm/memory-failure.c
# FUNCTION_NAME=get_hwpoison_page
# SOURCE_OP="icmp"
# CONSTANT_VALUE=3
# OCCURENCE=4

### 43. MAX_MADVISE_GUARD_RETRIES TODO huge diff...

### 44. MAX_OOM_REAP_RETRIES

# # %162 = icmp eq i32 %161, 11, !dbg !11089
# # Conclusion: []
#
# SOURCE_FILE=mm/oom_kill.c
# FUNCTION_NAME=oom_reaper
# SOURCE_OP="icmp"
# CONSTANT_VALUE=11
# OCCURENCE=1

### 45. OOM_REAPER_DELAY

# # %42 = add i64 %41, 2000, !dbg !12071
# # Conclusion: []
#
# SOURCE_FILE=mm/oom_kill.c
# FUNCTION_NAME=out_of_memory
# SOURCE_OP="add"
# CONSTANT_VALUE=2000
# OCCURENCE=1

# # %29 = add i64 %28, 2000, !dbg !13498
# # Conclusion: []
#
# SOURCE_FILE=mm/oom_kill.c
# FUNCTION_NAME=oom_kill_process
# SOURCE_OP="add"
# CONSTANT_VALUE=2000
# OCCURENCE=1

# # %210 = add i64 %209, 2000, !dbg !13837
# # Conclusion: []
#
# SOURCE_FILE=mm/oom_kill.c
# FUNCTION_NAME=oom_kill_process
# SOURCE_OP="add"
# CONSTANT_VALUE=2000
# OCCURENCE=2

### 46. SHMEM_MAX_IQ_TIME

# # store i32 604800, ptr %14, align 4, !dbg !5812
# # Conclusion: []
#
# SOURCE_FILE=mm/shmem_quota.c
# FUNCTION_NAME=shmem_read_file_info
# SOURCE_OP="store"
# CONSTANT_VALUE=604800
# OCCURENCE=2

### 47. SHMEM_MAX_DQ_TIME

# # store i32 604800, ptr %13, align 8, !dbg !5810
# # Conclusion: []
#
# SOURCE_FILE=mm/shmem_quota.c
# FUNCTION_NAME=shmem_read_file_info
# SOURCE_OP="store"
# CONSTANT_VALUE=604800
# OCCURENCE=1

### 48. RCU_JIFFIES_FQS_DIV

# # %20 = lshr i32 %19, 8, !dbg !11201
# # Conclusion: []
#
# SOURCE_FILE=kernel/rcu/tree.c
# FUNCTION_NAME=param_set_next_fqs_jiffies
# SOURCE_OP="lshr"
# CONSTANT_VALUE=8
# OCCURENCE=1

# # %19 = lshr i32 %18, 8, !dbg !11248
# # Conclusion: []
#
# SOURCE_FILE=kernel/rcu/tree.c
# FUNCTION_NAME=param_set_first_fqs_jiffies
# SOURCE_OP="lshr"
# CONSTANT_VALUE=8
# OCCURENCE=1

# # %12 = lshr i32 %10, 8, !dbg !29158
# # Conclusion: []
#
# SOURCE_FILE=kernel/rcu/tree.c
# FUNCTION_NAME=rcu_init_geometry
# SOURCE_OP="lshr"
# CONSTANT_VALUE=8
# OCCURENCE=1

### 49. BLK_MAX_REQUEST_COUNT

# # %9 = tail call i16 @llvm.umin.i16(i16 %1, i16 32), !dbg !15975
# # Conclusion: []
#
# SOURCE_FILE=block/blk-core.c
# FUNCTION_NAME=blk_start_plug_nr_ios
# SOURCE_OP="call"
# CONSTANT_VALUE=32
# OCCURENCE=1

# # %33 = select i1 %32, i16 64, i16 32, !dbg !18839
# # Conclusion: []
#
# SOURCE_FILE=block/blk-mq.c
# FUNCTION_NAME=blk_add_rq_to_plug
# SOURCE_OP="select"
# CONSTANT_VALUE=64
# OCCURENCE=1

### 50. PEEK_MAX_IMPORT

# # %39 = tail call i64 @llvm.umin.i64(i64 %37, i64 256), !dbg !7213
# # Conclusion: []
#
# SOURCE_FILE=io_uring/kbuf.c
# FUNCTION_NAME=io_ring_buffers_peek
# SOURCE_OP="call"
# CONSTANT_VALUE=256
# OCCURENCE=1

# # %40 = select i1 %38, i64 256, i64 %39, !dbg !7213
# # Conclusion: []
#
# SOURCE_FILE=io_uring/kbuf.c
# FUNCTION_NAME=io_ring_buffers_peek
# SOURCE_OP="select"
# CONSTANT_VALUE=256
# OCCURENCE=1

### 51. IO_POLL_REF_BIAS

# # %74 = icmp sgt i32 %73, 127, !dbg !13567
# # Conclusion: []
#
# SOURCE_FILE=io_uring/poll.c
# FUNCTION_NAME=__io_arm_poll_handler
# SOURCE_OP="icmp"
# CONSTANT_VALUE=127
# OCCURENCE=1

# # %149 = icmp sgt i32 %148, 127, !dbg !13738
# # Conclusion: []
#
# SOURCE_FILE=io_uring/poll.c
# FUNCTION_NAME=__io_arm_poll_handler
# SOURCE_OP="icmp"
# CONSTANT_VALUE=127
# OCCURENCE=2

# # %27 = icmp sgt i32 %26, 127, !dbg !14002
# # Conclusion: []
#
# SOURCE_FILE=io_uring/poll.c
# FUNCTION_NAME=io_poll_wake
# SOURCE_OP="icmp"
# CONSTANT_VALUE=127
# OCCURENCE=1

# # %9 = icmp sgt i32 %8, 127, !dbg !14134
# # Conclusion: []
#
# SOURCE_FILE=io_uring/poll.c
# FUNCTION_NAME=io_poll_can_finish_inline
# SOURCE_OP="icmp"
# CONSTANT_VALUE=127
# OCCURENCE=1

# # %5 = icmp sgt i32 %4, 127, !dbg !14265
# # Conclusion: []
#
# SOURCE_FILE=io_uring/poll.c
# FUNCTION_NAME=io_pollfree_wake
# SOURCE_OP="icmp"
# CONSTANT_VALUE=127
# OCCURENCE=1

# # %4 = icmp sgt i32 %3, 127, !dbg !14606
# # Conclusion: []
#
# SOURCE_FILE=io_uring/poll.c
# FUNCTION_NAME=io_poll_cancel_req
# SOURCE_OP="icmp"
# CONSTANT_VALUE=127
# OCCURENCE=1

# # %49 = icmp sgt i32 %48, 127, !dbg !15046
# # Conclusion: []
#
# SOURCE_FILE=io_uring/poll.c
# FUNCTION_NAME=io_poll_remove
# SOURCE_OP="icmp"
# CONSTANT_VALUE=127
# OCCURENCE=1

### 52. APOLL_MAX_RETRY

# # store i32 128, ptr %77, align 4, !dbg !13272
# # Conclusion: []
#
# SOURCE_FILE=io_uring/poll.c
# FUNCTION_NAME=io_arm_poll_handler
# SOURCE_OP="store"
# CONSTANT_VALUE=128
# OCCURENCE=1

### 53. IO_TCTX_REFS_CACHE_NR

# # %3 = sub i32 1024, %2, !dbg !23482
# # Conclusion: []
#
# SOURCE_FILE=io_uring/io_uring.c
# FUNCTION_NAME=io_task_refs_refill
# SOURCE_OP="sub"
# CONSTANT_VALUE=1024
# OCCURENCE=1

### 54. IORING_MAX_ENTRIES

# # %5 = icmp ugt i32 %0, 32768, !dbg !27519
# # Conclusion: []
#
# SOURCE_FILE=io_uring/io_uring.c
# FUNCTION_NAME=io_uring_fill_params
# SOURCE_OP="icmp"
# CONSTANT_VALUE=32768
# OCCURENCE=1

# # %12 = phi i32 [ 32768, %8 ], [ %0, %4 ]
# # Conclusion: []
#
# SOURCE_FILE=io_uring/io_uring.c
# FUNCTION_NAME=io_uring_fill_params
# SOURCE_OP="phi"
# CONSTANT_VALUE=32768
# OCCURENCE=1

# # %32 = icmp ugt i32 %29, 65536, !dbg !27565
# # Conclusion: []
#
# SOURCE_FILE=io_uring/io_uring.c
# FUNCTION_NAME=io_uring_fill_params
# SOURCE_OP="icmp"
# CONSTANT_VALUE=65536
# OCCURENCE=1

# # %37 = phi i32 [ %29, %31 ], [ 65536, %33 ], !dbg !27571
# # Conclusion: []
#
# SOURCE_FILE=io_uring/io_uring.c
# FUNCTION_NAME=io_uring_fill_params
# SOURCE_OP="phi"
# CONSTANT_VALUE=65536
# OCCURENCE=1

### 55. IO_LOCAL_TW_DEFAULT_MAX

# # %15 = call fastcc i32 @__io_run_local_work(ptr noundef %0, ptr noundef nonnull %2, i32 noundef 2147483647, i32 noundef 20) #30, !dbg !25496
# # Conclusion: []
#
# SOURCE_FILE=io_uring/io_uring.c
# FUNCTION_NAME=io_run_task_work_sig
# SOURCE_OP="call"
# CONSTANT_VALUE=2147483647
# OCCURENCE=1

# # %170 = call i32 @llvm.smax.i32(i32 %136, i32 20)
# # Conclusion: []
#
# SOURCE_FILE=io_uring/io_uring.c
# FUNCTION_NAME=__se_sys_io_uring_enter
# SOURCE_OP="call"
# CONSTANT_VALUE=20
# OCCURENCE=1

# # %348 = call i32 @llvm.smax.i32(i32 %327, i32 20), !dbg !26588
# # Conclusion: []
#
# SOURCE_FILE=io_uring/io_uring.c
# FUNCTION_NAME=__se_sys_io_uring_enter
# SOURCE_OP="call"
# CONSTANT_VALUE=20
# OCCURENCE=2

# # %12 = tail call i32 @llvm.smax.i32(i32 %1, i32 20), !dbg !27272
# # Conclusion: []
#
# SOURCE_FILE=io_uring/io_uring.c
# FUNCTION_NAME=io_run_local_work_locked
# SOURCE_OP="call"
# CONSTANT_VALUE=20
# OCCURENCE=1

### 56. WORKER_INIT_LIMIT

# # %54 = icmp sgt i32 %52, 2, !dbg !8220
# # Conclusion: []
#
# SOURCE_FILE=io_uring/io-wq.c
# FUNCTION_NAME=create_worker_cont
# SOURCE_OP="icmp"
# CONSTANT_VALUE=2
# OCCURENCE=1

# # %70 = icmp sgt i32 %68, 2, !dbg !10343
# # Conclusion: []
#
# SOURCE_FILE=io_uring/io-wq.c
# FUNCTION_NAME=create_io_worker
# SOURCE_OP="icmp"
# CONSTANT_VALUE=2
# OCCURENCE=2

### 57. MULTISHOT_MAX_RETRY

# # %89 = icmp ult i32 %87, 32, !dbg !13549
# # Conclusion: []
#
# SOURCE_FILE=io_uring/net.c
# FUNCTION_NAME=io_recv_finish
# SOURCE_OP="icmp"
# CONSTANT_VALUE=32
# OCCURENCE=1

### 58. EP_MAX_NESTS

# # %10 = icmp samesign ugt i32 %1, 4
# # Conclusion: []
#
# SOURCE_FILE=fs/eventpoll.c
# FUNCTION_NAME=ep_loop_check_proc
# SOURCE_OP="icmp"
# CONSTANT_VALUE=4
# OCCURENCE=1

# # %3 = icmp samesign ugt i32 %1, 4, !dbg !15208
# # Conclusion: []
#
# SOURCE_FILE=fs/eventpoll.c
# FUNCTION_NAME=reverse_path_check_proc
# SOURCE_OP="icmp"
# CONSTANT_VALUE=4
# OCCURENCE=1

### 59. MAX_SLACK

# # %30 = udiv i32 100000000, %29, !dbg !12583
# # Conclusion: []
#
# SOURCE_FILE=fs/select.c
# FUNCTION_NAME=select_estimate_accuracy
# SOURCE_OP="udiv"
# CONSTANT_VALUE=100000000
# OCCURENCE=1

# # %38 = call i64 @llvm.smin.i64(i64 %37, i64 100000000), !dbg !12562
# # Conclusion: []
#
# SOURCE_FILE=fs/select.c
# FUNCTION_NAME=select_estimate_accuracy
# SOURCE_OP="call"
# CONSTANT_VALUE=100000000
# OCCURENCE=1

# # %40 = phi i64 [ 0, %9 ], [ 100000000, %22 ], [ %38, %33 ], !dbg !12562
# # Conclusion: []
#
# SOURCE_FILE=fs/select.c
# FUNCTION_NAME=select_estimate_accuracy
# SOURCE_OP="phi"
# CONSTANT_VALUE=0
# OCCURENCE=1

# # %140 = udiv i32 100000000, %139, !dbg !13223
# # Conclusion: []
#
# SOURCE_FILE=fs/select.c
# FUNCTION_NAME=do_select
# SOURCE_OP="udiv"
# CONSTANT_VALUE=100000000
# OCCURENCE=1

# # %148 = call i64 @llvm.smin.i64(i64 %147, i64 100000000), !dbg !13212
# # Conclusion: []
#
# SOURCE_FILE=fs/select.c
# FUNCTION_NAME=do_select
# SOURCE_OP="call"
# CONSTANT_VALUE=100000000
# OCCURENCE=1

# # %150 = phi i64 [ 0, %119 ], [ 100000000, %132 ], [ %148, %143 ], !dbg !13212
# # Conclusion: []
#
# SOURCE_FILE=fs/select.c
# FUNCTION_NAME=do_select
# SOURCE_OP="phi"
# CONSTANT_VALUE=100000000
# OCCURENCE=1

# # %90 = udiv i32 100000000, %89, !dbg !14353
# # Conclusion: []
#
# SOURCE_FILE=fs/select.c
# FUNCTION_NAME=do_sys_poll
# SOURCE_OP="udiv"
# CONSTANT_VALUE=100000000
# OCCURENCE=1

# # %98 = call i64 @llvm.smin.i64(i64 %97, i64 100000000), !dbg !14342
# # Conclusion: []
#
# SOURCE_FILE=fs/select.c
# FUNCTION_NAME=do_sys_poll
# SOURCE_OP="call"
# CONSTANT_VALUE=100000000
# OCCURENCE=1

# # %100 = phi i64 [ 0, %69 ], [ 100000000, %82 ], [ %98, %93 ], !dbg !14342
# # Conclusion: []
#
# SOURCE_FILE=fs/select.c
# FUNCTION_NAME=do_sys_poll
# SOURCE_OP="phi"
# CONSTANT_VALUE=0
# OCCURENCE=1

### 60. SYNC_SHRINK_BATCH

# # %23 = tail call fastcc i64 @mb_cache_shrink(ptr noundef %0, i64 noundef 64) #13, !dbg !1450
# # Conclusion: []
#
# SOURCE_FILE=fs/mbcache.c
# FUNCTION_NAME=mb_cache_entry_create
# SOURCE_OP="call"
# CONSTANT_VALUE=64
# OCCURENCE=2

### 61. SHRINK_DIVISOR

# # %5 = lshr i64 %4, 4, !dbg !2063
# # Conclusion: []
#
# SOURCE_FILE=fs/mbcache.c
# FUNCTION_NAME=mb_cache_shrink_worker
# SOURCE_OP="lshr"
# CONSTANT_VALUE=4
# OCCURENCE=1

### 62. PIPE_MIN_DEF_BUFFERS

# # %41 = sub nsw i64 2, %28, !dbg !9368
# # Conclusion: []
#
# SOURCE_FILE=fs/pipe.c
# FUNCTION_NAME=alloc_pipe_info
# SOURCE_OP="sub"
# CONSTANT_VALUE=2
# OCCURENCE=1

# # %46 = phi i64 [ 2, %40 ], [ %28, %38 ], [ %28, %27 ], [ %28, %36 ], !dbg !9225
# # Conclusion: []
#
# SOURCE_FILE=fs/pipe.c
# FUNCTION_NAME=alloc_pipe_info
# SOURCE_OP="phi"
# CONSTANT_VALUE=2
# OCCURENCE=2

### 63. AIO_PLUG_THRESHOLD

# # %15 = icmp samesign ugt i64 %14, 2, !dbg !11277
# # Conclusion: []
#
# SOURCE_FILE=fs/aio.c
# FUNCTION_NAME=__se_sys_io_submit
# SOURCE_OP="icmp"
# CONSTANT_VALUE=2
# OCCURENCE=1

# # %21 = icmp samesign ugt i32 %20, 2, !dbg !13765
# # Conclusion: []
#
# SOURCE_FILE=fs/aio.c
# FUNCTION_NAME=__ia32_compat_sys_io_submit
# SOURCE_OP="icmp"
# CONSTANT_VALUE=2
# OCCURENCE=1

### 64. LAST_INO_BATCH

# # %5 = and i32 %4, 1023, !dbg !14456
# # Conclusion: []
#
# SOURCE_FILE=fs/inode.c
# FUNCTION_NAME=get_next_ino
# SOURCE_OP="and"
# CONSTANT_VALUE=1023
# OCCURENCE=1

# # %8 = tail call i32 asm sideeffect ".pushsection .smp_locks,\22a\22\0A.balign 4\0A.long 671f - .\0A.popsection\0A671:\0A\09lock; xaddl $0, $1\0A", "=r,=*m,0,*m,~{memory},~{cc},~{dirflag},~{fpsr},~{flags}"(ptr nonnull elementtype(i32) @get_next_ino.shared_last_ino, i32 1024, ptr nonnull elementtype(i32) @get_next_ino.shared_last_ino) #20, !dbg !14468, !srcloc !14092
# # Conclusion: []
#
# SOURCE_FILE=fs/inode.c
# FUNCTION_NAME=get_next_ino
# SOURCE_OP="call"
# CONSTANT_VALUE=1024
# OCCURENCE=1

### 65. IWALK_MAX_INODE_PREFETCH

# # %17 = tail call i32 @llvm.umin.i32(i32 %5, i32 2048), !dbg !7165
# # Conclusion: []
#
# SOURCE_FILE=fs/xfs/xfs_iwalk.c
# FUNCTION_NAME=xfs_iwalk
# SOURCE_OP="call"
# CONSTANT_VALUE=2048
# OCCURENCE=1

# # %24 = select i1 %16, i32 40, i32 %23, !dbg !7162
# # Conclusion: []
#
# SOURCE_FILE=fs/xfs/xfs_iwalk.c
# FUNCTION_NAME=xfs_iwalk
# SOURCE_OP="select"
# CONSTANT_VALUE=40
# OCCURENCE=1

# # %20 = call i32 @llvm.umin.i32(i32 %4, i32 2048)
# # Conclusion: []
#
# SOURCE_FILE=fs/xfs/xfs_iwalk.c
# FUNCTION_NAME=xfs_iwalk_threaded
# SOURCE_OP="call"
# CONSTANT_VALUE=2048
# OCCURENCE=1

# # %27 = select i1 %19, i32 40, i32 %26
# # Conclusion: []
#
# SOURCE_FILE=fs/xfs/xfs_iwalk.c
# FUNCTION_NAME=xfs_iwalk_threaded
# SOURCE_OP="select"
# CONSTANT_VALUE=40
# OCCURENCE=1

### 66. MAX_INOBT_WALK_PREFETCH

# # %18 = tail call i32 @llvm.umin.i32(i32 %17, i32 256), !dbg !8513
# # Conclusion: []
#
# SOURCE_FILE=fs/xfs/xfs_iwalk.c
# FUNCTION_NAME=xfs_inobt_walk
# SOURCE_OP="call"
# CONSTANT_VALUE=256
# OCCURENCE=1

# # %19 = select i1 %16, i32 256, i32 %18, !dbg !8508
# # Conclusion: []
#
# SOURCE_FILE=fs/xfs/xfs_iwalk.c
# FUNCTION_NAME=xfs_inobt_walk
# SOURCE_OP="select"
# CONSTANT_VALUE=256
# OCCURENCE=1

### 67. XFS_DISCARD_MAX_EXAMINE

# # %68 = phi i32 [ %73, %64 ], [ 100, %56 ]
# # Conclusion: []
#
# SOURCE_FILE=fs/xfs/xfs_discard.c
# FUNCTION_NAME=xfs_trim_gather_extents
# SOURCE_OP="phi"
# CONSTANT_VALUE=100
# OCCURENCE=1

### 68. XFS_ICOUNT_BATCH

# # tail call void @percpu_counter_add_batch(ptr noundef nonnull %57, i64 noundef %49, i32 noundef 128) #10, !dbg !8305
# # Conclusion: []
#
# SOURCE_FILE=fs/xfs/xfs_trans.c
# FUNCTION_NAME=xfs_trans_unreserve_and_mod_sb
# SOURCE_OP="call"
# CONSTANT_VALUE=128
# OCCURENCE=1

### 69. DEF_PRIORITY

# # store i64 2049, ptr %14, align 8, !dbg !14247
# # Conclusion: []
#
# SOURCE_FILE=fs/xfs/xfs_icache.c
# FUNCTION_NAME=xfs_inodegc_register_shrinker
# SOURCE_OP="store"
# CONSTANT_VALUE=2049
# OCCURENCE=1

# # %38 = phi i64 [ 0, %2 ], [ 0, %17 ], [ 0, %13 ], [ 0, %22 ], [ 4096, %26 ], !dbg !14273
# # Conclusion: []
#
# SOURCE_FILE=fs/xfs/xfs_icache.c
# FUNCTION_NAME=xfs_inodegc_shrinker_count
# SOURCE_OP="phi"
# CONSTANT_VALUE=0
# OCCURENCE=2

# # store i8 12, ptr %27, align 4, !dbg !13374, !DIAssignID !13375
# # Conclusion: []
#
# SOURCE_FILE=mm/vmscan.c
# FUNCTION_NAME=kswapd
# SOURCE_OP="store"
# CONSTANT_VALUE=12
# OCCURENCE=1

# # %230 = icmp eq i8 %229, 10
# # Conclusion: []
#
# SOURCE_FILE=mm/vmscan.c
# FUNCTION_NAME=kswapd
# SOURCE_OP="icmp"
# CONSTANT_VALUE=10
# OCCURENCE=1

# # %270 = icmp slt i8 %269, 10, !dbg !13571
# # Conclusion: []
#
# SOURCE_FILE=mm/vmscan.c
# FUNCTION_NAME=kswapd
# SOURCE_OP="icmp"
# CONSTANT_VALUE=10
# OCCURENCE=2

# # %505 = icmp eq i8 %256, 12
# # Conclusion: []
#
# SOURCE_FILE=mm/vmscan.c
# FUNCTION_NAME=shrink_node
# SOURCE_OP="icmp"
# CONSTANT_VALUE=12
# OCCURENCE=1

# # %857 = icmp sgt i8 %856, 9, !dbg !15534
# # Conclusion: []
#
# SOURCE_FILE=mm/vmscan.c
# FUNCTION_NAME=shrink_node
# SOURCE_OP="icmp"
# CONSTANT_VALUE=9
# OCCURENCE=1

# # store i8 12, ptr %17, align 4, !dbg !21129, !DIAssignID !21143
# # Conclusion: []
#
# SOURCE_FILE=mm/vmscan.c
# FUNCTION_NAME=try_to_free_pages
# SOURCE_OP="store"
# CONSTANT_VALUE=12
# OCCURENCE=1

# # %163 = icmp slt i8 %162, 10, !dbg !21768
# # Conclusion: []
#
# SOURCE_FILE=mm/vmscan.c
# FUNCTION_NAME=do_try_to_free_pages
# SOURCE_OP="icmp"
# CONSTANT_VALUE=10
# OCCURENCE=1

# # store i8 12, ptr %7, align 4, !dbg !22101, !DIAssignID !22124
# # Conclusion: []
#
# SOURCE_FILE=mm/vmscan.c
# FUNCTION_NAME=shrink_all_memory
# SOURCE_OP="store"
# CONSTANT_VALUE=12
# OCCURENCE=1

### 70. BLK_PLUG_FLUSH_SIZE

# # %44 = icmp ugt i32 %43, 131071, !dbg !18860
# # Conclusion: []
#
# SOURCE_FILE=block/blk-mq.c
# FUNCTION_NAME=blk_add_rq_to_plug
# SOURCE_OP="icmp"
# CONSTANT_VALUE=131071
# OCCURENCE=1

### 71. BOOST_GC_MULTIPLE

# # %77 = mul i32 %56, 5
# # Conclusion: []
#
# SOURCE_FILE=fs/f2fs/gc.c
# FUNCTION_NAME=do_garbage_collect
# SOURCE_OP="mul"
# CONSTANT_VALUE=5
# OCCURENCE=1

### 72. BTRFS_MAX_BIO_SECTORS

# # %26 = shl i32 %25, 8, !dbg !7628
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/direct-io.c
# FUNCTION_NAME=btrfs_dio_iomap_begin
# SOURCE_OP="shl"
# CONSTANT_VALUE=8
# OCCURENCE=1

### 73. RBIO_CACHE_SIZE

# # %58 = icmp sgt i32 %57, 1024, !dbg !10347
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/raid56.c
# FUNCTION_NAME=unlock_stripe
# SOURCE_OP="icmp"
# CONSTANT_VALUE=1024
# OCCURENCE=1

### 74. SEND_MAX_EXTENT_REFS

# # %22 = icmp ugt i64 %5, 1024, !dbg !20518
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/send.c
# FUNCTION_NAME=check_extent_item
# SOURCE_OP="icmp"
# CONSTANT_VALUE=1024
# OCCURENCE=1

### 75. BTRFS_DELAYED_WRITEBACK

# # %14 = icmp sgt i32 %13, 511, !dbg !9613
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=btrfs_balance_delayed_items
# SOURCE_OP="icmp"
# CONSTANT_VALUE=511
# OCCURENCE=1

# # %53 = icmp slt i32 %50, 512
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=btrfs_async_run_delayed_root
# SOURCE_OP="icmp"
# CONSTANT_VALUE=512
# OCCURENCE=1

### 76. BTRFS_DELAYED_BACKGROUND

# # %35 = icmp slt i32 %34, 128, !dbg !8646
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=btrfs_release_delayed_item
# SOURCE_OP="icmp"
# CONSTANT_VALUE=128
# OCCURENCE=1

# # %99 = icmp slt i32 %98, 128, !dbg !8923
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=__btrfs_update_delayed_inode
# SOURCE_OP="icmp"
# CONSTANT_VALUE=128
# OCCURENCE=1

# # %132 = icmp slt i32 %131, 128, !dbg !8995
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=__btrfs_update_delayed_inode
# SOURCE_OP="icmp"
# CONSTANT_VALUE=128
# OCCURENCE=2

# # %7 = icmp slt i32 %6, 128, !dbg !9602
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=btrfs_balance_delayed_items
# SOURCE_OP="icmp"
# CONSTANT_VALUE=128
# OCCURENCE=1

# # %33 = icmp sgt i32 %32, 127, !dbg !9686
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=btrfs_balance_delayed_items
# SOURCE_OP="icmp"
# CONSTANT_VALUE=127
# OCCURENCE=1

# # %44 = icmp sgt i32 %43, 127, !dbg !9706
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=btrfs_balance_delayed_items
# SOURCE_OP="icmp"
# CONSTANT_VALUE=127
# OCCURENCE=2

# # %13 = icmp slt i32 %12, 64, !dbg !9774
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=btrfs_async_run_delayed_root
# SOURCE_OP="icmp"
# CONSTANT_VALUE=64
# OCCURENCE=1

# # %46 = icmp slt i32 %45, 128, !dbg !12569
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=__btrfs_kill_delayed_node
# SOURCE_OP="icmp"
# CONSTANT_VALUE=128
# OCCURENCE=1

# # %81 = icmp slt i32 %80, 128, !dbg !12644
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=__btrfs_kill_delayed_node
# SOURCE_OP="icmp"
# CONSTANT_VALUE=128
# OCCURENCE=2

### 77. BTRFS_DELAYED_BATCH

# # %36 = and i32 %31, 15
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=btrfs_release_delayed_item
# SOURCE_OP="and"
# CONSTANT_VALUE=15
# OCCURENCE=1

# # %37 = icmp eq i32 %36, 15
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=btrfs_release_delayed_item
# SOURCE_OP="icmp"
# CONSTANT_VALUE=15
# OCCURENCE=1

# # %100 = and i32 %95, 15
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=__btrfs_update_delayed_inode
# SOURCE_OP="and"
# CONSTANT_VALUE=15
# OCCURENCE=1

# # %101 = icmp eq i32 %100, 15
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=__btrfs_update_delayed_inode
# SOURCE_OP="icmp"
# CONSTANT_VALUE=15
# OCCURENCE=1

# # %133 = and i32 %128, 15
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=__btrfs_update_delayed_inode
# SOURCE_OP="and"
# CONSTANT_VALUE=15
# OCCURENCE=2

# # %134 = icmp eq i32 %133, 15
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=__btrfs_update_delayed_inode
# SOURCE_OP="icmp"
# CONSTANT_VALUE=15
# OCCURENCE=2

# # %28 = add i32 %17, 16
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=btrfs_balance_delayed_items
# SOURCE_OP="add"
# CONSTANT_VALUE=16
# OCCURENCE=1

# # store i32 16, ptr %61, align 8, !dbg !9729
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=btrfs_balance_delayed_items
# SOURCE_OP="store"
# CONSTANT_VALUE=16
# OCCURENCE=1

# # %47 = and i32 %42, 15
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=__btrfs_kill_delayed_node
# SOURCE_OP="and"
# CONSTANT_VALUE=15
# OCCURENCE=1

# # %48 = icmp eq i32 %47, 15
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=__btrfs_kill_delayed_node
# SOURCE_OP="icmp"
# CONSTANT_VALUE=15
# OCCURENCE=1

# # %82 = and i32 %77, 15
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=__btrfs_kill_delayed_node
# SOURCE_OP="and"
# CONSTANT_VALUE=15
# OCCURENCE=2

# # %83 = icmp eq i32 %82, 15
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/delayed-inode.c
# FUNCTION_NAME=__btrfs_kill_delayed_node
# SOURCE_OP="icmp"
# CONSTANT_VALUE=15
# OCCURENCE=2

### 78. BTRFS_DEFRAG_BATCH

# # %130 = call i32 @btrfs_defrag_file(ptr noundef %99, ptr noundef nonnull %3, ptr noundef nonnull %2, i64 noundef %129, i64 noundef 1024) #16, !dbg !7255
# # Conclusion: []
#
# SOURCE_FILE=fs/btrfs/defrag.c
# FUNCTION_NAME=btrfs_run_defrag_inodes
# SOURCE_OP="call"
# CONSTANT_VALUE=1024
# OCCURENCE=1

### 79. RC_EXPIRE

# # %6 = add i64 %5, -120000, !dbg !12695
# # Conclusion: []
#
# SOURCE_FILE=fs/nfsd/nfscache.c
# FUNCTION_NAME=nfsd_prune_bucket_locked
# SOURCE_OP="add"
# CONSTANT_VALUE=-120000
# OCCURENCE=1

### 80. NFSD_LAUNDRETTE_DELAY

# # %69 = tail call zeroext i1 @queue_delayed_work_on(i32 noundef 64, ptr noundef %68, ptr noundef nonnull @nfsd_filecache_laundrette, i64 noundef 2000) #14, !dbg !13190
# # Conclusion: []
#
# SOURCE_FILE=fs/nfsd/filecache.c
# FUNCTION_NAME=nfsd_file_put
# SOURCE_OP="call"
# CONSTANT_VALUE=64
# OCCURENCE=1

# # %139 = call zeroext i1 @queue_delayed_work_on(i32 noundef 64, ptr noundef %138, ptr noundef nonnull @nfsd_filecache_laundrette, i64 noundef 2000) #14, !dbg !15890
# # Conclusion: []
#
# SOURCE_FILE=fs/nfsd/filecache.c
# FUNCTION_NAME=nfsd_file_gc_worker
# SOURCE_OP="call"
# CONSTANT_VALUE=64
# OCCURENCE=1

### 81. MAX_MKSPC_RETRIES

# # %37 = icmp eq i32 %36, 4, !dbg !6899
# # Conclusion: []
#
# SOURCE_FILE=fs/ubifs/budget.c
# FUNCTION_NAME=make_free_space
# SOURCE_OP="icmp"
# CONSTANT_VALUE=4
# OCCURENCE=1

### 82. NR_TO_WRITE

# # tail call void @writeback_inodes_sb_nr(ptr noundef %16, i64 noundef 16, i32 noundef 5) #6, !dbg !6852
# # Conclusion: []
#
# SOURCE_FILE=fs/ubifs/budget.c
# FUNCTION_NAME=make_free_space
# SOURCE_OP="call"
# CONSTANT_VALUE=16
# OCCURENCE=1

### 83. NFS4_POLL_RETRY_MIN

# # %36 = select i1 %34, i64 100, i64 %35, !dbg !19718
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs4proc.c
# FUNCTION_NAME=nfs4_handle_exception
# SOURCE_OP="select"
# CONSTANT_VALUE=100
# OCCURENCE=1

# # %50 = select i1 %48, i64 100, i64 %49, !dbg !19780
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs4proc.c
# FUNCTION_NAME=nfs4_handle_exception
# SOURCE_OP="select"
# CONSTANT_VALUE=100
# OCCURENCE=2

# # %29 = select i1 %27, i64 100, i64 %28, !dbg !21012
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs4proc.c
# FUNCTION_NAME=nfs4_async_handle_exception
# SOURCE_OP="select"
# CONSTANT_VALUE=100
# OCCURENCE=1

# # tail call void @rpc_delay(ptr noundef %0, i64 noundef 100) #20, !dbg !40040
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs4proc.c
# FUNCTION_NAME=nfs4_get_lease_time_done
# SOURCE_OP="call"
# CONSTANT_VALUE=100
# OCCURENCE=1

# # %124 = select i1 %121, i64 200, i64 %123, !dbg !40690
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs4proc.c
# FUNCTION_NAME=nfs4_proc_layoutget
# SOURCE_OP="select"
# CONSTANT_VALUE=200
# OCCURENCE=1

### 84. NFS4_POLL_RETRY_MAX

# # tail call void @rpc_delay(ptr noundef %0, i64 noundef 15000) #20, !dbg !17785
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs4proc.c
# FUNCTION_NAME=nfs41_sequence_call_done
# SOURCE_OP="call"
# CONSTANT_VALUE=15000
# OCCURENCE=1

# # tail call void @rpc_delay(ptr noundef %0, i64 noundef 15000) #20, !dbg !18039
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs4proc.c
# FUNCTION_NAME=nfs41_sequence_process
# SOURCE_OP="call"
# CONSTANT_VALUE=15000
# OCCURENCE=1

# # %35 = tail call i64 @llvm.umin.i64(i64 %33, i64 15000), !dbg !19718
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs4proc.c
# FUNCTION_NAME=nfs4_handle_exception
# SOURCE_OP="call"
# CONSTANT_VALUE=15000
# OCCURENCE=1

# # %49 = tail call i64 @llvm.umin.i64(i64 %47, i64 15000), !dbg !19780
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs4proc.c
# FUNCTION_NAME=nfs4_handle_exception
# SOURCE_OP="call"
# CONSTANT_VALUE=15000
# OCCURENCE=2

# # %28 = tail call i64 @llvm.umin.i64(i64 %26, i64 15000), !dbg !21012
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs4proc.c
# FUNCTION_NAME=nfs4_async_handle_exception
# SOURCE_OP="call"
# CONSTANT_VALUE=15000
# OCCURENCE=1

# # tail call void @rpc_delay(ptr noundef %0, i64 noundef 15000) #20, !dbg !24786
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs4proc.c
# FUNCTION_NAME=nfs4_reclaim_complete_done
# SOURCE_OP="call"
# CONSTANT_VALUE=15000
# OCCURENCE=1

# # %122 = call i64 @llvm.umin.i64(i64 %120, i64 15000), !dbg !40690
# # Conclusion: []
#
# SOURCE_FILE=fs/nfs/nfs4proc.c
# FUNCTION_NAME=nfs4_proc_layoutget
# SOURCE_OP="call"
# CONSTANT_VALUE=15000
# OCCURENCE=1

### 85. SOFT_LEBS_LIMIT

# # %47 = icmp samesign ugt i32 %45, 4, !dbg !7578
# # Conclusion: []
#
# SOURCE_FILE=fs/ubifs/gc.c
# FUNCTION_NAME=ubifs_garbage_collect
# SOURCE_OP="icmp"
# CONSTANT_VALUE=4
# OCCURENCE=1

# # %92 = icmp samesign ult i32 %45, 4, !dbg !7642
# # Conclusion: []
#
# SOURCE_FILE=fs/ubifs/gc.c
# FUNCTION_NAME=ubifs_garbage_collect
# SOURCE_OP="icmp"
# CONSTANT_VALUE=4
# OCCURENCE=2

### 86. HARD_LEBS_LIMIT

# # %52 = icmp samesign ugt i32 %45, 32, !dbg !7585
# # Conclusion: []
#
# SOURCE_FILE=fs/ubifs/gc.c
# FUNCTION_NAME=ubifs_garbage_collect
# SOURCE_OP="icmp"
# CONSTANT_VALUE=32
# OCCURENCE=1

### 87. DEF_RECLAIM_PREFREE_SEGMENTS

# # %32 = mul i32 %27, 5, !dbg !24812
# # Conclusion: []
#
# SOURCE_FILE=fs/f2fs/segment.c
# FUNCTION_NAME=f2fs_build_segment_manager
# SOURCE_OP="mul"
# CONSTANT_VALUE=5
# OCCURENCE=1

### 88. DEF_MAX_RECLAIM_PREFREE_SEGMENTS

# # %35 = icmp ugt i32 %32, 409699, !dbg !24815
# # Conclusion: []
#
# SOURCE_FILE=fs/f2fs/segment.c
# FUNCTION_NAME=f2fs_build_segment_manager
# SOURCE_OP="icmp"
# CONSTANT_VALUE=409699
# OCCURENCE=1

# # %36 = select i1 %35, i32 4096, i32 %33, !dbg !24815
# # Conclusion: []
#
# SOURCE_FILE=fs/f2fs/segment.c
# FUNCTION_NAME=f2fs_build_segment_manager
# SOURCE_OP="select"
# CONSTANT_VALUE=4096
# OCCURENCE=1

### 89. MAX_SKIP_GC_COUNT

# # %255 = icmp ult i32 %253, 17, !dbg !8825
# # Conclusion: []
#
# SOURCE_FILE=fs/f2fs/gc.c
# FUNCTION_NAME=f2fs_gc
# SOURCE_OP="icmp"
# CONSTANT_VALUE=17
# OCCURENCE=1

### 90. MAX_RA_NODE

# # tail call fastcc void @f2fs_ra_node_pages(ptr noundef nonnull %2, i32 noundef %28, i32 noundef 128) #18, !dbg !13609
# # Conclusion: []
#
# SOURCE_FILE=fs/f2fs/node.c
# FUNCTION_NAME=__get_node_page
# SOURCE_OP="call"
# CONSTANT_VALUE=128
# OCCURENCE=1

### 91. MAX_VMAP_RETRIES

# TODO

### 92. DEF_GC_THREAD_URGENT_SLEEP_TIME

# # store i32 500, ptr %11, align 8, !dbg !6940
# # Conclusion: []
#
# SOURCE_FILE=fs/f2fs/gc.c
# FUNCTION_NAME=f2fs_start_gc_thread
# SOURCE_OP="store"
# CONSTANT_VALUE=500
# OCCURENCE=1

### 93. MAX_SOFTIRQ_TIME

# # %108 = add i64 %107, -2, !dbg !10335
# # Conclusion: []
#
# SOURCE_FILE=kernel/softirq.c
# FUNCTION_NAME=handle_softirqs
# SOURCE_OP="add"
# CONSTANT_VALUE=-2
# OCCURENCE=1

### Try KLP bad case

# %278 = icmp sgt i32 %262, 15, !dbg !17195
# Conclusion: []
#
# SOURCE_FILE=net/ipv4/tcp.c
# FUNCTION_NAME=tcp_sendmsg_locked
# SOURCE_OP="icmp"
# CONSTANT_VALUE=15
# OCCURENCE=1
