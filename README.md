# VHDL pattern matcher generator
This project take in a list of patterns and generates the VHDL code for handle n bytes per cycle. 

## Design
The design generate is a version of the DCAM design propused in [this paper](https://ieeexplore.ieee.org/abstract/document/1364636?casa_token=aulTs1nUtxcAAAAA:rhx_o-sftSA6n3SJofUut30uNDR5ZJP5MZvp5e9JpCJsfxkkuohiCIBAkudZHM-r9vO_6w-4).

The general idé with this project to design then compontents in VHDL to get effectent compontents which is then mapped in python to create the complete design.

## Usage
Create a file with all pattern to match, one pattern per line, eariler pattern get priortiy on the output incase of a collision. Then run the following command:
```
python3 main.py <path to pattern file> <name of component to generate> <number of bytes per cycle>
```
This will create a new file in the current directory with the name \<name of component to generate>.vhdl.

To include this compontent into your design use this block
```
entity <name of component to generate> is
  port(inComp: in std_logic_vector((8*<number of bytes per cycle> -1 ) downto 0);
       outComp: out std_logic_vector( {ceil(log2(<number of patterns>))} downto 0);
       clk: in std_logic;
       isValid: out std_logic);
end <name of component to generate>;
```
Note that yout have to replace all \<> element and resolve the {} block.

## Known Issues/Improvements
We about three issue of that if fixed would improve performance:
* The decoder and encoder are not pipelined which if done would allow for higher frequerancy.  We recommand the encoder design found in [this paper](https://www.researchgate.net/publication/221046152_Packet_pre-filtering_for_network_intrusion_detection), as it allows but delay lower priority pattern in case of collision allowing those patterns to be displayed afterwards and the likelyhood of having detection each cycle is relavant low. Addionally this design handle the valid signal, which simplify the overall design.
* The fan-out is too high for some character at some delays, this make the design slower. The solution here is to update the logic for constructing the registers to build a tree backwords. As we know how much fan out we have at each delay for each character, we can grow then number of register able eariler so we enough signals at the given layer. Example our card has a maxium fanout 4, and we need a fanout of 9 at level 4, then we would at level 3 create 2 extra registers. So that 8 of the level 4 signal comes from 2 register at level 3 and the last signal at level 4 is connect to the last register.
