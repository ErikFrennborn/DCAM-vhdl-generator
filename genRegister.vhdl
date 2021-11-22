library ieee;
use ieee.std_logic_1164.all;

entity genRegister is
 port(d: in std_logic;
      q: out std_logic;
      clk: in std_logic);
end entity genRegister;

architecture genRegister_arch of genRegister is

begin

process(clk)
begin
if rising_edge(clk) then
  q <= d;
end if;

end process;

end genRegister_arch;