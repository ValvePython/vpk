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
            with self.pak[path] as f:
                self.assertTrue(f.verify())

    def test_file_count_as_list(self):
        print(repr(list(self.pak)))
        self.assertTrue(len(self.pak) == len(list(self.pak)))

    def test_file_count_as_dict(self):
        self.assertTrue(len(self.pak) == len(dict(self.pak.items())))

    def test_testfile1_txt(self):
        with self.pak["testfile1.txt"] as f:
            for i, line in enumerate(f.readlines(), start=1):
                self.assertEqual("line {0}".format(i).encode(), line.rstrip())

    def test_testfile2_txt(self):
        with self.pak["testdir/testfile2.txt"] as f:
            i = 1
            for line in f:
                self.assertEqual("line {0}".format(i).encode(), line.rstrip())
                i += 1

    def test_testfile3_bin(self):
        with self.pak["a/b/c/d/testfile3.bin"] as f:
            self.assertEqual(b"OK", f.readline())

    def test_filepath_type(self):
        self.assertIsInstance(list(self.pak)[0], str)

class testcase_vpk_bytes(unittest.TestCase):
    def setUp(self):
        self.pak = vpk.open('./tests/test_dir.vpk', path_enc=None)

    def test_verify_file_crc32(self):
        for path in self.pak:
            with self.pak[path] as f:
                self.assertTrue(f.verify())

    def test_file_count_as_list(self):
        print(repr(list(self.pak)))
        self.assertTrue(len(self.pak) == len(list(self.pak)))

    def test_file_count_as_dict(self):
        self.assertTrue(len(self.pak) == len(dict(self.pak.items())))

    def test_testfile1_txt(self):
        with self.pak[b"testfile1.txt"] as f:
            for i, line in enumerate(f.readlines(), start=1):
                self.assertEqual("line {0}".format(i).encode(), line.rstrip())

    def test_testfile2_txt(self):
        with self.pak[b"testdir/testfile2.txt"] as f:
            i = 1
            for line in f:
                self.assertEqual("line {0}".format(i).encode(), line.rstrip())
                i += 1

    def test_testfile3_bin(self):
        with self.pak[b"a/b/c/d/testfile3.bin"] as f:
            self.assertEqual(b"OK", f.readline())

    def test_filepath_type(self):
        self.assertIsInstance(list(self.pak)[0], bytes)

class testcase_newvpk(unittest.TestCase):
    def setUp(self):
        self.pak = vpk.open('./tests/test_dir.vpk')
        self.temp_path = "./tempout"

    def test_vpk_creation(self):
        temp = self.temp_path

        for path in self.pak:
            mktree(os.path.join(temp, *os.path.split(path)[:-1]))

            with self.pak[path] as f:
                f.save(os.path.join(temp, path))

        pak = vpk.new(temp)
        newpak = pak.save_and_open(os.path.join(temp, "temp.vpk"))

        for path in newpak:
            with newpak[path] as f:
                self.assertTrue(f.verify())

    def tearDown(self):
        if os.path.exists(self.temp_path):
            shutil.rmtree(self.temp_path)



