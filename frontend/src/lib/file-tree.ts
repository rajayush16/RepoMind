import type { FileEntry } from "@/lib/queries/code";

export interface TreeNode {
  name: string;
  path: string;
  type: "dir" | "file";
  children: TreeNode[];
  file?: FileEntry;
}

export function buildFileTree(files: FileEntry[]): TreeNode[] {
  const root: TreeNode[] = [];

  for (const file of files) {
    const parts = file.relative_path.split("/");
    let level = root;
    let currentPath = "";

    parts.forEach((part, index) => {
      currentPath = currentPath ? `${currentPath}/${part}` : part;
      const isFile = index === parts.length - 1;
      let node = level.find((n) => n.name === part && n.type === (isFile ? "file" : "dir"));

      if (!node) {
        node = {
          name: part,
          path: currentPath,
          type: isFile ? "file" : "dir",
          children: [],
          file: isFile ? file : undefined,
        };
        level.push(node);
      }

      level = node.children;
    });
  }

  const sortTree = (nodes: TreeNode[]) => {
    nodes.sort((a, b) => {
      if (a.type !== b.type) return a.type === "dir" ? -1 : 1;
      return a.name.localeCompare(b.name);
    });
    nodes.forEach((n) => sortTree(n.children));
  };
  sortTree(root);

  return root;
}
