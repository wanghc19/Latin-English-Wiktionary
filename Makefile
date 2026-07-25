PYTHON ?= python3
SOURCE_JSONL ?= data/raw/kaikki.org-dictionary-Latin-words.jsonl
BUILD_DIR = build
XML = $(BUILD_DIR)/Latin-English-Wiktionary.xml
REPORT = $(BUILD_DIR)/report.json
DICT_NAME = Latin-English Wiktionary

.PHONY: all xml test validate dictionary clean

all: dictionary

xml: $(XML)

$(XML): src/build_dictionary.py config/overrides.json $(SOURCE_JSONL)
	mkdir -p $(BUILD_DIR)
	$(PYTHON) src/build_dictionary.py \
		--input $(SOURCE_JSONL) \
		--output $(XML) \
		--report $(REPORT) \
		--overrides config/overrides.json

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

validate: $(XML)
	xmllint --stream --noout $(XML)

dictionary: validate
	DICT_DEV_KIT_OBJ_DIR="$(CURDIR)/$(BUILD_DIR)/objects" \
		"$(CURDIR)/DictionaryDevelopmentKit/bin/build_dict.sh" \
		"$(DICT_NAME)" "$(XML)" \
		"dictionary/LatinEnglish.css" "dictionary/Info.plist"

clean:
	rm -rf $(BUILD_DIR)
