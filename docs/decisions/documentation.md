# Documentation decisions

[日本語](documentation.ja.md)

Closed decisions about the documents of this repository. The layout of the English and Japanese
pairs is in [`AGENTS.md`](../../AGENTS.md).

## Cross-link line under each H1

- **Decision** (2026-10-20): the line under the H1 of a paired document is a link and nothing
  else: `[日本語](<name>.ja.md)` in the English file and `[English](<name>.md)` in the Japanese
  file.
- **Alternatives turned down**: a blockquote line that spells the pointer out as a sentence
  (`> 日本語版は … を参照してください.`). It was offered during the work of
  [#61](https://github.com/semnil/notification-sound-db/pull/61) and turned down. Do not propose
  it again.

## 固有 and 測定失敗 in the Japanese documents are kept on purpose

What each of the two terms follows is in the pull request that kept them:
[#61](https://github.com/semnil/notification-sound-db/pull/61).
