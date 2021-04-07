#=========================================================================
# Choose PyMTL or Verilog version
#=========================================================================
# Set this variable to 'pymtl' if you are using PyMTL for your RTL design
# (i.e., your design is in IntMulAltPRTL) or set this variable to
# 'verilog' if you are using Verilog for your RTL design (i.e., your
# design is in IntMulAltVRTL).

rtl_language = 'pymtl'

#-------------------------------------------------------------------------
# Do not edit below this line
#-------------------------------------------------------------------------
# This is the PyMTL wrapper for the corresponding Verilog RTL model.

from pymtl3 import *
from pymtl3.passes.backends.verilog import *

class SramVRTL( VerilogPlaceholder, Component ):

  # Constructor

  def construct( s, data_nbits=32, num_entries=256, mask_size=0 ):

    addr_width = clog2( num_entries )      # address width
    nbytes     = int( data_nbits + 7 ) // 8 # $ceil(num_bits/8)

    # Interface

    s.port0_val   = InPort ()
    s.port0_type  = InPort ()
    s.port0_idx   = InPort ( addr_width )
    s.port0_wdata = InPort ( data_nbits   )
    s.port0_rdata = OutPort( data_nbits   )

    if mask_size > 0:
      s.port0_wben = InPort( mk_bits(mask_size) )

    # Verilog import setup

    from os import path
    s.set_metadata( VerilogPlaceholderPass.src_file, path.dirname(__file__) + '/SramVRTL.v' )
    s.set_metadata( VerilogPlaceholderPass.top_module, 'sram_SramVRTL' )
    s.set_metadata( VerilogPlaceholderPass.params, {
      'p_data_nbits'  : data_nbits,
      'p_num_entries' : num_entries,
    })

# See if the course staff want to force testing a specific RTL language
# for their own testing.

# import sys
# if hasattr( sys, '_called_from_test' ):
  # if sys._pymtl_rtl_override:
    # rtl_language = sys._pymtl_rtl_override

# Import the appropriate version based on the rtl_language variable

if rtl_language == 'pymtl':
  from .SramPRTL import SramPRTL as _cls
elif rtl_language == 'verilog':
  _cls = SramVRTL
else:
  raise Exception("Invalid RTL language!")

class SramRTL( _cls ):
  def construct( s, data_nbits=32, num_entries=256, mask_size=0 ):
    super().construct( data_nbits, num_entries, mask_size )

    # The translated Verilog must be xRTL.v instead of xPRTL.v
    s.set_metadata( VerilogTranslationPass.explicit_module_name,
                    f'sram_SramRTL_mask{mask_size}_{data_nbits}b_{num_entries}words' )
