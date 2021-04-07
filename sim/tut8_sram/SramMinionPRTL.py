#========================================================================
# SRAM Minion Wrapper
#========================================================================
# This is a simple latency-insensitive minion wrapper around an SRAM that
# is supposed to be generated using a memory compiler. We add a skid
# buffer in order to support the latency-insensitive val/rdy protocol. A
# correct solution will have two or more elements of buffering in the
# memory response queue _and_ stall M0 if there are less than two free
# elements in the queue. Thus in the worst case, if M2 stalls we have
# room for two messages in the response queue: the message currently in
# M1 and the message currently in M0. Here is the updated design:
#
#         .------.          .------.
#         |      |          | 2elm |
#   M0 -> | sram | -> M1 -> | bypq | -> M2
#         |      |       .- |      |
#         '^-----'       |  '^-----'
#                        |
#  rdy <-(if count == 0)-'
#
# Here is the updated pipeline diagram.
#
#  cycle : 0  1  2  3  4  5
#  msg a : M0 M2
#  msg b :    M0 M2
#  msg c :       M0 M1 M2 M2 M2
#  msg d :          M0 q  q  q   # msg c is in skid buffer
#  msg e :             M0 M0 M0
#
#  cycle M0 M1 [q ] M2
#     0: a
#     1: b  a       a  # a is flows through bypass queue
#     2: c  b       b  # b is flows through bypass queue
#     3: d  c          # M2 is stalled, c will need to go into bypq
#     4: e  d    c     #
#     5: e      dc     # d skids behind c into the bypq
#
# Note, with a pipe queue you still need two elements of buffering.
# There could be a message in the response queue when M2 stalls and then
# you still don't have anywhere to put the message currently in M1.

from pymtl3                  import *
from pymtl3.passes.backends.verilog import *
from pymtl3.stdlib           import stream
from pymtl3.stdlib.mem       import mk_mem_msg, MemMsgType
from pymtl3.stdlib.basic_rtl import Reg, RegRst

from sram import SramRTL

class SramMinionPRTL( Component ):

  def construct( s ):
    s.set_metadata( VerilogTranslationPass.explicit_module_name, "SramMinionRTL" )

    # size is fixed as 32x128

    num_bits   = 32
    num_words  = 128
    addr_width = clog2( num_words )
    addr_start = clog2( num_bits / 8 )
    addr_end   = addr_start + addr_width

    BitsAddr   = mk_bits( addr_width )
    BitsData   = mk_bits( num_bits )

    # Default memory message has 8 bits opaque field and 32 bits address.

    MemReqType, MemRespType = mk_mem_msg( 8, 32, num_bits )

    # Interface

    s.minion = stream.ifcs.MinionIfcRTL( MemReqType, MemRespType )

    #---------------------------------------------------------------------
    # M0 stage
    #---------------------------------------------------------------------

    s.sram_addr_M0    = Wire( BitsAddr )
    s.sram_wen_M0     = Wire( Bits1    )
    s.sram_en_M0      = Wire( Bits1    )
    s.sram_wdata_M0   = Wire( BitsData )

    # translation work around
    MEM_MSG_TYPE_WRITE = b4(MemMsgType.WRITE)

    @update
    def comb_M0():
      s.sram_addr_M0  @= s.minion.req.msg.addr[addr_start:addr_end]
      s.sram_wen_M0   @= s.minion.req.val & ( s.minion.req.msg.type_ == MEM_MSG_TYPE_WRITE )
      s.sram_en_M0    @= s.minion.req.val & s.minion.req.rdy
      s.sram_wdata_M0 @= s.minion.req.msg.data

    # SRAM

    s.sram = m = SramRTL( num_bits, num_words )
    m.port0_idx   //= s.sram_addr_M0
    m.port0_type  //= s.sram_wen_M0
    m.port0_val   //= s.sram_en_M0
    m.port0_wdata //= s.sram_wdata_M0

    #---------------------------------------------------------------------
    # M1 stage
    #---------------------------------------------------------------------

    # Pipeline registers

    s.memreq_val_reg_M1 = m = RegRst( Bits1 )
    m.in_ //= s.sram_en_M0

    s.memreq_msg_reg_M1 = m = Reg( MemReqType )
    m.in_ //= s.minion.req.msg

    # Create the memory response message with data from SRAM if read

    s.memresp_msg_M1 = Wire( MemRespType )

    # translation work around
    MEM_MSG_TYPE_READ = b4(MemMsgType.READ)

    @update
    def comb_M1a():

      s.memresp_msg_M1.type_  @= s.memreq_msg_reg_M1.out.type_
      s.memresp_msg_M1.opaque @= s.memreq_msg_reg_M1.out.opaque
      s.memresp_msg_M1.test   @= 0
      s.memresp_msg_M1.len    @= s.memreq_msg_reg_M1.out.len

      if s.memreq_msg_reg_M1.out.type_ == MEM_MSG_TYPE_READ:
        s.memresp_msg_M1.data @= s.sram.port0_rdata
      else:
        s.memresp_msg_M1.data @= 0

    # Bypass queue

    s.memresp_q = stream.BypassQueueRTL( MemRespType, num_entries=2 )

    @update
    def comb_M1b():

      # enqueue messages into the bypass queue

      s.memresp_q.recv.val @= s.memreq_val_reg_M1.out
      s.memresp_q.recv.msg @= s.memresp_msg_M1

      # dequeue messages from the bypass queue
      s.minion.resp.val    @= s.memresp_q.send.val
      s.memresp_q.send.rdy @= s.minion.resp.rdy
      s.minion.resp.msg    @= s.memresp_q.send.msg

      # stop the minion interface if not enough skid buffering

      s.minion.req.rdy     @= s.memresp_q.count == 0

  def line_trace( s ):
    return '*' if s.memreq_val_reg_M1.out else ' '
