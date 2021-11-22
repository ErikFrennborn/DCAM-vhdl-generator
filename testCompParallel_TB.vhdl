library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity testCompParallel_tb is
end testCompParallel_tb;


architecture testCompParallel_tb_arch of testCompParallel_tb is

component testCompParallel is
  port(inComp: in std_logic_vector(15 downto 0);
       outComp: out std_logic_vector(1 downto 0);
       clk: in std_logic);
end component testCompParallel;

signal clk_tb: std_logic := '0';
signal inComp_tb: std_logic_vector(15 downto 0) := "0000000000000000";
signal outComp_tb: std_logic_vector(1 downto 0):= "00";

begin

testCompParallel_comp: 
 component testCompParallel
  port map(clk => clk_tb,
           inComp => inComp_tb,
            outComp => outComp_tb);

clk_tb_proc:
process
begin
 wait for 100 ns;
 clk_tb <= not clk_tb;
end process clk_tb_proc;

inComp_tb <= "0100000101000010",
	      "0100001001000011" after 250 ns,
              "0100000101000100" after 450 ns;

end testCompParallel_tb_arch;

