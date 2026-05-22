# SECTION 2: CUSTOM EXTENSION — SmartPath
#
# We subclass pathlib.Path to add:
#   1. safe_copy()        — copy a file with collision handling
#   2. checksum()         — compute MD5/SHA256 hash of file
#   3. word_count()       — count words in a text file
#   4. metadata()         — rich metadata dict (size, mtime, hash, type)
#   5. find_duplicates()  — find duplicate files in a directory tree
#   6. to_dict()          — serialise path info to a JSON-ready dict
#   7. backup()           — create timestamped backup of a file
#
# NOTE: Subclassing Path requires __new__ override (not __init__) because
# Path uses __new__ internally due to platform-specific class dispatch.

from pathlib import Path, PurePosixPath, PureWindowsPath, PurePath
import os
import shutil
import json
import hashlib
import datetime
from typing import Optional, Iterator, List
class SmartPath(Path):
    """
    An extended version of pathlib.Path that adds data-science-friendly
    utilities: checksumming, word counting, metadata export, safe copy,
    duplicate detection, and automatic backups.

    Demonstrates:
      - Inheritance    : SmartPath IS-A Path IS-A PurePath
      - Encapsulation  : internal helpers prefixed with _
      - Polymorphism   : overrides __truediv__ transparently
      - Abstraction    : hides hash/stat complexity behind simple methods
    """

    # Required override: Path uses __new__ for OS-specific subclass dispatch.
    # In Python 3.12+ Path can be subclassed normally via __init_subclass__,
    # but keeping __new__ ensures compatibility across 3.9–3.12.
    _flavour = Path(".")._flavour if hasattr(Path("."), "_flavour") else None

    def __new__(cls, *args, **kwargs):
        # Let Path handle platform-specific initialization
        obj = super().__new__(cls, *args, **kwargs)
        return obj

    # Private helper
    
    def _require_file(self) -> None:
        """Raise a clear error if this path is not a regular file."""
        if not self.is_file():
            raise FileNotFoundError(
                f"SmartPath.{self._require_file.__name__} requires a regular file; "
                f"'{self}' is not one."
            )

    # 1. checksum — NEW method (not in pathlib.Path)
    
    def checksum(self, algorithm: str = "md5") -> str:
        """
        Return the hex digest of the file using the given hash algorithm.

        Args:
            algorithm: 'md5', 'sha1', or 'sha256'  (default: 'md5')

        Returns:
            Hex string of the file's hash.

        Example:
            >>> SmartPath("report.pdf").checksum("sha256")
            'a3f5...'
        """
        self._require_file()
        h = hashlib.new(algorithm)
        with self.open("rb") as fh:
            # Read in 64 KB chunks — memory-efficient for large files
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
        
    # 2. word_count — NEW method
    
    def word_count(self, encoding: str = "utf-8") -> dict:
        """
        Count characters, words, and lines in a text file.

        Returns:
            {'chars': int, 'words': int, 'lines': int}
        """
        self._require_file()
        text = self.read_text(encoding=encoding)
        return {
            "chars": len(text),
            "words": len(text.split()),
            "lines": text.count("\n") + (1 if text else 0),
        }

    # 3. metadata — NEW method; overrides nothing but composes many calls
    
    def metadata(self) -> dict:
        """
        Return a comprehensive metadata dictionary for the file.

        Includes: name, extension, size_bytes, modified_at (ISO 8601),
                  checksum_md5, and (for text files) word_count stats.
        """
        self._require_file()
        stat = self.stat()
        info = {
            "path":         str(self),
            "name":         self.name,
            "stem":         self.stem,
            "suffix":       self.suffix,
            "size_bytes":   stat.st_size,
            "modified_at":  datetime.datetime.fromtimestamp(
                                stat.st_mtime
                            ).isoformat(),
            "checksum_md5": self.checksum("md5"),
        }
        # Add word stats only for text files
        text_exts = {".txt", ".py", ".md", ".csv", ".json", ".html", ".xml"}
        if self.suffix.lower() in text_exts:
            info["word_stats"] = self.word_count()
        return info

    # 4. safe_copy — NEW method
    
    def safe_copy(self, destination: "SmartPath | Path",
                  overwrite: bool = False) -> "SmartPath":
        """
        Copy this file to *destination*, handling name collisions gracefully.

        If overwrite=False and destination exists, appends _1, _2, … to stem.

        Returns:
            SmartPath pointing to the actual destination file.
        """
        self._require_file()
        dest = SmartPath(destination)

        if dest.is_dir():
            dest = dest / self.name   # copy into directory

        if dest.exists() and not overwrite:
            counter = 1
            while dest.exists():
                dest = SmartPath(
                    dest.parent / f"{self.stem}_{counter}{self.suffix}"
                )
                counter += 1

        shutil.copy2(self, dest)
        print(f"  [safe_copy] '{self.name}' → '{dest}'")
        return SmartPath(dest)

    # 5. backup — NEW method
    
    def backup(self, backup_dir: Optional["SmartPath | Path"] = None) -> "SmartPath":
        """
        Create a timestamped backup of this file.

        The backup is named: <stem>_backup_YYYYMMDD_HHMMSS<suffix>
        Placed in backup_dir (default: same folder as the original).

        Returns:
            SmartPath of the backup file.
        """
        self._require_file()
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{self.stem}_backup_{ts}{self.suffix}"

        if backup_dir is None:
            backup_dest = SmartPath(self.parent / backup_name)
        else:
            backup_dir = SmartPath(backup_dir)
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_dest = SmartPath(backup_dir / backup_name)

        shutil.copy2(self, backup_dest)
        print(f"  [backup] Created: '{backup_dest}'")
        return backup_dest

    # 6. find_duplicates — NEW class / static-style method on a dir path
    
    def find_duplicates(self, algorithm: str = "md5") -> dict:
        """
        Scan this directory tree for duplicate files (same content, any name).

        Returns:
            A dict mapping checksum → [list of SmartPath objects] for any
            checksum shared by more than one file.

        Example:
            dups = SmartPath("/data").find_duplicates()
            for cksum, paths in dups.items():
                print(cksum, [str(p) for p in paths])
        """
        if not self.is_dir():
            raise NotADirectoryError(f"'{self}' is not a directory.")

        seen: dict[str, list] = {}
        for file in self.rglob("*"):
            if file.is_file():
                ck = SmartPath(file).checksum(algorithm)
                seen.setdefault(ck, []).append(SmartPath(file))

        return {ck: paths for ck, paths in seen.items() if len(paths) > 1}

    # 7. to_dict — serialise path for JSON / data pipelines
    
    def to_dict(self) -> dict:
        """
        Return a JSON-serialisable dict of path components.

        Useful for storing path information in databases, logs, or configs.
        """
        return {
            "absolute": str(self.resolve()),
            "parts":    list(self.parts),
            "parent":   str(self.parent),
            "name":     self.name,
            "stem":     self.stem,
            "suffix":   self.suffix,
            "exists":   self.exists(),
            "is_file":  self.is_file(),
            "is_dir":   self.is_dir(),
        }

    # Override __truediv__ — ensures / returns SmartPath, not plain Path
    
    def __truediv__(self, key) -> "SmartPath":
        """Override / operator so child paths are also SmartPath instances."""
        result = super().__truediv__(key)
        return SmartPath(result)

    def __repr__(self) -> str:
        return f"SmartPath('{self}')"

# SECTION 3: DEMO — run as main to see everything in action

def run_demo():
    print("\n" + "=" * 60)
    print("  SmartPath DEMO")
    print("=" * 60)

    # Setup demo workspace
    demo_dir = SmartPath("D:/smartpath_demo")
    demo_dir.mkdir(exist_ok=True)

    # Create demo files
    readme = demo_dir / "README.md"
    readme.write_text(
        "# SmartPath Demo\n\nThis is a demonstration of the SmartPath class.\n"
        "It extends pathlib.Path with extra OOP features.\n"
        "Data Science students will love using it!\n"
    )

    data_file = demo_dir / "data.csv"
    data_file.write_text("id,name,score\n1,Alice,95\n2,Bob,87\n3,Carol,92\n")

    # Duplicate for duplicate-detection demo
    dup_file = demo_dir / "data_copy.csv"
    dup_file.write_text("id,name,score\n1,Alice,95\n2,Bob,87\n3,Carol,92\n")

    print("\n--- 1. SmartPath type chain ---")
    print(f"readme type : {type(readme).__name__}")
    print(f"Is Path?    : {isinstance(readme, Path)}")
    print(f"Is PurePath?: {isinstance(readme, PurePath)}")
    print(f"repr        : {readme!r}")

    print("\n--- 2. checksum() ---")
    print(f"README md5    : {readme.checksum('md5')}")
    print(f"README sha256 : {readme.checksum('sha256')}")

    print("\n--- 3. word_count() ---")
    wc = readme.word_count()
    print(f"README word stats: {wc}")

    print("\n--- 4. metadata() ---")
    meta = readme.metadata()
    print(json.dumps(meta, indent=2))

    print("\n--- 5. to_dict() ---")
    print(json.dumps(data_file.to_dict(), indent=2))

    print("\n--- 6. safe_copy() ---")
    copy_dir = demo_dir / "copies"
    copy_dir.mkdir(exist_ok=True)
    c1 = readme.safe_copy(copy_dir)          # first copy
    c2 = readme.safe_copy(copy_dir)          # collision → _1 appended
    c3 = readme.safe_copy(copy_dir)          # collision → _2 appended
    print(f"Copies created: {[p.name for p in copy_dir.iterdir()]}")

    print("\n--- 7. backup() ---")
    backup_dir = demo_dir / "backups"
    b = readme.backup(backup_dir=backup_dir)
    print(f"Backup file: {b.name}")

    print("\n--- 8. find_duplicates() ---")
    dupes = demo_dir.find_duplicates()
    if dupes:
        print("Duplicate files found:")
        for cksum, paths in dupes.items():
            print(f"  MD5={cksum[:12]}... → {[p.name for p in paths]}")
    else:
        print("No duplicates found.")

    print("\n--- 9. / operator returns SmartPath (overridden __truediv__) ---")
    child = demo_dir / "nested" / "deep" / "file.txt"
    print(f"child type : {type(child).__name__}")
    print(f"child repr : {child!r}")

    # Cleanup
    shutil.rmtree(str(demo_dir))
    print("\nDemo workspace cleaned up.")
    print("\nAll SmartPath features demonstrated successfully!")


if __name__ == "__main__":
    run_demo()
