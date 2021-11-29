library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity genDecoder is
  generic(outWidth: integer := 256;
          inWidth: integer := 8);
 port(decIn: in std_logic_vector(inWidth-1 downto 0);
      decOut: out std_logic_vector(outWidth-1 downto 0);
      clk: in std_logic);

end genDecoder;

architecture genDecoder_arch of genDecoder is
begin
process(decIn)
begin
decOut <= (others => '0'); -- default
decOut(to_integer(unsigned(decIn))) <= '1';
end process;

end genDecoder_arch;
