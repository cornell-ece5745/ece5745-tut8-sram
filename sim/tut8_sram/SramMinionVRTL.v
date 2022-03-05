//========================================================================
// SRAM Wrapper: 32 bits/word, 128 words
//========================================================================
// This is a simple val/rdy wrapper around an SRAM that is supposed to be
// generated using the CACTI-based memory compiler. Note that the SRAM is
// synchronous and cannot be stalled. This complicates ensuring that our
// val/rdy logic does not result in dropping messages. A naive solution
// might directly connect the memresp_queue_enq_rdy for a single entry
// bypass queue to the memreq_rdy signal like this:
//
//         .------.          .------.
//         |      |          | 1elm |
//   M0 -> | sram | -> M1 -> | bypq | -> M2
//         |      |       .- |      |
//         '^-----'       |  '^-----'
//                        |
//  rdy <-----------------'
//
// Since we cannot stall the SRAM, the above solution will not work.
// Consider the following pipeline diagram:
//
//  cycle : 0  1  2  3  4  5
//  msg a : M0 M2
//  msg b :    M0 M2
//  msg c :       M0 M1 M2 M2 M2
//  msg d :          M0 M1 M1 M1  # but wait, we cannot stall in M1!
//  msg e :             M0 M0 M0
//
//  cycle M0 M1 [q] M2
//     0: a
//     1: b  a      a  # a is flows through bypass queue
//     2: c  b      b  # b is flows through bypass queue
//     3: d  c         # M2 is stalled, c will need to go into bypq
//     4: e  d   c     # q is full at beginning of cycle, enq_rdy = 0
//     5: e      c     # what happens to d?
//
// So on cycle 3, the response interface is stalled and as a consequence
// message c must be written in the memory response queue. On cycle 4,
// the response queue is full (enq_rdy = 0) so memreq_rdy = 0 and message
// e will stall in M0 (i.e., will stall waiting to be accepted by the
// SRAM wrapper). The critical question is what happens to message d? It
// _cannot_ stall in M1 because we cannot stall the SRAM. So basically we
// just drop it.
//
// This is a classic situation where whe need more skid buffering. A
// correct solution will have two or more elements of buffering in the
// memory response queue _and_ stall M0 if there are less than two free
// elements in the queue. Thus in the worst case, if M2 stalls we have
// room for two messages in the response queue: the message currently in
// M1 and the message currently in M0. Here is the updated design:
//
//         .------.          .------.
//         |      |          | 2elm |
//   M0 -> | sram | -> M1 -> | bypq | -> M2
//         |      |       .- |      |
//         '^-----'       |  '^-----'
//                        |
//  rdy <-(if nfree == 2)-'
//
// Here is the updated pipeline
// diagram.
//
//  cycle : 0  1  2  3  4  5
//  msg a : M0 M2
//  msg b :    M0 M2
//  msg c :       M0 M1 M2 M2 M2
//  msg d :          M0 q  q  q   # msg c is in skid buffer
//  msg e :             M0 M0 M0
//
//  cycle M0 M1 [q ] M2
//     0: a
//     1: b  a       a  # a is flows through bypass queue
//     2: c  b       b  # b is flows through bypass queue
//     3: d  c          # M2 is stalled, c will need to go into bypq
//     4: e  d    c     #
//     5: e      dc     # d skids behind c into the bypq
//
// Note, with a pipe queue you still need two elements of buffering.
// There could be a message in the response queue when M2 stalls and then
// you still don't have anywhere to put the message currently in M1.
//

`ifndef TUT8_SRAM_MINION_VRTL_V
`define TUT8_SRAM_MINION_VRTL_V

`include "vc/mem-msgs.v"
`include "vc/queues.v"
`include "vc/assert.v"
`include "vc/trace.v"

`include "sram/SramVRTL.v"

module tut8_sram_SramMinionVRTL
(
  input  logic         clk,
  input  logic         reset,

  // Memory request port interface

  input  logic         minion_req_val,
  output logic         minion_req_rdy,
  input  mem_req_4B_t  minion_req_msg,

  // Memory response port interface

  output logic         minion_resp_val,
  input  logic         minion_resp_rdy,
  output mem_resp_4B_t minion_resp_msg
);

  mem_resp_4B_t minion_resp_msg_raw; //4-state sim fix
  assign minion_resp_msg = minion_resp_msg_raw & {48{minion_resp_val}};

  //----------------------------------------------------------------------
  // Local parameters
  //----------------------------------------------------------------------

  // Shorthand for the message types

  localparam c_read  = `VC_MEM_REQ_MSG_TYPE_READ;
  localparam c_write = `VC_MEM_REQ_MSG_TYPE_WRITE;

  //----------------------------------------------------------------------
  // M0 Pipeline Stage
  //----------------------------------------------------------------------

  // Unpack the request message

  logic [2:0]   memreq_msg_type_M0;
  logic [7:0]   memreq_msg_opaque_M0;
  logic [31:0]  memreq_msg_addr_M0;
  logic [2:0]   memreq_msg_len_M0;
  logic [31:0]  memreq_msg_data_M0;

  assign memreq_msg_type_M0   = minion_req_msg.type_;
  assign memreq_msg_opaque_M0 = minion_req_msg.opaque;
  assign memreq_msg_addr_M0   = minion_req_msg.addr;
  assign memreq_msg_len_M0    = minion_req_msg.len;
  assign memreq_msg_data_M0   = minion_req_msg.data;

  logic memreq_val_M0;
  assign memreq_val_M0 = minion_req_val;

  logic memreq_go;
  assign memreq_go = minion_req_val && minion_req_rdy;

  // Setup signals for SRAM

  logic [6:0]  sram_addr_M0;
  logic        sram_wen_M0;
  logic        sram_oen_M0;
  logic        sram_en_M0;
  logic [31:0] sram_write_data_M0;
  logic [31:0] sram_read_data_M1;

  assign sram_addr_M0 = memreq_msg_addr_M0[8:2];
  assign sram_wen_M0  = memreq_val_M0 && (memreq_msg_type_M0 == c_write);
  assign sram_en_M0   = memreq_go;

  // Instantiate SRAM

  sram_SramVRTL#(32,128) sram
  (
    .clk         (clk),
    .reset       (reset),
    .port0_idx   (sram_addr_M0),
    .port0_type  (sram_wen_M0),
    .port0_val   (sram_en_M0),
    .port0_wdata (memreq_msg_data_M0),
    .port0_rdata (sram_read_data_M1)
  );

  //----------------------------------------------------------------------
  // M0/M1 Pipeline Registers
  //----------------------------------------------------------------------
  // Note that we do not stall these pipeline registers. This is because
  // we cannot really stall the SRAM, so we are instead using skid
  // buffering in the response queue.

  logic         memreq_val_M1;
  logic [2:0]   memreq_msg_type_M1;
  logic [7:0]   memreq_msg_opaque_M1;
  logic [31:0]  memreq_msg_addr_M1;
  logic [1:0]   memreq_msg_len_M1;

  always @( posedge clk ) begin
    if (reset)
      memreq_val_M1 <= 1'b0;
    else
      memreq_val_M1 <= memreq_go;

    memreq_msg_type_M1   <= memreq_msg_type_M0;
    memreq_msg_opaque_M1 <= memreq_msg_opaque_M0;
    memreq_msg_addr_M1   <= memreq_msg_addr_M0;
    memreq_msg_len_M1    <= memreq_msg_len_M0;

  end

  //----------------------------------------------------------------------
  // M1 Pipeline Stage
  //----------------------------------------------------------------------

  // Shift the read data

  logic [31:0] memresp_msg_data_M1;
  assign memresp_msg_data_M1 = sram_read_data_M1;

  // Pack the response message

  mem_resp_4B_t memresp_msg_M1;

  assign memresp_msg_M1.type_  = memreq_msg_type_M1;
  assign memresp_msg_M1.opaque = memreq_msg_opaque_M1;
  assign memresp_msg_M1.test   = 2'b0;
  assign memresp_msg_M1.len    = ( memreq_msg_type_M1 == 3'b1) ? 4'b0 : memreq_msg_len_M1;   
  assign memresp_msg_M1.data   = ( memreq_msg_type_M1 == 3'b1) ? 32'b0 : memresp_msg_data_M1; // Connect data to zero on write requests

  // Output bypass queue

  logic       memresp_queue_rdy;
  logic [1:0] memresp_queue_num_free_entries_M1;

  vc_Queue
  #(
    .p_type      (`VC_QUEUE_BYPASS),
    .p_msg_nbits ($bits(memresp_msg_M1)),
    .p_num_msgs  (2)
  )
  memresp_queue
  (
    .clk               (clk),
    .reset             (reset),
    .recv_val          (memreq_val_M1),
    .recv_rdy          (memresp_queue_rdy),
    .recv_msg          (memresp_msg_M1),
    .send_val          (minion_resp_val),
    .send_rdy          (minion_resp_rdy),
    .send_msg          (minion_resp_msg_raw),
    .num_free_entries (memresp_queue_num_free_entries_M1)
  );

  assign minion_req_rdy = (memresp_queue_num_free_entries_M1 >= 2);

  //----------------------------------------------------------------------
  // General assertions
  //----------------------------------------------------------------------

  // val/rdy signals should never be x's

  `ifndef SYNTHESIS
  always @( posedge clk ) begin
    if ( !reset ) begin
      `VC_ASSERT_NOT_X( minion_req_val  );
      `VC_ASSERT_NOT_X( minion_resp_rdy );
    end
  end
  `endif

  //----------------------------------------------------------------------
  // Line tracing
  //----------------------------------------------------------------------

  `ifndef SYNTHESIS

  vc_MemReqMsg4BTrace memreq_trace
  (
    .clk   (clk),
    .reset (reset),
    .val   (minion_req_val),
    .rdy   (minion_req_rdy),
    .msg   (minion_req_msg)
  );

  vc_MemRespMsg4BTrace memresp_trace
  (
    .clk   (clk),
    .reset (reset),
    .val   (minion_resp_val),
    .rdy   (minion_resp_rdy),
    .msg   (minion_resp_msg)
  );

  `VC_TRACE_BEGIN
  begin
    memreq_trace.line_trace( trace_str );
    vc_trace.append_str( trace_str, "()" );
    memresp_trace.line_trace( trace_str );
  end
  `VC_TRACE_END

  `endif

endmodule

`endif /* TUT8_SRAM_MINION_VRTL_V */

