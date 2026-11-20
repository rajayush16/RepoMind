"use client";

import { useState } from "react";
import { ChevronRight, File, Folder, FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import type { TreeNode } from "@/lib/file-tree";

function TreeItem({
  node,
  depth,
  selectedPath,
  onSelect,
}: {
  node: TreeNode;
  depth: number;
  selectedPath: string | null;
  onSelect: (path: string) => void;
}) {
  const [open, setOpen] = useState(depth < 1);

  if (node.type === "dir") {
    return (
      <div>
        <button
          className="flex w-full items-center gap-1 rounded-md px-2 py-1 text-left text-sm text-foreground/80 hover:bg-secondary"
          style={{ paddingLeft: `${depth * 14 + 8}px` }}
          onClick={() => setOpen((v) => !v)}
        >
          <ChevronRight className={cn("size-3.5 shrink-0 transition-transform", open && "rotate-90")} />
          {open ? <FolderOpen className="size-3.5 shrink-0 text-muted-foreground" /> : <Folder className="size-3.5 shrink-0 text-muted-foreground" />}
          <span className="truncate">{node.name}</span>
        </button>
        {open && (
          <div>
            {node.children.map((child) => (
              <TreeItem key={child.path} node={child} depth={depth + 1} selectedPath={selectedPath} onSelect={onSelect} />
            ))}
          </div>
        )}
      </div>
    );
  }

  const active = node.path === selectedPath;

  return (
    <button
      className={cn(
        "flex w-full items-center gap-1.5 rounded-md px-2 py-1 text-left text-sm hover:bg-secondary",
        active ? "bg-sidebar-accent text-sidebar-accent-foreground" : "text-foreground/70",
      )}
      style={{ paddingLeft: `${depth * 14 + 26}px` }}
      onClick={() => onSelect(node.path)}
    >
      <File className="size-3.5 shrink-0 text-muted-foreground" />
      <span className="truncate">{node.name}</span>
    </button>
  );
}

export function FileTreeView({
  tree,
  selectedPath,
  onSelect,
}: {
  tree: TreeNode[];
  selectedPath: string | null;
  onSelect: (path: string) => void;
}) {
  return (
    <div className="flex flex-col gap-0.5">
      {tree.map((node) => (
        <TreeItem key={node.path} node={node} depth={0} selectedPath={selectedPath} onSelect={onSelect} />
      ))}
    </div>
  );
}
