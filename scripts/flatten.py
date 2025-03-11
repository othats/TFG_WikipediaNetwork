import bz2
import os

input_file = "input/ptwiki-latest-pages-articles.xml.bz2"
output_file = "input/ptwiki-latest-pages-articles.pageperline.xml"

page = False

# get size of file 
total_size = os.path.getsize(input_file) # bytes
last_percent = 0

# opening input file as r, output file as w
with bz2.open(input_file, "rt", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:

    while True:
        line = infile.readline()
        if not line: 
            break
        
        line = line.strip()

        # calculate estimated progress (not actual because file is compressed)
        current_position = infile.tell() # función tell retorna el offset de bytes leídos
        percent = int((current_position / total_size) * 100)
        if percent > last_percent:
            last_percent = percent
            print(f"Progress: {percent}%", end="\r", flush=True)

        # skip final line of the dump
        if line == '</mediawiki>': 
            continue

        # skip lines until first page 
        if not page: 
            if line != '<page>':
                continue   
            else:
                page = True

        # write line to output file
        outfile.write(line)

        # when we reach end of page, add new line to separate pages 
        if line == '</page>':
            outfile.write("\n")

print("\nProcessing complete.")
