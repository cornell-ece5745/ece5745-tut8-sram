
ECE 5745 Tutorial 8: SRAM Generators
==========================================================================

 - Author: Christopher Batten
 - Date: May 6, 2017

**Table of Contents**

 - Introduction
 - Synopsys Educational Memory Generator
 - CACTI Memory Generator
 - Using SRAMs in RTL Models
 - Manual ASIC Flow with SRAM Macros
 - Automated ASIC Flow with SRAM Macros

Introduction
--------------------------------------------------------------------------

Small memories can be easily synthesized using flip-flop or latch
standard cells, but synthesizing large memories can significantly impact
the area, energy, and timing of the overall design. ASIC designers often
use SRAM generators to "generate" arrays of memory bitcells and the
corresponding peripheral circuitry (e.g., address decoders, bitline
drivers, sense amps) which are combined into what is called an "SRAM
macro". These SRAM generators are parameterized to enable generating a
wide range of SRAM macros with different numbers of rows, columns, and
column muxes, as well as optional support for partial writes, built-in
self-test, and error correction. Similar to a standard-cell library, an
SRAM generator must generate not just layout but also all of the
necessary views to capture logical functionality, timing, geometry, and
power usage. These views can then by used by the ASIC tools to produce a
complete design which includes a mix of both standard cells and SRAM
macros.

The tutorial will first describe how to use both the Synopsys Educational
(SAED) memory generator to generate various views of an SRAM macro.
Unfortunately, the SAED memory generator can only produce smaller SRAM
macros which do not have support for partial writes. In ECE 5745, we need
to use much larger SRAM macros with partial writes, so we have created a
different memory generator based on the CACTI memory modeling tool. After
learning about both the SAED and CACTI memory generators, you will see
how to use an SRAM in an RTL model, how to generate the corresponding
SRAM macro, and then how to push a design which uses an SRAM macro
through the automated ASIC flow. This tutorial assumes you have already
completed the tutorials on Linux, Git, PyMTL, Verilog, the Synopsys ASIC
tools, and the automated ASIC flow.

The following diagram illustrates how the memory generator integrates
with the four primary tools covered in the previous tutorials. We run the
memory generator to generate various views which are then combined with
the standard cell views to create the complete library used in the ASIC
flow.

![](assets/fig/asic-flow-with-srams.png)

The first step is to source the setup script, clone this repository from
GitHub, and define an environment variable to keep track of the top
directory for the project.

```
 % source setup-ece5745.sh
 % mkdir $HOME/ece5745
 % cd $HOME/ece5745
 % git clone git@github.com:cornell-ece5745/ece5745-tut8-sram
 % cd ece5745-tut8-sram
 % TOPDIR=$PWD
```

Synopsys Educational Memory Generator
--------------------------------------------------------------------------

Just as with standard-cell libraries, acquiring real SRAM generators is a
complex and potentially expensive process. It requires gaining access to
a specific fabrication technology, negotiating with a company which makes
the SRAM generator, and usually signing multiple non-disclosure
agreements. The Synopsys Educational (SAED) memory generator is based on
the same "fake" 90nm technology that we are using for the Synopsys
Educational standard-cell library. The "fake" technology, standard-cell
library, and SRAM generator were all specifically designed by Synopsys
for teaching, and the technology is representative enough to provide
reasonable area, energy, and timing estimates for our purposes. In this
section, we will take a look at how to use the SAED memory generator to
generate various views of an SRAM macro.

A SRAM generator takes as input a configuration file which specifies the
various parameters for the desired SRAM macro. You can see an example
configuration file for the SAED memory generator here:

```
 % cd $TOPDIR/asic/saed-mc
 % more SRAM_64x64_1P.cfg

 instance_name=SRAM_64x64_1P
 work_dir=SRAM_64x64_1P

 mem_type=single_90 # specify technology and number of ports
 word_count=64      # total size of SRAM in bits
 word_bits=64       #  will be word_cout * word_bits

 do_spice=1         # Generate SPICE netlist
 do_gds=1           # Generate GDS layout
 do_logic=1         # Generate Verilog model
 do_lib=1           # Generate Liberty view
 do_lef=1           # Generate LEF view
```

In this example, we are generating a single-ported SRAM which has 64 rows
and 64 bits per row for a total capacity of 4096 bits or 512B. This size
is probably near the cross-over point where you might transition from
using synthesized memories to SRAM macros. You can see that we will be
generating many different views of the SRAM macro including: schematics,
layout, a Verilog behavioral model, a `.lib` file with the abstract
logical, timing, power view, and a `.lef` file with the physical view.
These views can then be used by the ASIC tools.

You can use the following commands to run the SAED memory generator.

```
 % cd $TOPDIR/asic/saed-mc
 % saed_mc SRAM_64x64_1P.cfg
```

It will take 5-10 minutes to generate the SRAM macro. Also note that the
SAED memory generator relies on the Synopsys Galaxy Custom Compiler (CC)
tool, and for some strange reason the tool opens up the GUI for Synopsys
Galaxy CC. You just have to wait for it to finish.

You can find out more information about the SAED memory generator in the
user manual which is located here:

```
 $BARE_PKGS_GLOBAL_PREFIX/saed-mc/doc
```

The following excerpt from the user manual illustrates the
microarchitecture used in the single-port SRAM macro. The functionality
of the pins are as follows:

 - `CE`: clock
 - `WEB`: write enable (active low)
 - `OEB`: output enable (active low)
 - `CSB`: whole SRAM enable (active low)
 - `A`: address
 - `I`: write data
 - `O`: read data

Notice that even though there are separate read and write data pins,
there is only one address and thus this SRAM macro only supports
executing a single transaction at a time.

![](assets/fig/saed-sram-uarch.png)

The following excerpt from the user manual show the timing diagram for a
read transaction.

![](assets/fig/saed-sram-timing-read.png)

The `CE` pin is used as the clock for the SRAM. In order to execute any
kind of transaction in the SRAM, we need to set the `CSB` pin low (note
that `CSB` is active low). Since this is a read transaction, the `WEB`
pin is set high (note that `WEB` is active low) and the `A` pins are set
to the row address. Note that this is a _row_ address not a _byte_
address. From the block diagram, we can see that the address is decoded
and used to select the desired row in the RAM array. After the rising
edge of the `CE` pin, the read data is driven from the RAM array through
the data select logic and I/O buffering to the `O` pins. Since we set the
address _before_ the rising edge and the data is valid _after_ the rising
edge, this is a _synchronous_ read SRAM. Compare this to a register file
which often provides a _combinational_ read where the address is set and
the data is valid sometime later during the _same_ cycle. Most SRAM
generators produce synchronous read SRAM macros.

You can take a look at the generated transistor-level netlist like this:

```
 % cd $TOPDIR/asic/saed-mc/SRAM_64x64_1P
 % less -P "bitcell " SRAM_64x64_1P.sp
 .subckt bitcell prim0 prim1 wlprim
 mg_nmos2 bitn bitp VSS VSS n12 l = 0.1u w = 0.3u m = 1
 mnmosin1 prim1 wlprim bitp VSS n12 l = 0.1u w = 0.21u m = 1
 mnmosin2 bitn wlprim prim0 VSS n12 l = 0.1u w = 0.21u m = 1
 mg_nmos1 bitp bitn VSS VSS n12 l = 0.1u w = 0.3u m = 1
 mg_pmos1 bitp bitn VDD VDD p12 l = 0.1u w = 0.12u m = 1
 mg_pmos2 bitn bitp VDD VDD p12 l = 0.1u w = 0.12u m = 1
 .IC V( bitn ) = 1.2
 .ends bitcell
```

This is showing the netlist for one bitcell in the SRAM. This is a
classic 6T SRAM bitcell with two cross-coupled inverters (`mg_nmos1`,
`mg_nmos2`, `mg_pmos1`, `mg_pmos2`) and two access transistors
(`mnmosin`, `mnmosin2`).

Now let's use Klayout look at the actual layout produced by the SAED
memory generator.

```
 % cd $TOPDIR/asic/saed-mc/SRAM_64x64_1P
 % klayout -l $ECE5745_STDCELLS/klayout.lyp SRAM_64x64_1P.gds
```

The following figure shows the layout for the SRAM macro. In Klayout, you
can show/hide layers by double clicking on them on the right panel. You
can show more of the hierarchy by selecting _Display > Increment
Hierarchy_ from the menu. In this specific figure, I have hidden the top
metal layer power routing in order to see the underlying array of
bitcells, the word drivers and decode logic on the right, and the column
circuitry at the bottom.

![](assets/fig/sram-64x64-1p.png)

The following figures shows the layout for a single SRAM bitcell. Notice
that two bitcells are actually encapsulated in a single bitcell "cell"
since the two bitcells are mirrored. The word lines are routed
horizontally on M1 (blue) and the bit lines are routed vertically on M2
(purple). See if you can map the layout to the canonical 6T SRAM bitcell
transistor-level implementation.

![](assets/fig/sram-bitcell.png)

Now let's look at the behavioral Verilog produced by the SAED memory
generator.

```
 % cd $TOPDIR/asic/saed-mc/SRAM_64x64_1P
 % less SRAM_64x64_1P.v
 module SRAM_64x64_1P (A,CE,WEB,OEB,CSB,I,O);
  input           CE;
  input           WEB;
  input           OEB;
  input           CSB;

  input   [5:0]   A;
  input   [63:0]  I;
  output  [63:0]  O;

  reg     [63:0]  memory[63:0];
  reg     [63:0]  data_out1;
  reg     [63:0]  O;

  wire            RE;
  wire            WE;

  and u1 (RE, ~CSB,  WEB);
  and u2 (WE, ~CSB, ~WEB);

  always @ (posedge CE)
    if (RE)
      data_out1 = memory[A];
    else
    if (WE)
      memory[A] = I;

  always @ (data_out1 or OEB)
    if (!OEB)
      O = data_out1;
    else
      O =  64'bz;
  endmodule
```

This is a simple behavior Verilog model which could be used for RTL
simulation, although notice the SRAM generator is not using non-blocking
assignments when reading/writing the `memory`. This could cause strange
behavior, so a designer would need to use this model with care.

Let’s look at snippet of the `.lib` file for the SRAM macro.

```
 % cd $TOPDIR/asic/saed-mc/SRAM_64x64_1P
 % less SRAM_64x64_1P.lib
 cell (SRAM_64x64_1P) {
   area :  59269.136 ;
   pin(A[0]) {
     direction : input;
     capacitance : 0.1;
     max_transition : 2.000;
   }
   ...
 }
```

As with the standard-cell library, the `.lib` includes information about
the area of the block, the capacitance on all pins, and power of the
circuit.

The `.lef` file will mostly contain large rectangular blockages which
mean that the ASIC tools should not route any M1, M2, M3, M4 wires over
the SRAM (because they would accidentally create short circuits with the
M1, M2, M3, M4 wires already in the SRAM macro). The `.lef` file also
identifies where all of the pins are physically located so the ASIC tools
can correctly connect to the SRAM macro.

Try experimenting with the configuration file to generate other SRAM
macros.

CACTI Memory Generator
--------------------------------------------------------------------------

While the SAED memory generator is useful for understanding how memory
generators work in general, the SRAM macros produced by the SAED memory
generator are not particularly useful in this course for two reasons.
First, the SAED memory generator can only generate SRAM macros with 16,
32, 64, or 128 rows and the maximum bits per row is 512. This is somewhat
limiting, but perhaps more importantly the SAED memory generator does not
support partial writes. So to build SRAMs suitable for use in caches we
would need to combine many smaller SRAMs, and we would need to carefully
write only one of these smaller SRAMs for a partial write. The SAED
memory generator also produces relatively simplistic `.lib` files which
make reasonable power analysis difficult. Given these issues, we will be
using a different memory generator based on the CACTI memory modeling
tool.

The CACTI memory generator is not a "real" memory generator, but instead
it uses first-order analytical modeling to estimate the area, energy, and
timing of SRAMs (and other memory array structures). We can "abuse" the
CACTI modeling tool to serve as a memory generator by taking the area,
energy, and timing estimates from CACTI and inserting them into carefully
developed `.v`, `.lib`, and `.lef` templates. Essentially we are fooling
the ASIC tools into thinking we have a real SRAM macro, when really all
we have if is a rough first-order estimate of a real SRAM macro. This
works well enough for teaching, but keep in mind there is no "real"
layout for these SRAM macros.

The CACTI memory generator also uses a configuration file to specify the
various parameters for the desired SRAM macro. You can see an example
configuration file for the CACTI memory generator here:

```
 % cd $TOPDIR/asic/cacti-mc
 % more SRAM_64x64_1P.cfg
 conf:
  baseName:   SRAM
  numWords:   64
  wordLength: 64
  numRWPorts: 1
  numRPorts:  0
  numWPorts:  0
  technology: 90
  opCond:     Typical
  debug:      False
  noBM:       False
```

You will only really want to change the `numWords` and the `wordLength`
parameters. As before, are generating a single-ported SRAM which has 64
rows and 64 bits per row for a total capacity of 4096 bits or 512B. If
you want to use a dual-ported SRAM you will need to work with the
instructors to modify the setup.

You can use the following commands to run the CACTI memory generator.

```
 % cd $TOPDIR/asic/cati-mc
 % cacti-mc SRAM_64x64_1P.cfg
```

It will take a few minutes to generate the SRAM macro. You can see the
resulting views here:

```
 % cd $TOPDIR/asic/cati-mc/SRAM_64x64_1P
 % ls -1
 % SRAM_64x64_1P.v
 % SRAM_64x64_1P.lib
 % SRAM_64x64_1P.db
 % SRAM_64x64_1P.lef
 % SRAM_64x64_1P.mw
```

Notice there is no real layout nor transistor-level netlist. Instead, the
CACTI memory generator has produced: a Verilog behavior model; a `.lib`
file with information area, leakage power, capacitance of each input pin,
internal power, logical functionality, and timing; a `.db` file which is
a binary version of the `.lib` file; a `.lef` file which includes
information on the dimensions of the cell and the location and dimensions
of both power/ground and signal pins; and a `.mw` file which is a
Milkyway database representation of the SRAM macro based on the `.lef`.

The CACTI SRAM macros have a very similar pin-level interface as the SAED
SRAM macros with the exception of an additional `WBM` pin which is used
as a write byte mask.

Using SRAMs in RTL Models
--------------------------------------------------------------------------

Now that we understand how an SRAM generator works, let's see how to
actually use an SRAM in your RTL models. We have create a behavioral SRAM
model in the `sim/sram` subdirectory.

```
 % cd $TOPDIR/sim/sram
 % ls
 ...
 SramPRTL.py
 SramVRTL.v
 SramRTL.py
```

There is both a PyMTL and Verilog version. Both are parameterized by the
number of words and the bits per word, and both have the same pin-level
interface:

 - `port0_val`: port enable
 - `port0_type`: transaction type (0 = read, 1 = write)
 - `port0_idx`: which row to read/write
 - `port0_wdata`: write data
 - `port0_wben`: write byte enable
 - `port0_rdata`: read data

SRAMs use a latency _sensitive_ interface meaning a user must carefully
manage the timing for correct operation (i.e., set the read address and
then exactly one cycle later use the read data). In addition, the SRAM
cannot be "stalled". To illustrate how to use SRAM macros, we will create
a latency _insensitive_ val/rdy wrapper around an SRAM which enables
writing and reading the SRAM using our standard memory messages. The
following figure illustrates a naive approach to implementing the SRAM
val/rdy wrapper.

![](assets/fig/sram-valrdy-wrapper-uarch1.png)

Consider what might happen if we use a single-element bypass queue. The
following pipeline diagram illustrates what can go wrong.

```
 cycle : 0  1  2  3  4  5  6  7  8
 msg a : M0 Mx
 msg b :    M0 Mx
 msg c :       M0 M1 M2 M2 M2       # M2 stalls on cycles 3-5
 msg d :          M0 M1 M1 M1 M2    # but wait, we cannot stall in M1!
 msg e :             M0 M0 M0 M0 Mx

 cycle M0 M1 [q] M2
    0: a
    1: b  a      a  # a flows through bypass queue
    2: c  b      b  # b flows through bypass queue
    3: d  c         # M2 is stalled, c will need to go into bypq
    4: e  d   c     # q is full at beginning of cycle, enq_rdy = 0
    5: e  ?   c     # what happens to d? cannot stall in M1!
```

Here we are using Mx to indicate when a transaction goes through M1 and
M2 in the same cycle because it flows straight through the bypass queue.
So on cycle 3, the response interface is stalled and as a consequence
message c must be enqueued into the memory response queue. On cycle 4,
the response queue is full (`enq_rdy` = 0) so `memreq_rdy` = 0 and
message e will stall in M0 (i.e., will stall waiting to be accepted by
the SRAM wrapper). The critical question is what happens to message d? It
_cannot_ stall in M1 because we cannot stall the SRAM. So basically we
just drop it. Increasing the amount of the buffering in the bypass queue
will not solve the problem. The key issue is that by the time we realize
the bypass queue is full we can potentially already have a transaction
executing in the SRAM, and this transaction cannot be stalled.

This is a classic situation where the need more skid buffering. A correct
solution will have two or more elements of buffering in the memory
response queue _and_ stall M0 if there are less than two free elements in
the queue. Thus in the worst case, if M2 stalls we have room for two
messages in the response queue: the message currently in M1 and the
message currently in M0. Here is the updated design:

![](assets/fig/sram-valrdy-wrapper-uarch2.png)

Here is the updated pipeline diagram.

```
 cycle : 0  1  2  3  4  5  6  7  8
 msg a : M0 Mx
 msg b :    M0 Mx
 msg c :       M0 M1 M2 M2 M2
 msg d :          M0 M1 q  q  M2     # msg c is in skid buffer
 msg e :             M0 M0 M0 M0 Mx

 cycle M0 M1 [q ] M2
    0: a
    1: b  a       a  # a flows through bypass queue
    2: c  b       b  # b flows through bypass queue
    3: d  c          # M2 is stalled, c will need to go into bypq
    4: e  d    c     #
    5: e      dc     # d skids behind c into the bypq
    6: e       d  c  # c is dequeued from bypq
    7: e          d  # d is dequeued from bypq
    8:    e       e  # e flows through bypass queue
```

Note, with a pipe queue you still need two elements of buffering. There
could be a message in the response queue when M2 stalls and then you
still don't have anywhere to put the message currently in M1.

Take a closer look at the SRAM val/rdy wrapper we provide you. Here is
the PyMTL version:

```
 % cd $TOPDIR/sim/tut8_sram
 % more SramValRdyPRTL.py
 from sram import SramRTL
 ...
 s.sram = m = SramRTL( num_bits, num_words )
```

And here is the Verilog version:

```
 % cd $TOPDIR/sim/tut8_sram
 % more SramValRdyVRTL.v
 `include "sram/SramVRTL.v"
 ...
 sram_SramVRTL#(32,256) sram
 (
   .clk         (clk),
   .reset       (reset),
   .port0_idx   (sram_addr_M0),
   .port0_type  (sram_wen_M0),
   .port0_wben  (sram_byte_wen_M0),
   .port0_val   (sram_en_M0),
   .port0_wdata (sram_write_data_M0),
   .port0_rdata (sram_read_data_M1)
 );
```

To use an SRAM in a PyMTL model, simply import `SramRTL`, instantiate the
SRAM, and set the number of words and number of bits per word. To use an
SRAM in a Verilog model, simply include `sram/SramVRTL.v` and again
instantiate the SRAM, and set the number of words and number of bits per
word.

We can run a test on the SRAM val/rdy wrapper like this:

```
 % mkdir -p $TOPDIR/sim/build
 % cd $TOPDIR/sim/build
 % py.test ../tut8_sram/test/SramValRdyRTL_test.py -k test_generic[random_0_3] -s
 ...
  2:
  3: wr:00:00000000:b1aa20f1ac2c79ec
  4: wr:01:00000008:eadb7347037714f4  wr:00:0:
  5: wr:02:00000010:f956c79b184e3089  #
  6: #                                #
  7: #                                #
  8: #                                wr:01:0:
  9: #                                #
 10: #                                #
 11: #                                #
 12: #                                wr:02:0:
 13: wr:03:00000018:af99be5f98bb9cf5  .
 14: wr:04:00000020:57dace845824f57a  wr:03:0:
 15: wr:05:00000028:567a0f9ff18ff8b2  #
 16: #                                wr:04:0:
```

The first write transaction takes a single cycle to go through the SRAM
val/rdy wrapper, but then the response interface is not ready on cycles
5-7. The second and third write transactions are still accepted by the
SRAM val/rdy wrapper and they will end up in the bypass queue, but the
fourth write transaction is stalled because the request interface is not
ready. No transactions are lost.

The SRAM module is parameterized to enable initial design space
exploration, but just because we choose a specific SRAM configuration
does not mean the files we need to create the corresponding SRAM macro
exist yet. Once we have finalized the SRAM size, we need to go through a
four step process.

**Step 1: See if SRAM configuration already exists**

The first step is to see if your desired SRAM configuration already
exists. You can do this by looking at the names of the `.cfg` files in
the `sim/sram` subdirectory.

```
 % cd $TOPDIR/sram
 % ls *.cfg
 SRAM_128x256_1P.cfg
 SRAM_32x256_1P.cfg
```

This means there are two SRAM configurations already available. One SRAM
has 256 words each with 128 bits and the other SRAM has 256 words each
with 32 bits. If the SRAM configuration you need already exists then you
are done and can skip the remaining steps.

**Step 2: Create SRAM configuration file**

The next step is to create a new SRAM configuration file. You must use a
very specific naming scheme. An SRAM with `N` words and `M` bits per word
must be named `SRAM_MxN_1P.cfg`. Create a configuration file named
`SRAM_64x64_1P.cfg` that we can use in the SRAM val/rdy wrapper. The
configuration file should contain the following contents:

```
 % cd $TOPDIR/sram
 % more SRAM_64x64_1P.cfg
 conf:
  baseName:   SRAM
  wordLength: 64
  numWords:   64
  numRWPorts: 1
  numRPorts:  0
  numWPorts:  0
  technology: 90
  opCond:     Typical
  debug:      False
  noBM:       False
```

**Step 3: Create an SRAM configuration RTL model**

The next step is to create an SRAM configuration RTL model. This new RTL
model should have the same name as the configuration file except a PyMTL
RTL model should use a `.py` filename extension and a Verilog RTL model
should use a `.v` filename extension. We have provided a generic SRAM RTL
model to make it easier to implement the SRAM configuration RTL model.
The generic PyMTL SRAM RTL model is in `SramGenericPRTL.py` and the
generic Verilog SRAM RTL model is in `SramGenericVRTL.v`. Go ahead and
create an SRAM configuration RTL model for the 64x64 configuration that
we used in the SRAM val/rdy wrapper.

Here is what this model should look like if you are using PyMTL:

```python
from pymtl           import *
from SramGenericPRTL import SramGenericPRTL

class SRAM_64x64_1P( Model ):

  # Make sure widths match the .v

  # This is only a behavior model, treated as a black box when translated
  # to Verilog.

  vblackbox      = True
  vbb_modulename = "SRAM_64x64_1P"
  vbb_no_reset   = True
  vbb_no_clk     = True

  def __init__( s ):

    # clock: in PyMTL simulation it uses implicit .clk port when
    # translated to Verilog, actual clock ports should be CE1

    s.CE1  = InPort ( 1  )  # clk
    s.WEB1 = InPort ( 1  )  # bar( write en )
    s.OEB1 = InPort ( 1  )  # bar( out en )
    s.CSB1 = InPort ( 1  )  # bar( whole SRAM en )
    s.A1   = InPort ( 6  )  # address
    s.I1   = InPort ( 64 )  # write data
    s.O1   = OutPort( 64 )  # read data
    s.WBM1 = InPort ( 8  )  # byte write en

    # instantiate a generic sram inside
    s.sram_generic = SramGenericPRTL( 64, 64 )

    s.connect( s.CE1,  s.sram_generic.CE1  )
    s.connect( s.WEB1, s.sram_generic.WEB1 )
    s.connect( s.OEB1, s.sram_generic.OEB1 )
    s.connect( s.CSB1, s.sram_generic.CSB1 )
    s.connect( s.A1,   s.sram_generic.A1   )
    s.connect( s.I1,   s.sram_generic.I1   )
    s.connect( s.O1,   s.sram_generic.O1   )
    s.connect( s.WBM1, s.sram_generic.WBM1 )
```

Notice how this is simply a wrapper around `SramGenericPRTL` instantiated
with the desired number of words and bits per word.

Here is what this model should look like if you are using Verilog:

```verilog
`ifndef SRAM_32x256_1P
`define SRAM_32x256_1P

`include "sram/SramGenericVRTL.v"

module SRAM_32x256_1P
(
  input         CE1,
  input         WEB1,
  input         OEB1,
  input         CSB1,
  input  [7:0]  A1,
  input  [31:0] I1,
  output [31:0] O1,
  input  [3:0]  WBM1
);

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

endmodule

`endif /* SRAM_32x256_1P */
```

Notice how this is simply a wrapper around `SramGenericVRTL` instantiated
with the desired number of words and bits per word.

**Step 3: Use new SRAM configuration RTL model in top-level SRAM model**

The final step is to modify the top-level SRAM model to select the proper
SRAM configuration RTL model. If you are using PyMTL, you will need to
modify `SramPRTL.py` like this:

```python
# Add this at the top of the file
from SRAM_64x64_1P  import SRAM_64x64_1P

...

   if   num_bits == 32 and num_words == 256:
      s.sram = m = SRAM_32x256_1P()
    elif num_bits == 128 and num_words == 256:
      s.sram = m = SRAM_128x256_1P()

    # Add the following to choose new SRAM configuration RTL model
    elif num_bits == 64  and num_words == 64:
      s.sram = m = SRAM_64x64_1P()

    else:
      s.sram = m = SramGenericPRTL( num_bits, num_words )
```

If you are using Verilog, you will need to modify `SramVRTL.v` like this:

```verilog
// Add this at the top of the file
`include "sram/SRAM_64x64_1P.v"

...

  generate
    if      ( p_data_nbits == 32  && p_num_entries == 256 )
      SRAM_32x256_1P  sram ( clk, ~t, 1'b0, ~v, i, wd, rd, wben );
    else if ( p_data_nbits == 128 && p_num_entries == 256 )
      SRAM_128x256_1P sram ( clk, ~t, 1'b0, ~v, i, wd, rd, wben );

    // Add the following to choose new SRAM configuration RTL model
    else if ( p_data_nbits == 64 && p_num_entries == 64 )
      SRAM_64x64_1P sram ( clk, ~t, 1'b0, ~v, i, wd, rd, wben );

    else
      SramGenericVRTL#(p_data_nbits,p_num_entries) sram
        (
          .CE1  ( clk  ),
          .WEB1 ( ~t   ),
          .OEB1 ( 1'b0 ),
          .CSB1 ( ~v   ),
          .A1   ( i    ),
          .I1   ( wd   ),
          .O1   ( rd   ),
          .WBM1(  wben )
        );
  endgenerate
```

One might ask what is the point of going through all of the trouble of
creating an SRAM configuration RTL model that is for a specific size if
we already have a generic SRAM RTL model. The key reason is that the ASIC
tools will use the _name_ of the SRAM to figure out where to swap in the
SRAM macro. So we need a explicit module name for every different SRAM
configuration to enable using SRAM macros in the ASIC tools.

**Step 4: Test new SRAM configuration**

The final step is to test the new configuration and verify everything
works. We start by adding a simple directed test to the `SramRTL_test.py`
test script. Here is an example:

```python
def test_direct_64x64( dump_vcd, test_verilog ):
  test_vectors = [ header_str,
    # val,  type,  wben,       idx,  wdata,              rdata
    [    1, 1,     0b11111111, 0x00, 0xdeadbeefcafe0123, '?'                ],
    [    1, 0,     0b00000000, 0x00, 0x0000000000000000, '?'                ],
    [    0, 0,     0b00000000, 0x00, 0x0000000000000000, 0xdeadbeefcafe0123 ],
    [    1, 1,     0b11111111, 0x3f, 0x0a0b0c0d0e0f0102, '?'                ],
    [    1, 0,     0b00000000, 0x3f, 0x0000000000000000, '?'                ],
    [    0, 0,     0b00000000, 0x00, 0x0000000000000000, 0x0a0b0c0d0e0f0102 ],
    [    1, 1,     0b11111111, 0x01, 0xaaaaaaaaaaaaaaaa, '?'                ],
    [    1, 1,     0b00000011, 0x01, 0x0123cafebeefdead, '?'                ],
    [    1, 0,     0b00000000, 0x01, 0x0000000000000000, '?'                ],
    [    0, 0,     0b00000000, 0x01, 0x0000000000000000, 0xaaaaaaaaaaaadead ],
    [    1, 1,     0b00001100, 0x01, 0x0123cafebeefdead, '?'                ],
    [    1, 0,     0b00000000, 0x01, 0x0000000000000000, '?'                ],
    [    0, 0,     0b00000000, 0x01, 0x0000000000000000, 0xaaaaaaaabeefdead ],
    [    1, 1,     0b00110000, 0x01, 0x0123cafebeefdead, '?'                ],
    [    1, 0,     0b00000000, 0x01, 0x0000000000000000, '?'                ],
    [    0, 0,     0b00000000, 0x01, 0x0000000000000000, 0xaaaacafebeefdead ],
    [    1, 1,     0b11000000, 0x01, 0x0123cafebeefdead, '?'                ],
    [    1, 0,     0b00000000, 0x01, 0x0000000000000000, '?'                ],
    [    0, 0,     0b00000000, 0x01, 0x0000000000000000, 0x0123cafebeefdead ],
  ]
  run_test_vector_sim( SramRTL(64, 64), test_vectors, dump_vcd, test_verilog )
```

This directed test writes a value to a specific word and then reads that
word to verify the value was written correctly. We test writing the first
word, the last word, and then partial word writes. We can run the
directed test like this:

```
 % cd $TOPDIR/sim/build
 % py.test ../sram/test/SramRTL_test.py -k test_direct_64x64
```

We have included a helper function that simplifies random testing. All
you need to do is add the configuration to the `sram_configs` variable in
the test script:

```
 sram_configs = [ (16, 32), (32, 256), (128, 256), (64,64) ]
```

Then you can run the random test like this:

```
 % cd $TOPDIR/sim/build
 % py.test ../sram/test/SramRTL_test.py -k test_random[64-64]
```

And of course we should run all of the tests to ensure we haven't broken
anything when adding this new configuration.

```
 % cd $TOPDIR/sim/build
 % py.test ../sram
```

Manual ASIC Flow with SRAM Macros
--------------------------------------------------------------------------

Now that we have added the desired SRAM configuration, we can use the
ASIC tools to generate layout for the SRAM val/rdy wrapper. In this
section, we will go through the steps manually, and in the next section
we will use the automated ASIC flow.

The first step is to run a simulator to generate the Verilog for pushing
through the flow.

```
 % cd $TOPDIR/sim/build
 % ../tut8_sram/sram-sim --impl rtl --input random --translate --dump-vcd
 % ls
 ...
 SramValRdyRTL.v
 SramValRdyRTL_blackbox.v
```

As an aside, the simulator will generate _two_ different Verilog files.
The first Verilog file is `SramValRdyRTL.v`, and it is a fully functional
RTL model which is what is actually simulated when use the `--translate`
command line option. The second Verilog file is
`SramValRdyRTL_blackbox.v` and it is what we use with the ASIC tools.
Search for the SRAM module in the blackbox Verilog file:

```
 % cd $TOPDIR/sim/build
 % less -p
 ...
 `default_nettype none
 module SRAM_64x64_1P
 (
   input  wire [   5:0] A1,
   input  wire [   0:0] CE1,
   input  wire [   0:0] CSB1,
   input  wire [  63:0] I1,
   output wire [  63:0] O1,
   input  wire [   0:0] OEB1,
   input  wire [   7:0] WBM1,
   input  wire [   0:0] WEB1
 );

 endmodule // SRAM_64x64_1P
 `default_nettype wire
```

Notice that this SRAM module is empty! In other words, in the blackbox
Verilog file, all SRAMs are implemented as "blackboxes" with no internal
functionality. If we included the behavioral implementation of the SRAM,
then Synopsys DC would try to synthesize the SRAM as opposed to using the
SRAM macro.

The next step is to run the CACTI memory generator to generate the SRAM
macro corresponding to the desired 64x64 configuration.

```
 % cd $TOPDIR/asic/cacti-mc
 % cacti-mc ../../sim/sram/SRAM_64x64_1P.cfg
 % cd SRAM_64x64_1P
 % mv *.lib *.db *.lef *.mw ..
```

Now we can use Synopsys DC to synthesize the logic which goes around the
SRAM macro.

```
 % mkdir -p $TOPDIR/asic/dc-syn/build-dc-manual
 % cd $TOPDIR/asic/dc-syn/build-dc-manual
 % dc_shell-xg-t

 dc_shell> set_app_var target_library "$env(ECE5745_STDCELLS)/stdcells.db ../../cacti-mc/SRAM_64x64_1P.db"
 dc_shell> set_app_var link_library   "* $env(ECE5745_STDCELLS)/stdcells.db ../../cacti-mc/SRAM_64x64_1P.db"
 dc_shell> analyze -format sverilog ../../../sim/build/SramValRdyRTL_blackbox.v
 dc_shell> elaborate SramValRdyRTL
 dc_shell> check_design
 dc_shell> create_clock clk -name ideal_clock1 -period 1
 dc_shell> compile
 dc_shell> write -format verilog -hierarchy -output post-synth.v
 dc_shell> exit
```

We are basically using the same steps we used in the Synopsys ASIC tool
tutorial. Notice how we must point Synopsys DC to the `.db` file
generated by the CACTI memory generator so Synopsys DC knows the abstract
logical, timing, power view of the SRAM. Also notice how we are pointing
Synopsys DC to the blackbox Verilog.

If you look for the SRAM module in the synthesized gate-level netlist,
you will see that it is referenced but not declared. This is what we
expect since we are not synthesizing the memory but instead using an SRAM
macro.

```
 % cd $TOPDIR/asic/dc-syn/build-dc-manual
 % less -p SRAM post-synth.v
```

Now we can use Synopsys ICC to place the SRAM macro and the standard
cells, and then automatically route everything together.

```
 % mkdir -p $TOPDIR/asic/icc-par/build-icc-manual
 % cd $TOPDIR/asic/icc-par/build-icc-manual
 % icc_shell -gui

 icc_shell> set_app_var target_library "$env(ECE5745_STDCELLS)/stdcells.db ../../cacti-mc/SRAM_64x64_1P.db"
 icc_shell> set_app_var link_library   "* $env(ECE5745_STDCELLS)/stdcells.db ../../cacti-mc/SRAM_64x64_1P.db"

 icc_shell> create_mw_lib -open \
    -tech                 "$env(ECE5745_STDCELLS)/rtk-tech.tf" \
    -mw_reference_library "$env(ECE5745_STDCELLS)/stdcells.mwlib ../../cacti-mc/SRAM_64x64_1P.mw" \
    "LIB"

 icc_shell> set_tlu_plus_files \
    -max_tluplus  "$env(ECE5745_STDCELLS)/rtk-max.tluplus" \
    -min_tluplus  "$env(ECE5745_STDCELLS)/rtk-min.tluplus" \
    -tech2itf_map "$env(ECE5745_STDCELLS)/rtk-tluplus.map"

 icc_shell> import_designs -format verilog "../../dc-syn/build-dc-manual/post-synth.v"
 icc_shell> create_clock clk -name ideal_clock1 -period 1
 icc_shell> create_floorplan -core_utilization 0.7
```

The following screen capture illustrates what you should see: a square
floorplan, the standard cells loosely arranged to the right of the
floorplan, and the SRAM macro positioned above the floorplan.

![](assets/fig/synopsys-icc-1.png)

We can now do a simple placement of the standard cells _and_ the SRAM
macro into the floorplan.

```
 icc_shell> create_fp_placement
```

We need to fix the location of the SRAM so that the rest of the flow can
rely on it not moving. We do that with the following command.

```
 icc_shell> set_dont_touch_placement [all_macro_cells]
```

Use the “zoom to fit” button in the toolbar to focus on the square
floorplan. The following screen capture illustrates what you should see:
all of the cells arranged into tight rows within the square floorplan.

![](assets/fig/synopsys-icc-2.png)

Notice how the SRAM macro is automatically placed in the upper left-hand
corner and the standard cells are arranged in rows to the right and below
the SRAM macro.

We can now finish up with automatic power, clock, and signal routing.

```
 icc_shell> derive_pg_connection \
  -power_net  "VDD" -power_pin  "VDD" \
  -ground_net "VSS" -ground_pin "VSS" \
  -create_ports top

 icc_shell> synthesize_fp_rail \
  -power_budget 1000 -voltage_supply 1.2 -target_voltage_drop 250 \
  -nets "VDD VSS" \
  -create_virtual_rails "M1" \
  -synthesize_power_plan -synthesize_power_pads -use_strap_ends_as_pads

 icc_shell> commit_fp_rail

 icc_shell> clock_opt

 icc_shell> route_opt
 icc_shell> insert_stdcell_filler \
  -cell_with_metal "SHFILL128 SHFILL64 SHFILL3 SHFILL2 SHFILL1" \
  -connect_to_power "VDD" -connect_to_ground "VSS"
```

The following screen capture illustrates the final layout.

![](assets/fig/synopsys-icc-3.png)

Notice that there are many wires connecting the SRAM to the standard
cells. The following screen capture shows a closer view of this routing.

![](assets/fig/synopsys-icc-4.png)

Finally, we might want to take a closer look at which cells are
associated with various modules in the layout using the following steps:

 - Choose _Placement > Color By Hierarchy_ from the menu
 - select _Reload_ in the sidebar on right
 - Select _Color hierarchical cells at level_ in the pop-up window
 - Click _OK_ in the pop up

![](assets/fig/synopsys-icc-5.png)

Recall that the only logic in the SRAM val/rdy wrapper besides the SRAM
macro is an input register for the memory request and the memory response
queue. The memory response queue has two entries and each entry is 110
bits for a total storage of about 220 bits. The SRAM macro includes 64
entries, each of which is 64 bits for a total storage of 4096 bits. From
the amoeba plot we can see that the memory response queue is _larger_ than
the SRAM macro even though the SRAM macro can store 18x more data! This
clearly illustrates the benefit of using an SRAM generator. We are able
to generate much denser memories, but also note that the SRAM macro has
higher latency (a full clock cycle vs. less than a cycle for the memory
response queue) and has lower throughput (a single port vs. a separate
read and write port for the memory response queue).

Automated ASIC Flow with SRAM Macros
--------------------------------------------------------------------------

Pushing a design through the automated ASIC flow is straight-forward. You
just need to include a list of the SRAM configurations used in your
design in the `Makefrag`. Here is the `Makefrag` entry for the SRAM
val/rdy wrapper:

```
 % cd $TOPDIR/asic
 % more Makefrag

 ifeq ($(design),tut8-sram)
   clock_period  = 2.0
   vsrc          = SramValRdyRTL_blackbox.v
   vcd           = sram-rtl-random.verilator1.vcd
   srams         = SRAM_64x64_1P
 endif
```

You can includes a whitespace-separated list of SRAM configurations. Now
set the `design` variable in the Makefrag to `tut8-sram`.

```
 % cd $TOPDIR/asic
 % grep "design =" Makefrag
 design = tut8-sram
```

We have created a `Makefile` to automate using the CACTI memory
generator.

```
 % cd $TOPDIR/asic/cacti-mc
 % make
```

After generating the SRAM macro, we can use Synopsys DC, ICC, and PT as
before.

```
 % cd $TOPDIR/asic/dc-syn  && make
 % cd $TOPDIR/asic/icc-par && make
 % cd $TOPDIR/asic/pt-pwr  && make

  vsrc       = SramValRdyRTL_blackbox.v
  input      = sram-rtl-random
  area       = 20435 # um^2
  constraint = 2.0 # ns
  slack      = 0.37 # ns
  cycle_time = 1.63 # ns
  exec_time  = 217 # cycles
  power      = 12.7 # mW
  energy     = 4.492117 # nJ
```

You might want to take a look at the layout in Synopsys ICC just to
confirm that everything looks correct. An amoeba plot is shown below.

![](assets/fig/sram-valrdy-wrapper-amoeba-plot.png)

The memory response queue is colored green. Notice that the area of the
memory response queue is much smaller than when we ran the Synopsys tools
manually. This is to be expected since the automated ASIC flow uses more
sophisticated commands and flags to force the tools to better optimize
the design.

When you look at the timing reports, the SRAM macro will show up as a
sequential module meaning it can start and end timing paths. You should
not see any paths going _through_ the SRAM macro since it is a
synchronous read SRAM. You can view the area report like this:

```
 % cd $TOPDIR/asic/icc-par
 % more current-icc/reports/chip_finish_icc.area.rpt

 Combinational area:               5696.409626
 Buf/Inv area:                     3291.033589
 Noncombinational area:            4349.030348
 Macro/Black Box area:             9787.801758
 Net Interconnect area:             601.858019

 Total cell area:                 19833.241732
 Total area:                      20435.099751

                                        Global      Local
                                        Cell Area   Cell Area
                                        ----------  -----------------------
 Hierarchical cell                      Abs                  Non    Black-
                                        Total  %     Comb    Comb   boxes
 ------------------                     ------ ----- ------- ------ -------  -----------------------------
 SramValRdyRTL                         19833.2 100.0  2669.8    0.0     0.0  SramValRdyRTL
 memreq_msg_reg                          629.4   3.2   281.0  348.3     0.0  RegRst
 memreq_val_reg                           35.9   0.2    11.0   24.8     0.0  RegRst
 memresp_queue                          5824.5  29.4    11.0    0.0     0.0  TwoElementBypassQueue
 memresp_queue/queue0                   2899.3  14.6     0.0    0.0     0.0  SingleElementBypassQueue
 memresp_queue/queue0/ctrl                51.6   0.3    26.7   24.8     0.0  SingleElementBypassQueueCtrl
 memresp_queue/queue0/dpath             2847.7  14.4     0.0    0.0     0.0  SingleElementBypassQueueDpath
 memresp_queue/queue0/dpath/bypass_mux   868.1   4.4   868.1   0.00     0.0  Mux
 memresp_queue/queue0/dpath/queue       1979.5  10.0     0.0 1940.8     0.0  RegEn
 memresp_queue/queue1                   2914.0  14.7     0.0    0.0     0.0  SingleElementBypassQueue
 memresp_queue/queue1/ctrl                66.3   0.3    41.4   24.8     0.0  SingleElementBypassQueueCtrl
 memresp_queue/queue1/dpath             2847.7  14.4     0.0    0.0     0.0  SingleElementBypassQueueDpath
 memresp_queue/queue1/dpath/bypass_mux   868.1   4.4   868.1    0.0     0.0  Mux
 memresp_queue/queue1/dpath/queue       1979.5  10.0     0.0 1940.8     0.0  RegEn
 sram                                  10673.4  53.8   885.6    0.0  9787.8  SramPRTL
 ------------------------------------- ------- ----- ------- ------ -------  -----------------------------
 Total                                                5696.4 4349.0  9787.8
```

Although the area of the SRAM is now about twice the area of the memory
response queue, keep in mind that the SRAM has a capacity that is 18x the
capacity of the memory response queue.

As a final experiment, let's rerun the simulation where all of the data
that is read and written is zeros.

```
 % cd $TOPDIR/sim/build
 % ../tut8_sram/sram-sim --impl rtl --input allzeros --translate --dump-vcd
```

We need to update the `Makefrag` to point to the new VCD file.

```
 % cd $TOPDIR/asic
 % more Makefrag

 ifeq ($(design),tut8-sram)
   clock_period  = 2.0
   vsrc          = SramValRdyRTL_blackbox.v
   vcd           = sram-rtl-allzero.verilator1.vcd
   srams         = SRAM_64x64_1P
 endif
```

Now we re-run Synopsys PT:

```
% cd $TOPDIR/asic/pt-pwr && make

  vsrc       = SramValRdyRTL_blackbox.v
  input      = sram-rtl-allzero
  area       = 20435 # um^2
  constraint = 2.0 # ns
  slack      = 0.37 # ns
  cycle_time = 1.63 # ns
  exec_time  = 217 # cycles
  power      = 9.349 # mW
  energy     = 3.30683479 # nJ
```

As expected, the energy has decreased from 4.5nJ to 3.3nJ.

