import type { Metadata } from "next";
import { EvalsView } from "@/components/evals-view";

export const metadata: Metadata = {
  title: "Evals — ShopMind",
};

export default function EvalsPage() {
  return <EvalsView />;
}
