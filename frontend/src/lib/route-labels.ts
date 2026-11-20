import { NAV_ITEMS, SETTINGS_ITEM } from "@/lib/nav-items";

const ALL_ITEMS = [...NAV_ITEMS, SETTINGS_ITEM];

export function labelForPathname(pathname: string): string {
  const match = ALL_ITEMS.find(
    (item) => pathname === item.href || pathname.startsWith(`${item.href}/`),
  );
  return match?.label ?? "RepoMind";
}
