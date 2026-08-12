export const sourceLabels = {
  "facebook-page": "FB Page",
  "facebook-group": "FB Group",
  "deep-research": "Deep Research"
} as const;

export type SourceKey = keyof typeof sourceLabels;

export function sourceLabel(source: SourceKey) {
  return sourceLabels[source];
}
