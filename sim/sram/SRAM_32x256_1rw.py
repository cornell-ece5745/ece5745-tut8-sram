#=========================================================================
# 32 bits x 256 words SRAM model
#=========================================================================

from pymtl3                         import *
from pymtl3.passes.backends.verilog import *
from .BaseSRAM1rw                   import BaseSRAM1rw

class SRAM_32x256_1rw( BaseSRAM1rw ):

  # Make sure widths match the .v

  def construct( s ):
    super().construct( 32, 256 )
