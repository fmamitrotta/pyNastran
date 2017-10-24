from __future__ import print_function
import os
import unittest
from six.moves import range
from numpy import array_equal, allclose

import pyNastran
from pyNastran.converters.panair.panair_grid import PanairGrid
from pyNastran.utils.log import get_logger

PKG_PATH = pyNastran.__path__[0]
TEST_PATH = os.path.join(PKG_PATH, 'converters', 'panair')


class TestPanair(unittest.TestCase):

    def test_panair_io_01(self):
        log = get_logger(level='warning')
        in_filename = os.path.join(TEST_PATH, 'M100', 'M100.inp')
        out_filename = os.path.join(TEST_PATH, 'M100', 'M100_out.inp')
        #with open(infile_name, 'w') as f:
            #f.write(lines)

        model = PanairGrid(log=log, debug=False)
        model.read_panair(in_filename)
        #assert len(cart3d.points) == 7, 'npoints=%s' % len(cart3d.points)
        #assert len(cart3d.elements) == 6, 'nelements=%s' % len(cart3d.elements)
        #assert len(cart3d.regions) == 6, 'nregions=%s' % len(cart3d.regions)
        #assert len(cart3d.loads) == 0, 'nloads=%s' % len(cart3d.loads)
        model.write_panair(out_filename)
        (points, elements, regions, kt, cp_nrom) = model.get_points_elements_regions()
        os.remove(out_filename)


if __name__ == '__main__':  # pragma: no cover
    import time
    time0 = time.time()
    unittest.main()
    print("dt = %s" % (time.time() - time0))
