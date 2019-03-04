#=========================================================================
# Choose PyMTL or Verilog version
#=========================================================================
# Set this variable to 'pymtl' if you are using PyMTL for your RTL design
# (i.e., your design is in IntMultBasePRTL) or set this variable to
# 'verilog' if you are using Verilog for your RTL design (i.e., your
# design is in IntMulBaseVRTL).

rtl_language = 'pymtl'

#-------------------------------------------------------------------------
# Do not edit below this line
#-------------------------------------------------------------------------

# This is the PyMTL wrapper for the corresponding Verilog RTL model.

from pymtl      import *
from pclib.ifcs import InValRdyBundle, OutValRdyBundle
from pclib.ifcs import MemReqMsg, MemRespMsg

class SramValRdyVRTL( VerilogModel ):

  vprefix    = "sram"
  vlinetrace = True

  def __init__( s ):

    # Explicit module name

    s.explicit_modulename = "SramValRdyRTL"

    # Interface

    s.memreq  = InValRdyBundle ( MemReqMsg ( 8, 32, 64 ) )
    s.memresp = OutValRdyBundle( MemRespMsg( 8,     64 ) )

    # connect to Verilog module

    s.set_ports({
      'clk'           : s.clk,
      'reset'         : s.reset,

      'memreq_msg'    : s.memreq.msg,
      'memreq_val'    : s.memreq.val,
      'memreq_rdy'    : s.memreq.rdy,

      'memresp_msg'   : s.memresp.msg,
      'memresp_val'   : s.memresp.val,
      'memresp_rdy'   : s.memresp.rdy,
    })


# See if the course staff want to force testing a specific RTL language
# for their own testing.

import sys
if hasattr( sys, '_called_from_test' ):
  if sys._pymtl_rtl_override:
    rtl_language = sys._pymtl_rtl_override

# Import the appropriate version based on the rtl_language variable

if   rtl_language == 'pymtl':
  from SramValRdyPRTL import SramValRdyPRTL as SramValRdyRTL
elif rtl_language == 'verilog':
  SramValRdyRTL = SramValRdyVRTL
else:
  raise Exception("Invalid RTL language!")

