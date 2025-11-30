; ModuleID = 'test_module'
source_filename = "test_module"

define void @foo(ptr %1, i32 %2) {
  %27 = alloca i8, align 8
  %55 = getelementptr inbounds nuw i8, ptr %27, i64 40 ; real kernel code
  br label %57
57:
  br label %dummy
61:
  br label %dummy
dummy:
  %65 = phi i32 [ 3600, %57 ], [ 7000, %61 ]           ; real kernel code
  store i32 %65, ptr %55, align 8                      ; real kernel code
  ret void
}
