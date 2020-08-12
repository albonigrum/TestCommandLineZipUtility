import os
import subprocess
import unittest
from pathlib import Path
import filecmp
import shutil


def size_of_directory(directory_path):
    path = Path(directory_path)
    return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())


class TestZip(unittest.TestCase):
    NAME_OF_ZIP_PROGRAM = "zip"
    NAME_OF_UNZIP_PROGRAM = "unzip"
    EXTENSION_OF_ZIPPED_FILE = "zip"
    FILE_TO_ZIP = "resources/skynet-master/monitor_envoy_stats.py"
    DIR_TO_ZIP = "resources/skynet-master"
    ZIP_ARCHIVE = "resources/skynet-master.zip"
    ANOTHER_ZIP_ARCHIVE = "resources/skynet-master_win_rar.zip"
    DIR_WITH_DELETED_FILES = "resources/skynet-master_with_deleted_files"
    TMP_DIR_NAME = "tmp"

    class TmpFolderHandler:
        def __enter__(self):
            tmp_dir_ = Path("./" + TestZip.TMP_DIR_NAME)
            if not tmp_dir_.is_dir():
                tmp_dir_.mkdir()
            return tmp_dir_

        def __exit__(self, exc_type, exc_val, exc_tb):
            try:
                shutil.rmtree(Path("./" + TestZip.TMP_DIR_NAME).__str__())
            except FileNotFoundError:
                pass

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
    def test_should_zip_unzip_object_by_path(self):
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

                with self.TmpFolderHandler() as path_tmp_dir_:
                    path_ = Path(path_to_object)
                    path_tmp_dir = path_tmp_dir_.__str__()

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

                contents_cwd_after = []
                for c in cwd_.iterdir():
                    contents_cwd_after.append(c.__str__())

                self.assertEqual(contents_cwd_before, contents_cwd_after,
                                 'contents before zip and unzip not same than after')

    def test_should_zip_unzip_file_with_password(self):
        with self.TmpFolderHandler() as path_tmp_dir_:
            path_ = Path(self.FILE_TO_ZIP).absolute()
            path_tmp_dir = path_tmp_dir_.__str__()

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

    def test_should_not_unzip_file_with_incorrect_password(self):
        with self.TmpFolderHandler() as path_tmp_dir_:
            path_ = Path(self.FILE_TO_ZIP).absolute()
            path_tmp_dir = path_tmp_dir_.__str__()

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

    def test_should_delete_file_from_zip_archive(self):
        with self.TmpFolderHandler() as path_tmp_dir_:
            path_ = Path(self.ZIP_ARCHIVE).absolute()
            self.assertTrue(path_.is_file(), 'there is not file ' + self.ZIP_ARCHIVE)

            zip_archive_name = path_.parts[-1]

            path_tmp_dir = path_tmp_dir_.__str__()

            path_zip_archive_in_tmp = Path(path_tmp_dir + "/" + zip_archive_name)

            shutil.copyfile(path_.__str__(), path_zip_archive_in_tmp.__str__())

            completed_process = subprocess.run([self.NAME_OF_ZIP_PROGRAM,
                                                "-d", zip_archive_name,
                                                "*.py", Path("skynet-master/README.md").__str__()],
                                               cwd=path_tmp_dir,
                                               stdout=subprocess.DEVNULL,
                                               stderr=subprocess.DEVNULL)

            self.assertEqual(0, completed_process.returncode, 'return code of deleting files from zip not zero')

            completed_process = subprocess.run([self.NAME_OF_UNZIP_PROGRAM,
                                                zip_archive_name],
                                               cwd=path_tmp_dir,
                                               stdout=subprocess.DEVNULL,
                                               stderr=subprocess.DEVNULL)

            self.assertEqual(0, completed_process.returncode,
                             'return code of unzip zip file with deleted files not zero')

            # Удаляем zip'ник чтобы можно было сравнить содержимое директорий
            path_zip_archive_in_tmp.unlink()

            self.assertEqual([], filecmp.dircmp(self.DIR_WITH_DELETED_FILES, path_tmp_dir).diff_files,
                             'expected folder and unzipped folder after deleting files not equal')

    # should unzip archive have made by another program
    def test_should_unzip_another_zip(self):
        with self.TmpFolderHandler() as path_tmp_dir_:
            path_ = Path(self.ANOTHER_ZIP_ARCHIVE).absolute()
            path_tmp_dir = path_tmp_dir_.__str__()

            another_zip = path_.parts[-1]

            path_zip_archive_in_tmp = Path(path_tmp_dir + "/" + another_zip)

            shutil.copyfile(path_.__str__(), path_zip_archive_in_tmp.__str__())

            completed_process = subprocess.run([self.NAME_OF_UNZIP_PROGRAM,
                                                another_zip],
                                               cwd=path_tmp_dir,
                                               stdout=subprocess.DEVNULL)

            self.assertEqual(0, completed_process.returncode, 'return code of unzip not zero')

            # Удаляем zip'ник чтобы можно было сравнить содержимое директорий
            path_zip_archive_in_tmp.unlink()

            self.assertEqual([], filecmp.dircmp(self.DIR_TO_ZIP, path_tmp_dir).diff_files,
                             'expected folder and unzipped folder after deleting files not equal')


class Test7Zip(TestZip):
    NAME_OF_ZIP_PROGRAM = "7z"
    COMMAND_TO_ADD_FILES_TO_ARCHIVE = "a"
    ZIP_ADDITIONAL_SWITCHES = "-tzip"
    COMMAND_TO_UNZIP = "x"
    COMMAND_TO_DELETE_FILES_FROM_ARCHIVE = "d"

    # path_..._ (ends with _) it is some Path object
    # path_... (ends not with _) it is string path
    def test_should_zip_unzip_object_by_path(self):
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

                with self.TmpFolderHandler() as path_tmp_dir_:
                    path_ = Path(path_to_object)
                    path_tmp_dir = path_tmp_dir_.__str__()

                    is_file = path_.is_file()
                    is_absolute_path = path_.is_absolute()
                    relative_path_from_tmp = None
                    if not is_absolute_path:
                        relative_path_from_tmp = Path("../" + path_to_object).__str__()

                    object_name = path_.parts[-1]
                    object_name_with_zip = object_name + "." + self.EXTENSION_OF_ZIPPED_FILE

                    args = [self.NAME_OF_ZIP_PROGRAM, self.COMMAND_TO_ADD_FILES_TO_ARCHIVE,
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

                contents_cwd_after = []
                for c in cwd_.iterdir():
                    contents_cwd_after.append(c.__str__())

                self.assertEqual(contents_cwd_before, contents_cwd_after,
                                 'contents before zip and unzip not same than after')

    def test_should_zip_unzip_file_with_password(self):
        with self.TmpFolderHandler() as path_tmp_dir_:
            path_ = Path(self.FILE_TO_ZIP).absolute()
            path_tmp_dir = path_tmp_dir_.__str__()

            object_name = path_.parts[-1]
            object_name_with_zip = object_name + "." + self.EXTENSION_OF_ZIPPED_FILE

            password = "DSfSDFfsdfdsfdfe32342"

            completed_process = subprocess.run([self.NAME_OF_ZIP_PROGRAM,
                                                self.COMMAND_TO_ADD_FILES_TO_ARCHIVE,
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

    def test_should_not_unzip_file_with_incorrect_password(self):
        with self.TmpFolderHandler() as path_tmp_dir_:
            path_ = Path(self.FILE_TO_ZIP).absolute()
            path_tmp_dir = path_tmp_dir_.__str__()

            object_name = path_.parts[-1]
            object_name_with_zip = object_name + "." + self.EXTENSION_OF_ZIPPED_FILE

            password = "DSfSDFfsdfdsfdfe32342"
            incorrect_password = password + "0"

            completed_process = subprocess.run([self.NAME_OF_ZIP_PROGRAM,
                                                self.COMMAND_TO_ADD_FILES_TO_ARCHIVE,
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

    def test_should_delete_file_from_zip_archive(self):
        with self.TmpFolderHandler() as path_tmp_dir_:
            path_ = Path(self.ZIP_ARCHIVE).absolute()
            self.assertTrue(path_.is_file(), 'there is not file ' + self.ZIP_ARCHIVE)

            zip_archive_name = path_.parts[-1]

            path_tmp_dir = path_tmp_dir_.__str__()

            path_zip_archive_in_tmp = Path(path_tmp_dir + "/" + zip_archive_name)

            shutil.copyfile(path_.__str__(), path_zip_archive_in_tmp.__str__())

            completed_process = subprocess.run([self.NAME_OF_ZIP_PROGRAM,
                                                self.COMMAND_TO_DELETE_FILES_FROM_ARCHIVE,
                                                zip_archive_name,
                                                "*.py", Path("skynet-master/README.md").__str__()],
                                               cwd=path_tmp_dir,
                                               stdout=subprocess.DEVNULL,
                                               stderr=subprocess.DEVNULL)

            self.assertEqual(0, completed_process.returncode, 'return code of deleting files from zip not zero')

            completed_process = subprocess.run([self.NAME_OF_ZIP_PROGRAM,
                                                self.COMMAND_TO_UNZIP,
                                                zip_archive_name],
                                               cwd=path_tmp_dir,
                                               stdout=subprocess.DEVNULL,
                                               stderr=subprocess.DEVNULL)

            self.assertEqual(0, completed_process.returncode,
                             'return code of unzip zip file with deleted files not zero')

            # Удаляем zip'ник чтобы можно было сравнить содержимое директорий
            path_zip_archive_in_tmp.unlink()

            self.assertEqual([], filecmp.dircmp(self.DIR_WITH_DELETED_FILES, path_tmp_dir).diff_files,
                             'expected folder and unzipped folder after deleting files not equal')

    # should unzip archive have made by another program
    def test_should_unzip_another_zip(self):
        with self.TmpFolderHandler() as path_tmp_dir_:
            path_ = Path(self.ANOTHER_ZIP_ARCHIVE).absolute()
            path_tmp_dir = path_tmp_dir_.__str__()

            another_zip = path_.parts[-1]

            path_zip_archive_in_tmp = Path(path_tmp_dir + "/" + another_zip)

            shutil.copyfile(path_.__str__(), path_zip_archive_in_tmp.__str__())

            completed_process = subprocess.run([self.NAME_OF_ZIP_PROGRAM,
                                                self.COMMAND_TO_UNZIP,
                                                another_zip],
                                               cwd=path_tmp_dir,
                                               stdout=subprocess.DEVNULL)

            self.assertEqual(0, completed_process.returncode, 'return code of unzip not zero')

            # Удаляем zip'ник чтобы можно было сравнить содержимое директорий
            path_zip_archive_in_tmp.unlink()

            self.assertEqual([], filecmp.dircmp(self.DIR_TO_ZIP, path_tmp_dir).diff_files,
                             'expected folder and unzipped folder after deleting files not equal')


if __name__ == "__main__":

    TestToTest = None
    if os.name == "nt":
        TestToTest = Test7Zip
    elif os.name == "posix":
        TestToTest = TestZip

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestToTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
