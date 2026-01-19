# Latin–English Wiktionary for macOS

This repository provides a **comprehensive Latin dictionary** formatted as a macOS `.dictionary` package, optimized for the Dictionary app and **three-finger lookup**. 

Wiktionary is one of the best **morphological analysis tools for Latin**, offering rich lexical data, inflection patterns, and part-of-speech information. This dictionary brings that data offline to macOS, making it ideal for classicists, linguists, and students who want a structured reference for Latin word forms and meanings.


## Data Sources

All dictionary entries are derived from Wiktionary.
The machine-readable JSONL files were obtained from Kaikki.org.

For details on Kaikki.org and its data processing pipeline, see Tatu Ylonen: [Wiktextract: Wiktionary as Machine-Readable Structured Data](http://www.lrec-conf.org/proceedings/lrec2022/pdf/2022.lrec-1.140.pdf), Proceedings of the 13th Conference on Language Resources and Evaluation (LREC), pp. 1317-1325, Marseille, 20-25 June 2022.

## Contents

The repository includes:

- `*.xml` — Original XML files of dictionary entries.  
- `*.css` — CSS files controlling the display style of entries in the Dictionary app.  
- `.dictionary` package ready for installation on macOS.

## Entry Format

Each entry is structured as follows:

```xml
<d:entry id="ENTRY_ID" d:title="WORD">
    <d:index d:value="WORD_VARIANT_1" />
    <d:index d:value="WORD_VARIANT_2" />
    <h1>WORD</h1>
    <p class="subhead">
        ( <span class="keyword">KEYWORD_1</span> ..., <span class="keyword">KEYWORD_N</span> ); 
        <span class="comment">COMMENT_TEXT</span>
    </p>
    <p class="pos">PART_OF_SPEECH</p>
    <p class="def">1. DEFINITION_1</p>
    <p class="def">2. DEFINITION_2</p>
    <!-- more definitions if present -->
</d:entry>

```

* **`ENTRY_ID`**: Unique identifier for the entry.
* **`WORD` / `WORD_VARIANT_X`**: Headword and variants.
* **`subhead`**: Contains keywords and additional comments.
* **`pos`**: Part of speech.
* **`def`**: Definitions, numbered sequentially.

This format ensures consistent rendering in macOS Dictionary and supports inline keywords, comments, and structured definitions.

## License

This dictionary is derived from Wiktionary data and is licensed under
the Creative Commons Attribution–ShareAlike 4.0 International (CC BY-SA 4.0).


## Installation

1. **Copy the `.dictionary` folder** (download it from the Release) to your Dictionaries folder:  
   Usually `~/Library/Dictionaries`.  
   You can open it from the Dictionary app by clicking **File → Open Dictionaries Folder** in the menu bar.

2. **Enable the dictionary**:  
   In the Dictionary app, go to **Dictionary → Settings** in the menu bar and select/check the newly added dictionary.

3. **Use the dictionary**:  
   Look up words offline using a **three-finger tap** or the search bar.


---

**Note:** Attribution to Wiktionary and Kaikki.org is required if this dictionary
is used in derivative works.

If you find any bugs, such as incorrect definitions or formatting errors, please feel free to open an issue on this repository. Your feedback is greatly appreciated!

