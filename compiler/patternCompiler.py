from math import log2, ceil

# Global
## [(name, data width)]
signals = []
registers = set()

# General helperfunction
def ceilToPow2(number):
    return pow(2, ceil(log2(number)))

# Helperfunctions for naming
def regNameTemplate(signal,signal_level):
    return f"{signal}_Reg_{signal_level}"

def signalTemplate(signal, signal_level):
    # Hack
    signal_depth = list(filter(lambda x: signal in x[0], signals))[0]
    if signal_depth[1] == 1:
        return f"sig_{signal}_Reg"
    else:
        return f"sig_{signal}_Reg({signal_level-1})"


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
    signals.append(("decOut_internal",256*number_of_bytes))
    result =""
    for i in range(number_of_bytes):
        inverse = number_of_bytes - i
        result += f"""
decComp{i}: genDecoder
port map(decIn => inComp({8*(inverse)-1} downto {8*(inverse-1)}),
    clk => clk,
    decOut => decOut_internal({256*(inverse)-1} downto {256*(inverse-1)}));
"""
    return result

## Genera vhdl for a single "network" register. Handles creation of
## output signal and mapping in input signal (include edge case
## where the previous component is the decoder)
def genRegisters(signal_usages, number_of_bytes):
    result = ""
    for signal in signal_usages:
        signal_depth = len(signal_usages[signal])
        signal = str(ord(signal))
        if signal_depth > 1:
            signals.append((f"sig_{signal}_Reg",signal_depth-1))
        for offset in range(number_of_bytes):
            for signal_level in range(signal_depth):
                signal_level += offset
                if signal_level < number_of_bytes:
                    continue;


                temp_reg = regNameTemplate(signal, signal_level)
                temp_signal = signalTemplate(signal,signal_level)
                if temp_reg in registers:
                    continue
                registers.add(temp_reg)

                input_signal = f"decOut_internal({int(signal)+256*(number_of_bytes-signal_level%number_of_bytes)})"\
                        if signal_level < number_of_bytes*2 \
                        else signalTemplate(signal,signal_level-number_of_bytes)
                result += f"""
{temp_reg}: genRegister
  port map(d => {input_signal},
           clk => clk,
           q => {temp_signal});\n
"""
    return result

## Creates the AND logic to implement the pattern. This will get
## more complex when handling more the one byte per cycle as
## we then needs to find the pattern in all the offsets.
def genAndGate(patterns,number_of_bytes):
    result = ""
    for (pattern_number, pattern) in enumerate(patterns):
        pattern = pattern.replace("\n","")
        if number_of_bytes != 1:
            signals.append((f"{pattern_number}_and_signals",number_of_bytes))
        for offset in range(number_of_bytes):
            signals_to_and = []
            for (index,char) in enumerate(pattern.replace("\n","")[::-1]):
                index += offset
                if index < number_of_bytes:
                    signals_to_and.append(f"decOut_internal({ord(char) + 256*(number_of_bytes-index%number_of_bytes - 1)})")
                else:
                    char = str(ord(char))
                    signals_to_and.append(signalTemplate(char, index))


            partial_pattern = " AND ".join(signals_to_and)
            if number_of_bytes == 1:
                result += f"patternOut({pattern_number}) <= " +  partial_pattern + ";\n\n"
            else:
                result += f"{pattern_number}_and_signals({offset}) <= " + partial_pattern + ";\n"
        if number_of_bytes != 1:
            result += f"patternOut({pattern_number}) <= or_reduce({pattern_number}_and_signals);\n\n"
    return result

## Creates the initial block, mostly just defines.
def initBlock(name, number_of_patterns, number_of_bytes):
    output_type = f"std_logic_vector({ceil(log2(ceilToPow2(number_of_patterns)))-1} downto 0)" if number_of_patterns > 2 else "std_logic"
    result = f""" -- THIS FILE IS GENERATE MODIFY AT YOUR OWN RISK
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;

entity {name} is
  port(inComp: in std_logic_vector({8*number_of_bytes-1} downto 0);
       outComp: out {output_type};
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
\n
"""
    return result

## Creates the Endblock, include the logic for outComp and isValid.
## It also need to handles the problem with patternOut having
## undefined signals when the number of patterns aren't a power of
## 2.
def genEndBlock(name, number_of_patterns):
    number_of_patterns_pow2 = ceilToPow2(number_of_patterns)

    if number_of_patterns > 2:
        output_width = f"ceil(log2(number_of_patterns_pow2)"
    else:
        output_width = "1"
    result = f"""
encComp: genEncoder
generic map(inWidth => {number_of_patterns_pow2},
          outWidth => {output_width})
 port map(encIn => patternOut,
      encOut => outComp);
"""
    if number_of_patterns >= 2:
        result += "isValid <= or_reduce(patternOut);"
    else:
        result += "isValid <= patternOut;"


    result += f"end {name}_arch;"
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
        for (char_index,char) in enumerate(line.replace("\n","")[::-1]):
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

def main(patterns, name, number_of_bytes):
    result = ""
    # Gets data from file

    signal_usages = parsePatterns(patterns)


    # Must be run before genSignals as we only know what signals
    # we need after this stage is down
    signals.append(("patternOut", len(patterns)))
    reg_gen_result = genRegisters(signal_usages, number_of_bytes)
    dec_gen_result = genDecoder(number_of_bytes)
    and_gen_result = genAndGate(patterns, number_of_bytes)

    result += initBlock(name, len(patterns), number_of_bytes)
    result += genSignals()
    result += "begin\n"
    result += dec_gen_result
    result += reg_gen_result
    result += and_gen_result
    result += genEndBlock(name, len(patterns))
    print(result)

    with open(f"{name}.vhdl","w") as target_file:
        target_file.write(result)
