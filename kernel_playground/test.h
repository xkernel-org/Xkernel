#ifndef __TEST_H__
#define __TEST_H__

#define XKERNEL_TEST_DEFINE(x)                                                 \
  void xkernel_test_##x(void);                                                 \
  EXPORT_SYMBOL(xkernel_test_##x);                                             \
  void xkernel_test_##x(void)

#define XKERNEL_TEST_RUN(x) xkernel_test_##x();

#endif
