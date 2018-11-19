#!/usr/bin/python

import argparse
import datetime
import json
import logging
import os
import shutil
import socket


class PurgeRemoteFolders(object):

    def __init__(self, biotank_archive_folder, age_in_days, dryrun):
        self.biotank_archive_folder = str(biotank_archive_folder)
        self.age_in_days = int(age_in_days)
        self.dryrun = bool(dryrun)

        hostname = socket.gethostname()
        self.directory = self.sanitize_path(
            self.biotank_archive_folder,
            os.path.join(
                "/data",
                hostname))
        self.logfile = os.path.join(self.directory, "KEEP_removed_archives.log")

    @staticmethod
    def sanitize_path(dirty_path, directory):
        if os.path.isabs(dirty_path):
            raise ValueError(
                "{p} is an absolute path which is not allowed at this point".format(
                    p=dirty_path))
        # fully resolve path to make sure that no symlinks or upward references are left and cause surprises
        clean_path = os.path.realpath(
            os.path.join(directory, dirty_path))
        # ensure that the resulting path is below the directory
        if not clean_path.startswith(directory):
            raise ValueError(
                "{p} appears to resolve to a path outside of {d} which is not allowed at this point".format(
                    p=dirty_path, d=directory))
        return clean_path

    def get_files_and_folders(self):
        older_than = datetime.date.today() - datetime.timedelta(days=self.age_in_days)

        def _path_should_be_purged(p):
            return datetime.date.fromtimestamp(
                os.stat(
                    os.path.join(
                        self.directory, p)).st_mtime) < older_than and not p.startswith("KEEP")

        return filter(
            _path_should_be_purged,
            os.listdir(self.directory))

    def purge_files_and_folders(self, files_and_folders_to_purge, logger):

        def _purge_path(p):
            purge_fn = shutil.rmtree if os.path.isdir(p) else os.unlink
            if not self.dryrun:
                purge_fn(p)
                logger.info(p)

        map(
            _purge_path,
            map(
                lambda p: self.sanitize_path(p, self.directory),
                files_and_folders_to_purge))

    def purge(self, logger):

        try:
            files_and_folders_to_purge = self.get_files_and_folders()
        except Exception as e:
            print(
                "encountered the following error when trying to determine files and folders to purge: {msg}".format(msg=e))
            raise

        try:
            self.purge_files_and_folders(files_and_folders_to_purge, logger)
        except Exception as e:
            print(
                "encountered the following error when trying to purge files and folders: {msg}".format(msg=e))
            raise

        return files_and_folders_to_purge


def main():

    parser = argparse.ArgumentParser(
        description="Purge archived runfolders from biotanks based on age")

    # Required arguments
    parser.add_argument(
        "--biotank_archive_folder",
        required=True,
        help="Path to the folder for archived runfolders, relative to the host-specific data path")
    parser.add_argument(
        "--age_in_days",
        required=True,
        help="Files and folders that haven't been modified in this many days will be removed")
    parser.add_argument(
        "--dryrun",
        required=False,
        action="store_true",
        help="If true, only a dry-run will be performed and nothing is removed")
    parser.set_defaults(dryrun=False)
    args = parser.parse_args()

    cleaner = PurgeRemoteFolders(args.biotank_archive_folder, args.age_in_days, args.dryrun)

    execution_id = os.environ.get("ST2_ACTION_EXECUTION_ID", "")
    # create logger
    logger = logging.getLogger("purge_remote_folder")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s,%(asctime)s,{id}'.format(id=execution_id))
    ch = logging.FileHandler(cleaner.logfile, delay=True)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    result_as_json = cleaner.purge(logger)
    print(json.dumps(result_as_json))


if __name__ == '__main__':
    main()
