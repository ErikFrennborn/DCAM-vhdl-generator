library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity genEncoder is
  generic(inWidth: integer := 256;
          outWidth: integer := 8);
 port(encIn: in std_logic_vector(inWidth-1 downto 0);
      encOut: out std_logic_vector(outWidth-1 downto 0));

end genEncoder;

architecture genEncoder_arch of genEncoder is

function encFunc(
 encFuncIn: std_logic_vector(inWidth-1 downto 0))
 return std_logic_vector is
 variable encFuncOut: std_logic_vector(outWidth-1 downto 0);
begin

for i in encFuncIn'range loop
 if encFuncIn(i) = '1' then
    return std_logic_vector(to_unsigned(i, outWidth));
 end if;
end loop;
return (others => '0');
end function encFunc;

begin

encOut <= encFunc(encIn);


end genEncoder_arch;
