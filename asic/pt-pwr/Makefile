#=======================================================================
# UCB VLSI FLOW: Makefile for pt-pwr
#-----------------------------------------------------------------------
# Yunsup Lee (yunsup@cs.berkeley.edu)
#
# This makefile will use Synopsys PrimeTime to check timing and analyze
# power of your gate-level verilog netlist.
#

include ../Makefrag

# Because we now only support the PyMTL flow, we can just generate these
# instead of requiring the user to specify them.

sim_build_dir = sim/build

vmname_temp = $(strip $(patsubst %.v, %, $(vsrc)))

# When we use SRAMs we end up with a _blackbox.v file. We need to also
# strip the _blackbox suffix to make the verilog module name. If there is
# no _blacbox suffix then this will just make vmname = vmname_temp

vmname = $(strip $(patsubst %_blackbox, %, $(vmname_temp)))

viname = TOP/v

default: all

basedir  = ../..

#--------------------------------------------------------------------
# Sources
#--------------------------------------------------------------------

basedir  = ../..

sim_search_dir = ../$(basedir)/$(sim_build_dir)

# Verilog sources (do not include test harness!)

vsrcs = $(basedir)/$(sim_build_dir)/$(vsrc)

# VCD

vcdsrc = $(basedir)/$(sim_build_dir)/$(vcd)

# Specify toplevel verilog module

toplevel = $(vmname)

# Extra option to preprocess-saif script for pure-Verilog flow

ifeq ($(flow),verilog)
  ppsaif_opt=--verilog-flow
else
  ppsaif_opt=
endif

# SRAMs

sram_dbs      = $(patsubst %, %.db, $(srams))
sram_mws      = $(patsubst %, %.mw, $(srams))
sram_mws_wdir = $(addprefix ../../cacti-mc/, $(sram_mws))

#--------------------------------------------------------------------
# Build rules
#--------------------------------------------------------------------

pt_exec         := pt_shell
build_suffix    := $(shell date +%Y-%m-%d_%H-%M)
build_pt_dir    := build-pt-$(build_suffix)
cur_build_pt_dir:= current-pt
reports_dir     := reports
results_dir     := results
log_dir         := log

vcs_dir         := ../vcs-sim-gl-par
vcs_timestamp   := $(vcs_dir)/timestamp
icc_dir         := ../icc-par/current-icc/$(results_dir)
icc_v           := $(icc_dir)/$(toplevel).output.v
icc_sdc         := $(icc_dir)/$(toplevel).output.sdc
icc_min_sbpf    := $(icc_dir)/$(toplevel).output.sbpf.min
icc_max_sbpf    := $(icc_dir)/$(toplevel).output.sbpf.max
icc_timestamp   := $(icc_dir)/../timestamp

pt_timestamp    := $(cur_build_pt_dir)/timestamp

vars_tcl        := rm_setup/common_setup.tcl rm_setup/pt_setup.tcl
makegen_tcl     := make_generated_vars.tcl

pt_avg_tcl      := rm_pt_scripts/pt.avg.tcl
pt_time_tcl     := rm_pt_scripts/pt.time.tcl

vcs_vpd = check
pt_avg_min_rpt = $(addprefix $(cur_build_pt_dir)/$(reports_dir)/, $(addsuffix .power.avg.min.report, $(vcs_vpd)))
pt_avg_max_rpt = $(addprefix $(cur_build_pt_dir)/$(reports_dir)/, $(addsuffix .power.avg.max.report, $(vcs_vpd)))
pt_time_min_rpt = $(addprefix $(cur_build_pt_dir)/$(reports_dir)/, $(addsuffix .power.time.min.report, $(vcs_vpd)))
pt_time_max_rpt = $(addprefix $(cur_build_pt_dir)/$(reports_dir)/, $(addsuffix .power.time.max.report, $(vcs_vpd)))

vars = \
	set DESIGN_NAME                 "$(toplevel)";\n \
	set ADDITIONAL_SEARCH_PATH      "$(adk_dir) ../../cacti-mc ../$(icc_dir)";\n \
	set TARGET_LIBRARY_FILES        "stdcells.db $(sram_dbs)";\n \
	set REPORTS_DIR                 "$(reports_dir)";\n \
	set NETLIST_FILES               "$(notdir $(icc_v))";\n \
	set CONSTRAINT_FILES           "../$(icc_sdc)";\n \

vars_avg = \
	set STRIP_PATH                  "$(viname)";\n \
	set PT_METHOD                   "avg";\n \

vars_time = \
	set STRIP_PATH                  "$(viname)";\n \
	set PT_METHOD                   "time";\n \

vars_min = \
	set PARASITIC_PATHS             "$(toplevel)";\n \
	set PARASITIC_FILES             "../$(icc_min_sbpf)";\n \
	set PT_PARASITIC                "min";\n \

vars_max = \
	set PARASITIC_PATHS             "$(toplevel)";\n \
	set PARASITIC_FILES             "../$(icc_max_sbpf)";\n \
	set PT_PARASITIC                "max";\n \

saif_file = $(cur_build_pt_dir)/temp2.saif

$(pt_timestamp): $(icc_timestamp) $(vars_tcl) $(constraints_tcl) $(pt_avg_tcl) $(pt_time_tcl)
	mkdir $(build_pt_dir)
	rm -f $(cur_build_pt_dir)
	ln -s $(build_pt_dir) $(cur_build_pt_dir)
	cp $(icc_timestamp) $(cur_build_pt_dir)/timestamp-icc
	date > $(pt_timestamp)

$(pt_avg_max_rpt): $(cur_build_pt_dir)/$(reports_dir)/%.power.avg.max.report: $(pt_timestamp)
	vcd2saif -64 -input $(vcdsrc) -output current-pt/rtl-sim.saif
	./preprocess-saif --verbose $(ppsaif_opt) ../icc-par/current-icc/reports/summary.txt \
    current-pt/rtl-sim.saif current-pt/rtl-sim-processed.saif current-pt/clk_def.tcl
	cp $(pt_avg_tcl) $(constraints_tcl) $(vars_tcl) $(cur_build_pt_dir)
	echo -e '$(vars)' > $(cur_build_pt_dir)/$(makegen_tcl)
	echo -e '$(vars_avg)' >> $(cur_build_pt_dir)/$(makegen_tcl)
	echo -e '$(vars_max)' >> $(cur_build_pt_dir)/$(makegen_tcl)
	echo -e 'set ACTIVITY_FILE rtl-sim-processed.saif;\n' >> $(cur_build_pt_dir)/$(makegen_tcl)
	echo -e 'set PT_EXEC pt-pwr;\n' >> $(cur_build_pt_dir)/$(makegen_tcl)
	cd $(cur_build_pt_dir); \
	cp ../../Makefrag .; \
	mkdir -p $(log_dir); \
	$(pt_exec) -f $(notdir $(pt_avg_tcl)) | tee $(log_dir)/$(notdir $(patsubst %.saif, %, $<)).pt.avg.max.log; \
	../summarize-results \
    $(vsrc) $(vcd) \
    ../../icc-par/current-icc/reports/summary.txt \
    rtl-sim-processed.saif \
    reports/pt-pwr.report > reports/summary.txt; \
	cat reports/summary.txt; \
	cd ..

pt: $(pt_avg_max_rpt)

#--------------------------------------------------------------------
# Default make target
#--------------------------------------------------------------------

.PHONY: pt

all: pt

#--------------------------------------------------------------------
# Clean up
#--------------------------------------------------------------------

junk +=

clean:
	rm -rf build* current* $(junk) *~ \#*
