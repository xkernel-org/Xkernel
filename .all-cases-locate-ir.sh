### 1. DFR_MAX

# SOURCE_FILE=net/sunrpc/cache.c
# DEFINITION_SOURCE_FILE=net/sunrpc/cache.c
# SED_PATTERN='s|\#define	DFR_MAX	300|#define	DFR_MAX	299|'

### 2. GSSD_MIN_TIMEOUT

# SOURCE_FILE=net/sunrpc/auth_gss/auth_gss.c
# DEFINITION_SOURCE_FILE=net/sunrpc/auth_gss/auth_gss.c
# SED_PATTERN='s|\#define GSSD_MIN_TIMEOUT (60 \* 60)|#define GSSD_MIN_TIMEOUT (60 \* 30)|'

### 3. SMC_TX_WORK_DELAY

# SOURCE_FILE=net/smc/smc_tx.c
# DEFINITION_SOURCE_FILE=net/smc/smc_tx.c
# SED_PATTERN='s|\#define SMC_TX_WORK_DELAY	0|#define SMC_TX_WORK_DELAY	7|'

### 4. SMC_LGR_NUM_INCR

# SOURCE_FILE=net/smc/smc_core.c
# DEFINITION_SOURCE_FILE=net/smc/smc_core.c
# SED_PATTERN='s|\#define SMC_LGR_NUM_INCR		256|#define SMC_LGR_NUM_INCR		253|'

### 5. RDS_IB_RECYCLE_BATCH_COUNT

# SOURCE_FILE=net/rds/ib_recv.c
# DEFINITION_SOURCE_FILE=net/rds/ib.h
# SED_PATTERN='s|\#define RDS_IB_RECYCLE_BATCH_COUNT	32|#define RDS_IB_RECYCLE_BATCH_COUNT	31|'

### 6. QUEUE_THRESHOLD

# SOURCE_FILE=net/sched/sch_pie.c
# DEFINITION_SOURCE_FILE=include/net/pie.h
# SED_PATTERN='s|\#define QUEUE_THRESHOLD	16384|#define QUEUE_THRESHOLD	16381|'

### 7. PIE_SCALE

# SOURCE_FILE=net/sched/sch_pie.c
# DEFINITION_SOURCE_FILE=include/net/pie.h
# SED_PATTERN='s|\#define PIE_SCALE	8|#define PIE_SCALE	7|'

### 8. BUSY_POLL_BUDGET (invoked in two files)

# SOURCE_FILE=io_uring/napi.c
# DEFINITION_SOURCE_FILE=include/net/busy_poll.h
# SED_PATTERN='s|\#define BUSY_POLL_BUDGET 8|\#define BUSY_POLL_BUDGET 7|'

# SOURCE_FILE=fs/eventpoll.c
# DEFINITION_SOURCE_FILE=include/net/busy_poll.h
# SED_PATTERN='s|\#define BUSY_POLL_BUDGET 8|\#define BUSY_POLL_BUDGET 7|'

### 9. MLD_MAX_QUEUE

# FIXME huge diff

# SOURCE_FILE=net/ipv6/mcast.c
# DEFINITION_SOURCE_FILE=include/net/mld.h
# SED_PATTERN='s|\#define MLD_MAX_QUEUE		8|\#define MLD_MAX_QUEUE		16|'

### 10. MLD_MAX_SKBS

# SOURCE_FILE=net/ipv6/mcast.c
# DEFINITION_SOURCE_FILE=include/net/mld.h
# SED_PATTERN='s|\#define MLD_MAX_SKBS		32|\#define MLD_MAX_SKBS		16|'

### 11. TCP_MAX_QUICKACKS

# SOURCE_FILE=net/ipv4/tcp_input.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_MAX_QUICKACKS	16U|\#define TCP_MAX_QUICKACKS	15U|'

### 12. TCP_MAX_WSCALE

# SOURCE_FILE=net/core/filter.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_MAX_WSCALE		14U|\#define TCP_MAX_WSCALE		13U|'

# SOURCE_FILE=net/ipv4/tcp.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_MAX_WSCALE		14U|\#define TCP_MAX_WSCALE		13U|'

# SOURCE_FILE=net/ipv4/tcp_input.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_MAX_WSCALE		14U|\#define TCP_MAX_WSCALE		13U|'

# SOURCE_FILE=net/ipv4/tcp_output.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_MAX_WSCALE		14U|\#define TCP_MAX_WSCALE		13U|'

# SOURCE_FILE=net/netfilter/nf_conntrack_proto_tcp.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_MAX_WSCALE		14U|\#define TCP_MAX_WSCALE		13U|'

# SOURCE_FILE=net/netfilter/nf_synproxy_core.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_MAX_WSCALE		14U|\#define TCP_MAX_WSCALE		13U|'

### 13. TCP_DELACK_MAX

# SOURCE_FILE=net/core/filter.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_DELACK_MAX	((unsigned)(HZ/5))|\#define TCP_DELACK_MAX	10|'

# SOURCE_FILE=net/dccp/output.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_DELACK_MAX	((unsigned)(HZ/5))|\#define TCP_DELACK_MAX	10|'

# SOURCE_FILE=net/ipv4/tcp.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_DELACK_MAX	((unsigned)(HZ/5))|\#define TCP_DELACK_MAX	10|'

# SOURCE_FILE=net/ipv4/tcp_input.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_DELACK_MAX	((unsigned)(HZ/5))|\#define TCP_DELACK_MAX	10|'

# FIXME huge diff
# SOURCE_FILE=net/ipv4/tcp_output.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_DELACK_MAX	((unsigned)(HZ/5))|\#define TCP_DELACK_MAX	10|'

### 14. TCP_DELACK_MIN

# SOURCE_FILE=net/dccp/timer.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_DELACK_MIN	((unsigned)(HZ/25))|\#define TCP_DELACK_MIN	10|'

# SOURCE_FILE=net/ipv4/tcp_output.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_DELACK_MIN	((unsigned)(HZ/25))|\#define TCP_DELACK_MIN	10|'

### 15. TCP_ATO_MIN

# SOURCE_FILE=net/dccp/output.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_ATO_MIN	((unsigned)(HZ/25))|\#define TCP_ATO_MIN	10|'

# SOURCE_FILE=net/dccp/timer.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_ATO_MIN	((unsigned)(HZ/25))|\#define TCP_ATO_MIN	10|'

# SOURCE_FILE=net/ipv4/tcp_input.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_ATO_MIN	((unsigned)(HZ/25))|\#define TCP_ATO_MIN	10|'

# SOURCE_FILE=net/ipv4/tcp_output.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_ATO_MIN	((unsigned)(HZ/25))|\#define TCP_ATO_MIN	10|'

# SOURCE_FILE=net/ipv4/tcp_timer.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_ATO_MIN	((unsigned)(HZ/25))|\#define TCP_ATO_MIN	10|'

### 16. TCP_TIMEOUT_MIN

# SOURCE_FILE=net/core/filter.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_TIMEOUT_MIN	(2U)|\#define TCP_TIMEOUT_MIN	10|'

# SOURCE_FILE=net/ipv4/tcp_input.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_TIMEOUT_MIN	(2U)|\#define TCP_TIMEOUT_MIN	10|'

# SOURCE_FILE=net/ipv4/tcp_timer.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_TIMEOUT_MIN	(2U)|\#define TCP_TIMEOUT_MIN	10|'

### 17. TCP_TIMEOUT_MIN_US

# SOURCE_FILE=net/ipv4/tcp_output.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_TIMEOUT_MIN_US (2\*USEC_PER_MSEC)|\#define TCP_TIMEOUT_MIN_US 10|'

# SOURCE_FILE=net/ipv4/tcp_recovery.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_TIMEOUT_MIN_US (2\*USEC_PER_MSEC)|\#define TCP_TIMEOUT_MIN_US 10|'

### 18. MAX_GRO_SKBS

# SOURCE_FILE=net/core/gro.c
# DEFINITION_SOURCE_FILE=net/core/gro.c
# SED_PATTERN='s|\#define MAX_GRO_SKBS 8|\#define MAX_GRO_SKBS 7|'

### 19. BLK_MQ_CPU_WORK_BATCH

# SOURCE_FILE=block/blk-mq.c
# DEFINITION_SOURCE_FILE=block/blk-mq.h
# SED_PATTERN='s|\#define BLK_MQ_CPU_WORK_BATCH	(8)|\#define BLK_MQ_CPU_WORK_BATCH	(7)|'

### 20. TCP_THIN_LINEAR_RETRIES

# SOURCE_FILE=net/ipv4/tcp_timer.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_THIN_LINEAR_RETRIES 6|\#define TCP_THIN_LINEAR_RETRIES 5|'

### 21. TCP_INIT_CWND

# SOURCE_FILE=net/ipv4/tcp.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_INIT_CWND		10|\#define TCP_INIT_CWND		9|'

# SOURCE_FILE=net/ipv4/tcp_bbr.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_INIT_CWND		10|\#define TCP_INIT_CWND		9|'

# SOURCE_FILE=net/ipv4/tcp_input.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_INIT_CWND		10|\#define TCP_INIT_CWND		9|'

# SOURCE_FILE=net/mptcp/protocol.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_INIT_CWND		10|\#define TCP_INIT_CWND		9|'

### 22. TCP_PLB_SCALE

# SOURCE_FILE=net/ipv4/tcp_dctcp.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_PLB_SCALE 8|\#define TCP_PLB_SCALE 7|'

# SOURCE_FILE=net/ipv4/tcp_ipv4.c
# DEFINITION_SOURCE_FILE=include/net/tcp.h
# SED_PATTERN='s|\#define TCP_PLB_SCALE 8|\#define TCP_PLB_SCALE 7|'

### 23. AMT_DISCOVERY_TIMEOUT

# SOURCE_FILE=drivers/net/amt.c
# DEFINITION_SOURCE_FILE=include/net/amt.h
# SED_PATTERN='s|\#define AMT_DISCOVERY_TIMEOUT	5000|\#define AMT_DISCOVERY_TIMEOUT	10|'
