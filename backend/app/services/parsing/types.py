from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedSymbol:
    name: str
    symbol_type: str  # function | method | class | interface | struct
    start_line: int
    end_line: int
    parent: str | None
    signature: str


@dataclass(frozen=True)
class ExtractedImport:
    module: str
    line: int


@dataclass(frozen=True)
class ExtractedCall:
    callee_name: str
    line: int
    caller_symbol: str | None


@dataclass(frozen=True)
class ParsedFile:
    symbols: list[ExtractedSymbol]
    imports: list[ExtractedImport]
    calls: list[ExtractedCall]
