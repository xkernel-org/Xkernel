; ModuleID = 'tests/7_locate_the_right_target.c'
source_filename = "tests/7_locate_the_right_target.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @foo() #0 !dbg !10 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  %3 = alloca i32, align 4
  %4 = alloca i32, align 4
  %5 = alloca i32, align 4
  %6 = alloca i32, align 4
  %7 = alloca i32, align 4
  %8 = alloca i32, align 4
  %9 = alloca i32, align 4
    #dbg_declare(ptr %1, !15, !DIExpression(), !16)
  store i32 3600, ptr %1, align 4, !dbg !16
    #dbg_declare(ptr %2, !17, !DIExpression(), !18)
  store i32 3600, ptr %2, align 4, !dbg !18
    #dbg_declare(ptr %3, !19, !DIExpression(), !20)
    #dbg_declare(ptr %4, !21, !DIExpression(), !22)
    #dbg_declare(ptr %5, !23, !DIExpression(), !24)
    #dbg_declare(ptr %6, !25, !DIExpression(), !26)
    #dbg_declare(ptr %7, !27, !DIExpression(), !28)
    #dbg_declare(ptr %8, !29, !DIExpression(), !30)
    #dbg_declare(ptr %9, !31, !DIExpression(), !32)
  %10 = load i32, ptr %1, align 4, !dbg !33
  %11 = add nsw i32 %10, 1, !dbg !34
  store i32 %11, ptr %3, align 4, !dbg !35
  %12 = load i32, ptr %1, align 4, !dbg !36
  %13 = sdiv i32 %12, 3, !dbg !37
  store i32 %13, ptr %4, align 4, !dbg !38
  %14 = load i32, ptr %3, align 4, !dbg !39
  %15 = load i32, ptr %4, align 4, !dbg !40
  %16 = mul nsw i32 %14, %15, !dbg !41
  store i32 %16, ptr %5, align 4, !dbg !42
  %17 = load i32, ptr %2, align 4, !dbg !43
  %18 = load i32, ptr %4, align 4, !dbg !44
  %19 = add nsw i32 %17, %18, !dbg !45
  store i32 %19, ptr %6, align 4, !dbg !46
  %20 = load i32, ptr %6, align 4, !dbg !47
  %21 = load i32, ptr %5, align 4, !dbg !48
  %22 = srem i32 %20, %21, !dbg !49
  store i32 %22, ptr %8, align 4, !dbg !50
  %23 = load i32, ptr %8, align 4, !dbg !51
  %24 = add nsw i32 %23, 1, !dbg !51
  store i32 %24, ptr %8, align 4, !dbg !51
  store i32 %23, ptr %9, align 4, !dbg !52
  ret i32 0, !dbg !53
}

attributes #0 = { noinline nounwind optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4, !5, !6, !7, !8}
!llvm.ident = !{!9}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "Ubuntu clang version 20.1.8 (++20250708082409+6fb913d3e2ec-1~exp1~20250708202428.132)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "tests/7_locate_the_right_target.c", directory: "/home/wentaoz5/wentaoz5/xkernel/defuse/tmp", checksumkind: CSK_MD5, checksum: "d3d3dda5d4794916eb41fff3f775fdff")
!2 = !{i32 7, !"Dwarf Version", i32 5}
!3 = !{i32 2, !"Debug Info Version", i32 3}
!4 = !{i32 1, !"wchar_size", i32 4}
!5 = !{i32 8, !"PIC Level", i32 2}
!6 = !{i32 7, !"PIE Level", i32 2}
!7 = !{i32 7, !"uwtable", i32 2}
!8 = !{i32 7, !"frame-pointer", i32 2}
!9 = !{!"Ubuntu clang version 20.1.8 (++20250708082409+6fb913d3e2ec-1~exp1~20250708202428.132)"}
!10 = distinct !DISubprogram(name: "foo", scope: !1, file: !1, line: 6, type: !11, scopeLine: 6, spFlags: DISPFlagDefinition, unit: !0, retainedNodes: !14)
!11 = !DISubroutineType(types: !12)
!12 = !{!13}
!13 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!14 = !{}
!15 = !DILocalVariable(name: "a", scope: !10, file: !1, line: 7, type: !13)
!16 = !DILocation(line: 7, column: 9, scope: !10)
!17 = !DILocalVariable(name: "b", scope: !10, file: !1, line: 8, type: !13)
!18 = !DILocation(line: 8, column: 9, scope: !10)
!19 = !DILocalVariable(name: "c", scope: !10, file: !1, line: 9, type: !13)
!20 = !DILocation(line: 9, column: 9, scope: !10)
!21 = !DILocalVariable(name: "d", scope: !10, file: !1, line: 9, type: !13)
!22 = !DILocation(line: 9, column: 12, scope: !10)
!23 = !DILocalVariable(name: "e", scope: !10, file: !1, line: 9, type: !13)
!24 = !DILocation(line: 9, column: 15, scope: !10)
!25 = !DILocalVariable(name: "f", scope: !10, file: !1, line: 9, type: !13)
!26 = !DILocation(line: 9, column: 18, scope: !10)
!27 = !DILocalVariable(name: "g", scope: !10, file: !1, line: 9, type: !13)
!28 = !DILocation(line: 9, column: 21, scope: !10)
!29 = !DILocalVariable(name: "h", scope: !10, file: !1, line: 9, type: !13)
!30 = !DILocation(line: 9, column: 24, scope: !10)
!31 = !DILocalVariable(name: "i", scope: !10, file: !1, line: 9, type: !13)
!32 = !DILocation(line: 9, column: 27, scope: !10)
!33 = !DILocation(line: 11, column: 9, scope: !10)
!34 = !DILocation(line: 11, column: 11, scope: !10)
!35 = !DILocation(line: 11, column: 7, scope: !10)
!36 = !DILocation(line: 12, column: 9, scope: !10)
!37 = !DILocation(line: 12, column: 11, scope: !10)
!38 = !DILocation(line: 12, column: 7, scope: !10)
!39 = !DILocation(line: 13, column: 9, scope: !10)
!40 = !DILocation(line: 13, column: 13, scope: !10)
!41 = !DILocation(line: 13, column: 11, scope: !10)
!42 = !DILocation(line: 13, column: 7, scope: !10)
!43 = !DILocation(line: 15, column: 9, scope: !10)
!44 = !DILocation(line: 15, column: 13, scope: !10)
!45 = !DILocation(line: 15, column: 11, scope: !10)
!46 = !DILocation(line: 15, column: 7, scope: !10)
!47 = !DILocation(line: 16, column: 9, scope: !10)
!48 = !DILocation(line: 16, column: 13, scope: !10)
!49 = !DILocation(line: 16, column: 11, scope: !10)
!50 = !DILocation(line: 16, column: 7, scope: !10)
!51 = !DILocation(line: 17, column: 10, scope: !10)
!52 = !DILocation(line: 17, column: 7, scope: !10)
!53 = !DILocation(line: 19, column: 5, scope: !10)
