; ModuleID = 'tests/2_local.c'
source_filename = "tests/2_local.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @foo() #0 !dbg !10 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  %3 = alloca i32, align 4
    #dbg_declare(ptr %2, !15, !DIExpression(), !16)
  store i32 100, ptr %2, align 4, !dbg !16
    #dbg_declare(ptr %3, !17, !DIExpression(), !18)
  store i32 3600, ptr %3, align 4, !dbg !18
  %4 = load i32, ptr %2, align 4, !dbg !19
  %5 = load i32, ptr %3, align 4, !dbg !21
  %6 = icmp eq i32 %4, %5, !dbg !22
  br i1 %6, label %7, label %8, !dbg !22

7:                                                ; preds = %0
  store i32 1, ptr %1, align 4, !dbg !23
  br label %9, !dbg !23

8:                                                ; preds = %0
  store i32 0, ptr %1, align 4, !dbg !24
  br label %9, !dbg !24

9:                                                ; preds = %8, %7
  %10 = load i32, ptr %1, align 4, !dbg !25
  ret i32 %10, !dbg !25
}

attributes #0 = { noinline nounwind optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4, !5, !6, !7, !8}
!llvm.ident = !{!9}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "Ubuntu clang version 20.1.8 (++20250708082409+6fb913d3e2ec-1~exp1~20250708202428.132)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "tests/2_local.c", directory: "/home/wentaoz5/wentaoz5/xkernel/defuse/tmp", checksumkind: CSK_MD5, checksum: "1a254e534a3d51bbbf0a50409ad0189f")
!2 = !{i32 7, !"Dwarf Version", i32 5}
!3 = !{i32 2, !"Debug Info Version", i32 3}
!4 = !{i32 1, !"wchar_size", i32 4}
!5 = !{i32 8, !"PIC Level", i32 2}
!6 = !{i32 7, !"PIE Level", i32 2}
!7 = !{i32 7, !"uwtable", i32 2}
!8 = !{i32 7, !"frame-pointer", i32 2}
!9 = !{!"Ubuntu clang version 20.1.8 (++20250708082409+6fb913d3e2ec-1~exp1~20250708202428.132)"}
!10 = distinct !DISubprogram(name: "foo", scope: !1, file: !1, line: 5, type: !11, scopeLine: 5, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !14)
!11 = !DISubroutineType(types: !12)
!12 = !{!13}
!13 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!14 = !{}
!15 = !DILocalVariable(name: "a", scope: !10, file: !1, line: 6, type: !13)
!16 = !DILocation(line: 6, column: 9, scope: !10)
!17 = !DILocalVariable(name: "b", scope: !10, file: !1, line: 7, type: !13)
!18 = !DILocation(line: 7, column: 9, scope: !10)
!19 = !DILocation(line: 8, column: 9, scope: !20)
!20 = distinct !DILexicalBlock(scope: !10, file: !1, line: 8, column: 9)
!21 = !DILocation(line: 8, column: 14, scope: !20)
!22 = !DILocation(line: 8, column: 11, scope: !20)
!23 = !DILocation(line: 9, column: 9, scope: !20)
!24 = !DILocation(line: 10, column: 5, scope: !10)
!25 = !DILocation(line: 11, column: 1, scope: !10)
