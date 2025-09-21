
BLK_MAX_REQUEST_COUNT

---

- url: https://github.com/torvalds/linux/commit/55c022bbddb2c056b5dff1bd1b1758d31b6d64c9
- time: Jul 8, 2011
- definition
  - `#define BLK_MAX_REQUEST_COUNT 16`
- reference
  ```c
  if (plug->count >= BLK_MAX_REQUEST_COUNT)
			blk_flush_plug_list(plug, false);
  ```
- commit message:
  - block: avoid building too big plug list
  When I test fio script with big I/O depth, I found the total throughput drops
  compared to some relative small I/O depth. The reason is the thread accumulates
  big requests in its plug list and causes some delays (surely this depends
  on CPU speed).
  I thought we'd better have a threshold for requests. When a threshold reaches,
  this means there is no request merge and queue lock contention isn't severe
  when pushing per-task requests to queue, so the main advantages of blk plug
  don't exist. We can force a plug list flush in this case.
  With this, my test throughput actually increases and almost equals to small
  I/O depth. Another side effect is irq off time decreases in blk_flush_plug_list()
  for big I/O depth.
  The BLK_MAX_REQUEST_COUNT is choosen arbitarily, but 16 is efficiently to
  reduce lock contention to me. But I'm open here, 32 is ok in my test too.
- note:
  - First commit when the constant is introduced:

---

- url: https://github.com/torvalds/linux/commit/320ae51feed5c2f13664aa05a76bec198967e04d
- commit message:
  - blk-mq: new multi-queue block IO queueing mechanism
- note:
  - a large commit, helpful to understand the block level


---

- url: https://github.com/torvalds/linux/commit/7f2a6a69f7ced6db8220298e0497cf60482a9d4b
- time: Sep 8, 2021
- definition:
  ```c
  /*
  * Allow 4x BLK_MAX_REQUEST_COUNT requests on plug queue for multiple
  * queues. This is important for md arrays to benefit from merging
  * requests.
  */
  static inline unsigned short blk_plug_max_rq_count(struct blk_plug *plug)
  {
    if (plug->multiple_queues)
      return BLK_MAX_REQUEST_COUNT * 4;
    return BLK_MAX_REQUEST_COUNT;
  }
  ```
- reference:
  - from: `if (request_count >= BLK_MAX_REQUEST_COUNT || (last &&`
  - to: `if (request_count >= blk_plug_max_rq_count(plug) || (last &&`
- commit message:
  - blk-mq: allow 4x BLK_MAX_REQUEST_COUNT at blk_plug for multiple_queues
  - Limiting number of request to BLK_MAX_REQUEST_COUNT at blk_plug hurts
  performance for large md arrays. [1] shows resync speed of md array drops
  for md array with more than 16 HDDs.
  - Fix this by allowing more request at plug queue. The multiple_queue flag
  is used to only apply higher limit to multiple queue cases.
  - [1] https://lore.kernel.org/linux-raid/CAFDAVznS71BXW8Jxv6k9dXc2iR3ysX3iZRBww_rzA8WifBFxGg@mail.gmail.com/
- note:
  - the commit to introduce the *4

---

- url: https://github.com/torvalds/linux/commit/ba0ffdd8ce48ad7f7e85191cd29f9674caca3745
- time: Oct 18, 2021
- definition:
  - #define BLK_MAX_REQUEST_COUNT	32
- reference
    ```c
    // from
    /*
    * Allow 4x BLK_MAX_REQUEST_COUNT requests on plug queue for multiple
    * queues. This is important for md arrays to benefit from merging
    * requests.
    */
    static inline unsigned short blk_plug_max_rq_count(struct blk_plug *plug)
    {
      if (plug->multiple_queues)
        return BLK_MAX_REQUEST_COUNT * 4;
      return BLK_MAX_REQUEST_COUNT;
    }

    // to
    static inline unsigned short blk_plug_max_rq_count(struct blk_plug *plug)
    {
      if (plug->multiple_queues)
        return BLK_MAX_REQUEST_COUNT * 2;
      return BLK_MAX_REQUEST_COUNT;
    }

    ```
- commit message:
  - block: bump max plugged deferred size from 16 to 32
  - Particularly for NVMe with efficient deferred submission for many
    requests, there are nice benefits to be seen by bumping the default max
    plug count from 16 to 32. This is especially true for virtualized setups,
    where the submit part is more expensive. But can be noticed even on
    native hardware.
  - Reduce the multiple queue factor from 4 to 2, since we're changing the
    default size.
  - While changing it, move the defines into the block layer private header.
    These aren't values that anyone outside of the block layer uses, or
    should use.
  - Signed-off-by: Jens Axboe <axboe@kernel.dk>
