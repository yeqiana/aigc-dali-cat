from __future__ import annotations
import concurrent.futures as cf,time,unittest
class PreimageParallelTest(unittest.TestCase):
 def test_real_threads_overlap(self):
  started=time.monotonic()
  with cf.ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(lambda _:time.sleep(.5),range(4)))
  self.assertLess(time.monotonic()-started,1.5)
