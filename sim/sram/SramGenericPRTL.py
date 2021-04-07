#=========================================================================
# Generic model of the SRAM
#=========================================================================
# This is meant to be instantiated within a carefully named outer module
# so the outer module corresponds to an SRAM generated with the
# OpenRAM memory compiler.

from pymtl3 import *

class SramGenericPRTL( Component ):

  def construct( s, data_nbits=32, num_entries=256 ):

    addr_width = clog2( num_entries )      # address width
    nbytes     = int( data_nbits + 7 ) // 8 # $ceil(data_nbits/8)

    # port names set to match the ARM memory compiler

    # clock (in PyMTL simulation it uses implict .clk port when
    # translated to Verilog, actual clock ports should be CE1

    s.clk0  = InPort ()                      # clk
    s.web0  = InPort ()                      # bar( write en )
    s.csb0  = InPort ()                      # bar( whole SRAM en )
    s.addr0 = InPort ( addr_width )          # address
    s.din0  = InPort ( data_nbits )          # write data
    s.dout0 = OutPort( data_nbits )          # read data

    # memory array

    s.ram = [ Wire( data_nbits ) for _ in range( num_entries ) ]

    # read path

    @update_ff
    def read_logic():
      if ~s.csb0 & s.web0:
        s.dout0 <<= s.ram[ s.addr0 ]
      else:
        s.dout0 <<= 0

    # write path

    @update_ff
    def write_logic():
      if ~s.csb0 & ~s.web0:
        s.ram[s.addr0] <<= s.din0
