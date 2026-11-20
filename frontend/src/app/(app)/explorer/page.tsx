import { Suspense } from "react";
import { ExplorerView } from "@/components/explorer/explorer-view";

export default function ExplorerPage() {
  return (
    <Suspense>
      <ExplorerView />
    </Suspense>
  );
}
