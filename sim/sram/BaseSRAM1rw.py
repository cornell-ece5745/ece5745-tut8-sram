#=========================================================================
# 32 bits x 256 words SRAM model
#=========================================================================

from pymtl3                         import *
from pymtl3.passes.backends.verilog import *
from .SramGenericPRTL               import SramGenericPRTL

class BaseSRAM1rw( Component ):

  # Make sure widths match the .v

  def construct( s, data_nbits, num_entries ):

    # clock (in PyMTL simulation it uses implict .clk port when
    # translated to Verilog, actual clock ports should be CE1

    s.clk0  = InPort () # clk
    s.web0  = InPort () # bar( write en )
    s.csb0  = InPort () # bar( whole SRAM en )
    s.addr0 = InPort ( clog2(num_entries) ) # address
    s.din0  = InPort ( data_nbits ) # write data
    s.dout0 = OutPort( data_nbits ) # read data

    # This is a blackbox that shouldn't be translated

    s.set_metadata( VerilogTranslationPass.no_synthesis, True )
    s.set_metadata( VerilogTranslationPass.no_synthesis_no_clk, True )
    s.set_metadata( VerilogTranslationPass.no_synthesis_no_reset, True )
    s.set_metadata( VerilogTranslationPass.explicit_module_name, f'SRAM_{data_nbits}x{num_entries}_1rw' )

    # instantiate a generic sram inside

    s.sram_generic = m = SramGenericPRTL( data_nbits, num_entries )
    m.clk0  //= s.clk0
    m.web0  //= s.web0
    m.csb0  //= s.csb0
    m.addr0 //= s.addr0
    m.din0  //= s.din0
    m.dout0 //= s.dout0

  def line_trace( s ):
    return s.sram_generic.line_trace()
