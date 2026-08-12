export const sourceLabels = {
  "facebook-page": "FBページ",
  "facebook-group": "FBグループ",
  "deep-research": "DeepResearch"
} as const;

export type SourceKey = keyof typeof sourceLabels;

export function sourceLabel(source: SourceKey) {
  return sourceLabels[source];
}
