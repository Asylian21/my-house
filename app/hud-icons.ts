import {
  Box,
  CircleHelp,
  Crosshair,
  DoorOpen,
  DraftingCompass,
  Eye,
  Focus,
  Footprints,
  Fullscreen,
  House,
  Layers3,
  Map,
  MapPin,
  Orbit,
  Plane,
  Route,
  Trees,
  UserRound,
  type LucideIcon,
} from "lucide-react";

import type { CommandIcon } from "@/lib/twin-commands";

/**
 * One icon per command concept, shared by the dock and the palette so the same
 * action never appears with two different glyphs.
 */
export const COMMAND_ICONS: Readonly<Record<CommandIcon, LucideIcon>> = {
  garden: Trees,
  street: Route,
  axonometric: Box,
  plan: Map,
  parcels: MapPin,
  focus: Focus,
  orbit: Orbit,
  flight: Plane,
  walk: Footprints,
  room: DoorOpen,
  avatar: UserRound,
  layer: Layers3,
  // The drawing instrument against the finished house: the clearest possible
  // pair for the two modes when the switcher has no room for words.
  documentation: DraftingCompass,
  experience: House,
  recenter: Crosshair,
  eye: Eye,
  help: CircleHelp,
  fullscreen: Fullscreen,
};
