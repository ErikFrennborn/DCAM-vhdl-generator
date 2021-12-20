from math import log, log2, ceil

# Global
## [(name, data width)]
signals = {}
registers = set()

# General helperfunction
def ceilToPow2(number):
    return pow(2, ceil(log2(number)))

# Helperfunctions for naming
def regNameTemplate(signal,signal_level):
    return f"Reg_{signal}_{signal_level}"

def signalTemplate(signal, signal_level):
    # Hack, slow pls fix
    return f"sig_{signal}_Reg({signal_level-1})"


# Functions for generating submodules
## Uses global signals and creates vhdl need to define them
def genSignals():
    result = ""
    for signal in signals:
        width = signals[signal]
        result += f"signal {signal}: std_logic_vector({width-1} downto 0);\n"
    return result


## Handles logic around the decoder(s), will get more complex when
## handling more the one byte per cycle
def genDecoder(number_of_bytes):
    signals["decOut_internal"] = 256*number_of_bytes
    result =""
    for i in range(number_of_bytes):
        inverse = number_of_bytes - i
        result += f"""
decComp{i}: genDecoder
  port map(decIn => inComp({8*(inverse)-1} downto {8*(inverse-1)}),
    clk => clk,
    decOut => decOut_internal({256*(i+1)-1} downto {256*i}));
"""
    return result

def getNeedWidthPerLevel(signal_usage, fanout):
    need_width = 1
    max_fanout_at_level = 1
    need_width_at_last_level = 0
    width_at_level = []
    for level in range(len(signal_usage))[::-1]:
        max_fanout_at_level *= fanout
        need_fanout_at_level = len(signal_usage[level]) + need_width_at_last_level
        if (need_fanout_at_level > fanout):
            need_width_at_last_level = ceil(need_fanout_at_level/fanout)

        width_at_level.append(need_fanout_at_level)
        print(level,need_fanout_at_level, max_fanout_at_level, need_width)

    return width_at_level

def getMaxWidth(signal_usage,fanout):
    widthest = 0
    for level in range(len(signal_usage)):
        width_at_level = getNeedWidthPerLevel(signal_usage, level, fanout)
        print(level, width_at_level)
        if widthest < width_at_level:
            widthest = width_at_level
    return widthest

## Genera vhdl for a single "network" register. Handles creation of
## output signal and mapping in input signal (include edge case
## where the previous component is the decoder)
def genRegisters(signal_usages, number_of_bytes):
    result = ""
    for signal in signal_usages:
        signal_depth = len(signal_usages[signal])
        signal = str(ord(signal))
        if signal_depth > 1:
            signals[f"sig_{signal}_Reg"]= signal_depth-1
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
                input_signal = f"decOut_internal({int(signal)+256*((number_of_bytes-signal_level)%number_of_bytes)})"\
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
            signals[f"sig_{pattern_number}_and_signals"] = number_of_bytes
        for offset in range(number_of_bytes):
            signals_to_and = [[]]
            for (index,char) in enumerate(pattern.replace("\n","")[::-1]):
                index += offset
                if index < number_of_bytes:
                    #  signals_to_and.append(f"decOut_internal({ord(char) + 256*((number_of_bytes-index)%number_of_bytes)})")
                    signals_to_and[0].append(f"decOut_internal({ord(char) + 256*(number_of_bytes-index%number_of_bytes - 1)})")
                else:
                    char = str(ord(char))
                    signals_to_and[0].append(signalTemplate(char, index))

            # pipelines and logic
            number_of_signals = len(signals_to_and[0])
            if number_of_signals == 1:
                result += f"patternOut({pattern_number}) <= {signals_to_and[0][0]};\n\n"
                continue

            NUMBER_OF_INPUTS_PER_LUTS = 6
            and_tree_depth = ceil(log(number_of_signals, NUMBER_OF_INPUTS_PER_LUTS))
            and_tree_width = ceil(number_of_signals/NUMBER_OF_INPUTS_PER_LUTS)
            signals[f"and_tree_{pattern_number}"] = and_tree_depth*and_tree_width
            signals[f"and_tree_{pattern_number}_internal"] = and_tree_depth*and_tree_width
            for and_level in range(and_tree_depth):
                signals_to_and.append([])
                for and_width in range(and_tree_width):
                    temp = []
                    for i in range(NUMBER_OF_INPUTS_PER_LUTS):
                        current_index = i + and_width*and_tree_width
                        if  current_index >= len(signals_to_and[and_level]):
                            break
                        temp.append(signals_to_and[and_level][current_index])
                    if len(temp) == 0:
                        break
                    in_signal = " AND ".join(temp)
                    intermediate_signal = f"and_tree_{pattern_number}_internal({and_tree_width*and_level+ and_width})"
                    out_signal = f"and_tree_{pattern_number}({and_tree_width*and_level+ and_width})"
                    result += f"""
{intermediate_signal} <= {in_signal};
and_reg_{pattern_number}_{and_level*and_tree_width+and_width}: genRegister
  port map(d => {intermediate_signal},
           clk => clk,
           q => {out_signal});\n
"""

                    signals_to_and[and_level+1].append(out_signal)

            partial_pattern = signals_to_and[-1:][0][0]
            if number_of_bytes == 1:
                result += f"patternOut({pattern_number}) <= " +  partial_pattern + ";\n\n"
            else:
                result += f"sig_{pattern_number}_and_signals({offset}) <= " + partial_pattern + ";\n"
        if number_of_bytes != 1:
            result += f"patternOut({pattern_number}) <= or_reduce(sig_{pattern_number}_and_signals);\n\n"
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

    #  Must be done other we have unassigned signal and vhdl breaks
    if (number_of_patterns_pow2 - number_of_patterns == 0):
        patternOut_workaround = ""
    else:
        patternOut_workaround = f"patternOut({number_of_patterns_pow2 -1} downto {number_of_patterns }) <= (others => '0');\n"

    if number_of_patterns > 2:
        output_width = f"{ceil(log2(number_of_patterns_pow2))}"
    else:
        output_width = "1"
    result = f"""
{patternOut_workaround}
encComp: genEncoder
generic map(inWidth => {number_of_patterns_pow2},
          outWidth => {output_width})
 port map(encIn => patternOut,
      encOut => outComp);
"""
    if number_of_patterns >= 2:
        result += f"isValid <= or_reduce(patternOut({number_of_patterns -1} downto 0));"
    else:
        result += "isValid <= patternOut;"


    result += f"\nend {name}_arch;"
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
    number_of_patterns = len(patterns)

    # Must be run before genSignals as we only know what signals
    # we need after this stage is down
    signals["patternOut"] = ceilToPow2(number_of_patterns)
    reg_gen_result = genRegisters(signal_usages, number_of_bytes)
    dec_gen_result = genDecoder(number_of_bytes)
    and_gen_result = genAndGate(patterns, number_of_bytes)

    result += initBlock(name, number_of_patterns, number_of_bytes)
    result += genSignals()
    result += "begin\n"
    result += dec_gen_result
    result += reg_gen_result
    result += and_gen_result
    result += genEndBlock(name, number_of_patterns)
    #  print(result)

    with open(f"{name}.vhdl","w") as target_file:
        target_file.write(result)
