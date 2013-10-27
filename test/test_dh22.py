
from __future__ import division, print_function, unicode_literals

import os
# import glob
# import subprocess
import unittest
import hashlib

# import numpy as np

from context import nutmeg


path_module = os.path.dirname(os.path.abspath(__file__))


class Test_Valid_Executables(unittest.TestCase):
    """
    Test ability to find and run application executable.
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_individual_conv(self):
        name = nutmeg.video.CONV
        val = nutmeg.video.assert_executable(name)

        self.assertTrue(val)

    def test_individual_probe(self):
        name = nutmeg.video.PROBE
        val = nutmeg.video.assert_executable(name)

        self.assertTrue(val)

    def test_individual_play(self):
        name = nutmeg.video.PLAY
        val = nutmeg.video.assert_executable(name)
        self.assertTrue(val)

    def test_all(self):
        val = nutmeg.video.assert_all_executables()
        self.assertTrue(val)


class Test_File_Info(unittest.TestCase):
    """
    Basic tests about extracting metadata from video file.
    """
    def setUp(self):
        self.fname_video_ref = os.path.join(path_module, 'example.mp4')

    def tearDown(self):
        pass

    def test_container_info_type(self):
        res = nutmeg.video.get_file_info(self.fname_video_ref)

        self.assertTrue(len(res) == 2)

        info_format, info_streams = res

        self.assertTrue(type(info_format) == dict)
        self.assertTrue(type(info_streams) == list)
        self.assertTrue(type(info_streams[0]) == dict)

    def test_container_info_keys(self):
        info_format, list_streams = nutmeg.video.get_file_info(self.fname_video_ref)

        keys_format = ['bit_rate', 'duration', 'filename', 'format_long_name', 'format_name',
                       'nb_streams', 'size', 'start_time']

        keys_stream = ['avg_frame_rate', 'codec_long_name', 'codec_name', 'codec_type', 'duration',
                       'height', 'width', 'nb_frames', 'pix_fmt']

        for k in keys_format:
            self.assertTrue(k in info_format)

        info_streams = list_streams[0]
        for k in keys_stream:
            self.assertTrue(k in info_streams)

    def test_container_info_reference_file(self):
        res = nutmeg.video.get_file_info(self.fname_video_ref)

        self.assertTrue(len(res) == 2)

        info_format, info_streams = res

        self.assertTrue(info_streams[0]['height'] == 256)
        self.assertTrue(info_streams[0]['width'] == 222)
        self.assertTrue(info_streams[0]['pix_fmt'] == 'yuvj420p')


class Test_Decode(unittest.TestCase):
    """
    Basic tests for decoding a video file.
    """
    def setUp(self):
        self.fname_video_ref = os.path.join(path_module, '2012-07-14 10.37.35.mp4')

    def tearDown(self):
        pass

    def test_decode(self):
        data = nutmeg.video.decode(self.fname_video_ref)

        h_0 = hashlib.sha512(data[0])
        h_1 = hashlib.sha512(data[1])
        h_2 = hashlib.sha512(data[2])

        v_0 = '26d7c0297c91b80b9d0f251bf2943d15570f25ca52d60d9c407f31d7e77e9b21d4312e1d9a8728188c68914241d4ccdf29e7d6a1a516d0903bd830fdb83338e1'
        v_1 = 'dcfdc50c6c2b4a6c2cb566b1262a41e6e1df728991fc05a07276e74a8842fb7776b2e652564d66a07615d18a22ef68d2aec6cc92e3ea02de851155b45a8cbc71'
        v_2 = '7f0cfdf01dfe4bc74d5593f8cbfcfdcb85b8c9d54b67a4a91c719735831f52bd0d87d2d3071d7dd5cb2d3dc587aecb1cbd4a0226e165954c90fd0c803ec16139'

        self.assertTrue(h_0.hexdigest() == v_0)
        self.assertTrue(h_1.hexdigest() == v_1)
        self.assertTrue(h_2.hexdigest() == v_2)

        self.assertTrue(data.shape[0] == 329)


    # def test_encode_decode(self):
        # num_frames = 300
        # num_lines = 50
        # num_samples = 80

        # data_orig = \
          # (np.random.uniform(size=(num_frames, num_lines, num_samples))*255).astype(np.uint8)

        # fname_video = self.name_work + '.mp4'
        # f = nutmeg.video.encode(fname_video, data_orig)

        # data_new = nutmeg.video.decode(fname_video)

        # # print('rms')
        # rms = np.sqrt(np.mean( (data_orig.astype(np.float) - data_new.astype(np.float))**2 ))

        # self.assertTrue(rms == 0)


# Standalone.
if __name__ == '__main__':
    unittest.main(verbosity=2)
