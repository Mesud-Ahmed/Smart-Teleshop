import { MiniApp } from "@/components/mini-app";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function Home() {
  return <MiniApp apiBaseUrl={apiBaseUrl} />;
}
