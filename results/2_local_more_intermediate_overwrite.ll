; ModuleID = 'tests/2_local_more_intermediate_overwrite.c'
source_filename = "tests/2_local_more_intermediate_overwrite.c"
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
    #dbg_declare(ptr %2, !15, !DIExpression(), !16)
  store i32 100, ptr %2, align 4, !dbg !16
    #dbg_declare(ptr %3, !17, !DIExpression(), !18)
  store i32 3600, ptr %3, align 4, !dbg !18
    #dbg_declare(ptr %4, !19, !DIExpression(), !20)
    #dbg_declare(ptr %5, !21, !DIExpression(), !22)
    #dbg_declare(ptr %6, !23, !DIExpression(), !24)
    #dbg_declare(ptr %7, !25, !DIExpression(), !26)
    #dbg_declare(ptr %8, !27, !DIExpression(), !28)
    #dbg_declare(ptr %9, !29, !DIExpression(), !30)
  %10 = load i32, ptr %3, align 4, !dbg !31
  store i32 %10, ptr %9, align 4, !dbg !32
  store i32 42, ptr %3, align 4, !dbg !33
  %11 = load i32, ptr %3, align 4, !dbg !34
  %12 = load i32, ptr %2, align 4, !dbg !35
  %13 = add nsw i32 %11, %12, !dbg !36
  store i32 %13, ptr %4, align 4, !dbg !37
  %14 = load i32, ptr %4, align 4, !dbg !38
  %15 = load i32, ptr %3, align 4, !dbg !39
  %16 = sub nsw i32 %14, %15, !dbg !40
  store i32 %16, ptr %5, align 4, !dbg !41
  %17 = load i32, ptr %5, align 4, !dbg !42
  %18 = load i32, ptr %2, align 4, !dbg !43
  %19 = mul nsw i32 %17, %18, !dbg !44
  store i32 %19, ptr %6, align 4, !dbg !45
  %20 = load i32, ptr %6, align 4, !dbg !46
  %21 = load i32, ptr %3, align 4, !dbg !47
  %22 = sdiv i32 %20, %21, !dbg !48
  store i32 %22, ptr %7, align 4, !dbg !49
  %23 = load i32, ptr %7, align 4, !dbg !50
  %24 = load i32, ptr %4, align 4, !dbg !51
  %25 = srem i32 %23, %24, !dbg !52
  store i32 %25, ptr %8, align 4, !dbg !53
  %26 = load i32, ptr %2, align 4, !dbg !54
  %27 = load i32, ptr %8, align 4, !dbg !56
  %28 = icmp eq i32 %26, %27, !dbg !57
  br i1 %28, label %29, label %30, !dbg !57

29:                                               ; preds = %0
  store i32 1, ptr %1, align 4, !dbg !58
  br label %31, !dbg !58

30:                                               ; preds = %0
  store i32 0, ptr %1, align 4, !dbg !59
  br label %31, !dbg !59

31:                                               ; preds = %30, %29
  %32 = load i32, ptr %1, align 4, !dbg !60
  ret i32 %32, !dbg !60
}

attributes #0 = { noinline nounwind optnone uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cmov,+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4, !5, !6, !7, !8}
!llvm.ident = !{!9}

!0 = distinct !DICompileUnit(language: DW_LANG_C11, file: !1, producer: "Ubuntu clang version 20.1.8 (++20250708082409+6fb913d3e2ec-1~exp1~20250708202428.132)", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug, splitDebugInlining: false, nameTableKind: None)
!1 = !DIFile(filename: "tests/2_local_more_intermediate_overwrite.c", directory: "/home/wentaoz5/wentaoz5/xkernel/defuse/tmp", checksumkind: CSK_MD5, checksum: "62bacad56436d3795a9b2ab93c891e1a")
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
!19 = !DILocalVariable(name: "c", scope: !10, file: !1, line: 8, type: !13)
!20 = !DILocation(line: 8, column: 9, scope: !10)
!21 = !DILocalVariable(name: "d", scope: !10, file: !1, line: 8, type: !13)
!22 = !DILocation(line: 8, column: 12, scope: !10)
!23 = !DILocalVariable(name: "e", scope: !10, file: !1, line: 8, type: !13)
!24 = !DILocation(line: 8, column: 15, scope: !10)
!25 = !DILocalVariable(name: "f", scope: !10, file: !1, line: 8, type: !13)
!26 = !DILocation(line: 8, column: 18, scope: !10)
!27 = !DILocalVariable(name: "g", scope: !10, file: !1, line: 8, type: !13)
!28 = !DILocation(line: 8, column: 21, scope: !10)
!29 = !DILocalVariable(name: "z", scope: !10, file: !1, line: 9, type: !13)
!30 = !DILocation(line: 9, column: 9, scope: !10)
!31 = !DILocation(line: 11, column: 9, scope: !10)
!32 = !DILocation(line: 11, column: 7, scope: !10)
!33 = !DILocation(line: 13, column: 7, scope: !10)
!34 = !DILocation(line: 15, column: 9, scope: !10)
!35 = !DILocation(line: 15, column: 13, scope: !10)
!36 = !DILocation(line: 15, column: 11, scope: !10)
!37 = !DILocation(line: 15, column: 7, scope: !10)
!38 = !DILocation(line: 16, column: 9, scope: !10)
!39 = !DILocation(line: 16, column: 13, scope: !10)
!40 = !DILocation(line: 16, column: 11, scope: !10)
!41 = !DILocation(line: 16, column: 7, scope: !10)
!42 = !DILocation(line: 17, column: 9, scope: !10)
!43 = !DILocation(line: 17, column: 13, scope: !10)
!44 = !DILocation(line: 17, column: 11, scope: !10)
!45 = !DILocation(line: 17, column: 7, scope: !10)
!46 = !DILocation(line: 18, column: 9, scope: !10)
!47 = !DILocation(line: 18, column: 13, scope: !10)
!48 = !DILocation(line: 18, column: 11, scope: !10)
!49 = !DILocation(line: 18, column: 7, scope: !10)
!50 = !DILocation(line: 19, column: 9, scope: !10)
!51 = !DILocation(line: 19, column: 13, scope: !10)
!52 = !DILocation(line: 19, column: 11, scope: !10)
!53 = !DILocation(line: 19, column: 7, scope: !10)
!54 = !DILocation(line: 21, column: 9, scope: !55)
!55 = distinct !DILexicalBlock(scope: !10, file: !1, line: 21, column: 9)
!56 = !DILocation(line: 21, column: 14, scope: !55)
!57 = !DILocation(line: 21, column: 11, scope: !55)
!58 = !DILocation(line: 22, column: 9, scope: !55)
!59 = !DILocation(line: 23, column: 5, scope: !10)
!60 = !DILocation(line: 24, column: 1, scope: !10)
