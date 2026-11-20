from tree_sitter import Node, Parser, Query, QueryCursor

from app.services.parsing.languages import LanguageSpec, LANGUAGES, get_language
from app.services.parsing.types import ExtractedCall, ExtractedImport, ExtractedSymbol, ParsedFile

SYMBOL_TYPE_FROM_CAPTURE = {
    "function.name": "function",
    "method.name": "method",
    "class.name": "class",
    "interface.name": "interface",
    "struct.name": "struct",
}

MAX_SIGNATURE_LENGTH = 200


def _decode(source_bytes: bytes, node: Node) -> str:
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _signature(source_bytes: bytes, node: Node) -> str:
    line_end = source_bytes.find(b"\n", node.start_byte)
    if line_end == -1 or line_end > node.end_byte:
        line_end = node.end_byte
    return source_bytes[node.start_byte : line_end].decode("utf-8", errors="replace").strip()[
        :MAX_SIGNATURE_LENGTH
    ]


def _find_container_name(node: Node, spec: LanguageSpec, source_bytes: bytes) -> str | None:
    current = node.parent
    while current is not None:
        if current.type in spec.container_node_types:
            container = current if spec.key == "python" else current.parent
            if container is None:
                return None
            name_node = container.child_by_field_name("name")
            return _decode(source_bytes, name_node) if name_node is not None else None
        current = current.parent
    return None


def extract_symbols(root: Node, spec: LanguageSpec, source_bytes: bytes) -> list[ExtractedSymbol]:
    query = Query(get_language(spec.key), spec.definitions_query)
    cursor = QueryCursor(query)
    symbols: list[ExtractedSymbol] = []

    for _, captures in cursor.matches(root):
        for name_capture, base_type in SYMBOL_TYPE_FROM_CAPTURE.items():
            if name_capture not in captures:
                continue
            name_node = captures[name_capture][0]
            def_capture = f"{name_capture.split('.')[0]}.def"
            def_node = captures[def_capture][0] if def_capture in captures else name_node

            parent = _find_container_name(def_node, spec, source_bytes)
            symbol_type = "method" if base_type == "function" and parent is not None else base_type

            symbols.append(
                ExtractedSymbol(
                    name=_decode(source_bytes, name_node),
                    symbol_type=symbol_type,
                    start_line=def_node.start_point[0] + 1,
                    end_line=def_node.end_point[0] + 1,
                    parent=parent,
                    signature=_signature(source_bytes, def_node),
                )
            )

    return symbols


def extract_imports(root: Node, spec: LanguageSpec, source_bytes: bytes) -> list[ExtractedImport]:
    query = Query(get_language(spec.key), spec.imports_query)
    cursor = QueryCursor(query)
    imports: list[ExtractedImport] = []

    for _, captures in cursor.matches(root):
        for node in captures.get("import.module", []):
            text = _decode(source_bytes, node).strip().strip("\"<>")
            if text:
                imports.append(ExtractedImport(module=text, line=node.start_point[0] + 1))

    return imports


def _enclosing_symbol_name(line: int, symbols: list[ExtractedSymbol]) -> str | None:
    best: ExtractedSymbol | None = None
    for symbol in symbols:
        if symbol.start_line <= line <= symbol.end_line:
            if best is None or (symbol.end_line - symbol.start_line) < (best.end_line - best.start_line):
                best = symbol
    return best.name if best else None


def extract_calls(
    root: Node, spec: LanguageSpec, source_bytes: bytes, symbols: list[ExtractedSymbol]
) -> list[ExtractedCall]:
    query = Query(get_language(spec.key), spec.calls_query)
    cursor = QueryCursor(query)
    calls: list[ExtractedCall] = []

    for _, captures in cursor.matches(root):
        for node in captures.get("call.name", []):
            line = node.start_point[0] + 1
            calls.append(
                ExtractedCall(
                    callee_name=_decode(source_bytes, node),
                    line=line,
                    caller_symbol=_enclosing_symbol_name(line, symbols),
                )
            )

    return calls


def parse_source(content: str, language_key: str) -> ParsedFile:
    spec = LANGUAGES[language_key]
    parser = Parser(get_language(language_key))
    source_bytes = content.encode("utf-8", errors="replace")
    tree = parser.parse(source_bytes)

    symbols = extract_symbols(tree.root_node, spec, source_bytes)
    imports = extract_imports(tree.root_node, spec, source_bytes)
    calls = extract_calls(tree.root_node, spec, source_bytes, symbols)

    return ParsedFile(symbols=symbols, imports=imports, calls=calls)
