import fitz  # PyMuPDF
import re
import os

input_pdf_name = "2012 Mazda 6 Factory Service Manual.pdf"
output_dir = "chunks"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print("Step 1: Extracting link destinations from the TOC...")
doc = fitz.open(input_pdf_name)
toc_data = []

# Loop through the first 54 pages to steal the hidden links
for page_num in range(54):
    page = doc[page_num]
    for link in page.get_links():
        if link["kind"] == fitz.LINK_GOTO:
            raw_text = page.get_textbox(link["from"]).replace('\n', ' ').strip()
            clean_text = re.sub(r'\s+', ' ', raw_text)

            if len(clean_text) < 4: continue
            if "previous" in clean_text.lower() or "next" in clean_text.lower() or "back to top" in clean_text.lower(): continue
            if clean_text.lower().startswith("id0") or clean_text.lower().startswith("id1"): continue

            clean_text = clean_text.replace("I N ", "IN ").replace("RADI ATOR", "RADIATOR").replace("DI AGNOSTI C", "DIAGNOSTIC").replace("W I NDSHI ELD", "WINDSHIELD")
            toc_data.append({"title": clean_text, "start_page": link["page"]})

toc_data.sort(key=lambda x: x["start_page"])

unique_toc = []
last_page = -1
for item in toc_data:
    if item["start_page"] != last_page:
        unique_toc.append(item)
        last_page = item["start_page"]

# Define the boundaries of every chunk so we know where to point the translated links
total_pages = len(doc)
for i in range(len(unique_toc)):
    if i + 1 < len(unique_toc):
        unique_toc[i]["end_page"] = unique_toc[i + 1]["start_page"] - 1
    else:
        unique_toc[i]["end_page"] = total_pages - 1

def get_target_url(target_page_num):
    # Find which chunk owns the target page
    for chunk in unique_toc:
        if chunk["start_page"] <= target_page_num <= chunk["end_page"]:
            # Calculate exactly which page inside the chunk it lands on
            offset = (target_page_num - chunk["start_page"]) + 1
            # Format it as a standard web link with a PDF page jumper
            return f"section_{chunk['start_page']}.pdf#page={offset}"
    return None

print(f"Found {len(unique_toc)} unique sections. Slicing and translating links... (This will take a few minutes)")

html_links = ""

for i in range(len(unique_toc)):
    start = unique_toc[i]["start_page"]
    end = unique_toc[i]["end_page"]

    chunk_filename = f"section_{start}.pdf"
    chunk_path = os.path.join(output_dir, chunk_filename)
    
    chunk_doc = fitz.open()
    chunk_doc.insert_pdf(doc, from_page=start, to_page=end)

    # --- THE FIX: Read links from the ORIGINAL master document ---
    for offset, orig_page_num in enumerate(range(start, end + 1)):
        orig_page = doc[orig_page_num]
        orig_links = orig_page.get_links()
        
        chunk_page = chunk_doc[offset]
        
        # Wipe any surviving internal links from the copy process to prevent duplicates
        for existing_link in chunk_page.get_links():
            chunk_page.delete_link(existing_link)
            
        # Inject the translated Web URIs
        for link in orig_links:
            if link["kind"] == fitz.LINK_GOTO:
                original_target = link["page"]
                target_url = get_target_url(original_target)
                
                if target_url:
                    chunk_page.insert_link({
                        "kind": fitz.LINK_URI,
                        "from": link["from"],
                        "uri": target_url
                    })

    # Save the chunk, overwriting old ones if necessary
    chunk_doc.save(chunk_path)
    chunk_doc.close()

    searchable_string = re.sub(r'[^a-z0-9]', '', unique_toc[i]['title'].lower())
    html_links += f"""
        <a href="chunks/{chunk_filename}" class="result" data-search="{searchable_string}">
            <span class="title">{unique_toc[i]['title']}</span>
        </a>
    """
    
    if (i + 1) % 50 == 0:
        print(f"Processed {i + 1} / {len(unique_toc)} chunks...")

print("\nStep 3: Building the Index Web Page...")

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Mazda 6 Service Manual</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; padding: 15px; background: #f4f4f9; margin: 0; }}
        h2 {{ color: #1e293b; text-align: center; }}
        input {{ width: 100%; padding: 15px; font-size: 18px; border: 2px solid #cbd5e1; border-radius: 8px; margin-bottom: 20px; box-sizing: border-box; }}
        .result {{ background: white; padding: 15px; margin-bottom: 10px; border-radius: 8px; display: block; text-decoration: none; color: #334155; font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .result:active {{ background: #e2e8f0; }}
        .hidden {{ display: none !important; }}
    </style>
</head>
<body>
    <h2>Mazda 6 Manual Search</h2>
    <input type="text" id="search" placeholder="Search for 'radiator', 'torque'..." onkeyup="filter()">
    
    <div id="results">
        {html_links}
    </div>
    
    <script>
        function filter() {{
            let input = document.getElementById('search').value.toLowerCase().replace(/[^a-z0-9]/g, '');
            let results = document.getElementsByClassName('result');
            
            for (let i = 0; i < results.length; i++) {{
                let searchData = results[i].getAttribute('data-search');
                if (searchData.includes(input)) {{
                    results[i].classList.remove('hidden');
                }} else {{
                    results[i].classList.add('hidden');
                }}
            }}
        }}
    </script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

doc.close()
print("All Done! Open index.html in your browser.")