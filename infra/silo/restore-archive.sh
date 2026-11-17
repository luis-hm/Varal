#!/bin/sh
# Restore only into an empty, separately provisioned Silo recovery volume.
# The caller must verify the deployed mount points before starting this script.
set -eu
umask 077

exec python3 - <<'PY'
import gzip
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tarfile
from pathlib import Path, PurePosixPath


class RestoreError(Exception):
    pass


def reject(message):
    raise RestoreError(message)


def positive_integer(name, default):
    value = os.environ.get(name, str(default))
    if not re.fullmatch(r"[0-9]+", value) or int(value) <= 0:
        reject("Invalid restore resource limit.")
    return int(value)


def normal_name(member):
    name = member.name
    if (
        not isinstance(name, str)
        or len(name) > 4096
        or "\\" in name
        or any(ord(char) < 32 or ord(char) == 127 for char in name)
    ):
        reject("Unsafe archive member path.")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        reject("Archive traversal or absolute path rejected.")
    parts = tuple(part for part in path.parts if part not in ("", "."))
    if any(":" in part for part in parts):
        reject("Ambiguous archive member path rejected.")
    if member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE):
        reject("Archive links, devices, or unsupported member types rejected.")
    if member.issparse() or any(key.startswith("GNU.sparse") for key in member.pax_headers):
        reject("Sparse archive members rejected.")
    if not parts and not member.isdir():
        reject("Invalid archive root member.")
    if member.size < 0 or (member.isdir() and member.size):
        reject("Invalid archive member size.")
    return parts


def require_empty(target):
    if target.is_symlink() or not target.is_dir():
        reject("Restore target must be an existing directory, not a symlink.")
    with os.scandir(target) as entries:
        if next(entries, None) is not None:
            reject("Restore target is not empty; refusing to overwrite any data.")


def open_directory(root_fd, parts):
    descriptor = os.dup(root_fd)
    try:
        for part in parts:
            try:
                os.mkdir(part, mode=0o700, dir_fd=descriptor)
                os.fsync(descriptor)
            except FileExistsError:
                pass
            child = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def main():
    volume_name = os.environ.get("SILO_RESTORE_VOLUME_NAME", "")
    if not re.fullmatch(r"varal-silo-restore-[a-z0-9][a-z0-9_.-]{0,100}", volume_name):
        reject("Restore volume name must use the varal-silo-restore- prefix.")
    filename = os.environ.get("SILO_BACKUP_FILENAME", "")
    if (
        not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,249}\.tar\.gz", filename)
        or ".." in filename
    ):
        reject("Select one explicit tar.gz backup basename; paths and globs are forbidden.")
    expected_hash = os.environ.get("SILO_BACKUP_EXPECTED_SHA256", "")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
        reject("An explicit expected backup SHA-256 is required.")
    max_members = positive_integer("SILO_RESTORE_MAX_MEMBERS", 100000)
    max_bytes = positive_integer("SILO_RESTORE_MAX_BYTES", 40 * 1024**3)
    min_free = positive_integer("SILO_RESTORE_MIN_FREE_BYTES", 1024**3)
    source_directory = Path("/backup")
    target = Path("/restore")
    if source_directory.is_symlink() or not source_directory.is_dir():
        reject("Backup directory is unavailable or is a symlink.")
    if os.path.samefile(source_directory, target):
        reject("Backup and restore directories must be separate.")
    require_empty(target)
    archive_path = source_directory / filename
    descriptor = os.open(archive_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            reject("Backup must be a regular file.")
        with os.fdopen(descriptor, "rb", closefd=False) as archive:
            digest = hashlib.file_digest(archive, "sha256").hexdigest()
            if digest != expected_hash.lower():
                reject("Backup SHA-256 mismatch; no extraction performed.")
            archive.seek(0)
            # Read through the gzip trailer, including CRC, before touching the target.
            with gzip.GzipFile(fileobj=archive, mode="rb") as compressed:
                decoded_bytes = 0
                while chunk := compressed.read(1024 * 1024):
                    decoded_bytes += len(chunk)
                    if decoded_bytes > max_bytes + max_members * 8192:
                        reject("Archive exceeds the configured decoded size limit.")
            archive.seek(0)
            members = {}
            regular_files = 0
            total_bytes = 0
            with tarfile.open(fileobj=archive, mode="r|gz") as bundle:
                for member in bundle:
                    parts = normal_name(member)
                    if parts in members:
                        reject("Duplicate archive destination rejected.")
                    members[parts] = member.isdir()
                    if len(members) > max_members:
                        reject("Archive exceeds the configured member limit.")
                    if member.isfile():
                        regular_files += 1
                        total_bytes += member.size
                        if total_bytes > max_bytes:
                            reject("Archive exceeds the configured unpacked size limit.")
            if not regular_files:
                reject("Backup has no regular files; refusing an empty restore.")
            for parts in members:
                for position in range(1, len(parts)):
                    if members.get(parts[:position]) is False:
                        reject("Archive file/directory path conflict rejected.")
            if shutil.disk_usage(target).free < total_bytes + min_free:
                reject("Insufficient free space for restore and configured safety reserve.")
            require_empty(target)
            archive.seek(0)
            root_fd = os.open(target, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            try:
                with tarfile.open(fileobj=archive, mode="r|gz") as bundle:
                    for member in bundle:
                        parts = normal_name(member)
                        if member.isdir():
                            directory_fd = open_directory(root_fd, parts)
                            os.fsync(directory_fd)
                            os.close(directory_fd)
                            continue
                        parent_fd = open_directory(root_fd, parts[:-1])
                        output_fd = None
                        try:
                            output_fd = os.open(
                                parts[-1],
                                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                                0o600,
                                dir_fd=parent_fd,
                            )
                            with bundle.extractfile(member) as source, os.fdopen(output_fd, "wb") as output:
                                output_fd = None
                                shutil.copyfileobj(source, output, length=1024 * 1024)
                                if output.tell() != member.size:
                                    reject("Truncated archive member rejected.")
                                output.flush()
                                os.fsync(output.fileno())
                            os.fsync(parent_fd)
                        finally:
                            if output_fd is not None:
                                os.close(output_fd)
                            os.close(parent_fd)
                os.fsync(root_fd)
            finally:
                os.close(root_fd)
            archive.seek(0)
            if hashlib.file_digest(archive, "sha256").hexdigest() != digest:
                reject("Backup changed during restore; do not start the restored service.")
    finally:
        os.close(descriptor)
    print(json.dumps({"status": "restored", "archive_sha256": digest, "regular_files": regular_files, "unpacked_bytes": total_bytes}))


try:
    main()
except RestoreError as error:
    print("Restore refused: " + str(error), file=sys.stderr)
    sys.exit(1)
except (OSError, EOFError, ValueError, tarfile.TarError) as error:
    # Exception text can contain archive-controlled names or filesystem information.
    print("Restore failed safely (" + type(error).__name__ + "); source was not changed.", file=sys.stderr)
    sys.exit(1)
PY
