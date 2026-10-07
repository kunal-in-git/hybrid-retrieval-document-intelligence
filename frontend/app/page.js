import BackendStatus from "@/components/BackendStatus";
import AskPanel from "@/components/AskPanel";

export default function Home() {
  return (
    <main>
      <h1>Hybrid Retrieval Document Intelligence</h1>
      <BackendStatus />
      <AskPanel />
    </main>
  );
}
