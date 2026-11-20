"use client";

import { usePathname, useRouter } from "next/navigation";
import { ChevronRight, PanelRight, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { labelForPathname } from "@/lib/route-labels";
import { useUIStore } from "@/stores/ui-store";
import { useCurrentUser, useLogout } from "@/lib/queries/auth";

function initialsFor(name: string | null, email: string): string {
  if (name) {
    const parts = name.trim().split(/\s+/);
    return parts
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join("");
  }
  return email.slice(0, 2).toUpperCase();
}

export function Topbar() {
  const pathname = usePathname();
  const router = useRouter();
  const setCommandPaletteOpen = useUIStore((state) => state.setCommandPaletteOpen);
  const toggleRightPanel = useUIStore((state) => state.toggleRightPanel);
  const sectionLabel = labelForPathname(pathname);
  const { data: user } = useCurrentUser();
  const logout = useLogout();

  function handleLogout() {
    logout.mutate(undefined, {
      onSuccess: () => router.replace("/login"),
    });
  }

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-background/95 px-4">
      <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
        <span>RepoMind</span>
        <ChevronRight className="size-3.5" />
        <span className="font-medium text-foreground">{sectionLabel}</span>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          className="h-8 gap-2 text-muted-foreground"
          onClick={() => setCommandPaletteOpen(true)}
        >
          <Search className="size-3.5" />
          <span className="hidden sm:inline">Search...</span>
          <kbd className="ml-2 hidden rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-medium sm:inline">
            Ctrl K
          </kbd>
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className="size-8"
          aria-label="Toggle contextual panel"
          onClick={toggleRightPanel}
        >
          <PanelRight className="size-4" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center rounded-full outline-none ring-offset-background focus-visible:ring-2 focus-visible:ring-ring">
              <Avatar className="size-8">
                {user?.github_avatar_url && <AvatarImage src={user.github_avatar_url} />}
                <AvatarFallback className="bg-secondary text-xs">
                  {user ? initialsFor(user.name, user.email) : "RM"}
                </AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="text-xs text-muted-foreground">
              {user?.email ?? "Signed-in account"}
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem disabled>
              {user?.github_connected ? `GitHub: @${user.github_username}` : "GitHub not connected"}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={handleLogout}>Log out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
