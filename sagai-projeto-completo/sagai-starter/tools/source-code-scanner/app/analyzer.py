import re
from pathlib import Path


def read_file(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1", errors="ignore")


def detect_layer(relative_path: str) -> str:
    path = relative_path.lower()
    if "controller" in path or "route" in path:
        return "controller"
    if "service" in path:
        return "service"
    if "usecase" in path or "use-case" in path:
        return "usecase"
    if "repository" in path:
        return "repository"
    if "entity" in path or "model" in path:
        return "entity"
    if "dto" in path:
        return "dto"
    if "component" in path:
        return "frontend_component"
    if "page" in path:
        return "frontend_page"
    return "unknown"


def detect_domain(relative_path: str) -> str:
    parts = relative_path.replace("\\", "/").split("/")
    ignored = {
        "src", "app", "components", "pages", "infra", "infrastructure",
        "domain", "application", "services", "controllers", "repositories",
        "entities", "dtos", "models", "utils", "shared", "common",
    }
    for part in parts:
        clean = part.lower().split(".")[0]
        if clean not in ignored and clean and not clean.startswith("index"):
            return clean
    return "unknown"


def extract_imports(content: str) -> list[str]:
    patterns = [
        r"import\s+.*?\s+from\s+['\"](.+?)['\"]",
        r"require\(['\"](.+?)['\"]\)",
        r"using\s+([A-Za-z0-9_.]+);",
    ]
    values = []
    for pattern in patterns:
        values.extend(re.findall(pattern, content))
    return sorted(set(values))


def extract_classes(content: str) -> list[str]:
    patterns = [
        r"class\s+([A-Za-z0-9_]+)",
        r"interface\s+([A-Za-z0-9_]+)",
        r"record\s+([A-Za-z0-9_]+)",
    ]
    values = []
    for pattern in patterns:
        values.extend(re.findall(pattern, content))
    return sorted(set(values))


def extract_functions(content: str) -> list[str]:
    patterns = [
        r"function\s+([A-Za-z0-9_]+)\s*\(",
        r"async\s+function\s+([A-Za-z0-9_]+)\s*\(",
        r"const\s+([A-Za-z0-9_]+)\s*=\s*async\s*\(",
        r"const\s+([A-Za-z0-9_]+)\s*=\s*\(",
        r"public\s+[A-Za-z0-9_<>, ?]+\s+([A-Za-z0-9_]+)\s*\(",
        r"private\s+[A-Za-z0-9_<>, ?]+\s+([A-Za-z0-9_]+)\s*\(",
    ]
    values = []
    for pattern in patterns:
        values.extend(re.findall(pattern, content))
    ignored = {"if", "for", "while", "switch", "catch"}
    return sorted(set(value for value in values if value not in ignored))


def extract_routes(content: str) -> list[dict]:
    routes = []
    nest_pattern = r"@(Get|Post|Put|Patch|Delete)\(['\"]?(.*?)['\"]?\)"
    for method, path in re.findall(nest_pattern, content):
        routes.append({"method": method.upper(), "path": path or "/", "framework": "nestjs"})

    express_pattern = r"router\.(get|post|put|patch|delete)\(['\"](.*?)['\"]"
    for method, path in re.findall(express_pattern, content):
        routes.append({"method": method.upper(), "path": path, "framework": "express"})

    spring_pattern = r"@(GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping)\(['\"]?(.*?)['\"]?\)"
    spring_methods = {
        "GetMapping": "GET", "PostMapping": "POST", "PutMapping": "PUT",
        "PatchMapping": "PATCH", "DeleteMapping": "DELETE",
    }
    for annotation, path in re.findall(spring_pattern, content):
        routes.append({"method": spring_methods.get(annotation, annotation), "path": path or "/", "framework": "spring"})

    return routes


def extract_validations(content: str) -> list[str]:
    decorators = re.findall(r"@(Is[A-Za-z0-9_]+|MinLength|MaxLength|Length|Matches|IsOptional|NotNull|NotBlank|Size|Email)", content)
    return sorted(set(decorators))


def extract_error_messages(content: str) -> list[str]:
    patterns = [
        r"throw new Error\(['\"](.+?)['\"]\)",
        r"BadRequestException\(['\"](.+?)['\"]\)",
        r"NotFoundException\(['\"](.+?)['\"]\)",
        r"UnauthorizedException\(['\"](.+?)['\"]\)",
        r"new RuntimeException\(['\"](.+?)['\"]\)",
        r"throw new Exception\(['\"](.+?)['\"]\)",
    ]
    values = []
    for pattern in patterns:
        values.extend(re.findall(pattern, content))
    return sorted(set(values))


def analyze_file(file_path: Path, root: Path) -> dict:
    content = read_file(file_path)
    relative_path = str(file_path.relative_to(root)).replace("\\", "/")
    layer = detect_layer(relative_path)
    domain = detect_domain(relative_path)
    imports = extract_imports(content)
    classes = extract_classes(content)
    functions = extract_functions(content)
    routes = extract_routes(content)
    validations = extract_validations(content)
    error_messages = extract_error_messages(content)

    summary_parts = [
        f"Arquivo {relative_path}.",
        f"Camada detectada: {layer}.",
        f"Domínio provável: {domain}.",
    ]
    if classes:
        summary_parts.append(f"Classes/interfaces encontradas: {', '.join(classes)}.")
    if routes:
        summary_parts.append("Rotas encontradas: " + ", ".join(f"{r['method']} {r['path']}" for r in routes) + ".")

    return {
        "file": relative_path,
        "extension": file_path.suffix,
        "layer": layer,
        "domain": domain,
        "imports": imports,
        "classes": classes,
        "functions": functions[:80],
        "routes": routes,
        "validations": validations,
        "error_messages": error_messages,
        "summary": " ".join(summary_parts),
        "content_preview": content[:3000],
    }
