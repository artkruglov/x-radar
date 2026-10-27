import brand from "../../brand.json";
/**
 * Look & brand of the episode. Change this file (not the scenes) to restyle the series.
 * Pick a preset with THEME_NAME or add your own. Fonts available in public/fonts:
 * Unbounded (700/900), Inter (500–900), JetBrains Mono (500/700), Literata (500, italic), Caveat (700).
 */
export type Theme = {
  ink: string;      // dark surface + dark text (cover, chips, cards on light art)
  accent: string;   // highlight colour (chips, «стало», accents in headlines)
  paper: string;    // card background
  link: string;     // small link-ish text on cards
  headline: string; // font-family for big headlines
  body: string; mono: string; serif: string; hand: string;
  radius: number;   // card corner radius
};
export const THEMES: Record<string, Theme> = {
  lime:  { ink: "#0B0B0F", accent: "#C8FF3C", paper: "#FFFFFF", link: "#3346F0", headline: "'Unbounded', 'Inter', sans-serif", body: "'Inter', system-ui, sans-serif", mono: "'JetBrains Mono', monospace", serif: "'Literata', Georgia, serif", hand: "'Caveat', cursive", radius: 32 },
  coral: { ink: "#14110F", accent: "#FF7A59", paper: "#FFF8F0", link: "#B23A1E", headline: "'Literata', Georgia, serif", body: "'Inter', system-ui, sans-serif", mono: "'JetBrains Mono', monospace", serif: "'Literata', Georgia, serif", hand: "'Caveat', cursive", radius: 18 },
  terminal: { ink: "#05070A", accent: "#7CC8FF", paper: "#F2F6FA", link: "#1B5FD1", headline: "'JetBrains Mono', monospace", body: "'Inter', system-ui, sans-serif", mono: "'JetBrains Mono', monospace", serif: "'Literata', Georgia, serif", hand: "'Caveat', cursive", radius: 8 },
};
export const THEME_NAME = "lime";
export const TH = THEMES[THEME_NAME];

/** Copy brand.example.json to brand.json in an episode project. */
export const BRAND = brand;
