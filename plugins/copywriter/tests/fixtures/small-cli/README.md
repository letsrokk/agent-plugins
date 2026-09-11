# Linecount

[![Fixture](https://img.shields.io/badge/fixture-synthetic-blue)](#license)

Linecount counts lines from standard input. This is a local synthetic evaluation fixture, not a published package.

<a id="overview"></a>
## Overview

It gives a line count for piped text. Empty input counts as zero, and a final newline does not add an empty line. It does not inspect files by path or watch changes.

## First use

Requires Node.js 24 or later. No dependencies or installation are needed. From this directory:

```sh
printf 'red\nblue\n' | node count.mjs
```

Expected output:

```text
2
```

See [behavior](docs/behavior.md) for input rules.

## License

Fixture text and code follow the repository license. Preserve this wording during targeted edits.
