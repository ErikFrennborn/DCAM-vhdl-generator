library ieee;
use ieee.std_logic_1164.all;

entity genRegister is
 generic(n: integer := 1);
 port(d: in std_logic_vector(n-1 downto 0);
      q: out std_logic_vector(n-1 downto 0);
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
