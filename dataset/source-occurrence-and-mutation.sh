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

### 24. AMT_INIT_REQ_TIMEOUT

SOURCE_FILE=drivers/net/amt.c
DEFINITION_SOURCE_FILE=include/net/amt.h
SED_PATTERN='s|\#define AMT_INIT_REQ_TIMEOUT	1|\#define AMT_INIT_REQ_TIMEOUT	10|'

### 25. AMT_MAX_REQ_TIMEOUT

# SOURCE_FILE=drivers/net/amt.c
# DEFINITION_SOURCE_FILE=include/net/amt.h
# SED_PATTERN='s|\#define AMT_MAX_REQ_TIMEOUT	120|\#define AMT_MAX_REQ_TIMEOUT	121|'

### 26. AMT_MAX_REQ_COUNT

# SOURCE_FILE=drivers/net/amt.c
# DEFINITION_SOURCE_FILE=include/net/amt.h
# SED_PATTERN='s|\#define AMT_MAX_REQ_COUNT	3|\#define AMT_MAX_REQ_COUNT	7|'

### 27. AMT_SECRET_TIMEOUT

# SOURCE_FILE=drivers/net/amt.c
# DEFINITION_SOURCE_FILE=include/net/amt.h
# SED_PATTERN='s|\#define AMT_SECRET_TIMEOUT	60000|\#define AMT_SECRET_TIMEOUT	60001|'

### 28. IPVS_SYNC_WAKEUP_RATE

# SOURCE_FILE=net/netfilter/ipvs/ip_vs_sync.c
# DEFINITION_SOURCE_FILE=include/net/ip_vs.h
# SED_PATTERN='s|\#define IPVS_SYNC_WAKEUP_RATE	8|\#define IPVS_SYNC_WAKEUP_RATE	7|'

### 29. IPVS_SYNC_SEND_DELAY

# SOURCE_FILE=net/netfilter/ipvs/ip_vs_sync.c
# DEFINITION_SOURCE_FILE=include/net/ip_vs.h
# SED_PATTERN='s|\#define IPVS_SYNC_SEND_DELAY	(HZ / 50)|\#define IPVS_SYNC_SEND_DELAY	10|'

### 30. IPVS_SYNC_CHECK_PERIOD

# SOURCE_FILE=net/netfilter/ipvs/ip_vs_sync.c
# DEFINITION_SOURCE_FILE=include/net/ip_vs.h
# SED_PATTERN='s|\#define IPVS_SYNC_CHECK_PERIOD	HZ|\#define IPVS_SYNC_CHECK_PERIOD	2 \* HZ|'

### 31. IPVS_SYNC_FLUSH_TIME

# SOURCE_FILE=net/netfilter/ipvs/ip_vs_sync.c
# DEFINITION_SOURCE_FILE=include/net/ip_vs.h
# SED_PATTERN='s|\#define IPVS_SYNC_FLUSH_TIME	(HZ \* 2)|\#define IPVS_SYNC_FLUSH_TIME	(HZ \* 3)|'

### 32. TCP_RACK_RECOVERY_THRESH

# SOURCE_FILE=net/ipv4/tcp_input.c
# DEFINITION_SOURCE_FILE=include/linux/tcp.h
# SED_PATTERN='s|\#define TCP_RACK_RECOVERY_THRESH 16|\#define TCP_RACK_RECOVERY_THRESH 13|'

# SOURCE_FILE=net/ipv4/tcp_recovery.c
# DEFINITION_SOURCE_FILE=include/linux/tcp.h
# SED_PATTERN='s|\#define TCP_RACK_RECOVERY_THRESH 16|\#define TCP_RACK_RECOVERY_THRESH 13|'

### 33. SBQ_WAKE_BATCH

# SOURCE_FILE=lib/sbitmap.c
# DEFINITION_SOURCE_FILE=include/linux/sbitmap.h
# SED_PATTERN='s|\#define SBQ_WAKE_BATCH 8|\#define SBQ_WAKE_BATCH 7|'

### 34. BLK_MQ_MAX_DEPTH

# SOURCE_FILE=block/blk-mq.c
# DEFINITION_SOURCE_FILE=include/linux/blk-mq.h
# SED_PATTERN='s|\#define BLK_MQ_MAX_DEPTH	(10240)|\#define BLK_MQ_MAX_DEPTH	(10239)|'

# SOURCE_FILE=drivers/md/dm-rq.c
# DEFINITION_SOURCE_FILE=include/linux/blk-mq.h
# SED_PATTERN='s|\#define BLK_MQ_MAX_DEPTH	(10240)|\#define BLK_MQ_MAX_DEPTH	(10239)|'

# SOURCE_FILE=drivers/nvme/host/core.c
# DEFINITION_SOURCE_FILE=include/linux/blk-mq.h
# SED_PATTERN='s|\#define BLK_MQ_MAX_DEPTH	(10240)|\#define BLK_MQ_MAX_DEPTH	(10239)|'

### 35. BLK_MIN_SG_TIMEOUT

# SOURCE_FILE=block/bsg.c
# DEFINITION_SOURCE_FILE=include/linux/blkdev.h
# SED_PATTERN='s|\#define BLK_MIN_SG_TIMEOUT	(7 \* HZ)|\#define BLK_MIN_SG_TIMEOUT	(5 \* HZ)|'

# SOURCE_FILE=drivers/scsi/scsi_ioctl.c
# DEFINITION_SOURCE_FILE=include/linux/blkdev.h
# SED_PATTERN='s|\#define BLK_MIN_SG_TIMEOUT	(7 \* HZ)|\#define BLK_MIN_SG_TIMEOUT	(5 \* HZ)|'

### 36. NFS_JUKEBOX_RETRY_TIME

# SOURCE_FILE=fs/nfs/flexfilelayout/flexfilelayout.c
# DEFINITION_SOURCE_FILE=include/linux/nfs_fs.h
# SED_PATTERN='s|\#define NFS_JUKEBOX_RETRY_TIME (5 \* HZ)|\#define NFS_JUKEBOX_RETRY_TIME (7 \* HZ)|'

# SOURCE_FILE=fs/nfs/nfs3proc.c
# DEFINITION_SOURCE_FILE=include/linux/nfs_fs.h
# SED_PATTERN='s|\#define NFS_JUKEBOX_RETRY_TIME (5 \* HZ)|\#define NFS_JUKEBOX_RETRY_TIME (7 \* HZ)|'

### 37. MAX_NR_FOLIOS_PER_FREE

# SOURCE_FILE=mm/mmu_gather.c
# DEFINITION_SOURCE_FILE=mm/mmu_gather.c
# SED_PATTERN='s|\#define MAX_NR_FOLIOS_PER_FREE		512|\#define MAX_NR_FOLIOS_PER_FREE		256|'

### 38. PCPU_SLOT_FAIL_THRESHOLD

# SOURCE_FILE=mm/percpu.c
# DEFINITION_SOURCE_FILE=mm/percpu.c
# SED_PATTERN='s|\#define PCPU_SLOT_FAIL_THRESHOLD	3|\#define PCPU_SLOT_FAIL_THRESHOLD	11|'

### 39. NR_MAX_MIGRATE_PAGES_RETRY

# SOURCE_FILE=mm/migrate.c
# DEFINITION_SOURCE_FILE=mm/migrate.c
# SED_PATTERN='s|\#define NR_MAX_MIGRATE_PAGES_RETRY	10|\#define NR_MAX_MIGRATE_PAGES_RETRY	11|'

### 40. SHRINK_BATCH

# SOURCE_FILE=mm/shrinker.c
# DEFINITION_SOURCE_FILE=mm/shrinker.c
# SED_PATTERN='s|\#define SHRINK_BATCH 128|\#define SHRINK_BATCH 64|'

### 41. MMAP_LOTSAMISS

# SOURCE_FILE=mm/filemap.c
# DEFINITION_SOURCE_FILE=mm/filemap.c
# SED_PATTERN='s|\#define MMAP_LOTSAMISS  (100)|\#define MMAP_LOTSAMISS  (99)|'

### 42. GET_PAGE_MAX_RETRY_NUM

# SOURCE_FILE=mm/memory-failure.c
# DEFINITION_SOURCE_FILE=mm/memory-failure.c
# SED_PATTERN='s|\#define GET_PAGE_MAX_RETRY_NUM 3|\#define GET_PAGE_MAX_RETRY_NUM 7|'

### 43. MAX_MADVISE_GUARD_RETRIES

# TODO huge diff...
# SOURCE_FILE=mm/madvise.c
# DEFINITION_SOURCE_FILE=mm/madvise.c
# SED_PATTERN='s|\#define MAX_MADVISE_GUARD_RETRIES 3|\#define MAX_MADVISE_GUARD_RETRIES 5|'

### 44. MAX_OOM_REAP_RETRIES

# SOURCE_FILE=mm/oom_kill.c
# DEFINITION_SOURCE_FILE=mm/oom_kill.c
# SED_PATTERN='s|\#define MAX_OOM_REAP_RETRIES 10|\#define MAX_OOM_REAP_RETRIES 11|'

### 45. OOM_REAPER_DELAY

# SOURCE_FILE=mm/oom_kill.c
# DEFINITION_SOURCE_FILE=mm/oom_kill.c
# SED_PATTERN='s|\#define OOM_REAPER_DELAY (2\*HZ)|\#define OOM_REAPER_DELAY (3\*HZ)|'

### 46. SHMEM_MAX_IQ_TIME

# SOURCE_FILE=mm/shmem_quota.c
# DEFINITION_SOURCE_FILE=mm/shmem_quota.c
# SED_PATTERN='s|\#define SHMEM_MAX_IQ_TIME 604800|\#define SHMEM_MAX_IQ_TIME 604801|'

### 47. SHMEM_MAX_DQ_TIME

# SOURCE_FILE=mm/shmem_quota.c
# DEFINITION_SOURCE_FILE=mm/shmem_quota.c
# SED_PATTERN='s|\#define SHMEM_MAX_DQ_TIME 604800|\#define SHMEM_MAX_DQ_TIME 604801|'

### 48. RCU_JIFFIES_FQS_DIV

# SOURCE_FILE=kernel/rcu/tree.c
# DEFINITION_SOURCE_FILE=kernel/rcu/tree.h
# SED_PATTERN='s|\#define RCU_JIFFIES_FQS_DIV	256|\#define RCU_JIFFIES_FQS_DIV	128|'

### 49. BLK_MAX_REQUEST_COUNT

# SOURCE_FILE=block/blk-core.c
# DEFINITION_SOURCE_FILE=block/blk.h
# SED_PATTERN='s|\#define BLK_MAX_REQUEST_COUNT	32|\#define BLK_MAX_REQUEST_COUNT	16|'

# SOURCE_FILE=block/blk-mq.c
# DEFINITION_SOURCE_FILE=block/blk.h
# SED_PATTERN='s|\#define BLK_MAX_REQUEST_COUNT	32|\#define BLK_MAX_REQUEST_COUNT	16|'

### 50. PEEK_MAX_IMPORT

# SOURCE_FILE=io_uring/kbuf.c
# DEFINITION_SOURCE_FILE=io_uring/kbuf.c
# SED_PATTERN='s|\#define PEEK_MAX_IMPORT		256|\#define PEEK_MAX_IMPORT		128|'

### 51. IO_POLL_REF_BIAS

# SOURCE_FILE=io_uring/poll.c
# DEFINITION_SOURCE_FILE=io_uring/poll.c
# SED_PATTERN='s|\#define IO_POLL_REF_BIAS	128|\#define IO_POLL_REF_BIAS	64|'

### 52. APOLL_MAX_RETRY

# SOURCE_FILE=io_uring/poll.c
# DEFINITION_SOURCE_FILE=io_uring/poll.c
# SED_PATTERN='s|\#define APOLL_MAX_RETRY		128|\#define APOLL_MAX_RETRY		64|'

### 53. IO_TCTX_REFS_CACHE_NR

# SOURCE_FILE=io_uring/io_uring.c
# DEFINITION_SOURCE_FILE=io_uring/io_uring.c
# SED_PATTERN='s|\#define IO_TCTX_REFS_CACHE_NR	(1U << 10)|\#define IO_TCTX_REFS_CACHE_NR	(1U << 9)|'

### 54. IORING_MAX_ENTRIES

# SOURCE_FILE=io_uring/io_uring.c
# DEFINITION_SOURCE_FILE=io_uring/io_uring.h
# SED_PATTERN='s|\#define IORING_MAX_ENTRIES	32768|\#define IORING_MAX_ENTRIES	16384|'

# SOURCE_FILE=io_uring/io_uring.c
# DEFINITION_SOURCE_FILE=io_uring/io_uring.h
# SED_PATTERN='s|\#define IORING_MAX_CQ_ENTRIES	(2 \* IORING_MAX_ENTRIES)|\#define IORING_MAX_CQ_ENTRIES	32768|'

### 55. IO_LOCAL_TW_DEFAULT_MAX

# SOURCE_FILE=io_uring/io_uring.c
# DEFINITION_SOURCE_FILE=io_uring/io_uring.c
# SED_PATTERN='s|\#define IO_LOCAL_TW_DEFAULT_MAX		20|\#define IO_LOCAL_TW_DEFAULT_MAX		19|'

### 56. WORKER_INIT_LIMIT

# SOURCE_FILE=io_uring/io-wq.c
# DEFINITION_SOURCE_FILE=io_uring/io-wq.c
# SED_PATTERN='s|\#define WORKER_INIT_LIMIT	3|\#define WORKER_INIT_LIMIT	7|'

### 57. MULTISHOT_MAX_RETRY

# SOURCE_FILE=io_uring/net.c
# DEFINITION_SOURCE_FILE=io_uring/net.c
# SED_PATTERN='s|\#define MULTISHOT_MAX_RETRY	32|\#define MULTISHOT_MAX_RETRY	16|'

### 58. EP_MAX_NESTS

# SOURCE_FILE=fs/eventpoll.c
# DEFINITION_SOURCE_FILE=fs/eventpoll.c
# SED_PATTERN='s|\#define EP_MAX_NESTS 4|\#define EP_MAX_NESTS 3|'

### 59. MAX_SLACK

# SOURCE_FILE=fs/select.c
# DEFINITION_SOURCE_FILE=fs/select.c
# SED_PATTERN='s|\#define MAX_SLACK	(100 \* NSEC_PER_MSEC)|\#define MAX_SLACK	(50 \* NSEC_PER_MSEC)|'

### 60. SYNC_SHRINK_BATCH

# SOURCE_FILE=fs/mbcache.c
# DEFINITION_SOURCE_FILE=fs/mbcache.c
# SED_PATTERN='s|\#define SYNC_SHRINK_BATCH 64|\#define SYNC_SHRINK_BATCH 32|'

### 61. SHRINK_DIVISOR

# SOURCE_FILE=fs/mbcache.c
# DEFINITION_SOURCE_FILE=fs/mbcache.c
# SED_PATTERN='s|\#define SHRINK_DIVISOR 16|\#define SHRINK_DIVISOR 8|'

### 62. PIPE_MIN_DEF_BUFFERS

# SOURCE_FILE=fs/pipe.c
# DEFINITION_SOURCE_FILE=fs/pipe.c
# SED_PATTERN='s|\#define PIPE_MIN_DEF_BUFFERS 2|\#define PIPE_MIN_DEF_BUFFERS 3|'

### 63. AIO_PLUG_THRESHOLD

# SOURCE_FILE=fs/aio.c
# DEFINITION_SOURCE_FILE=fs/aio.c
# SED_PATTERN='s|\#define AIO_PLUG_THRESHOLD	2|\#define AIO_PLUG_THRESHOLD	3|'

### 64. LAST_INO_BATCH

# SOURCE_FILE=fs/inode.c
# DEFINITION_SOURCE_FILE=fs/inode.c
# SED_PATTERN='s|\#define LAST_INO_BATCH 1024|\#define LAST_INO_BATCH 512|'

### 65. IWALK_MAX_INODE_PREFETCH

# SOURCE_FILE=fs/xfs/xfs_iwalk.c
# DEFINITION_SOURCE_FILE=fs/xfs/xfs_iwalk.c
# SED_PATTERN='s|\#define IWALK_MAX_INODE_PREFETCH	(2048U)|\#define IWALK_MAX_INODE_PREFETCH	(1024U)|'

### 66. MAX_INOBT_WALK_PREFETCH

# SOURCE_FILE=fs/xfs/xfs_iwalk.c
# DEFINITION_SOURCE_FILE=fs/xfs/xfs_iwalk.c
# SED_PATTERN='s|	(PAGE_SIZE / sizeof(struct xfs_inobt_rec_incore))|	(PAGE_SIZE / 2 / sizeof(struct xfs_inobt_rec_incore))|'

### 67. XFS_DISCARD_MAX_EXAMINE

# SOURCE_FILE=fs/xfs/xfs_discard.c
# DEFINITION_SOURCE_FILE=fs/xfs/xfs_discard.c
# SED_PATTERN='s|\#define XFS_DISCARD_MAX_EXAMINE	(100)|\#define XFS_DISCARD_MAX_EXAMINE	(99)|'
