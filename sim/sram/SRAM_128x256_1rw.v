//------------------------------------------------------------------------
// 128 bits x 256 words SRAM
//------------------------------------------------------------------------

`ifndef SRAM_128x256_1rw
`define SRAM_128x256_1rw

`include "sram/SramGenericVRTL.v"

`ifndef SYNTHESIS

module SRAM_128x256_1rw
(
  input  logic         clk0,
  input  logic         web0,
  input  logic         csb0,
  input  logic [7:0]   addr0,
  input  logic [127:0] din0,
  output logic [127:0] dout0
);

  sram_SramGenericVRTL
  #(
    .p_data_nbits  (128),
    .p_num_entries (256)
  )
  sram_generic
  (
    .clk0  (clk0),
    .addr0 (addr0),
    .web0  (web0),
    .csb0  (csb0),
    .din0  (din0),
    .dout0 (dout0)
  );

endmodule

`endif /* SYNTHESIS */

`endif /* SRAM_128x256_1rw */
