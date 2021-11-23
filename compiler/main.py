#!/bin/python3.10

# THIS SCRIPT USES python3.10 FEATURES!

# usage: python3.10 main.py <path to pattern file>

from math import log2, ceil
import sys

# Global
## [(name, data width)]
signals = []

# General helperfunction
def ceilToPow2(number):
    return pow(2, ceil(log2(number)))

# Helperfunctions for naming
def regNameTemplate(signal,signal_level):
    return f"{signal}_Reg_{signal_level}"

def signalTemplate(signal, signal_level):
    return f"sig_{regNameTemplate(signal,signal_level)}"


# Functions for generating submodules
## Uses global signals and creates vhdl need to define them
def genSignals():
    result = ""
    for (signal,width) in signals:
        result += f"signal {signal}: "
        if width == 1:
            result += "std_logic;\n"
        else:
            result += f"std_logic_vector({width-1} downto 0);\n"
    return result


## Handles logic around the decoder(s), will get more complex when
## handling more the one byte per cycle
def genDecoder(number_of_bytes):
    if number_of_bytes == 1:
        signals.append(("decOut_internal",256))
        result ="""
    decComp: genDecoder
    port map(decIn => inComp,
            clk => clk,
            decOut => decOut_internal);
"""
    else:
        raise NotImplemented
    return result

## Genera vhdl for a single "network" register. Handles creation of
## output signal and mapping in input signal (include edge case
## where the previous component is the decoder)
def genRegisters(signal_usages):
    result = ""
    for signal in signal_usages:
        signal_depth = len(signal_usages[signal])
        for signal_level in range(signal_depth):
            if signal_level == 0:
                continue;

            temp_reg = regNameTemplate(signal, signal_level)
            temp_signal = signalTemplate(signal,signal_level)
            signals.append((temp_signal,1))

            input_signal = f"decOut_internal({ord(signal)})"\
                    if signal_level == 1\
                    else signalTemplate(signal,signal_level-1)
            result += f"""
{temp_reg}: genRegister
  port map(d => {input_signal},
           clk => clk,
           q => {temp_signal});
"""
    return result

## Creates the AND logic to implement the pattern. This will get
## more complex when handling more the one byte per cycle as
## we then needs to find the pattern in all the offsets.
def genAndGate(patterns):
    result = ""
    for (pattern_number, pattern) in enumerate(patterns):
        signals_to_and = []
        for (index,char) in enumerate(pattern.strip()[::-1]):
            if index == 0:
                signals_to_and.append(f"decOut_internal({ord(char)})")
            else:
                signals_to_and.append(signalTemplate(char, index))

        result += f"patternOut({pattern_number}) <= " + " AND ".join(signals_to_and) + "\n"
    return result

## Creates the initial block, mostly just defines.
def initBlock(name, number_of_patterns):
    result = f"""
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;

entity {name} is
  port(inComp: in std_logic_vector(7 downto 0);
       outComp: out std_logic_vector({ceilToPow2(number_of_patterns)-1} downto 0);
       clk: in std_logic;
       isValid: out std_logic);

end {name};

architecture {name}_arch of {name} is


-- define components to be used
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
"""
    return result

## Creates the Endblock, include the logic for outComp and isValid.
## It also need to handles the problem with patternOut having
## undefined signals when the number of patterns aren't a power of
## 2.
def genEndBlock(name, number_of_patterns):
    number_of_patterns_pow2 = ceilToPow2(number_of_patterns)

    #  Must be done other we have unassigned signal and vhdl breaks
    match number_of_patterns_pow2 - number_of_patterns:
        case 0:
            patternOut_workaround = ""
        case 1:
            patternOut_workaround = f"patternOut({number_of_patterns}) <= '1';"
        case _:
            patternOut_workaround = f'patternOut({number_of_patterns_pow2 -1} downto {number_of_patterns -1}) <= "00";'
    result = f"""
{patternOut_workaround}
encComp: genEncoder
generic map(inWidth => {number_of_patterns_pow2},
          outWidth => {ceil(log2(number_of_patterns_pow2))})
 port map(encIn => patternOut,
      encOut => outComp);


isValid <= or_reduce(patternOut);


end {name}_arch;"""
    return result


# Function for parsing the patterns into a dict of key: char & value:
# with pattern has which char at a specific offset. This can be made
# more efficient however but no need this is run once at compile time
# and it is fast enough.
def parsePatterns(patterns):
    char_usaged = {}

    max_length = max(map(lambda x: len(x),patterns))

    # Find with char is used at each index
    for (line_index,line) in enumerate(patterns):
        for (char_index,char) in enumerate(line.strip()[::-1]):
            if char == '\n':
                continue
            if not char in char_usaged:
                # Creates list of the longest pattern, inefficient
                # by quick enough
                char_usaged[char] = [[] for _ in range(max_length)]
            char_usaged[char][char_index].append(line_index)

    # Strip unused indexes
    for key in char_usaged:
        temp = []
        result = []
        for index in char_usaged[key]:
            temp.append(index)
            if len(index) != 0:
                result += temp
                temp = []

        char_usaged[key] = result


    return char_usaged


# TODO: Delay the short patterns so that all the patterns have the
# same latency so it sync up with the data.
def main(argv):
    patterns=[]
    result = ""

    # Gets data from file
    with open(argv[0]) as file:
        patterns = list(file)
    signal_usages = parsePatterns(patterns)

    # Must be run before genSignals as we only know what signals
    # we need after this stage is down
    signals.append(("patternOut", ceilToPow2(len(patterns))))
    reg_gen_result =  genRegisters(signal_usages)
    dec_gen_result = genDecoder(1)

    result += initBlock("test_comp", len(patterns))
    result += genSignals()
    result += "begin"
    result += dec_gen_result
    result += reg_gen_result
    result += genAndGate(patterns)
    result += genEndBlock("test_comp", len(patterns))

    print(result)
if __name__ == "__main__":
    main(sys.argv[1:])