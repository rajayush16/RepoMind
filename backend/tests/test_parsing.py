from app.services.parsing.extractor import parse_source


def test_parse_python_extracts_functions_classes_methods_imports_calls() -> None:
    code = """
import os
from typing import List

def foo(a, b):
    return bar(a) + os.getcwd()

class Greeter:
    def greet(self, name):
        return foo(name, name)
"""
    result = parse_source(code, "python")

    names = {(s.name, s.symbol_type, s.parent) for s in result.symbols}
    assert ("foo", "function", None) in names
    assert ("Greeter", "class", None) in names
    assert ("greet", "method", "Greeter") in names

    assert {i.module for i in result.imports} == {"os", "typing"}

    callee_names = {c.callee_name for c in result.calls}
    assert "bar" in callee_names
    assert "foo" in callee_names

    greet_call = next(c for c in result.calls if c.callee_name == "foo")
    assert greet_call.caller_symbol == "greet"


def test_parse_javascript_extracts_functions_classes_methods() -> None:
    code = """
import { useState } from "react";

function add(a, b) { return a + b; }

class Widget {
  render() { return add(1, 2); }
}
"""
    result = parse_source(code, "javascript")
    names = {(s.name, s.symbol_type, s.parent) for s in result.symbols}
    assert ("add", "function", None) in names
    assert ("Widget", "class", None) in names
    assert ("render", "method", "Widget") in names
    assert {i.module for i in result.imports} == {"react"}


def test_parse_typescript_extracts_interfaces_and_classes() -> None:
    code = """
import { Foo } from "./foo";

interface Point { x: number; y: number; }

class Shape {
  area(): number { return 0; }
}
"""
    result = parse_source(code, "typescript")
    types = {(s.name, s.symbol_type) for s in result.symbols}
    assert ("Point", "interface") in types
    assert ("Shape", "class") in types
    assert ("area", "method") in types
    assert {i.module for i in result.imports} == {"./foo"}


def test_parse_java_extracts_classes_interfaces_methods() -> None:
    code = """
import java.util.List;

public class Foo {
    public int bar(int a) { return a; }
}
interface Baz {}
"""
    result = parse_source(code, "java")
    types = {(s.name, s.symbol_type) for s in result.symbols}
    assert ("Foo", "class") in types
    assert ("Baz", "interface") in types
    assert ("bar", "method") in types
    assert {i.module for i in result.imports} == {"java.util.List"}


def test_parse_cpp_extracts_functions_classes_structs() -> None:
    code = """
#include <iostream>

int add(int a, int b) { return a + b; }

class Foo {
public:
    void bar() {}
};

struct Point { int x; int y; };
"""
    result = parse_source(code, "cpp")
    types = {(s.name, s.symbol_type) for s in result.symbols}
    assert ("add", "function") in types
    assert ("Foo", "class") in types
    assert ("Point", "struct") in types
    assert {i.module for i in result.imports} == {"iostream"}


def test_parse_go_extracts_functions_methods_structs() -> None:
    code = """
package main

import "fmt"

func Add(a int, b int) int { return a + b }

type Point struct {
    X int
    Y int
}

func (p Point) String() string { return fmt.Sprintf("") }
"""
    result = parse_source(code, "go")
    types = {(s.name, s.symbol_type) for s in result.symbols}
    assert ("Add", "function") in types
    assert ("Point", "struct") in types
    assert ("String", "method") in types
    assert {i.module for i in result.imports} == {"fmt"}
