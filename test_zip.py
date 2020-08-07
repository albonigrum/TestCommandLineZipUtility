import os
import subprocess
import unittest
from pathlib import Path
import filecmp
import shutil


def size_of_directory(directory):
    path = Path(directory)
    return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())


class TestZip(unittest.TestCase):
    NAME_OF_ZIP_PROGRAM = "zip"
    NAME_OF_UNZIP_PROGRAM = "unzip"
    EXTENSION_OF_ZIPPED_FILE = "zip"
    FILE_TO_ZIP = "resources/skynet-master/monitor_envoy_stats.py"
    DIR_TO_ZIP = "resources/skynet-master"
    TMP_DIR_NAME = "tmp"

    @staticmethod
    def delete_tmp_folder():
        try:
            shutil.rmtree(Path("./" + TestZip.TMP_DIR_NAME).__str__())
        except FileNotFoundError:
            pass

    @staticmethod
    def create_tmp_folder():
        tmp_dir_obj = Path("./" + TestZip.TMP_DIR_NAME)
        if not tmp_dir_obj.is_dir():
            tmp_dir_obj.mkdir()

    def test_should_open(self):
        completed_process = subprocess.run([self.NAME_OF_ZIP_PROGRAM],
                                           stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL,
                                           stdin=subprocess.DEVNULL)  # Без этой строчки зависает, требуя непонятно чего
        self.assertEqual(0, completed_process.returncode, 'return code not zero')

    def test_should_have_keys(self):
        keys = ["-h", "--help"]
        for key in keys:
            with self.subTest(msg=self.NAME_OF_ZIP_PROGRAM + " run with key [" + key + "]"):
                completed_process = subprocess.run([self.NAME_OF_ZIP_PROGRAM, key],
                                                   stdout=subprocess.DEVNULL)
                self.assertEqual(0, completed_process.returncode, 'return code not zero')

    # path_..._ (ends with _) it is some Path object
    # path_... (ends not with _) it is string path
    def test_should_zip_unzip_file_by_path(self):
        try:
            path_objects_to_zip = [
                Path(self.FILE_TO_ZIP).__str__(),
                Path(self.DIR_TO_ZIP).__str__(),
                Path(self.FILE_TO_ZIP).absolute().__str__(),
                Path(self.DIR_TO_ZIP).absolute().__str__()
            ]

            for path_to_object in path_objects_to_zip:
                with self.subTest(msg="test zip by path to object: " + path_to_object):
                    cwd_ = Path(".")
                    contents_cwd_before = []
                    for c in cwd_.iterdir():
                        contents_cwd_before.append(c.__str__())

                    self.create_tmp_folder()

                    path_ = Path(path_to_object)
                    path_tmp_dir = Path(cwd_.__str__() + "/" + self.TMP_DIR_NAME).__str__()

                    is_file = path_.is_file()
                    is_absolute_path = path_.is_absolute()
                    relative_path_from_tmp = None
                    if not is_absolute_path:
                        relative_path_from_tmp = Path("../" + path_to_object).__str__()

                    object_name = path_.parts[-1]
                    object_name_with_zip = object_name + "." + self.EXTENSION_OF_ZIPPED_FILE

                    args = [self.NAME_OF_ZIP_PROGRAM, "-r", "-j", "-9", object_name_with_zip]
                    if is_absolute_path:
                        args.append(path_to_object)
                    else:
                        args.append(relative_path_from_tmp)

                    completed_process = subprocess.run(args,
                                                       cwd=path_tmp_dir,
                                                       stdout=subprocess.DEVNULL)

                    self.assertEqual(0, completed_process.returncode, 'return code of zip not zero')

                    path_to_zipped_file_ = Path(path_tmp_dir + "/" + object_name_with_zip)

                    self.assertTrue(path_to_zipped_file_.is_file(), 'zip file not exists or not a file')

                    expected_size = path_.stat().st_size if is_file else size_of_directory(path_.__str__())
                    actual_size = path_to_zipped_file_.stat().st_size

                    self.assertGreater(expected_size, actual_size, 'size of zip file more than original')

                    with self.subTest(msg="test unzip file: " + object_name_with_zip):
                        args = [self.NAME_OF_UNZIP_PROGRAM, object_name_with_zip]
                        if not is_file:
                            args.extend(["-d", object_name])
                        completed_process = subprocess.run(args,
                                                           cwd=path_tmp_dir,
                                                           stdout=subprocess.DEVNULL)
                        self.assertEqual(0, completed_process.returncode, 'return code of unzip not zero')

                        path_to_unzipped_object = Path(path_tmp_dir + "/" + object_name).__str__()

                        if is_file:
                            self.assertTrue(filecmp.cmp(path_to_object, path_to_unzipped_object),
                                            'original file and unzipped file not equal')
                        else:
                            self.assertEqual([], filecmp.dircmp(path_to_object, path_to_unzipped_object).diff_files,
                                             'original folder and unzipped folder not equal')

                        self.delete_tmp_folder()

                        contents_cwd_after = []
                        for c in cwd_.iterdir():
                            contents_cwd_after.append(c.__str__())

                        self.assertEqual(contents_cwd_before, contents_cwd_after,
                                         'contents before zip and unzip not same than after')
        finally:
            self.delete_tmp_folder()

    def test_should_zip_unzip_file_with_password(self):
        self.create_tmp_folder()
        try:
            path_ = Path(self.FILE_TO_ZIP).absolute()
            path_tmp_dir = Path(Path(".").absolute().__str__() + "/" + self.TMP_DIR_NAME).__str__()

            object_name = path_.parts[-1]
            object_name_with_zip = object_name + "." + self.EXTENSION_OF_ZIPPED_FILE

            password = "DSfSDFfsdfdsfdfe32342"

            completed_process = subprocess.run([self.NAME_OF_ZIP_PROGRAM,
                                                "-P", password,
                                                "-r", "-j", "-9",
                                                object_name_with_zip,
                                                path_.__str__()],
                                               cwd=path_tmp_dir,
                                               stdout=subprocess.DEVNULL)

            self.assertEqual(0, completed_process.returncode, 'return code of zip not zero')

            with self.subTest(msg="test unzip file: " + object_name_with_zip + " with password: " + password):
                completed_process = subprocess.run([self.NAME_OF_UNZIP_PROGRAM,
                                                    "-P", password,
                                                    object_name_with_zip],
                                                   cwd=path_tmp_dir,
                                                   stdout=subprocess.DEVNULL)

                self.assertEqual(0, completed_process.returncode, 'return code of unzip not zero')
        finally:
            self.delete_tmp_folder()

    def test_should_not_unzip_file_with_incorrect_password(self):
        self.create_tmp_folder()
        try:
            path_ = Path(self.FILE_TO_ZIP).absolute()
            path_tmp_dir = Path(Path(".").absolute().__str__() + "/" + self.TMP_DIR_NAME).__str__()

            object_name = path_.parts[-1]
            object_name_with_zip = object_name + "." + self.EXTENSION_OF_ZIPPED_FILE

            password = "DSfSDFfsdfdsfdfe32342"
            incorrect_password = password + "0"

            completed_process = subprocess.run([self.NAME_OF_ZIP_PROGRAM,
                                                "-P", password,
                                                "-r", "-j", "-9",
                                                object_name_with_zip,
                                                path_.__str__()],
                                               cwd=path_tmp_dir,
                                               stdout=subprocess.DEVNULL)

            self.assertEqual(0, completed_process.returncode, 'return code of zip not zero')

            with self.subTest(msg="test unzip file: " + object_name_with_zip + " with password: " + incorrect_password):
                completed_process = subprocess.run([self.NAME_OF_UNZIP_PROGRAM,
                                                    "-P", incorrect_password,
                                                    object_name_with_zip],
                                                   cwd=path_tmp_dir,
                                                   stdout=subprocess.DEVNULL,
                                                   stderr=subprocess.DEVNULL)

                self.assertNotEqual(0, completed_process.returncode, 'return code of incorrect unzip zero')
        finally:
            self.delete_tmp_folder()


class Test7Zip(TestZip):
    NAME_OF_ZIP_PROGRAM = "7z"
    COMMAND_TO_ZIP = "a"
    ZIP_ADDITIONAL_SWITCHES = "-tzip"
    COMMAND_TO_UNZIP = "x"

    # path_..._ (ends with _) it is some Path object
    # path_... (ends not with _) it is string path
    def test_should_zip_unzip_file_by_path(self):
        try:
            path_objects_to_zip = [
                Path(self.FILE_TO_ZIP).__str__(),
                Path(self.DIR_TO_ZIP).__str__(),
                Path(self.FILE_TO_ZIP).absolute().__str__(),
                Path(self.DIR_TO_ZIP).absolute().__str__()
            ]

            for path_to_object in path_objects_to_zip:
                with self.subTest(msg="test zip by path to object: " + path_to_object):
                    cwd_ = Path(".")
                    contents_cwd_before = []
                    for c in cwd_.iterdir():
                        contents_cwd_before.append(c.__str__())

                    self.create_tmp_folder()

                    path_ = Path(path_to_object)
                    path_tmp_dir = Path(cwd_.__str__() + "/" + self.TMP_DIR_NAME).__str__()

                    is_file = path_.is_file()
                    is_absolute_path = path_.is_absolute()
                    relative_path_from_tmp = None
                    if not is_absolute_path:
                        relative_path_from_tmp = Path("../" + path_to_object).__str__()

                    object_name = path_.parts[-1]
                    object_name_with_zip = object_name + "." + self.EXTENSION_OF_ZIPPED_FILE

                    args = [self.NAME_OF_ZIP_PROGRAM, self.COMMAND_TO_ZIP,
                            self.ZIP_ADDITIONAL_SWITCHES, object_name_with_zip]
                    if is_absolute_path:
                        args.append(path_to_object)
                    else:
                        args.append(relative_path_from_tmp)

                    completed_process = subprocess.run(args,
                                                       cwd=path_tmp_dir,
                                                       stdout=subprocess.DEVNULL)

                    self.assertEqual(0, completed_process.returncode, 'return code of zip not zero')

                    path_to_zipped_file_ = Path(path_tmp_dir + "/" + object_name_with_zip)

                    self.assertTrue(path_to_zipped_file_.is_file(), 'zip file not exists or not a file')

                    expected_size = path_.stat().st_size if is_file else size_of_directory(path_.__str__())
                    actual_size = path_to_zipped_file_.stat().st_size

                    self.assertGreater(expected_size, actual_size, 'size of zip file more than original')

                    with self.subTest(msg="test unzip file: " + object_name_with_zip):
                        args = [self.NAME_OF_ZIP_PROGRAM, self.COMMAND_TO_UNZIP, object_name_with_zip]
                        completed_process = subprocess.run(args,
                                                           cwd=path_tmp_dir,
                                                           stdout=subprocess.DEVNULL)

                        self.assertEqual(0, completed_process.returncode, 'return code of unzip not zero')

                        path_to_unzipped_object = Path(path_tmp_dir + "/" + object_name).__str__()

                        if is_file:
                            self.assertTrue(filecmp.cmp(path_to_object, path_to_unzipped_object),
                                            'original file and unzipped file not equal')
                        else:
                            self.assertEqual([], filecmp.dircmp(path_to_object, path_to_unzipped_object).diff_files,
                                             'original folder and unzipped folder not equal')

                        self.delete_tmp_folder()

                        contents_cwd_after = []
                        for c in cwd_.iterdir():
                            contents_cwd_after.append(c.__str__())

                        self.assertEqual(contents_cwd_before, contents_cwd_after,
                                         'contents before zip and unzip not same than after')
        finally:
            self.delete_tmp_folder()

    def test_should_zip_unzip_file_with_password(self):
        self.create_tmp_folder()
        try:
            path_ = Path(self.FILE_TO_ZIP).absolute()
            path_tmp_dir = Path(Path(".").absolute().__str__() + "/" + self.TMP_DIR_NAME).__str__()

            object_name = path_.parts[-1]
            object_name_with_zip = object_name + "." + self.EXTENSION_OF_ZIPPED_FILE

            password = "DSfSDFfsdfdsfdfe32342"

            completed_process = subprocess.run([self.NAME_OF_ZIP_PROGRAM,
                                                self.COMMAND_TO_ZIP,
                                                self.ZIP_ADDITIONAL_SWITCHES,
                                                "-p" + password,
                                                object_name_with_zip,
                                                path_.__str__()],
                                               cwd=path_tmp_dir,
                                               stdout=subprocess.DEVNULL)

            self.assertEqual(0, completed_process.returncode, 'return code of zip not zero')

            with self.subTest(msg="test unzip file: " + object_name_with_zip + " with password: " + password):
                completed_process = subprocess.run([self.NAME_OF_ZIP_PROGRAM,
                                                    "-p" + password,
                                                    self.COMMAND_TO_UNZIP,
                                                    object_name_with_zip],
                                                   cwd=path_tmp_dir,
                                                   stdout=subprocess.DEVNULL)

                self.assertEqual(0, completed_process.returncode, 'return code of unzip not zero')
        finally:
            self.delete_tmp_folder()

    def test_should_not_unzip_file_with_incorrect_password(self):
        self.create_tmp_folder()
        try:
            path_ = Path(self.FILE_TO_ZIP).absolute()
            path_tmp_dir = Path(Path(".").absolute().__str__() + "/" + self.TMP_DIR_NAME).__str__()

            object_name = path_.parts[-1]
            object_name_with_zip = object_name + "." + self.EXTENSION_OF_ZIPPED_FILE

            password = "DSfSDFfsdfdsfdfe32342"
            incorrect_password = password + "0"

            completed_process = subprocess.run([self.NAME_OF_ZIP_PROGRAM,
                                                self.COMMAND_TO_ZIP,
                                                self.ZIP_ADDITIONAL_SWITCHES,
                                                "-p" + password,
                                                object_name_with_zip,
                                                path_.__str__()],
                                               cwd=path_tmp_dir,
                                               stdout=subprocess.DEVNULL)

            self.assertEqual(0, completed_process.returncode, 'return code of zip not zero')

            with self.subTest(msg="test unzip file: " + object_name_with_zip + " with password: " + incorrect_password):
                completed_process = subprocess.run([self.NAME_OF_ZIP_PROGRAM,
                                                    "-p" + incorrect_password,
                                                    self.COMMAND_TO_UNZIP,
                                                    object_name_with_zip],
                                                   cwd=path_tmp_dir,
                                                   stdout=subprocess.DEVNULL,
                                                   stderr=subprocess.DEVNULL)

                self.assertNotEqual(0, completed_process.returncode, 'return code of incorrect unzip zero')
        finally:
            self.delete_tmp_folder()


if __name__ == "__main__":

    TestToTest = None
    if os.name == "nt":
        TestToTest = Test7Zip
    elif os.name == "posix":
        TestToTest = TestZip

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestToTest)
    unittest.TextTestRunner().run(suite)
