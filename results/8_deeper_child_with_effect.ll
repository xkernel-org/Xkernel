; ModuleID = 'tests/8_deeper_child_with_effect.c'
source_filename = "tests/8_deeper_child_with_effect.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-pc-linux-gnu"

@g = dso_local global i32 0, align 4, !dbg !0

; Function Attrs: noinline nounwind optnone uwtable
define dso_local void @baz(i32 noundef %0) #0 !dbg !14 {
  %2 = alloca i32, align 4
  store i32 %0, ptr %2, align 4
    #dbg_declare(ptr %2, !18, !DIExpression(), !19)
  %3 = load i32, ptr %2, align 4, !dbg !20
  store i32 %3, ptr @g, align 4, !dbg !21
  ret void, !dbg !22
}

; Function Attrs: noinline nounwind optnone uwtable
define dso_local void @bar(i32 noundef %0) #0 !dbg !23 {
  %2 = alloca i32, align 4
  %3 = alloca i32, align 4
  store i32 %0, ptr %2, align 4
    #dbg_declare(ptr %2, !24, !DIExpression(), !25)
    #dbg_declare(ptr %3, !26, !DIExpression(), !27)
  store i32 3000, ptr %3, align 4, !dbg !27
  %4 = load i32, ptr %3, align 4, !dbg !28
  call void @baz(i32 noundef %4), !dbg !29
  %5 = load i32, ptr %2, align 4, !dbg !30
  call void @baz(i32 noundef %5), !dbg !31
  ret void, !dbg !32
}

; Function Attrs: noinline nounwind optnone uwtable
define dso_local i32 @foo() #0 !dbg !33 {
  call void @bar(i32 noundef 3600), !dbg !36
  ret i32 0, !dbg !37
}

attributes #0 = { noinline nounwind optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }

!llvm.dbg.cu = !{!2}
!llvm.module.flags = !{!6, !7, !8, !9, !10, !11, !12}
!llvm.ident = !{!13}

!0 = !DIGlobalVariableExpression(var: !1, expr: !DIExpression())
!1 = distinct !DIGlobalVariable(name: "g", scope: !2, file: !3, line: 5, type: !5, isLocal: false, isDefinition: true)
!2 = distinct !DICompileUnit(language: DW_LANG_C11, file: !3, producer: "Ubuntu clang version 20.1.8 (++20250708082409+6fb913d3e2ec-1~exp1~20250708202428.132)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, globals: !4, splitDebugInlining: false, nameTableKind: None)
!3 = !DIFile(filename: "tests/8_deeper_child_with_effect.c", directory: "/home/wentaoz5/wentaoz5/xkernel/defuse/tmp", checksumkind: CSK_MD5, checksum: "e3ee3044d838f8634ea829b201a743dd")
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
!14 = distinct !DISubprogram(name: "baz", scope: !3, file: !3, line: 7, type: !15, scopeLine: 7, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !2, retainedNodes: !17)
!15 = !DISubroutineType(types: !16)
!16 = !{null, !5}
!17 = !{}
!18 = !DILocalVariable(name: "x", arg: 1, scope: !14, file: !3, line: 7, type: !5)
!19 = !DILocation(line: 7, column: 14, scope: !14)
!20 = !DILocation(line: 8, column: 9, scope: !14)
!21 = !DILocation(line: 8, column: 7, scope: !14)
!22 = !DILocation(line: 9, column: 1, scope: !14)
!23 = distinct !DISubprogram(name: "bar", scope: !3, file: !3, line: 11, type: !15, scopeLine: 11, flags: DIFlagPrototyped, spFlags: DISPFlagDefinition, unit: !2, retainedNodes: !17)
!24 = !DILocalVariable(name: "x", arg: 1, scope: !23, file: !3, line: 11, type: !5)
!25 = !DILocation(line: 11, column: 14, scope: !23)
!26 = !DILocalVariable(name: "y", scope: !23, file: !3, line: 12, type: !5)
!27 = !DILocation(line: 12, column: 9, scope: !23)
!28 = !DILocation(line: 13, column: 9, scope: !23)
!29 = !DILocation(line: 13, column: 5, scope: !23)
!30 = !DILocation(line: 14, column: 9, scope: !23)
!31 = !DILocation(line: 14, column: 5, scope: !23)
!32 = !DILocation(line: 15, column: 1, scope: !23)
!33 = distinct !DISubprogram(name: "foo", scope: !3, file: !3, line: 17, type: !34, scopeLine: 17, spFlags: DISPFlagDefinition, unit: !2)
!34 = !DISubroutineType(types: !35)
!35 = !{!5}
!36 = !DILocation(line: 18, column: 5, scope: !33)
!37 = !DILocation(line: 19, column: 5, scope: !33)
