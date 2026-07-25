# Latin-English Wiktionary for macOS

Build a Latin–English dictionary for the macOS Dictionary app from the
machine-readable English Wiktionary data published by Kaikki.org.

The repository contains the conversion code and the Dictionary source files. It
does not include the large source dataset, Apple's Dictionary Development Kit,
or generated build artifacts.

## Requirements

- macOS
- Python 3.9 or newer
- `make`
- `xmllint`, used to validate the generated XML
- Apple's Dictionary Development Kit, needed only to compile the final
  `.dictionary` bundle

The Python code uses only the standard library. No packages need to be installed
with `pip`, and a virtual environment is optional. To use a particular Python
interpreter, pass it to Make, for example `make PYTHON=/path/to/python3 test`.

Building the complete dataset requires several gigabytes of free disk space.

## Download the Latin JSONL data

1. Open the [Kaikki.org Latin word list](https://kaikki.org/dictionary/Latin/words/index.html).
2. Use the **Download** link near the bottom of that page to obtain the
   post-processed Latin JSONL file. The current direct-download filename is
   [`kaikki.org-dictionary-Latin-words.jsonl`](https://kaikki.org/dictionary/Latin/words/kaikki.org-dictionary-Latin-words.jsonl).
3. Create the local data directory and place the file at:

   ```text
   data/raw/kaikki.org-dictionary-Latin-words.jsonl
   ```

For example:

```sh
mkdir -p data/raw
mv /path/to/kaikki.org-dictionary-Latin-words.jsonl data/raw/
```

Kaikki.org regenerates its Wiktionary extracts regularly, so results can change
when the source file is updated.

## Obtain the Dictionary Development Kit

The Dictionary Development Kit is an older Apple tool and is not included in
this repository or in a normal Xcode installation.

1. Sign in to [Apple Developer Downloads](https://developer.apple.com/download/all/)
   with an Apple Account.
2. Search the downloads for **Additional Tools for Xcode** and download a
   package that contains `Dictionary Development Kit`.
3. Copy or rename that directory into the repository root as
   `DictionaryDevelopmentKit`.
4. Confirm that this file exists:

   ```text
   DictionaryDevelopmentKit/bin/build_dict.sh
   ```

The historical setup and build process is discussed in
[How can I create a dictionary for Mac OS X?](https://apple.stackexchange.com/questions/80099/how-can-i-create-a-dictionary-for-mac-os-x).
This project keeps the kit inside the repository working directory instead of
installing it globally; the directory is excluded from Git.

The expected local layout is therefore:

```text
Latin-English-Wiktionary-macOS/
├── DictionaryDevelopmentKit/       # local, not tracked
│   └── bin/build_dict.sh
├── data/
│   └── raw/
│       └── kaikki.org-dictionary-Latin-words.jsonl  # local, not tracked
├── dictionary/
├── src/
├── tests/
└── Makefile
```

## Build and test

Run the following commands from the repository root:

```sh
make test
make xml
make validate
make dictionary
```

The commands perform these steps:

- `make test` runs the unit tests.
- `make xml` streams the JSONL source into Apple Dictionary XML and writes a
  build report.
- `make validate` checks that the complete XML is well-formed.
- `make dictionary` invokes Apple's Dictionary Development Kit to compile the
  installable bundle.

Generated files are written to:

```text
build/Latin-English-Wiktionary.xml
build/report.json
build/objects/Latin-English Wiktionary.dictionary
```

The legacy Dictionary Development Kit may print locale or remote DTD warnings.
The build is successful when it ends with `Finished building` and the
`.dictionary` bundle exists.

## Install the dictionary

Quit Dictionary if it is running, then copy the compiled bundle into your user
dictionary directory:

```sh
mkdir -p ~/Library/Dictionaries
cp -R "build/objects/Latin-English Wiktionary.dictionary" ~/Library/Dictionaries/
```

Reopen Dictionary and enable **Latin-English Wiktionary** in Dictionary's
settings if it is not enabled automatically. When replacing an older build,
quit and reopen Dictionary so that it reloads the bundle.

## Data conversion

The streaming builder keeps memory usage bounded while processing the complete
JSONL file. It derives display headings from Wiktionary's rendered head-template
expansion instead of trusting inconsistent `forms[].canonical` metadata.

Wiktextract represents nested Wiktionary definitions as root-to-leaf gloss
paths. The builder formats those paths as readable flat definitions, removes a
repeated parent when a qualified leaf restates it, and suppresses a standalone
definition when the following definition is its complete colon extension.

Known source-specific corrections can be added to `config/overrides.json`, keyed
as `word|part-of-speech`. Supported fields are `heads`, `subtitle`, and
`definitions`.

## Repository policy

The source JSONL, Dictionary Development Kit, generated XML, and compiled
dictionary bundle are intentionally excluded from Git. This keeps the repository
small and avoids redistributing Apple's development tools.

## License and attribution

The generated dictionary data is derived from Wiktionary and is subject to the
Creative Commons Attribution-ShareAlike 4.0 license. See [LICENSE](LICENSE).

Kaikki.org requests attribution to the Wiktextract project and its author when
the data is used in research. See the download page for its current citation
guidance and extraction metadata.
