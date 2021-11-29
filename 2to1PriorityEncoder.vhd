library ieee;
use ieee.std_logic_1164.all;


entity Prio2to1 is
        generic(inWidth: integer);
	port(Load_en: in std_logic;
             clk: in std_logic;
             Load_en_out: out std_logic_vector(1 downto 0);
             Reg1In: in std_logic_vector(inWidth downto 0); -- bit 0 is valid bit
	     Reg2In: in std_logic_vector(inWidth downto 0);
             EncOut: out std_logic_vector(inWidth+1 downto 0));
end entity Prio2to1;


architecture Prio2to1_arch of Prio2to1 is

component genRegister is
 generic(n: integer := 1);
 port(d: in std_logic_vector(n-1 downto 0);
      q: out std_logic_vector(n-1 downto 0);
      clk: in std_logic);
end component genRegister;

signal Reg1Internal: std_logic_vector(inWidth downto 0);
signal Reg2Internal: std_logic_vector(inWidth downto 0);
signal loadenout: std_logic_vector(1 downto 0);
signal RegOutInternal: std_logic_vector(inWidth+1 downto 0);
signal RegOutInInternal: std_logic_vector(inWidth+1 downto 0);
signal load_en_clk: std_logic_vector(2 downto 0);



begin

Register1In: genRegister
  generic map(n => inWidth+1)
  port map(clk => load_en_clk(0) ,
           d => Reg1In,
           q => Reg1Internal);

Register2In: genRegister
  generic map(n => inWidth+1)
  port map(clk => load_en_clk(1),
           d => Reg2In,
           q => Reg2Internal);

RegisterOut: genRegister
  generic map(n => inWidth+2)
  port map(clk => load_en_clk(2),
           d => RegOutInInternal,
           q => RegOutInternal);

with Reg1Internal(0) select
        RegOutInInternal(inWidth downto 1) <= Reg1Internal(inWidth downto 1) when '1',
                       Reg2Internal(inWidth downto 1) when others;

RegOutInInternal(0) <= Reg1Internal(0) AND Reg2Internal(0);
RegOutInInternal(inWidth+1) <= NOT Reg1Internal(0);

loadenout(0) <= RegOutInInternal(inWidth+1)OR (NOT RegOutInternal(inWidth+1) AND RegoutInternal(0));
loadenout(1) <= NOT Reg1Internal(0)OR (RegOutInternal(inWidth+1) AND RegoutInternal(0));

load_en_clk(0) <= clk AND loadenout(0);
load_en_clk(1) <= clk AND loadenout(1);
load_en_clk(2) <= clk AND Load_en;

EncOut <= RegOutInternal;
Load_en_out <= loadenout;
end Prio2to1_arch;