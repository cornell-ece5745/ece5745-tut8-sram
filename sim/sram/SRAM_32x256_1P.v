//========================================================================
// 32 bits x 256 words SRAM
//========================================================================

`ifndef SRAM_32x256_1P
`define SRAM_32x256_1P

`include "sram/SramGenericVRTL.v"

module SRAM_32x256_1P
(
  input  logic        CE1,
  input  logic        WEB1,
  input  logic        OEB1,
  input  logic        CSB1,
  input  logic [7:0]  A1,
  input  logic [31:0] I1,
  output logic [31:0] O1,
  input  logic [3:0]  WBM1
);

  `ifndef SYNTHESIS

  sram_SramGenericVRTL
  #(
    .p_data_nbits  (32),
    .p_num_entries (256)
  )
  sram_generic
  (
    .CE1  (CE1),
    .A1   (A1),
    .WEB1 (WEB1),
    .WBM1 (WBM1),
    .OEB1 (OEB1),
    .CSB1 (CSB1),
    .I1   (I1),
    .O1   (O1)
  );

  `endif /* SYNTHESIS */

endmodule

`endif /* SRAM_32x256_1P */

