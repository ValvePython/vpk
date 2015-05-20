import unittest
import vpk


class testcase_vpk(unittest.TestCase):
    def setUp(self):
        self.pak = vpk.VPK('./tests/test_dir.vpk')

    def test_verify_file_crc32(self):
        pak = vpk.VPK('./tests/test_dir.vpk')

        for path in pak:
            self.assertTrue(pak.get_file(path).verify())

    def test_file_count_as_list(self):
        self.assertTrue(len(self.pak) == len(list(self.pak)))

    def test_file_count_as_dict(self):
        self.assertTrue(len(self.pak) == len(dict(self.pak.items())))

    def test_testfile1_txt(self):
        with self.pak.get_file("testfile1.txt") as f:
            for i, line in enumerate(f.readlines(), start=1):
                self.assertEqual("line {0}".format(i).encode(), line.rstrip())

    def test_testfile2_txt(self):
        f = self.pak.get_file("testdir/testfile2.txt")

        i = 1
        for line in f:
            self.assertEqual("line {0}".format(i).encode(), line.rstrip())
            i += 1

    def test_testfile3_bin(self):
        self.assertEqual(b"OK", self.pak.get_file("a/b/c/d/testfile3.bin").readline())
