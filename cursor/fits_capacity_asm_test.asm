
fits_capacity_asm_test.o:     file format elf64-x86-64


Disassembly of section .text:

0000000000000000 <__pfx_test_simple_capacity>:
   0:	90                   	nop
   1:	90                   	nop
   2:	90                   	nop
   3:	90                   	nop
   4:	90                   	nop
   5:	90                   	nop
   6:	90                   	nop
   7:	90                   	nop
   8:	90                   	nop
   9:	90                   	nop
   a:	90                   	nop
   b:	90                   	nop
   c:	90                   	nop
   d:	90                   	nop
   e:	90                   	nop
   f:	90                   	nop

0000000000000010 <test_simple_capacity>:
  10:	e8 00 00 00 00       	call   15 <test_simple_capacity+0x5>
  15:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 1c <test_simple_capacity+0xc>
  1c:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # 23 <test_simple_capacity+0x13>
  23:	55                   	push   %rbp
  24:	48 8d 14 92          	lea    (%rdx,%rdx,4),%rdx
  28:	48 c1 e0 0a          	shl    $0xa,%rax
  2c:	48 c1 e2 08          	shl    $0x8,%rdx
  30:	48 89 e5             	mov    %rsp,%rbp
  33:	5d                   	pop    %rbp
  34:	48 39 c2             	cmp    %rax,%rdx
  37:	0f 92 c0             	setb   %al
  3a:	0f b6 c0             	movzbl %al,%eax
  3d:	31 d2                	xor    %edx,%edx
  3f:	e9 00 00 00 00       	jmp    44 <test_simple_capacity+0x34>
  44:	66 66 2e 0f 1f 84 00 	data16 cs nopw 0x0(%rax,%rax,1)
  4b:	00 00 00 00 
  4f:	90                   	nop

0000000000000050 <__pfx_test_capacity_loop>:
  50:	90                   	nop
  51:	90                   	nop
  52:	90                   	nop
  53:	90                   	nop
  54:	90                   	nop
  55:	90                   	nop
  56:	90                   	nop
  57:	90                   	nop
  58:	90                   	nop
  59:	90                   	nop
  5a:	90                   	nop
  5b:	90                   	nop
  5c:	90                   	nop
  5d:	90                   	nop
  5e:	90                   	nop
  5f:	90                   	nop

0000000000000060 <test_capacity_loop>:
  60:	e8 00 00 00 00       	call   65 <test_capacity_loop+0x5>
  65:	55                   	push   %rbp
  66:	48 89 e5             	mov    %rsp,%rbp
  69:	41 55                	push   %r13
  6b:	41 54                	push   %r12
  6d:	45 31 e4             	xor    %r12d,%r12d
  70:	53                   	push   %rbx
  71:	31 db                	xor    %ebx,%ebx
  73:	48 83 ec 30          	sub    $0x30,%rsp
  77:	65 48 8b 04 25 28 00 	mov    %gs:0x28,%rax
  7e:	00 00 
  80:	48 89 45 e0          	mov    %rax,-0x20(%rbp)
  84:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # 8b <test_capacity_loop+0x2b>
  8b:	48 89 45 b8          	mov    %rax,-0x48(%rbp)
  8f:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # 96 <test_capacity_loop+0x36>
  96:	48 89 45 c0          	mov    %rax,-0x40(%rbp)
  9a:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # a1 <test_capacity_loop+0x41>
  a1:	48 89 45 c8          	mov    %rax,-0x38(%rbp)
  a5:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # ac <test_capacity_loop+0x4c>
  ac:	48 89 45 d0          	mov    %rax,-0x30(%rbp)
  b0:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # b7 <test_capacity_loop+0x57>
  b7:	4c 8b 2d 00 00 00 00 	mov    0x0(%rip),%r13        # be <test_capacity_loop+0x5e>
  be:	48 89 45 d8          	mov    %rax,-0x28(%rbp)
  c2:	49 c1 e5 0a          	shl    $0xa,%r13
  c6:	48 63 f3             	movslq %ebx,%rsi
  c9:	48 83 fe 05          	cmp    $0x5,%rsi
  cd:	73 43                	jae    112 <test_capacity_loop+0xb2>
  cf:	48 8b 44 dd b8       	mov    -0x48(%rbp,%rbx,8),%rax
  d4:	48 8d 04 80          	lea    (%rax,%rax,4),%rax
  d8:	48 c1 e0 08          	shl    $0x8,%rax
  dc:	4c 39 e8             	cmp    %r13,%rax
  df:	41 83 d4 00          	adc    $0x0,%r12d
  e3:	48 83 c3 01          	add    $0x1,%rbx
  e7:	48 83 fb 05          	cmp    $0x5,%rbx
  eb:	75 d9                	jne    c6 <test_capacity_loop+0x66>
  ed:	48 8b 45 e0          	mov    -0x20(%rbp),%rax
  f1:	65 48 2b 04 25 28 00 	sub    %gs:0x28,%rax
  f8:	00 00 
  fa:	75 24                	jne    120 <test_capacity_loop+0xc0>
  fc:	48 83 c4 30          	add    $0x30,%rsp
 100:	44 89 e0             	mov    %r12d,%eax
 103:	5b                   	pop    %rbx
 104:	41 5c                	pop    %r12
 106:	41 5d                	pop    %r13
 108:	5d                   	pop    %rbp
 109:	31 f6                	xor    %esi,%esi
 10b:	31 ff                	xor    %edi,%edi
 10d:	e9 00 00 00 00       	jmp    112 <test_capacity_loop+0xb2>
 112:	48 c7 c7 00 00 00 00 	mov    $0x0,%rdi
 119:	e8 00 00 00 00       	call   11e <test_capacity_loop+0xbe>
 11e:	eb af                	jmp    cf <test_capacity_loop+0x6f>
 120:	e8 00 00 00 00       	call   125 <test_capacity_loop+0xc5>
 125:	66 66 2e 0f 1f 84 00 	data16 cs nopw 0x0(%rax,%rax,1)
 12c:	00 00 00 00 

0000000000000130 <__pfx_test_conditional_assign>:
 130:	90                   	nop
 131:	90                   	nop
 132:	90                   	nop
 133:	90                   	nop
 134:	90                   	nop
 135:	90                   	nop
 136:	90                   	nop
 137:	90                   	nop
 138:	90                   	nop
 139:	90                   	nop
 13a:	90                   	nop
 13b:	90                   	nop
 13c:	90                   	nop
 13d:	90                   	nop
 13e:	90                   	nop
 13f:	90                   	nop

0000000000000140 <test_conditional_assign>:
 140:	e8 00 00 00 00       	call   145 <test_conditional_assign+0x5>
 145:	55                   	push   %rbp
 146:	48 8d 14 bf          	lea    (%rdi,%rdi,4),%rdx
 14a:	48 89 f1             	mov    %rsi,%rcx
 14d:	48 01 ff             	add    %rdi,%rdi
 150:	48 c1 e2 08          	shl    $0x8,%rdx
 154:	48 c1 e1 0a          	shl    $0xa,%rcx
 158:	48 89 f0             	mov    %rsi,%rax
 15b:	48 39 ca             	cmp    %rcx,%rdx
 15e:	48 89 e5             	mov    %rsp,%rbp
 161:	48 0f 42 c7          	cmovb  %rdi,%rax
 165:	5d                   	pop    %rbp
 166:	31 d2                	xor    %edx,%edx
 168:	31 c9                	xor    %ecx,%ecx
 16a:	31 f6                	xor    %esi,%esi
 16c:	31 ff                	xor    %edi,%edi
 16e:	e9 00 00 00 00       	jmp    173 <test_conditional_assign+0x33>
 173:	66 66 2e 0f 1f 84 00 	data16 cs nopw 0x0(%rax,%rax,1)
 17a:	00 00 00 00 
 17e:	66 90                	xchg   %ax,%ax

0000000000000180 <__pfx_test_complex_expression>:
 180:	90                   	nop
 181:	90                   	nop
 182:	90                   	nop
 183:	90                   	nop
 184:	90                   	nop
 185:	90                   	nop
 186:	90                   	nop
 187:	90                   	nop
 188:	90                   	nop
 189:	90                   	nop
 18a:	90                   	nop
 18b:	90                   	nop
 18c:	90                   	nop
 18d:	90                   	nop
 18e:	90                   	nop
 18f:	90                   	nop

0000000000000190 <test_complex_expression>:
 190:	e8 00 00 00 00       	call   195 <test_complex_expression+0x5>
 195:	48 8d 04 76          	lea    (%rsi,%rsi,2),%rax
 199:	55                   	push   %rbp
 19a:	48 c1 e8 02          	shr    $0x2,%rax
 19e:	48 39 f8             	cmp    %rdi,%rax
 1a1:	48 8d 04 bf          	lea    (%rdi,%rdi,4),%rax
 1a5:	0f 92 c2             	setb   %dl
 1a8:	48 c1 e0 08          	shl    $0x8,%rax
 1ac:	48 89 e5             	mov    %rsp,%rbp
 1af:	5d                   	pop    %rbp
 1b0:	48 c1 e6 0a          	shl    $0xa,%rsi
 1b4:	48 39 f0             	cmp    %rsi,%rax
 1b7:	0f 92 c0             	setb   %al
 1ba:	0f b6 c0             	movzbl %al,%eax
 1bd:	21 d0                	and    %edx,%eax
 1bf:	31 d2                	xor    %edx,%edx
 1c1:	31 f6                	xor    %esi,%esi
 1c3:	31 ff                	xor    %edi,%edi
 1c5:	e9 00 00 00 00       	jmp    1ca <test_complex_expression+0x3a>
 1ca:	66 0f 1f 44 00 00    	nopw   0x0(%rax,%rax,1)

00000000000001d0 <__pfx_test_nested_capacity>:
 1d0:	90                   	nop
 1d1:	90                   	nop
 1d2:	90                   	nop
 1d3:	90                   	nop
 1d4:	90                   	nop
 1d5:	90                   	nop
 1d6:	90                   	nop
 1d7:	90                   	nop
 1d8:	90                   	nop
 1d9:	90                   	nop
 1da:	90                   	nop
 1db:	90                   	nop
 1dc:	90                   	nop
 1dd:	90                   	nop
 1de:	90                   	nop
 1df:	90                   	nop

00000000000001e0 <test_nested_capacity>:
 1e0:	e8 00 00 00 00       	call   1e5 <test_nested_capacity+0x5>
 1e5:	55                   	push   %rbp
 1e6:	48 8d 04 b6          	lea    (%rsi,%rsi,4),%rax
 1ea:	48 8d 34 bf          	lea    (%rdi,%rdi,4),%rsi
 1ee:	48 c1 e2 0a          	shl    $0xa,%rdx
 1f2:	48 c1 e6 08          	shl    $0x8,%rsi
 1f6:	48 c1 e0 08          	shl    $0x8,%rax
 1fa:	48 c1 e1 0a          	shl    $0xa,%rcx
 1fe:	48 89 e5             	mov    %rsp,%rbp
 201:	48 39 d6             	cmp    %rdx,%rsi
 204:	73 1a                	jae    220 <test_nested_capacity+0x40>
 206:	48 39 c8             	cmp    %rcx,%rax
 209:	5d                   	pop    %rbp
 20a:	0f 93 c0             	setae  %al
 20d:	0f b6 c0             	movzbl %al,%eax
 210:	83 c0 01             	add    $0x1,%eax
 213:	31 d2                	xor    %edx,%edx
 215:	31 c9                	xor    %ecx,%ecx
 217:	31 f6                	xor    %esi,%esi
 219:	31 ff                	xor    %edi,%edi
 21b:	e9 00 00 00 00       	jmp    220 <test_nested_capacity+0x40>
 220:	48 39 c8             	cmp    %rcx,%rax
 223:	5d                   	pop    %rbp
 224:	0f 92 c0             	setb   %al
 227:	0f b6 c0             	movzbl %al,%eax
 22a:	01 c0                	add    %eax,%eax
 22c:	31 d2                	xor    %edx,%edx
 22e:	31 c9                	xor    %ecx,%ecx
 230:	31 f6                	xor    %esi,%esi
 232:	31 ff                	xor    %edi,%edi
 234:	e9 00 00 00 00       	jmp    239 <test_nested_capacity+0x59>
 239:	0f 1f 80 00 00 00 00 	nopl   0x0(%rax)

0000000000000240 <__pfx_test_arithmetic_with_capacity>:
 240:	90                   	nop
 241:	90                   	nop
 242:	90                   	nop
 243:	90                   	nop
 244:	90                   	nop
 245:	90                   	nop
 246:	90                   	nop
 247:	90                   	nop
 248:	90                   	nop
 249:	90                   	nop
 24a:	90                   	nop
 24b:	90                   	nop
 24c:	90                   	nop
 24d:	90                   	nop
 24e:	90                   	nop
 24f:	90                   	nop

0000000000000250 <test_arithmetic_with_capacity>:
 250:	e8 00 00 00 00       	call   255 <test_arithmetic_with_capacity+0x5>
 255:	55                   	push   %rbp
 256:	48 8d 14 bf          	lea    (%rdi,%rdi,4),%rdx
 25a:	48 c1 e6 0a          	shl    $0xa,%rsi
 25e:	48 89 f8             	mov    %rdi,%rax
 261:	48 c1 e2 08          	shl    $0x8,%rdx
 265:	48 8d 0c 3f          	lea    (%rdi,%rdi,1),%rcx
 269:	48 39 f2             	cmp    %rsi,%rdx
 26c:	48 89 e5             	mov    %rsp,%rbp
 26f:	48 0f 42 c1          	cmovb  %rcx,%rax
 273:	5d                   	pop    %rbp
 274:	31 d2                	xor    %edx,%edx
 276:	31 c9                	xor    %ecx,%ecx
 278:	31 f6                	xor    %esi,%esi
 27a:	31 ff                	xor    %edi,%edi
 27c:	e9 00 00 00 00       	jmp    281 <test_arithmetic_with_capacity+0x31>
 281:	66 66 2e 0f 1f 84 00 	data16 cs nopw 0x0(%rax,%rax,1)
 288:	00 00 00 00 
 28c:	0f 1f 40 00          	nopl   0x0(%rax)

0000000000000290 <__pfx_test_different_types>:
 290:	90                   	nop
 291:	90                   	nop
 292:	90                   	nop
 293:	90                   	nop
 294:	90                   	nop
 295:	90                   	nop
 296:	90                   	nop
 297:	90                   	nop
 298:	90                   	nop
 299:	90                   	nop
 29a:	90                   	nop
 29b:	90                   	nop
 29c:	90                   	nop
 29d:	90                   	nop
 29e:	90                   	nop
 29f:	90                   	nop

00000000000002a0 <test_different_types>:
 2a0:	e8 00 00 00 00       	call   2a5 <test_different_types+0x5>
 2a5:	48 8b 0d 00 00 00 00 	mov    0x0(%rip),%rcx        # 2ac <test_different_types+0xc>
 2ac:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # 2b3 <test_different_types+0x13>
 2b3:	55                   	push   %rbp
 2b4:	48 8b 35 00 00 00 00 	mov    0x0(%rip),%rsi        # 2bb <test_different_types+0x1b>
 2bb:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 2c2 <test_different_types+0x22>
 2c2:	8d 0c 89             	lea    (%rcx,%rcx,4),%ecx
 2c5:	c1 e0 0a             	shl    $0xa,%eax
 2c8:	c1 e1 08             	shl    $0x8,%ecx
 2cb:	48 89 e5             	mov    %rsp,%rbp
 2ce:	5d                   	pop    %rbp
 2cf:	39 c1                	cmp    %eax,%ecx
 2d1:	48 8d 0c b6          	lea    (%rsi,%rsi,4),%rcx
 2d5:	0f 9c c0             	setl   %al
 2d8:	48 c1 e1 08          	shl    $0x8,%rcx
 2dc:	48 c1 e2 0a          	shl    $0xa,%rdx
 2e0:	0f b6 c0             	movzbl %al,%eax
 2e3:	48 39 d1             	cmp    %rdx,%rcx
 2e6:	83 d0 00             	adc    $0x0,%eax
 2e9:	31 d2                	xor    %edx,%edx
 2eb:	31 c9                	xor    %ecx,%ecx
 2ed:	31 f6                	xor    %esi,%esi
 2ef:	e9 00 00 00 00       	jmp    2f4 <test_different_types+0x54>
 2f4:	66 66 2e 0f 1f 84 00 	data16 cs nopw 0x0(%rax,%rax,1)
 2fb:	00 00 00 00 
 2ff:	90                   	nop

0000000000000300 <__pfx_test_with_constants>:
 300:	90                   	nop
 301:	90                   	nop
 302:	90                   	nop
 303:	90                   	nop
 304:	90                   	nop
 305:	90                   	nop
 306:	90                   	nop
 307:	90                   	nop
 308:	90                   	nop
 309:	90                   	nop
 30a:	90                   	nop
 30b:	90                   	nop
 30c:	90                   	nop
 30d:	90                   	nop
 30e:	90                   	nop
 30f:	90                   	nop

0000000000000310 <test_with_constants>:
 310:	e8 00 00 00 00       	call   315 <test_with_constants+0x5>
 315:	48 8b 0d 00 00 00 00 	mov    0x0(%rip),%rcx        # 31c <test_with_constants+0xc>
 31c:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # 323 <test_with_constants+0x13>
 323:	55                   	push   %rbp
 324:	48 8b 35 00 00 00 00 	mov    0x0(%rip),%rsi        # 32b <test_with_constants+0x1b>
 32b:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 332 <test_with_constants+0x22>
 332:	48 8d 0c 89          	lea    (%rcx,%rcx,4),%rcx
 336:	48 c1 e0 0a          	shl    $0xa,%rax
 33a:	48 c1 e1 08          	shl    $0x8,%rcx
 33e:	48 89 e5             	mov    %rsp,%rbp
 341:	5d                   	pop    %rbp
 342:	48 39 c1             	cmp    %rax,%rcx
 345:	48 8d 0c b6          	lea    (%rsi,%rsi,4),%rcx
 349:	0f 92 c0             	setb   %al
 34c:	48 c1 e1 08          	shl    $0x8,%rcx
 350:	48 c1 e2 0a          	shl    $0xa,%rdx
 354:	0f b6 c0             	movzbl %al,%eax
 357:	48 39 d1             	cmp    %rdx,%rcx
 35a:	48 8b 0d 00 00 00 00 	mov    0x0(%rip),%rcx        # 361 <test_with_constants+0x51>
 361:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 368 <test_with_constants+0x58>
 368:	83 d0 00             	adc    $0x0,%eax
 36b:	48 8d 0c 89          	lea    (%rcx,%rcx,4),%rcx
 36f:	48 c1 e2 0a          	shl    $0xa,%rdx
 373:	48 c1 e1 08          	shl    $0x8,%rcx
 377:	48 39 d1             	cmp    %rdx,%rcx
 37a:	48 8b 0d 00 00 00 00 	mov    0x0(%rip),%rcx        # 381 <test_with_constants+0x71>
 381:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 388 <test_with_constants+0x78>
 388:	83 d0 00             	adc    $0x0,%eax
 38b:	48 8d 0c 89          	lea    (%rcx,%rcx,4),%rcx
 38f:	48 c1 e2 0a          	shl    $0xa,%rdx
 393:	48 c1 e1 08          	shl    $0x8,%rcx
 397:	48 39 d1             	cmp    %rdx,%rcx
 39a:	83 d0 00             	adc    $0x0,%eax
 39d:	31 d2                	xor    %edx,%edx
 39f:	31 c9                	xor    %ecx,%ecx
 3a1:	31 f6                	xor    %esi,%esi
 3a3:	e9 00 00 00 00       	jmp    3a8 <test_with_constants+0x98>
 3a8:	0f 1f 84 00 00 00 00 	nopl   0x0(%rax,%rax,1)
 3af:	00 

00000000000003b0 <__pfx_test_switch_capacity>:
 3b0:	90                   	nop
 3b1:	90                   	nop
 3b2:	90                   	nop
 3b3:	90                   	nop
 3b4:	90                   	nop
 3b5:	90                   	nop
 3b6:	90                   	nop
 3b7:	90                   	nop
 3b8:	90                   	nop
 3b9:	90                   	nop
 3ba:	90                   	nop
 3bb:	90                   	nop
 3bc:	90                   	nop
 3bd:	90                   	nop
 3be:	90                   	nop
 3bf:	90                   	nop

00000000000003c0 <test_switch_capacity>:
 3c0:	e8 00 00 00 00       	call   3c5 <test_switch_capacity+0x5>
 3c5:	48 8d 04 bf          	lea    (%rdi,%rdi,4),%rax
 3c9:	48 c1 e6 0a          	shl    $0xa,%rsi
 3cd:	55                   	push   %rbp
 3ce:	48 c1 e0 08          	shl    $0x8,%rax
 3d2:	48 39 f0             	cmp    %rsi,%rax
 3d5:	19 c0                	sbb    %eax,%eax
 3d7:	48 89 e5             	mov    %rsp,%rbp
 3da:	5d                   	pop    %rbp
 3db:	83 e0 9c             	and    $0xffffff9c,%eax
 3de:	05 c8 00 00 00       	add    $0xc8,%eax
 3e3:	31 f6                	xor    %esi,%esi
 3e5:	31 ff                	xor    %edi,%edi
 3e7:	e9 00 00 00 00       	jmp    3ec <test_switch_capacity+0x2c>
 3ec:	0f 1f 40 00          	nopl   0x0(%rax)

00000000000003f0 <__pfx_get_capacity>:
 3f0:	90                   	nop
 3f1:	90                   	nop
 3f2:	90                   	nop
 3f3:	90                   	nop
 3f4:	90                   	nop
 3f5:	90                   	nop
 3f6:	90                   	nop
 3f7:	90                   	nop
 3f8:	90                   	nop
 3f9:	90                   	nop
 3fa:	90                   	nop
 3fb:	90                   	nop
 3fc:	90                   	nop
 3fd:	90                   	nop
 3fe:	90                   	nop
 3ff:	90                   	nop

0000000000000400 <get_capacity>:
 400:	e8 00 00 00 00       	call   405 <get_capacity+0x5>
 405:	55                   	push   %rbp
 406:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # 40d <get_capacity+0xd>
 40d:	48 89 e5             	mov    %rsp,%rbp
 410:	5d                   	pop    %rbp
 411:	e9 00 00 00 00       	jmp    416 <get_capacity+0x16>
 416:	66 2e 0f 1f 84 00 00 	cs nopw 0x0(%rax,%rax,1)
 41d:	00 00 00 

0000000000000420 <__pfx_get_max_capacity>:
 420:	90                   	nop
 421:	90                   	nop
 422:	90                   	nop
 423:	90                   	nop
 424:	90                   	nop
 425:	90                   	nop
 426:	90                   	nop
 427:	90                   	nop
 428:	90                   	nop
 429:	90                   	nop
 42a:	90                   	nop
 42b:	90                   	nop
 42c:	90                   	nop
 42d:	90                   	nop
 42e:	90                   	nop
 42f:	90                   	nop

0000000000000430 <get_max_capacity>:
 430:	e8 00 00 00 00       	call   435 <get_max_capacity+0x5>
 435:	55                   	push   %rbp
 436:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # 43d <get_max_capacity+0xd>
 43d:	48 89 e5             	mov    %rsp,%rbp
 440:	5d                   	pop    %rbp
 441:	e9 00 00 00 00       	jmp    446 <get_max_capacity+0x16>
 446:	66 2e 0f 1f 84 00 00 	cs nopw 0x0(%rax,%rax,1)
 44d:	00 00 00 

0000000000000450 <__pfx_test_with_function_calls>:
 450:	90                   	nop
 451:	90                   	nop
 452:	90                   	nop
 453:	90                   	nop
 454:	90                   	nop
 455:	90                   	nop
 456:	90                   	nop
 457:	90                   	nop
 458:	90                   	nop
 459:	90                   	nop
 45a:	90                   	nop
 45b:	90                   	nop
 45c:	90                   	nop
 45d:	90                   	nop
 45e:	90                   	nop
 45f:	90                   	nop

0000000000000460 <test_with_function_calls>:
 460:	e8 00 00 00 00       	call   465 <test_with_function_calls+0x5>
 465:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 46c <test_with_function_calls+0xc>
 46c:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # 473 <test_with_function_calls+0x13>
 473:	55                   	push   %rbp
 474:	48 8d 14 92          	lea    (%rdx,%rdx,4),%rdx
 478:	48 c1 e0 0a          	shl    $0xa,%rax
 47c:	48 c1 e2 08          	shl    $0x8,%rdx
 480:	48 89 e5             	mov    %rsp,%rbp
 483:	5d                   	pop    %rbp
 484:	48 39 c2             	cmp    %rax,%rdx
 487:	0f 92 c0             	setb   %al
 48a:	0f b6 c0             	movzbl %al,%eax
 48d:	31 d2                	xor    %edx,%edx
 48f:	e9 00 00 00 00       	jmp    494 <test_with_function_calls+0x34>
 494:	66 66 2e 0f 1f 84 00 	data16 cs nopw 0x0(%rax,%rax,1)
 49b:	00 00 00 00 
 49f:	90                   	nop

00000000000004a0 <__pfx_test_multiple_capacity_checks>:
 4a0:	90                   	nop
 4a1:	90                   	nop
 4a2:	90                   	nop
 4a3:	90                   	nop
 4a4:	90                   	nop
 4a5:	90                   	nop
 4a6:	90                   	nop
 4a7:	90                   	nop
 4a8:	90                   	nop
 4a9:	90                   	nop
 4aa:	90                   	nop
 4ab:	90                   	nop
 4ac:	90                   	nop
 4ad:	90                   	nop
 4ae:	90                   	nop
 4af:	90                   	nop

00000000000004b0 <test_multiple_capacity_checks>:
 4b0:	e8 00 00 00 00       	call   4b5 <test_multiple_capacity_checks+0x5>
 4b5:	48 8b 0d 00 00 00 00 	mov    0x0(%rip),%rcx        # 4bc <test_multiple_capacity_checks+0xc>
 4bc:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # 4c3 <test_multiple_capacity_checks+0x13>
 4c3:	55                   	push   %rbp
 4c4:	48 8b 35 00 00 00 00 	mov    0x0(%rip),%rsi        # 4cb <test_multiple_capacity_checks+0x1b>
 4cb:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 4d2 <test_multiple_capacity_checks+0x22>
 4d2:	48 8d 0c 89          	lea    (%rcx,%rcx,4),%rcx
 4d6:	48 c1 e0 0a          	shl    $0xa,%rax
 4da:	48 c1 e1 08          	shl    $0x8,%rcx
 4de:	48 89 e5             	mov    %rsp,%rbp
 4e1:	5d                   	pop    %rbp
 4e2:	48 39 c1             	cmp    %rax,%rcx
 4e5:	48 8d 0c b6          	lea    (%rsi,%rsi,4),%rcx
 4e9:	0f 92 c0             	setb   %al
 4ec:	48 c1 e1 08          	shl    $0x8,%rcx
 4f0:	48 c1 e2 0a          	shl    $0xa,%rdx
 4f4:	0f b6 c0             	movzbl %al,%eax
 4f7:	48 39 d1             	cmp    %rdx,%rcx
 4fa:	48 8b 0d 00 00 00 00 	mov    0x0(%rip),%rcx        # 501 <test_multiple_capacity_checks+0x51>
 501:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 508 <test_multiple_capacity_checks+0x58>
 508:	83 d0 00             	adc    $0x0,%eax
 50b:	48 8d 0c 89          	lea    (%rcx,%rcx,4),%rcx
 50f:	48 c1 e2 0a          	shl    $0xa,%rdx
 513:	48 c1 e1 08          	shl    $0x8,%rcx
 517:	48 39 d1             	cmp    %rdx,%rcx
 51a:	48 8b 0d 00 00 00 00 	mov    0x0(%rip),%rcx        # 521 <test_multiple_capacity_checks+0x71>
 521:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 528 <test_multiple_capacity_checks+0x78>
 528:	83 d0 00             	adc    $0x0,%eax
 52b:	48 8d 0c 89          	lea    (%rcx,%rcx,4),%rcx
 52f:	48 c1 e2 0a          	shl    $0xa,%rdx
 533:	48 c1 e1 08          	shl    $0x8,%rcx
 537:	48 39 d1             	cmp    %rdx,%rcx
 53a:	48 8b 0d 00 00 00 00 	mov    0x0(%rip),%rcx        # 541 <test_multiple_capacity_checks+0x91>
 541:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 548 <test_multiple_capacity_checks+0x98>
 548:	83 d0 00             	adc    $0x0,%eax
 54b:	48 8d 0c 89          	lea    (%rcx,%rcx,4),%rcx
 54f:	48 c1 e2 0a          	shl    $0xa,%rdx
 553:	48 c1 e1 08          	shl    $0x8,%rcx
 557:	48 39 d1             	cmp    %rdx,%rcx
 55a:	48 8b 0d 00 00 00 00 	mov    0x0(%rip),%rcx        # 561 <test_multiple_capacity_checks+0xb1>
 561:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 568 <test_multiple_capacity_checks+0xb8>
 568:	83 d0 00             	adc    $0x0,%eax
 56b:	48 8d 0c 89          	lea    (%rcx,%rcx,4),%rcx
 56f:	48 c1 e2 0a          	shl    $0xa,%rdx
 573:	48 c1 e1 08          	shl    $0x8,%rcx
 577:	48 39 d1             	cmp    %rdx,%rcx
 57a:	48 8b 0d 00 00 00 00 	mov    0x0(%rip),%rcx        # 581 <test_multiple_capacity_checks+0xd1>
 581:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 588 <test_multiple_capacity_checks+0xd8>
 588:	83 d0 00             	adc    $0x0,%eax
 58b:	48 8d 0c 89          	lea    (%rcx,%rcx,4),%rcx
 58f:	48 c1 e2 0a          	shl    $0xa,%rdx
 593:	48 c1 e1 08          	shl    $0x8,%rcx
 597:	48 39 d1             	cmp    %rdx,%rcx
 59a:	83 d0 00             	adc    $0x0,%eax
 59d:	31 d2                	xor    %edx,%edx
 59f:	31 c9                	xor    %ecx,%ecx
 5a1:	31 f6                	xor    %esi,%esi
 5a3:	e9 00 00 00 00       	jmp    5a8 <test_multiple_capacity_checks+0xf8>

Disassembly of section .exit.text:

0000000000000000 <__pfx_cleanup_module>:
   0:	90                   	nop
   1:	90                   	nop
   2:	90                   	nop
   3:	90                   	nop
   4:	90                   	nop
   5:	90                   	nop
   6:	90                   	nop
   7:	90                   	nop
   8:	90                   	nop
   9:	90                   	nop
   a:	90                   	nop
   b:	90                   	nop
   c:	90                   	nop
   d:	90                   	nop
   e:	90                   	nop
   f:	90                   	nop

0000000000000010 <cleanup_module>:
  10:	55                   	push   %rbp
  11:	48 c7 c7 00 00 00 00 	mov    $0x0,%rdi
  18:	48 89 e5             	mov    %rsp,%rbp
  1b:	e8 00 00 00 00       	call   20 <cleanup_module+0x10>
  20:	5d                   	pop    %rbp
  21:	31 c0                	xor    %eax,%eax
  23:	31 ff                	xor    %edi,%edi
  25:	e9 00 00 00 00       	jmp    2a <__UNIQUE_ID___addressable_test_with_constants260+0x2>

Disassembly of section .init.text:

0000000000000000 <__pfx_init_module>:
   0:	90                   	nop
   1:	90                   	nop
   2:	90                   	nop
   3:	90                   	nop
   4:	90                   	nop
   5:	90                   	nop
   6:	90                   	nop
   7:	90                   	nop
   8:	90                   	nop
   9:	90                   	nop
   a:	90                   	nop
   b:	90                   	nop
   c:	90                   	nop
   d:	90                   	nop
   e:	90                   	nop
   f:	90                   	nop

0000000000000010 <init_module>:
  10:	e8 00 00 00 00       	call   15 <init_module+0x5>
  15:	55                   	push   %rbp
  16:	48 c7 c7 00 00 00 00 	mov    $0x0,%rdi
  1d:	48 89 e5             	mov    %rsp,%rbp
  20:	e8 00 00 00 00       	call   25 <init_module+0x15>
  25:	48 c7 05 00 00 00 00 	movq   $0x320,0x0(%rip)        # 30 <init_module+0x20>
  2c:	20 03 00 00 
  30:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 3b <init_module+0x2b>
  37:	00 04 00 00 
  3b:	48 c7 05 00 00 00 00 	movq   $0x1f4,0x0(%rip)        # 46 <init_module+0x36>
  42:	f4 01 00 00 
  46:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 51 <init_module+0x41>
  4d:	00 04 00 00 
  51:	48 c7 05 00 00 00 00 	movq   $0x320,0x0(%rip)        # 5c <init_module+0x4c>
  58:	20 03 00 00 
  5c:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 67 <init_module+0x57>
  63:	00 04 00 00 
  67:	48 c7 05 00 00 00 00 	movq   $0x384,0x0(%rip)        # 72 <init_module+0x62>
  6e:	84 03 00 00 
  72:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 7d <init_module+0x6d>
  79:	00 04 00 00 
  7d:	48 c7 05 00 00 00 00 	movq   $0x3e8,0x0(%rip)        # 88 <init_module+0x78>
  84:	e8 03 00 00 
  88:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 93 <init_module+0x83>
  8f:	00 04 00 00 
  93:	48 c7 05 00 00 00 00 	movq   $0x4b0,0x0(%rip)        # 9e <init_module+0x8e>
  9a:	b0 04 00 00 
  9e:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # a9 <init_module+0x99>
  a5:	00 04 00 00 
  a9:	48 c7 05 00 00 00 00 	movq   $0x320,0x0(%rip)        # b4 <init_module+0xa4>
  b0:	20 03 00 00 
  b4:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # bf <init_module+0xaf>
  bb:	00 04 00 00 
  bf:	48 c7 05 00 00 00 00 	movq   $0x384,0x0(%rip)        # ca <init_module+0xba>
  c6:	84 03 00 00 
  ca:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # d5 <init_module+0xc5>
  d1:	00 04 00 00 
  d5:	48 c7 05 00 00 00 00 	movq   $0x200,0x0(%rip)        # e0 <init_module+0xd0>
  dc:	00 02 00 00 
  e0:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # eb <init_module+0xdb>
  e7:	00 04 00 00 
  eb:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # f6 <init_module+0xe6>
  f2:	00 04 00 00 
  f6:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 101 <init_module+0xf1>
  fd:	00 04 00 00 
 101:	48 c7 05 00 00 00 00 	movq   $0x500,0x0(%rip)        # 10c <init_module+0xfc>
 108:	00 05 00 00 
 10c:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 117 <init_module+0x107>
 113:	00 04 00 00 
 117:	48 c7 05 00 00 00 00 	movq   $0x320,0x0(%rip)        # 122 <init_module+0x112>
 11e:	20 03 00 00 
 122:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 12d <init_module+0x11d>
 129:	00 04 00 00 
 12d:	48 c7 05 00 00 00 00 	movq   $0x320,0x0(%rip)        # 138 <init_module+0x128>
 134:	20 03 00 00 
 138:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 143 <init_module+0x133>
 13f:	00 04 00 00 
 143:	48 c7 05 00 00 00 00 	movq   $0x258,0x0(%rip)        # 14e <init_module+0x13e>
 14a:	58 02 00 00 
 14e:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 159 <init_module+0x149>
 155:	00 04 00 00 
 159:	48 c7 05 00 00 00 00 	movq   $0x2bc,0x0(%rip)        # 164 <init_module+0x154>
 160:	bc 02 00 00 
 164:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 16f <init_module+0x15f>
 16b:	00 04 00 00 
 16f:	48 c7 05 00 00 00 00 	movq   $0x320,0x0(%rip)        # 17a <init_module+0x16a>
 176:	20 03 00 00 
 17a:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 185 <init_module+0x175>
 181:	00 04 00 00 
 185:	48 c7 05 00 00 00 00 	movq   $0x384,0x0(%rip)        # 190 <init_module+0x180>
 18c:	84 03 00 00 
 190:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 19b <init_module+0x18b>
 197:	00 04 00 00 
 19b:	48 c7 05 00 00 00 00 	movq   $0x3e8,0x0(%rip)        # 1a6 <init_module+0x196>
 1a2:	e8 03 00 00 
 1a6:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 1b1 <init_module+0x1a1>
 1ad:	00 04 00 00 
 1b1:	48 c7 05 00 00 00 00 	movq   $0x44c,0x0(%rip)        # 1bc <init_module+0x1ac>
 1b8:	4c 04 00 00 
 1bc:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 1c7 <init_module+0x1b7>
 1c3:	00 04 00 00 
 1c7:	48 c7 05 00 00 00 00 	movq   $0x4b0,0x0(%rip)        # 1d2 <init_module+0x1c2>
 1ce:	b0 04 00 00 
 1d2:	48 c7 05 00 00 00 00 	movq   $0x400,0x0(%rip)        # 1dd <init_module+0x1cd>
 1d9:	00 04 00 00 
 1dd:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 1e4 <init_module+0x1d4>
 1e4:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # 1eb <init_module+0x1db>
 1eb:	48 8d 14 92          	lea    (%rdx,%rdx,4),%rdx
 1ef:	48 c1 e2 08          	shl    $0x8,%rdx
 1f3:	48 c1 e0 0a          	shl    $0xa,%rax
 1f7:	48 39 c2             	cmp    %rax,%rdx
 1fa:	0f 92 c0             	setb   %al
 1fd:	0f b6 c0             	movzbl %al,%eax
 200:	89 05 00 00 00 00    	mov    %eax,0x0(%rip)        # 206 <init_module+0x1f6>
 206:	e8 00 00 00 00       	call   20b <init_module+0x1fb>
 20b:	89 c2                	mov    %eax,%edx
 20d:	8b 05 00 00 00 00    	mov    0x0(%rip),%eax        # 213 <init_module+0x203>
 213:	01 d0                	add    %edx,%eax
 215:	89 05 00 00 00 00    	mov    %eax,0x0(%rip)        # 21b <init_module+0x20b>
 21b:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 222 <init_module+0x212>
 222:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # 229 <init_module+0x219>
 229:	48 89 d6             	mov    %rdx,%rsi
 22c:	48 8d 0c 80          	lea    (%rax,%rax,4),%rcx
 230:	48 c1 e6 0a          	shl    $0xa,%rsi
 234:	48 01 c0             	add    %rax,%rax
 237:	48 c1 e1 08          	shl    $0x8,%rcx
 23b:	48 39 f1             	cmp    %rsi,%rcx
 23e:	48 0f 42 d0          	cmovb  %rax,%rdx
 242:	8b 05 00 00 00 00    	mov    0x0(%rip),%eax        # 248 <init_module+0x238>
 248:	01 d0                	add    %edx,%eax
 24a:	89 05 00 00 00 00    	mov    %eax,0x0(%rip)        # 250 <init_module+0x240>
 250:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 257 <init_module+0x247>
 257:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # 25e <init_module+0x24e>
 25e:	8b 35 00 00 00 00    	mov    0x0(%rip),%esi        # 264 <init_module+0x254>
 264:	48 89 d7             	mov    %rdx,%rdi
 267:	48 8d 14 52          	lea    (%rdx,%rdx,2),%rdx
 26b:	48 8d 0c 80          	lea    (%rax,%rax,4),%rcx
 26f:	48 c1 e7 0a          	shl    $0xa,%rdi
 273:	48 c1 e1 08          	shl    $0x8,%rcx
 277:	48 39 f9             	cmp    %rdi,%rcx
 27a:	0f 92 c1             	setb   %cl
 27d:	48 c1 ea 02          	shr    $0x2,%rdx
 281:	48 39 c2             	cmp    %rax,%rdx
 284:	0f 92 c0             	setb   %al
 287:	0f b6 c0             	movzbl %al,%eax
 28a:	21 c8                	and    %ecx,%eax
 28c:	01 f0                	add    %esi,%eax
 28e:	89 05 00 00 00 00    	mov    %eax,0x0(%rip)        # 294 <init_module+0x284>
 294:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # 29b <init_module+0x28b>
 29b:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 2a2 <init_module+0x292>
 2a2:	48 8b 35 00 00 00 00 	mov    0x0(%rip),%rsi        # 2a9 <init_module+0x299>
 2a9:	48 8b 0d 00 00 00 00 	mov    0x0(%rip),%rcx        # 2b0 <init_module+0x2a0>
 2b0:	48 c1 e2 0a          	shl    $0xa,%rdx
 2b4:	48 8d 0c 89          	lea    (%rcx,%rcx,4),%rcx
 2b8:	48 c1 e1 08          	shl    $0x8,%rcx
 2bc:	48 39 d1             	cmp    %rdx,%rcx
 2bf:	0f 83 53 01 00 00    	jae    418 <init_module+0x408>
 2c5:	48 8d 14 b6          	lea    (%rsi,%rsi,4),%rdx
 2c9:	48 c1 e0 0a          	shl    $0xa,%rax
 2cd:	48 c1 e2 08          	shl    $0x8,%rdx
 2d1:	48 39 c2             	cmp    %rax,%rdx
 2d4:	0f 93 c0             	setae  %al
 2d7:	0f b6 c0             	movzbl %al,%eax
 2da:	83 c0 01             	add    $0x1,%eax
 2dd:	8b 15 00 00 00 00    	mov    0x0(%rip),%edx        # 2e3 <init_module+0x2d3>
 2e3:	01 d0                	add    %edx,%eax
 2e5:	89 05 00 00 00 00    	mov    %eax,0x0(%rip)        # 2eb <init_module+0x2db>
 2eb:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 2f2 <init_module+0x2e2>
 2f2:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # 2f9 <init_module+0x2e9>
 2f9:	48 c1 e2 0a          	shl    $0xa,%rdx
 2fd:	48 8d 0c 80          	lea    (%rax,%rax,4),%rcx
 301:	48 8d 34 00          	lea    (%rax,%rax,1),%rsi
 305:	48 c1 e1 08          	shl    $0x8,%rcx
 309:	48 39 d1             	cmp    %rdx,%rcx
 30c:	8b 15 00 00 00 00    	mov    0x0(%rip),%edx        # 312 <init_module+0x302>
 312:	48 0f 42 c6          	cmovb  %rsi,%rax
 316:	01 d0                	add    %edx,%eax
 318:	89 05 00 00 00 00    	mov    %eax,0x0(%rip)        # 31e <init_module+0x30e>
 31e:	48 8b 3d 00 00 00 00 	mov    0x0(%rip),%rdi        # 325 <init_module+0x315>
 325:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 32c <init_module+0x31c>
 32c:	48 8b 35 00 00 00 00 	mov    0x0(%rip),%rsi        # 333 <init_module+0x323>
 333:	48 8b 0d 00 00 00 00 	mov    0x0(%rip),%rcx        # 33a <init_module+0x32a>
 33a:	8b 05 00 00 00 00    	mov    0x0(%rip),%eax        # 340 <init_module+0x330>
 340:	48 8d 34 b6          	lea    (%rsi,%rsi,4),%rsi
 344:	48 c1 e6 08          	shl    $0x8,%rsi
 348:	48 c1 e1 0a          	shl    $0xa,%rcx
 34c:	48 39 ce             	cmp    %rcx,%rsi
 34f:	8d 0c bf             	lea    (%rdi,%rdi,4),%ecx
 352:	83 d0 00             	adc    $0x0,%eax
 355:	c1 e1 08             	shl    $0x8,%ecx
 358:	c1 e2 0a             	shl    $0xa,%edx
 35b:	39 d1                	cmp    %edx,%ecx
 35d:	0f 9c c2             	setl   %dl
 360:	0f b6 d2             	movzbl %dl,%edx
 363:	01 d0                	add    %edx,%eax
 365:	89 05 00 00 00 00    	mov    %eax,0x0(%rip)        # 36b <init_module+0x35b>
 36b:	e8 00 00 00 00       	call   370 <init_module+0x360>
 370:	89 c2                	mov    %eax,%edx
 372:	8b 05 00 00 00 00    	mov    0x0(%rip),%eax        # 378 <init_module+0x368>
 378:	01 d0                	add    %edx,%eax
 37a:	89 05 00 00 00 00    	mov    %eax,0x0(%rip)        # 380 <init_module+0x370>
 380:	48 8b 05 00 00 00 00 	mov    0x0(%rip),%rax        # 387 <init_module+0x377>
 387:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 38e <init_module+0x37e>
 38e:	48 c1 e0 0a          	shl    $0xa,%rax
 392:	48 8d 14 92          	lea    (%rdx,%rdx,4),%rdx
 396:	48 c1 e2 08          	shl    $0x8,%rdx
 39a:	48 39 c2             	cmp    %rax,%rdx
 39d:	8b 15 00 00 00 00    	mov    0x0(%rip),%edx        # 3a3 <init_module+0x393>
 3a3:	19 c0                	sbb    %eax,%eax
 3a5:	83 e0 9c             	and    $0xffffff9c,%eax
 3a8:	8d 84 02 c8 00 00 00 	lea    0xc8(%rdx,%rax,1),%eax
 3af:	89 05 00 00 00 00    	mov    %eax,0x0(%rip)        # 3b5 <init_module+0x3a5>
 3b5:	48 8b 0d 00 00 00 00 	mov    0x0(%rip),%rcx        # 3bc <init_module+0x3ac>
 3bc:	48 8b 15 00 00 00 00 	mov    0x0(%rip),%rdx        # 3c3 <init_module+0x3b3>
 3c3:	8b 05 00 00 00 00    	mov    0x0(%rip),%eax        # 3c9 <init_module+0x3b9>
 3c9:	48 8d 0c 89          	lea    (%rcx,%rcx,4),%rcx
 3cd:	48 c1 e2 0a          	shl    $0xa,%rdx
 3d1:	48 c1 e1 08          	shl    $0x8,%rcx
 3d5:	48 39 d1             	cmp    %rdx,%rcx
 3d8:	83 d0 00             	adc    $0x0,%eax
 3db:	89 05 00 00 00 00    	mov    %eax,0x0(%rip)        # 3e1 <init_module+0x3d1>
 3e1:	e8 00 00 00 00       	call   3e6 <init_module+0x3d6>
 3e6:	48 c7 c7 00 00 00 00 	mov    $0x0,%rdi
 3ed:	89 c2                	mov    %eax,%edx
 3ef:	8b 05 00 00 00 00    	mov    0x0(%rip),%eax        # 3f5 <init_module+0x3e5>
 3f5:	01 d0                	add    %edx,%eax
 3f7:	89 05 00 00 00 00    	mov    %eax,0x0(%rip)        # 3fd <init_module+0x3ed>
 3fd:	8b 35 00 00 00 00    	mov    0x0(%rip),%esi        # 403 <init_module+0x3f3>
 403:	e8 00 00 00 00       	call   408 <init_module+0x3f8>
 408:	31 c0                	xor    %eax,%eax
 40a:	5d                   	pop    %rbp
 40b:	31 d2                	xor    %edx,%edx
 40d:	31 c9                	xor    %ecx,%ecx
 40f:	31 f6                	xor    %esi,%esi
 411:	31 ff                	xor    %edi,%edi
 413:	e9 00 00 00 00       	jmp    418 <init_module+0x408>
 418:	48 8d 14 b6          	lea    (%rsi,%rsi,4),%rdx
 41c:	48 c1 e0 0a          	shl    $0xa,%rax
 420:	48 c1 e2 08          	shl    $0x8,%rdx
 424:	48 39 c2             	cmp    %rax,%rdx
 427:	0f 92 c0             	setb   %al
 42a:	0f b6 c0             	movzbl %al,%eax
 42d:	01 c0                	add    %eax,%eax
 42f:	e9 a9 fe ff ff       	jmp    2dd <init_module+0x2cd>
