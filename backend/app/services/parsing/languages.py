from dataclasses import dataclass
from typing import Callable

import tree_sitter_cpp as tscpp
import tree_sitter_go as tsgo
import tree_sitter_java as tsjava
import tree_sitter_javascript as tsjs
import tree_sitter_python as tspython
import tree_sitter_typescript as tsts
from tree_sitter import Language


@dataclass(frozen=True)
class LanguageSpec:
    key: str
    language_fn: Callable[[], object]
    definitions_query: str
    imports_query: str
    calls_query: str
    # Node types whose children (name-bearing descendants) should be treated as the
    # class/struct/interface "container" when deciding if a function is a method.
    container_node_types: tuple[str, ...]


PYTHON = LanguageSpec(
    key="python",
    language_fn=tspython.language,
    definitions_query="""
    (function_definition name: (identifier) @function.name) @function.def
    (class_definition name: (identifier) @class.name) @class.def
    """,
    imports_query="""
    (import_statement name: (dotted_name) @import.module)
    (import_from_statement module_name: (dotted_name) @import.module)
    """,
    calls_query="""
    (call function: (identifier) @call.name)
    (call function: (attribute attribute: (identifier) @call.name))
    """,
    container_node_types=("class_definition",),
)

JAVASCRIPT = LanguageSpec(
    key="javascript",
    language_fn=tsjs.language,
    definitions_query="""
    (function_declaration name: (identifier) @function.name) @function.def
    (class_declaration name: (identifier) @class.name) @class.def
    (method_definition name: (property_identifier) @method.name) @method.def
    """,
    imports_query="""
    (import_statement source: (string (string_fragment) @import.module))
    """,
    calls_query="""
    (call_expression function: (identifier) @call.name)
    (call_expression function: (member_expression property: (property_identifier) @call.name))
    """,
    container_node_types=("class_body",),
)

TYPESCRIPT = LanguageSpec(
    key="typescript",
    language_fn=tsts.language_typescript,
    definitions_query="""
    (function_declaration name: (identifier) @function.name) @function.def
    (class_declaration name: (type_identifier) @class.name) @class.def
    (interface_declaration name: (type_identifier) @interface.name) @interface.def
    (method_definition name: (property_identifier) @method.name) @method.def
    """,
    imports_query="""
    (import_statement source: (string (string_fragment) @import.module))
    """,
    calls_query="""
    (call_expression function: (identifier) @call.name)
    (call_expression function: (member_expression property: (property_identifier) @call.name))
    """,
    container_node_types=("class_body",),
)

TSX = LanguageSpec(
    key="tsx",
    language_fn=tsts.language_tsx,
    definitions_query=TYPESCRIPT.definitions_query,
    imports_query=TYPESCRIPT.imports_query,
    calls_query=TYPESCRIPT.calls_query,
    container_node_types=("class_body",),
)

JAVA = LanguageSpec(
    key="java",
    language_fn=tsjava.language,
    definitions_query="""
    (class_declaration name: (identifier) @class.name) @class.def
    (interface_declaration name: (identifier) @interface.name) @interface.def
    (method_declaration name: (identifier) @method.name) @method.def
    """,
    imports_query="""
    (import_declaration (scoped_identifier) @import.module)
    """,
    calls_query="""
    (method_invocation name: (identifier) @call.name)
    """,
    container_node_types=("class_body", "interface_body"),
)

CPP = LanguageSpec(
    key="cpp",
    language_fn=tscpp.language,
    definitions_query="""
    (function_definition declarator: (function_declarator declarator: (identifier) @function.name)) @function.def
    (function_definition declarator: (function_declarator declarator: (field_identifier) @method.name)) @method.def
    (class_specifier name: (type_identifier) @class.name) @class.def
    (struct_specifier name: (type_identifier) @struct.name) @struct.def
    """,
    imports_query="""
    (preproc_include path: (_) @import.module)
    """,
    calls_query="""
    (call_expression function: (identifier) @call.name)
    (call_expression function: (field_expression field: (field_identifier) @call.name))
    """,
    container_node_types=("field_declaration_list",),
)

GO = LanguageSpec(
    key="go",
    language_fn=tsgo.language,
    definitions_query="""
    (function_declaration name: (identifier) @function.name) @function.def
    (method_declaration name: (field_identifier) @method.name) @method.def
    (type_spec name: (type_identifier) @struct.name (struct_type)) @struct.def
    """,
    imports_query="""
    (import_spec path: (interpreted_string_literal) @import.module)
    """,
    calls_query="""
    (call_expression function: (identifier) @call.name)
    (call_expression function: (selector_expression field: (field_identifier) @call.name))
    """,
    container_node_types=(),
)

LANGUAGES: dict[str, LanguageSpec] = {
    spec.key: spec
    for spec in [PYTHON, JAVASCRIPT, TYPESCRIPT, TSX, JAVA, CPP, GO]
}

EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".mts": "typescript",
    ".tsx": "tsx",
    ".java": "java",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".h": "cpp",
    ".go": "go",
}

_LANGUAGE_CACHE: dict[str, Language] = {}


def get_language(key: str) -> Language:
    if key not in _LANGUAGE_CACHE:
        spec = LANGUAGES[key]
        _LANGUAGE_CACHE[key] = Language(spec.language_fn())
    return _LANGUAGE_CACHE[key]


def language_for_path(path: str) -> str | None:
    for ext, key in EXTENSION_TO_LANGUAGE.items():
        if path.endswith(ext):
            return key
    return None
