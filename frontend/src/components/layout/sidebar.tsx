"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Boxes, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { NAV_ITEMS, SETTINGS_ITEM } from "@/lib/nav-items";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

function NavLink({ item, pathname }: { item: (typeof NAV_ITEMS)[number]; pathname: string }) {
  const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      className={cn(
        "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
        active
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "text-sidebar-foreground/70 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
      )}
    >
      <Icon className="size-4 shrink-0" />
      <span className="truncate">{item.label}</span>
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar md:flex">
      <div className="flex h-14 items-center gap-2 border-b border-sidebar-border px-4">
        <div className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <Boxes className="size-4" />
        </div>
        <span className="text-sm font-semibold tracking-tight text-sidebar-foreground">
          RepoMind
        </span>
      </div>

      <div className="border-b border-sidebar-border px-3 py-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex w-full items-center justify-between rounded-md border border-sidebar-border bg-sidebar-accent/40 px-3 py-2 text-left text-sm text-sidebar-foreground hover:bg-sidebar-accent/60">
              <span className="truncate font-medium">Personal Workspace</span>
              <ChevronsUpDown className="size-3.5 shrink-0 text-sidebar-foreground/50" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-56">
            <DropdownMenuItem disabled>Personal Workspace</DropdownMenuItem>
            <DropdownMenuItem disabled className="text-muted-foreground">
              Workspace switching lands with Phase 3 (auth & workspaces)
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-3">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.href} item={item} pathname={pathname} />
        ))}
      </nav>

      <div className="border-t border-sidebar-border px-3 py-3">
        <NavLink item={SETTINGS_ITEM} pathname={pathname} />
      </div>
    </aside>
  );
}
