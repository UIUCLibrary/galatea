## v0.4.1 (2025-08-27)

### Feat

- add experimental Jinja2 support for merging data

### Fix

- merge_data.read_mapping_toml_data catches bad toml formatting

## v0.4.0 (2025-07-23)

### Feat

- galatea can merge data from alma records
- galatea uses a config to configure application
- Added 'authorized-terms check' subcommand as a replacement for `authority-check`
- resolving authorized terms with verbose will show diff
- authorized-terms command

### Fix

- init-mapper subcommand is now formatted correctly
- resolve_authorized_terms sniffs input tsv file dialect to match output if unknown dialect
- tab completion support added via argcomplete

## v0.3.1 (2025-03-06)

### Feat

- Remove relator terms
- Remove double quotations from notes fields
- add argcomplete support
- authority-check command added
- clean-tsv prints diff when --verbose flag is used
- Trailing periods are removed in the following fields: 650, 651, 655, 600, 610, 611, 700, 710, and 711
- Double dashes -- are removed and spaces are added after punctuation in the 710 field
- double dashes -- are replace with spaces in 610 field.
- Remove trailing punctuation 300
- Remove trailing punctuation from 260 and 264 fields
- tsv-clean removes brackets appearing in 260 and 264 fields
- Question marks from 260 and 264 fields

### Fix

- error message is shown when galatea is run without a subcommand

### Refactor

- Move tsv related functions into own module
- Use RowTransformer()

## v0.2.0 (2025-01-15)

## v0.1.0 (2024-10-08)

### BREAKING CHANGE

- if no output is selected with clean-tsv, it's assumed to be inplace

### Feat

- clean-tsv cleans up tsv file

### Fix

- version information is retained within the standalone distributions
