import unittest
import vpk
import os
import errno
import shutil

def mktree(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass


class testcase_vpk(unittest.TestCase):
    def setUp(self):
        self.pak = vpk.open('./tests/test_dir.vpk')

    def test_verify_file_crc32(self):
        for path in self.pak:
            self.assertTrue(self.pak[path].verify())

    def test_file_count_as_list(self):
        self.assertTrue(len(self.pak) == len(list(self.pak)))

    def test_file_count_as_dict(self):
        self.assertTrue(len(self.pak) == len(dict(self.pak.items())))

    def test_testfile1_txt(self):
        with self.pak["testfile1.txt"] as f:
            for i, line in enumerate(f.readlines(), start=1):
                self.assertEqual("line {0}".format(i).encode(), line.rstrip())

    def test_testfile2_txt(self):
        i = 1
        for line in self.pak["testdir/testfile2.txt"]:
            self.assertEqual("line {0}".format(i).encode(), line.rstrip())
            i += 1

    def test_testfile3_bin(self):
        self.assertEqual(b"OK", self.pak["a/b/c/d/testfile3.bin"].readline())


class testcase_newvpk(unittest.TestCase):
    def setUp(self):
        self.pak = vpk.open('./tests/test_dir.vpk')

    def test_vpk_creation(self):
        temp = "./tempout"

        for path in self.pak:
            mktree(os.path.join(temp, *os.path.split(path)[:-1]))

            self.pak[path].save(os.path.join(temp, path))

        pak = vpk.new(temp)
        newpak = pak.save_and_open(os.path.join(temp, "temp.vpk"))

        for path in newpak:
            self.assertTrue(newpak[path].verify())

        if os.path.exists(temp):
            shutil.rmtree(temp)



