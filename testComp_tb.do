restart -f -nowave
view signals wave
add wave -r /*
--radix decimal inComp_tb outComp_tb
--add wave clk_tb
run 1800 ns
