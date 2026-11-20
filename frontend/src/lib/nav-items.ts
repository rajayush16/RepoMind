import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  FolderGit2,
  Code2,
  Workflow,
  Sparkles,
  Bug,
  Waypoints,
  GitPullRequest,
  FlaskConical,
  BarChart3,
  Settings,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  shortcut?: string;
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Overview", href: "/overview", icon: LayoutDashboard },
  { label: "Repositories", href: "/repositories", icon: FolderGit2 },
  { label: "Code Explorer", href: "/explorer", icon: Code2 },
  { label: "Architecture Graph", href: "/architecture", icon: Workflow },
  { label: "AI Assistant", href: "/assistant", icon: Sparkles },
  { label: "Bug Investigation", href: "/investigations", icon: Bug },
  { label: "Impact Analysis", href: "/impact", icon: Waypoints },
  { label: "Pull Request Review", href: "/pull-requests", icon: GitPullRequest },
  { label: "Test Generation", href: "/tests", icon: FlaskConical },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
];

export const SETTINGS_ITEM: NavItem = {
  label: "Settings",
  href: "/settings",
  icon: Settings,
};
