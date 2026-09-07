import type { Metadata } from "next";
import ConceptPage, { metadata as originalMetadata } from "@/versions/v2/app/koncept-2d/page";

export const metadata: Metadata = {
  ...originalMetadata,
  title: "Dom · Dispozičné štúdio 2D · v2",
};

export default ConceptPage;
