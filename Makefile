obj-m += find_functions.o
obj-m += analyze_function.o
obj-m += find_util_fits.o
obj-m += find_inline.o
obj-m += find_fits_capacity.o
obj-m += analyze_fits_capacity.o
obj-m += complete_assembly_analyzer.o
obj-m += generic_macro_analyzer.o
obj-m += advanced_macro_analyzer.o
obj-m += fits_capacity_asm_test.o

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean 