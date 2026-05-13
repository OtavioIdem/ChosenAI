from app.scanner import scan_source_code
from app.exporter import export_json


def main() -> None:
    source_path = "/source"
    output_path = "/output/source_code_knowledge.json"

    result = scan_source_code(source_path)
    export_json(result, output_path)

    print(f"Scanner finalizado. Arquivo gerado em: {output_path}")


if __name__ == "__main__":
    main()
