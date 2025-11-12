; ModuleID = 'tests/4_global_indirect.c'
source_filename = "tests/4_global_indirect.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

@g = dso_local global i32 0, align 4, !dbg !0

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @foo() #0 !dbg !14 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
    #dbg_declare(ptr %1, !18, !DIExpression(), !19)
  store i32 3600, ptr %1, align 4, !dbg !19
    #dbg_declare(ptr %2, !20, !DIExpression(), !21)
  %3 = load i32, ptr %1, align 4, !dbg !22
  store i32 %3, ptr %2, align 4, !dbg !21
  %4 = load i32, ptr %1, align 4, !dbg !23
  store i32 %4, ptr @g, align 4, !dbg !24
  ret i32 0, !dbg !25
}

attributes #0 = { noinline nounwind optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }

!llvm.dbg.cu = !{!2}
!llvm.module.flags = !{!6, !7, !8, !9, !10, !11, !12}
!llvm.ident = !{!13}

!0 = !DIGlobalVariableExpression(var: !1, expr: !DIExpression())
!1 = distinct !DIGlobalVariable(name: "g", scope: !2, file: !3, line: 5, type: !5, isLocal: false, isDefinition: true)
!2 = distinct !DICompileUnit(language: DW_LANG_C11, file: !3, producer: "Ubuntu clang version 20.1.8 (++20250708082409+6fb913d3e2ec-1~exp1~20250708202428.132)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, globals: !4, splitDebugInlining: false, nameTableKind: None)
!3 = !DIFile(filename: "tests/4_global_indirect.c", directory: "/home/wentaoz5/wentaoz5/xkernel/defuse/tmp", checksumkind: CSK_MD5, checksum: "24f7eb7abec3c51aa6adae2588a06f05")
!4 = !{!0}
!5 = !DIBasicType(name: "int", size: 32, encoding: DW_ATE_signed)
!6 = !{i32 7, !"Dwarf Version", i32 5}
!7 = !{i32 2, !"Debug Info Version", i32 3}
!8 = !{i32 1, !"wchar_size", i32 4}
!9 = !{i32 8, !"PIC Level", i32 2}
!10 = !{i32 7, !"PIE Level", i32 2}
!11 = !{i32 7, !"uwtable", i32 2}
!12 = !{i32 7, !"frame-pointer", i32 2}
!13 = !{!"Ubuntu clang version 20.1.8 (++20250708082409+6fb913d3e2ec-1~exp1~20250708202428.132)"}
!14 = distinct !DISubprogram(name: "foo", scope: !3, file: !3, line: 7, type: !15, scopeLine: 7, spFlags: DISPFlagDefinition, unit: !2, retainedNodes: !17)
!15 = !DISubroutineType(types: !16)
!16 = !{!5}
!17 = !{}
!18 = !DILocalVariable(name: "a", scope: !14, file: !3, line: 8, type: !5)
!19 = !DILocation(line: 8, column: 9, scope: !14)
!20 = !DILocalVariable(name: "b", scope: !14, file: !3, line: 9, type: !5)
!21 = !DILocation(line: 9, column: 9, scope: !14)
!22 = !DILocation(line: 9, column: 13, scope: !14)
!23 = !DILocation(line: 10, column: 9, scope: !14)
!24 = !DILocation(line: 10, column: 7, scope: !14)
!25 = !DILocation(line: 11, column: 5, scope: !14)
