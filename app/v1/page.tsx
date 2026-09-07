import type { Metadata } from "next";
import { TwinStudio } from "@/versions/v1/app/twin-studio";
import "@/versions/v1/app/globals.css";

export const metadata: Metadata = {
  title: "Dom 6012/26 · Digitálne dvojča · v1",
};

export default function VersionOnePage() {
  return <TwinStudio />;
}
