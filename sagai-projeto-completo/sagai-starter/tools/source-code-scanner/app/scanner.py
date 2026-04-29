from pathlib import Path

from app.analyzer import analyze_file


IGNORED_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", "coverage",
    "__pycache__", ".venv", "venv", "target", ".idea", ".vscode",
}

ALLOWED_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".java", ".py", ".sql", ".cs",
}


def should_ignore(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def scan_source_code(source_path: str) -> dict:
    root = Path(source_path)
    files = []

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if should_ignore(file_path):
            continue
        if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        analyzed = analyze_file(file_path, root)
        if analyzed:
            files.append(analyzed)

    return {
        "title": "Mapa técnico do código-fonte",
        "document_type": "source_code_map",
        "source_type": "source_code",
        "total_files": len(files),
        "files": files,
    }
