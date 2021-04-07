#=========================================================================
# conftest
#=========================================================================

import pytest
import random

#-------------------------------------------------------------------------
# pytest_addoption
#-------------------------------------------------------------------------

def pytest_addoption(parser):

  parser.addoption( "--prtl", action="store_true",
                    help="use PRTL implementations" )

  parser.addoption( "--vrtl", action="store_true",
                    help="use VRTL implementations" )

#-------------------------------------------------------------------------
# Handle other command line options
#-------------------------------------------------------------------------

def pytest_configure(config):
  import sys
  sys._called_from_test   = True
  sys._pymtl_rtl_override = False
  if config.option.prtl:
    sys._pymtl_rtl_override = 'pymtl'
  elif config.option.vrtl:
    sys._pymtl_rtl_override = 'verilog'

def pytest_unconfigure(config):
  import sys
  del sys._called_from_test
  del sys._pymtl_rtl_override

#-------------------------------------------------------------------------
# fix_randseed
#-------------------------------------------------------------------------

def pytest_report_header(config):
  if config.option.prtl:
    return "forcing RTL language to be pymtl"
  elif config.option.vrtl:
    return "forcing RTL language to be verilog"

#-------------------------------------------------------------------------
# fix_randseed
#-------------------------------------------------------------------------
# fix random seed to make tests reproducable

@pytest.fixture(autouse=True)
def fix_randseed():
  """Set the random seed prior to each test case."""
  random.seed(0xdeadbeef)

