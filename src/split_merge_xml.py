import os

# Number of header lines at the start of the XML file
HEADER_LINES = 2
# Number of footer lines at the end of the XML file
FOOTER_LINES = 1

def split_xml(input_file, parts=4, output_prefix="la-en-dict"):
    """
    Split a large XML file into multiple smaller files.
    Each entry is assumed to be one line.
    The header and footer are preserved in each part.
    
    Args:
        input_file (str): Path to the original XML file.
        parts (int): Number of parts to split into.
        output_prefix (str): Prefix for output files.
    """
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Preserve header and footer
    header = lines[:HEADER_LINES]  # first HEADER_LINES lines
    footer = lines[-FOOTER_LINES:] # last FOOTER_LINES lines
    body = lines[HEADER_LINES:-FOOTER_LINES]  # lines containing <d:entry>

    total_entries = len(body)
    per_part = (total_entries + parts - 1) // parts  # round up

    for i in range(parts):
        part_lines = body[i*per_part:(i+1)*per_part]
        if not part_lines:
            continue
        output_file = f"{output_prefix}{i+1}.xml"
        with open(output_file, "w", encoding="utf-8") as out:
            out.writelines(header + part_lines + footer)
        print(f"Written {output_file} ({len(part_lines)} entries)")

def merge_xml(input_files, output_file="la-en-dict.xml"):
    """
    Merge multiple XML parts back into a single XML file.
    The header is taken from the first file, and the footer from the last file.
    
    Args:
        input_files (list): List of XML part filenames in order.
        output_file (str): Filename of the merged XML.
    """
    merged_entries = []

    for idx, file in enumerate(input_files):
        with open(file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if idx == 0:
            # keep the header from the first file
            merged_entries.extend(lines[:HEADER_LINES])
        # keep the body (skip header/footer)
        merged_entries.extend(lines[HEADER_LINES:-FOOTER_LINES])
        if idx == len(input_files) - 1:
            # keep the footer from the last file
            merged_entries.extend(lines[-FOOTER_LINES:])

    with open(output_file, "w", encoding="utf-8") as out:
        out.writelines(merged_entries)
    print(f"Merged {len(input_files)} files into {output_file}")

# =========================
# Example Usage
# =========================
if __name__ == "__main__":
    # To split a large XML file into 4 parts
    split_xml("la-en-dict.xml", parts=4)

    # To merge parts back into a single XML
    # merge_xml(["la-en-dict1.xml", "la-en-dict2.xml", "la-en-dict3.xml", "la-en-dict4.xml"])