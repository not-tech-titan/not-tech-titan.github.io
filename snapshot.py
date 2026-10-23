from pathlib import Path
from datetime import datetime
import argparse


# Folders that should not be included in the snapshot
IGNORED_DIRS = {
    ".git",
    "raygui.h",
    ".vs",
    ".vscode",
    "build",
    "raylib",
    "lua",
    "cmake-build-debug",
    "cmake-build-release",
    "out",
    "bin",
    "obj",
    "Debug",
    "Release",
    "x64",
    "x86",
    "__pycache__",
    
}


# Files that should not be included in the snapshot
IGNORED_FILES = {
    "snapshot.py",
    "snapshot.txt"
}


# File extensions whose contents should be exported
CODE_EXTENSIONS = {
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cc",
    ".hh",
    ".cxx",
    ".hxx",
    ".py",
    ".java",
    ".cs",
    ".js",
    ".ts",
    ".html",
    ".css",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".toml",
    ".cmake",
    ".txt",
    ".md",
}


def should_ignore(path: Path, output_path: Path | None = None):
    """
    Determines whether a file or directory should be ignored.
    """

    # Ignore directories anywhere in the path
    if any(part in IGNORED_DIRS for part in path.parts):
        return True

    # Ignore specific files
    if path.name in IGNORED_FILES:
        return True

    # Ignore the output snapshot file
    if output_path is not None:
        try:
            if path.resolve() == output_path.resolve():
                return True
        except OSError:
            pass

    return False


def get_file_tree(root: Path, output_path: Path):
    lines = []

    def walk(directory: Path, prefix=""):
        try:
            entries = sorted(
                [
                    entry
                    for entry in directory.iterdir()
                    if not should_ignore(entry, output_path)
                ],
                key=lambda p: (p.is_file(), p.name.lower())
            )
        except PermissionError:
            return

        for index, entry in enumerate(entries):
            is_last = index == len(entries) - 1

            branch = "└── " if is_last else "├── "
            next_prefix = prefix + ("    " if is_last else "│   ")

            if entry.is_dir():
                lines.append(f"{prefix}{branch}{entry.name}/")
                walk(entry, next_prefix)
            else:
                lines.append(f"{prefix}{branch}{entry.name}")

    lines.append(f"{root.name}/")
    walk(root)

    return "\n".join(lines)


def get_code_files(root: Path, output_path: Path):
    files = []

    for path in root.rglob("*"):
        if path.is_file() and not should_ignore(path, output_path):
            if path.suffix.lower() in CODE_EXTENSIONS:
                files.append(path)

    return sorted(files)


def create_snapshot(project_path: Path, output_path: Path):
    project_path = project_path.resolve()
    output_path = output_path.resolve()

    with open(output_path, "w", encoding="utf-8") as snapshot:

        # --------------------------------------------------
        # HEADER
        # --------------------------------------------------

        snapshot.write("=" * 80 + "\n")
        snapshot.write("PROJECT SNAPSHOT\n")
        snapshot.write("=" * 80 + "\n\n")

        snapshot.write(f"Project: {project_path.name}\n")
        snapshot.write(f"Path: {project_path}\n")
        snapshot.write(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        # --------------------------------------------------
        # FILE STRUCTURE
        # --------------------------------------------------

        snapshot.write("=" * 80 + "\n")
        snapshot.write("FILE STRUCTURE\n")
        snapshot.write("=" * 80 + "\n\n")

        snapshot.write(get_file_tree(project_path, output_path))
        snapshot.write("\n\n")

        # --------------------------------------------------
        # FILE CONTENTS
        # --------------------------------------------------

        snapshot.write("=" * 80 + "\n")
        snapshot.write("FILE CONTENTS\n")
        snapshot.write("=" * 80 + "\n\n")

        code_files = get_code_files(project_path, output_path)

        for file_path in code_files:

            relative_path = file_path.relative_to(project_path)

            snapshot.write("\n")
            snapshot.write("=" * 80 + "\n")
            snapshot.write(f"FILE: {relative_path}\n")
            snapshot.write("=" * 80 + "\n\n")

            try:
                content = file_path.read_text(encoding="utf-8")
                snapshot.write(content)

            except UnicodeDecodeError:
                snapshot.write("[Could not decode file as UTF-8]")

            except Exception as error:
                snapshot.write(f"[Error reading file: {error}]")

            snapshot.write("\n\n")

    print(f"Snapshot created: {output_path}")


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Export a project's file structure and source code "
            "into a snapshot."
        )
    )

    parser.add_argument(
        "project",
        nargs="?",
        default=".",
        help=(
            "Project directory to snapshot. "
            "Defaults to the current directory."
        )
    )

    parser.add_argument(
        "-o",
        "--output",
        default="snapshot.txt",
        help=(
            "Output file name. "
            "Defaults to snapshot.txt."
        )
    )

    args = parser.parse_args()

    script_directory = Path(__file__).resolve().parent

    project_path = script_directory
    output_path = script_directory / args.output

    if not project_path.exists():
        print(
            f"Error: Project path does not exist: "
            f"{project_path}"
        )
        return

    if not project_path.is_dir():
        print(
            f"Error: Project path is not a directory: "
            f"{project_path}"
        )
        return

    create_snapshot(project_path, output_path)


if __name__ == "__main__":
    main()