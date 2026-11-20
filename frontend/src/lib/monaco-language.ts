const LANGUAGE_MAP: Record<string, string> = {
  python: "python",
  javascript: "javascript",
  typescript: "typescript",
  tsx: "typescript",
  java: "java",
  cpp: "cpp",
  go: "go",
};

export function monacoLanguageFor(language: string): string {
  return LANGUAGE_MAP[language] ?? "plaintext";
}
