#=========================================================================
# Choose PyMTL or Verilog version
# =========================================================================
# Set this variable to 'pymtl' if you are using PyMTL for your RTL design
# or set this variable to 'verilog' if you are using Verilog for your RTL
# design.

rtl_language = 'verilog'

#-------------------------------------------------------------------------
# Do not edit below this line
#-------------------------------------------------------------------------

# This is the PyMTL wrapper for the corresponding Verilog RTL model.

from pymtl3                         import *
from pymtl3.stdlib                  import stream
from pymtl3.passes.backends.verilog import *
from pymtl3.stdlib.mem              import mk_mem_msg, MemMsgType

class SramMinionVRTL( VerilogPlaceholder, Component ):

  # Constructor

  def construct( s ):

    # If translated into Verilog, we use the explicit name

    s.set_metadata( VerilogTranslationPass.explicit_module_name, 'SramMinionRTL' )

    # Default memory message has 8 bits opaque field and 32 bits address

    MemReqType, MemRespType = mk_mem_msg( 8, 32, 32 )

    # Interface

    s.minion = stream.ifcs.MinionIfcRTL( MemReqType, MemRespType )

# See if the course staff want to force testing a specific RTL language
# for their own testing.

import sys
if hasattr( sys, '_called_from_test' ):
  if sys._pymtl_rtl_override:
    rtl_language = sys._pymtl_rtl_override

# Import the appropriate version based on the rtl_language variable

if rtl_language == 'pymtl':
  from .SramMinionPRTL import SramMinionPRTL as SramMinionRTL
elif rtl_language == 'verilog':
  SramMinionRTL = SramMinionVRTL
else:
  raise Exception("Invalid RTL language!")
