library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity testComp_tb is
end testComp_tb;


architecture testComp_tb_arch of testComp_tb is

component testComp is
  port(inComp: in std_logic_vector(7 downto 0);
       outComp: out std_logic_vector(1 downto 0);
       clk: in std_logic);
end component testComp;

signal clk_tb: std_logic := '0';
signal inComp_tb: std_logic_vector(7 downto 0) := "00000000";
signal outComp_tb: std_logic_vector(1 downto 0):= "00";

begin

testComp_comp: 
 component testComp
  port map(clk => clk_tb,
           inComp => inComp_tb,
            outComp => outComp_tb);

clk_tb_proc:
process
begin
 wait for 100 ns;
 clk_tb <= not clk_tb;
end process clk_tb_proc;

inComp_tb <= "01000001",
              "01000010" after 250 ns,
	      "01000010" after 450 ns,
              "01000011" after 650 ns,
              "01000001" after 850 ns;

end testComp_tb_arch;

