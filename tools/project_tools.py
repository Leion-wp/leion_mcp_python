from pathlib import Path
from fastmcp import FastMCP


def _scan_directory(root: Path, max_files: int = 500) -> list[dict]:
    """
    Lightweight project scan: returns a list of files with relative paths
    and basic metadata.
    """
    files: list[dict] = []
    for path in root.rglob('*'):
        if len(files) >= max_files:
            break
        if path.is_file():
            rel = path.relative_to(root)
            files.append(
                {
                    'path': str(rel),
                    'size': path.stat().st_size,
                    'suffix': path.suffix,
                }
            )
    return files


def register_project_tools(server: FastMCP):

    @server.tool()
    def project_scan(root_path: str, max_files: int = 500):
        """
        Scan a project directory and return a lightweight file inventory.

        - root_path: root of the project (e.g. D:/claude_code/leion-autobuilder)
        - max_files: safety limit to avoid huge traversals.
        """
        root = Path(root_path)
        if not root.exists():
            return {'error': "root_path does not exist", 'root_path': root_path}
        if not root.is_dir():
            return {'error': "root_path is not a directory", 'root_path': root_path}

        files = _scan_directory(root, max_files=max_files)
        return {
            'root': str(root),
            'count': len(files),
            'max_files': max_files,
            'files': files,
        }

    @server.tool()
    def project_summary(root_path: str, max_files: int = 500):
        """
        High-level summary of a project: counts by extension, total size, etc.
        """
        root = Path(root_path)
        if not root.exists():
            return {'error': "root_path does not exist", 'root_path': root_path}
        if not root.is_dir():
            return {'error': "root_path is not a directory", 'root_path': root_path}

        files = _scan_directory(root, max_files=max_files)
        by_ext: dict[str, int] = {}
        total_size = 0
        for f in files:
            ext = f['suffix'] or ''
            by_ext[ext] = by_ext.get(ext, 0) + 1
            total_size += f['size']

        return {
            'root': str(root),
            'file_count': len(files),
            'max_files': max_files,
            'total_size': total_size,
            'by_extension': by_ext,
        }
