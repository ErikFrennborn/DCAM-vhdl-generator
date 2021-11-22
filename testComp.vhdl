library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;

entity testComp is
  port(inComp: in std_logic_vector(7 downto 0);
       outComp: out std_logic_vector(1 downto 0);
       clk: in std_logic;
       isValid: out std_logic);

end testComp;

architecture testComp_arch of testComp is

component genDecoder is
	generic(outWidth: integer := 256;
                 inWidth: integer := 8);
        port(decIn: in std_logic_vector(inWidth-1 downto 0);
             clk: in std_logic;
             decOut: out std_logic_vector(outWidth-1 downto 0));
end component genDecoder;

component genEncoder is
  generic(inWidth: integer := 4;
          outWidth: integer := 2);
 port(encIn: in std_logic_vector(inWidth-1 downto 0);
      encOut: out std_logic_vector(outWidth-1 downto 0));

end component genEncoder;

component genRegister is
 port(d: in std_logic;
      q: out std_logic;
      clk: in std_logic);
end component genRegister;


signal decOut_internal: std_logic_vector(255 downto 0);
signal AReg_internal: std_logic;
signal BReg_internal: std_logic;
signal CReg_internal: std_logic;
signal patternOut: std_logic_vector(3 downto 0);

begin



decComp: genDecoder
  port map(decIn => inComp,
           clk => clk,
           decOut => decOut_internal);

AReg: genRegister
  port map(d => decOut_internal(65),
           clk => clk,
           q => AReg_internal);

BReg: genRegister
  port map(d => decOut_internal(66),
           clk => clk,
           q => BReg_internal);

CReg: genRegister
  port map(d => decOut_internal(67),
           clk => clk,
           q => CReg_internal);



encComp: genEncoder
generic map(inWidth => 4,
          outWidth => 2)
 port map(encIn => patternOut,
      encOut => outComp);

patternOut(3) <= '0'; -- Alla signal i vector måste vara definerade för att or_reduce ska vara valid.
patternOut(2) <= CReg_internal AND decOut_internal(65);
patternOut(1) <= BReg_internal AND decOut_internal(66); --Generalisera detta
patternOut(0) <= AReg_internal AND decOut_internal(66);

isValid <= or_reduce(patternOut);


end testComp_arch;

