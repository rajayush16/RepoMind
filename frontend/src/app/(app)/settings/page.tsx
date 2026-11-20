import { Settings as SettingsIcon } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";

export default function SettingsPage() {
  return (
    <div className="flex flex-1 flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Account, workspace, and integration settings.
        </p>
      </div>

      <EmptyState
        icon={SettingsIcon}
        title="Account & workspace settings not implemented yet"
        description="Settings depend on authentication and workspace membership, which land in Phase 3."
      />
    </div>
  );
}
