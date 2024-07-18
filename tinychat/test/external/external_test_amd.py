import unittest
from tinygrad import Device, Tensor
from tinygrad.engine.schedule import create_schedule
from tinygrad.runtime.ops_amd import AMDDevice

class TestAMD(unittest.TestCase):
  @classmethod
  def setUpClass(self):
    TestAMD.d0: AMDDevice = Device["AMD"]
    TestAMD.a = Tensor([0.,1.], device="AMD").realize()
    TestAMD.b = self.a + 1
    si = create_schedule([self.b.lazydata])[-1]
    TestAMD.d0_runner = TestAMD.d0.get_runner(*si.ast)
    TestAMD.b.lazydata.buffer.allocate()

  def test_amd_ring_64bit_doorbell(self):
    TestAMD.d0.pm4_write_pointer[0] = TestAMD.d0.pm4_write_pointer[0] + (2 << 32) - TestAMD.d0.pm4_ring.size // 4
    for _ in range(2000):
      TestAMD.d0_runner.clprg(TestAMD.b.lazydata.buffer._buf, TestAMD.a.lazydata.buffer._buf,
                              global_size=TestAMD.d0_runner.global_size, local_size=TestAMD.d0_runner.local_size)
      TestAMD.d0_runner.clprg(TestAMD.a.lazydata.buffer._buf, TestAMD.b.lazydata.buffer._buf,
                              global_size=TestAMD.d0_runner.global_size, local_size=TestAMD.d0_runner.local_size)
    assert (val:=TestAMD.a.lazydata.buffer.as_buffer().cast("f")[0]) == 4000.0, f"got val {val}"

if __name__ == "__main__":
  unittest.main()

