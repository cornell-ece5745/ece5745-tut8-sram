#=======================================================================
# Toplevel Makefile
#=======================================================================
# The toplevel makefile connects together all the tools in the
# toolflow. Each tool should include a target which will enter the
# appropriate tool directory and do a default make. Tool dependencies
# should be expressed simply by adding the appropriate producer tool
# targets to the consumer tool. For example, let's say we have three
# tools (ToolA, ToolB, and ToolC) and that ToolC uses the output from
# both ToolA and ToolB. We would write our tool targets as follows,
# assuming that there are appropriate tool directories named ToolA,
# ToolB, and ToolC. Notice that we should always add the tools to
# the running "tools" make variable so that make clean and other
# miscellaneous targets can be properly setup.
#
#  tools += ToolA
#  ToolA:
#    cd ToolA; make
#
#  tools += ToolB
#  ToolB:
#    cd ToolB; make
#
#  tools += ToolC
#  ToolC: ToolA ToolB
#    cd ToolC; make
#

default: pt-pwr

tools:=

#--------------------------------------------------------------------
# cacti-mc
#--------------------------------------------------------------------

cacti-mc:
	cd cacti-mc; make

cacti-mc-clean:
	cd cacti-mc; make clean

tools += cacti-mc

#--------------------------------------------------------------------
# dc-syn
#--------------------------------------------------------------------

dc-syn:
	cd dc-syn; make

dc-syn-clean:
	cd dc-syn; make clean

tools += dc-syn

#--------------------------------------------------------------------
# icc-par
#--------------------------------------------------------------------

icc-par: dc-syn
	cd icc-par; make

icc-par-clean:
	cd icc-par; make clean

tools += icc-par

#--------------------------------------------------------------------
# pt-pwr
#--------------------------------------------------------------------

pt-pwr: icc-par
	cd pt-pwr; make

pt-pwr-clean:
	cd pt-pwr; make clean

tools += pt-pwr

#--------------------------------------------------------------------
# Misc
#--------------------------------------------------------------------

.PHONY: $(tools)

clean:
	@echo ""; \
	echo -n "  Are you sure you want to do a FULL clean? [Y/N] "; \
	read ans; \
	if [ "$$ans" == "Y" ]; \
	then \
	  for tool in $(tools); \
	  do \
        cd $$tool; make clean; cd ..; \
	  done; \
	  rm -rf *~ \#*; \
	fi; \
	echo "";

