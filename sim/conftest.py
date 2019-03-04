#=========================================================================
# conftest
#=========================================================================

import pytest
import random

#-------------------------------------------------------------------------
# pytest_addoption
#-------------------------------------------------------------------------

def pytest_addoption(parser):

  parser.addoption( "--dump-vcd", action="store_true",
                    help="dump vcd for each test" )

  parser.addoption( "--dump-asm", action="store_true",
                    help="dump asm file for each test" )

  parser.addoption( "--dump-bin", action="store_true",
                    help="dump binary file for each test" )

  parser.addoption( "--test-verilog", action="store",
                    default='', nargs='?', const='zeros',
                    choices=[ '', 'zeros', 'ones', 'rand' ],
                    help="run verilog translation" )

  parser.addoption( "--prtl", action="store_true",
                    help="use PRTL implementations" )

  parser.addoption( "--vrtl", action="store_true",
                    help="use VRTL implementations" )

#-------------------------------------------------------------------------
# handle command line options
#-------------------------------------------------------------------------

@pytest.fixture()
def dump_vcd(request):
  """Dump VCD for each test."""
  if request.config.option.dump_vcd:
    test_module = request.module.__name__
    test_name   = request.node.name
    return '{}.{}.vcd'.format( test_module, test_name )
  else:
    return ''

@pytest.fixture()
def dump_asm(request):
  """Dump Assembly File for each test."""
  return request.config.option.dump_asm

@pytest.fixture()
def dump_bin(request):
  """Dump Binary File for each test."""
  return request.config.option.dump_bin

@pytest.fixture
def test_verilog(request):
  """Test Verilog translation rather than python."""
  return request.config.option.test_verilog

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

def pytest_cmdline_preparse(config, args):
  """Don't write *.pyc and __pycache__ files."""
  import sys
  sys.dont_write_bytecode = True

def pytest_runtest_setup(item):
  test_verilog = item.config.option.test_verilog
  if test_verilog and 'test_verilog' not in item.funcargnames:
    pytest.skip("ignoring non-Verilog tests")

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

