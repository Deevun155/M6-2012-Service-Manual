import fitz  # PyMuPDF
import re

input_pdf_name = "2012 Mazda 6 Factory Service Manual.pdf"

# ==============================================================================
# 1. THE AUTOMOTIVE MEGA-DICTIONARY
# ==============================================================================
AUTOMOTIVE_VOCAB = [
    # General / Action Words
    "TROUBLESHOOTING", "IDENTIFICATION", "MALFUNCTIONING", "INITIALIZATION",
    "PERSONALIZATION", "INSTRUMENTATION", "SPECIFICATION", "CONFIGURATION",
    "COMMUNICATION", "INTERMITTENT", "INSUFFICIENT", "ACCELERATION",
    "DECELERATION", "CONDITIONER", "TRANSMISSION", "REFRIGERANT",
    "TEMPERATURE", "PERFORMANCE", "INSTALLATION", "DISASSEMBLY",
    "MEASUREMENT", "INFORMATION", "COMBINATION", "ILLUMINATION",
    "ENTERTAINMENT", "MAINTENANCE", "CONVENTIONAL", "COMPARTMENT",
    "REPLACEMENT", "LUBRICATION", "OVERHEATING", "CONSUMPTION",
    "PRECAUTION", "DIAGNOSTIC", "DIAGNOSIS", "INSPECTION", "OPERATION",
    "PROCEDURES", "CHARGING", "RECOVERY", "PRESSURE", "LOCATION", "ABSOLUTE",
    "POSITION", "DIAGRAM", "REMOVAL", "COMMAND", "KNOCKING", "PINGING",
    "ECONOMY", "WARNINGS", "CAUTIONS", "FUNCTION", "WORKSHOP", "SYMPTOM",
    "MONITORING", "INDICATOR", "INTERLOCK", "OPERATING", "CONTROL", "SERVICE",
    "MANUAL", "REPAIR", "VERIFY", "ASSIST", "ENOUGH", "WHILE", "BLOWN",
    "INDEX", "NOISE", "FRONT", "REAR", "LEFT", "RIGHT", "INNER", "OUTER",
    "UPPER", "LOWER", "AMOUNT", "ACTIVE", "MODES", "FOGGED", "VEHICLE",
    "DYNAMIC", "DEFECTIVE", "FREEZE", "FRAME", "SECURITY", "RECEIVER",
    "KEYLESS", "ADVANCED", "ENTRY", "GENERAL", "PROCEDURE", "THIS",
    "JACKING", "POSITIONS", "LIFT", "RIGID", "DEVICE", "RELATIONSHIP",
    "MELTING", "MAIN", "WILL", "ERRATIC", "WORK", "SUFFICIENTLY", "ALWAYS",
    "WIDE", "CONDITIONS", "TIMING", "ELECTRONIC", "FOLLOWING", "LIGHTS",
    "WITH", "WARNING", "MALFUNCTION", "BASIC", "SHIFT", "POINT", "HIGH",
    "KICKDOWN", "SLIPS", "WHEN", "UPSHIFTING", "DOWNSHIFTING", "ACCELERATING",
    "EXCESSIVE", "BRAKING", "DOWN", "MAGNETIC", "WEIGHT", "CALIBRATION",
    "ENCOUNTERING", "FOREIGN", "MOVING", "DRIVER", "SIDE", "INOPERATIVE",
    "WINDOWS", "USING", "IMMOBILIZER", "FOREWORD", "ENTIRE", "CONFIRMATION",
    "RECEPTION", "SIRIUS", "SATELLITE", "FILE", "SELECTION", "QUICK",
    "WITHOUT", "ILLUMINATE", "ILLUMINATES", "TAILLIGHTS", "INDICATION",
    "EXTERIOR", "AERODYNAMIC", "SYSTEMS", "RAIN", "INITIAL", "SETTING",
    "DISENGAGE", "SHIFTED", "UPSHIFT", "DOWNSHIFT", "RECEIVE", "TRANSMIT",
    
    # Parts / Mechanical
    "WINDSHIELD", "CROSSMEMBER", "SUSPENSION", "STABILIZER", "INTERMEDIATE",
    "COMPLIANCE", "CONTINUOUSLY", "CLEARANCE", "THERMOSTAT", "ACCELERATOR",
    "BAROMETRIC", "CRANKSHAFT", "DEACTIVATION", "DEPLOYMENT", "MICROPHONE",
    "NAVIGATION", "ACTUATOR", "ASSEMBLY", "ALIGNMENT", "ABSORBER", "DISPOSAL",
    "TRANSVERSE", "TECHNICAL", "BLEEDING", "CYLINDER", "STABILITY",
    "TRANSAXLE", "CLEARING", "MULTIPLEX", "VIBRATION", "CAMSHAFT",
    "RESTRAINTS", "PASSENGER", "DISCHARGE", "AMPLIFIER", "EVAPORATOR",
    "CLUTCH", "SENSOR", "MODULE", "DISPLAY", "EXHAUST", "COOLING", "COOLANT",
    "MANIFOLD", "VARIABLE", "STEERING", "BATTERY", "IGNITION", "TERMINAL",
    "RADIATOR", "LINKAGE", "WIRING", "SYSTEM", "CLIMATE", "FILTER", "VENTS",
    "POWER", "FLUID", "DRIVE", "SHAFT", "WHEEL", "BRAKE", "PANEL", "GLASS",
    "DOOR", "SEAT", "LOCK", "TRUNK", "HOOD", "BUMPER", "LIGHT", "SWITCH",
    "RELAY", "FUSE", "MOTOR", "PUMP", "VALVE", "BELT", "CHAIN", "GEAR",
    "JOINT", "MOUNT", "COVER", "GUARD", "BOARD", "AUDIO", "RADIO", "VIDEO",
    "CAMERA", "BLIND", "SPOT", "RADAR", "SMOKE", "ODOR", "LEAKAGE", "INTAKE",
    "ENGINE", "LINE", "DRIVELINE", "AXLE", "TIRE", "UNIT", "DISC", "CALIPER",
    "PARKING", "ROTOR", "PAD", "SHOE", "DRUM", "MASTER", "BOOSTER",
    "EMERGENCY", "TRACTION", "STRUT", "SHOCK", "SPRING", "ARM", "BUSHING",
    "BALL", "LINK", "SWAY", "BAR", "RACK", "PINION", "KNUCKLE", "PISTON",
    "HEAD", "BLOCK", "GASKET", "PAN", "HOSE", "TENSIONER", "PULLEY", "MUFFLER",
    "CATALYTIC", "CONVERTER", "EMISSION", "AUTOMATIC", "FLYWHEEL", "TORQUE",
    "DIFFERENTIAL", "BOOT", "ALTERNATOR", "STARTER", "SPARK", "PLUG", "COIL",
    "WIRE", "HARNESS", "CONNECTOR", "HEATER", "CORE", "BLOWER", "FAN",
    "COMPRESSOR", "CONDENSER", "VENT", "DUCT", "LAMP", "BULB", "HEADLIGHT",
    "TAILLIGHT", "WIPER", "WASHER", "WINDOW", "MIRROR", "AIRBAG", "RESTRAINT",
    "DASH", "CONSOLE", "FENDER", "GRILLE", "DEFROSTER", "SOLENOID", "TUMBLE",
    "CANISTER", "RATIO", "COWL", "TRIM", "CUSHION", "WARMER", "FILLER",
    "STRIKER", "TRANSMITTER", "REGISTRATION", "DRAIN", "PILLAR", "WATER",
    "IDLE", "CURTAIN", "INSTRUMENT",
    
    # Specific Diagnostic Codes / Model Codes
    "FS5A", "AY6A", "B00A0", "B00B5", "B10C6", "B10C7", "B10C8", "B10C9", 
    "B11FD", "B1210", "U0423", "U3003"
]

# Short words we need to process separately so they don't corrupt larger words
SHORT_VOCAB = ["AIR", "OIL", "DTC", "PID", "PCM", "TCM", "BCM", "ABS", "DSC", "TPMS", 
               "MZR", "MZI", "HVAC", "SST", "MIL", "WMA", "MIX", "DIM", "LID", "ITS", 
               "IN", "IS", "IT", "ON", "OF", "OR", "TO", "UP", "ID", "IG"]

# Sort by length descending so longer words match first (e.g., checks DIAGNOSTIC before DIAG)
AUTOMOTIVE_VOCAB.sort(key=len, reverse=True)
SHORT_VOCAB.sort(key=len, reverse=True)


print("Step 1: Mapping the existing PDF chunks...")
doc = fitz.open(input_pdf_name)
toc_links = []

for page_num in range(54):
    for link in doc[page_num].get_links():
        if link["kind"] == fitz.LINK_GOTO:
            toc_links.append(link["page"])

valid_starts = sorted(list(set(toc_links)))

def get_target_url(target_page):
    for i in range(len(valid_starts)):
        start = valid_starts[i]
        end = valid_starts[i+1] - 1 if i+1 < len(valid_starts) else len(doc)
        if start <= target_page <= end:
            offset = (target_page - start) + 1
            return f"chunks/section_{start}.pdf#page={offset}"
    return None

def shred_spaces(text):
    for word in AUTOMOTIVE_VOCAB:
        pattern = r'\b' + r'\s*'.join(list(word)) + r'\b'
        text = re.sub(pattern, word, text, flags=re.IGNORECASE)
        
    for word in SHORT_VOCAB:
        pattern = r'\b' + r'\s*'.join(list(word)) + r'\b'
        text = re.sub(pattern, word, text, flags=re.IGNORECASE)

    # Reconnect broken digits (e.g. "2 0 1 2" -> "2012")
    for _ in range(3):
        text = re.sub(r'\b(\d)\s+(\d)\b', r'\1\2', text)

    # TYPOGRAPHY KERNING REPAIRS (Fixes Slashes, Brackets, Hex Codes, etc.)
    text = re.sub(r'\s*/\s*', '/', text)
    text = re.sub(r'\[\s+', '[', text)
    text = re.sub(r'\s+\]', ']', text)
    text = re.sub(r'\(\s+', '(', text)
    text = re.sub(r'\s+\)', ')', text)
    text = re.sub(r'([A-Za-z0-9])\s*-\s*([A-Za-z0-9])', r'\1-\2', text)
    text = re.sub(r'(\d)\s*\.\s*(\d)', r'\1.\2', text)
    text = re.sub(r'\s*:\s*', ': ', text)
    
    # HEX SUFFIX FIXER: Reconnects hex codes in DTCs (e.g., "7 B" -> "7B", "1 F" -> "1F")
    text = re.sub(r'\b(\d)\s+([A-F])\b', r'\1\2', text, flags=re.IGNORECASE)
    
    text = re.sub(r'W\s*orkshop', 'Workshop', text, flags=re.IGNORECASE)
    
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text

print("Step 2: Activating Regex Shredder & Multi-Line Fusion Engine...")
raw_lines = []
radar_flags = 0

for page_num in range(54):
    page = doc[page_num]
    links = page.get_links()
    dict_data = page.get_text("dict")
    
    lines = []
    for block in dict_data.get("blocks", []):
        if block.get("type") == 0:
            for line in block.get("lines", []):
                text = "".join([s["text"] for s in line["spans"]]).strip()
                if len(text) < 3: continue
                
                color = line["spans"][0]["color"] if line["spans"] else 0
                size = line["spans"][0]["size"] if line["spans"] else 0
                y0 = line["bbox"][1]
                rect = fitz.Rect(line["bbox"])
                
                lines.append({
                    "text": text, "rect": rect, "color": color, 
                    "size": size, "y0": y0
                })
    
    lines.sort(key=lambda x: x["y0"])
    
    for line in lines:
        text = line["text"]
        text_lower = text.lower()
        
        if "previous" in text_lower or "next" in text_lower or "back to top" in text_lower: continue
        if text_lower.startswith("id0") or text_lower.startswith("id1"): continue
        if text_lower.startswith("--- page"): continue
        
        is_link = False
        target_url = ""
        for link in links:
            if link["kind"] == fitz.LINK_GOTO and fitz.Rect(link["from"]).intersects(line["rect"]):
                is_link = True
                target_url = get_target_url(link["page"])
                break
        
        clean_text = shred_spaces(text).replace("•", "").strip()
        
        # ==============================================================================
        # THE KERNING RADAR
        # Scans the healed text for floating single letters and prints a warning
        # ==============================================================================
        words = clean_text.split()
        if any(len(w) == 1 and w.isalpha() and w.upper() not in ["A", "I"] for w in words):
            print(f"⚠️ RADAR - Missing word detected in: '{clean_text}'")
            radar_flags += 1

        searchable_string = re.sub(r'[^a-z0-9]', '', clean_text.lower())
        
        item_type = 'normal'
        if is_link and target_url:
            item_type = 'link'
        else:
            r = (line["color"] >> 16) & 255
            g = (line["color"] >> 8) & 255
            b = line["color"] & 255
            if r > 150 and g < 100 and b < 100:
                item_type = 'sub'
                clean_text = clean_text.upper()
            elif line["size"] > 11:
                item_type = 'main'
                
        raw_lines.append({
            'text': clean_text,
            'url': target_url,
            'type': item_type,
            'searchable': searchable_string
        })

print(f"\nRadar Check Complete: Found {radar_flags} broken strings you might want to add to the Dictionary.\n")

merged_lines = []
for item in raw_lines:
    if item['type'] == 'link' and len(merged_lines) > 0 and merged_lines[-1]['type'] == 'link':
        if merged_lines[-1]['url'] == item['url']:
            merged_lines[-1]['text'] += " " + item['text']
            merged_lines[-1]['searchable'] += item['searchable']
            continue
    merged_lines.append(item)

print("Step 3: Constructing Drop-Down Folders...")
tree = []
current_main = None
current_sub = None

for item in merged_lines:
    if item['type'] == 'main':
        current_main = {'text': item['text'], 'searchable': item['searchable'], 'subs': [], 'links': []}
        tree.append(current_main)
        current_sub = None
    elif item['type'] == 'sub':
        if not current_main:
            current_main = {'text': "General / Misc", 'searchable': "generalmisc", 'subs': [], 'links': []}
            tree.append(current_main)
        current_sub = {'text': item['text'], 'searchable': item['searchable'], 'links': []}
        current_main['subs'].append(current_sub)
    elif item['type'] == 'link':
        if current_sub:
            current_sub['links'].append(item)
            current_sub['searchable'] += " " + item['searchable']
            current_main['searchable'] += " " + item['searchable']
        elif current_main:
            current_main['links'].append(item)
            current_main['searchable'] += " " + item['searchable']
        else:
            current_main = {'text': "General / Misc", 'searchable': "generalmisc " + item['searchable'], 'subs': [], 'links': [item]}
            tree.append(current_main)

print("Step 4: Generating Flawless HTML...")

html_links = ""
for main in tree:
    if not main['subs'] and not main['links']: continue
    
    html_links += f'<details class="main-details searchable" open data-search="{main["searchable"]}"><summary class="main-header">{main["text"]}</summary>\n'
    
    for link in main['links']:
        html_links += f'<a href="{link["url"]}" class="link-item searchable" data-search="{link["searchable"]}">{link["text"]}</a>\n'
        
    for sub in main['subs']:
        if not sub['links']: continue
        html_links += f'<details class="sub-details searchable" data-search="{sub["searchable"]}"><summary class="sub-header">{sub["text"]}</summary>\n'
        for link in sub['links']:
            html_links += f'<a href="{link["url"]}" class="link-item searchable" data-search="{link["searchable"]}">{link["text"]}</a>\n'
        html_links += '</details>\n'
        
    html_links += '</details>\n'

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Mazda 6 Service Manual</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 10px; background: #fff; margin: 0; line-height: 1.3; }}
        h2 {{ font-size: 20px; margin: 5px 0 15px 0; color: #111; text-align: center; }}
        
        .search-container {{ position: sticky; top: 0; background: #fff; padding: 10px 0; border-bottom: 1px solid #ddd; margin-bottom: 12px; z-index: 100; }}
        input {{ width: 100%; padding: 12px; font-size: 16px; border: 1px solid #888; border-radius: 4px; box-sizing: border-box; }}
        input:focus {{ outline: none; border-color: #005A9E; box-shadow: 0 0 0 2px rgba(0, 90, 158, 0.2); }}
        #results {{ padding-bottom: 30px; }}
        
        /* Dropdown Folder Styling */
        details {{ margin-bottom: 4px; }}
        summary {{ cursor: pointer; outline: none; list-style-position: inside; }}
        
        .main-header {{ font-size: 15px; font-weight: bold; color: #000; background: #f0f4f8; padding: 8px 10px; border-left: 4px solid #005A9E; border-radius: 3px; }}
        .sub-header {{ font-size: 13px; font-weight: bold; color: #a80000; padding: 6px 10px; margin-top: 4px; margin-left: 15px; }}
        
        /* Standard Hyperlink Styling */
        .link-item {{ display: list-item; list-style-type: disc; color: #005A9E; text-decoration: underline; margin: 6px 0 6px 45px; font-size: 14px; }}
        .link-item:hover {{ color: #cc0000; }}
        
        .hidden {{ display: none !important; }}
    </style>
</head>
<body>
    <h2>Mazda 6 Manual</h2>
    
    <div class="search-container">
        <input type="text" id="search" placeholder="Search 'radiator', 'torque'..." onkeyup="filter()">
    </div>
    
    <div id="results">
        {html_links}
    </div>
    
    <script>
        function filter() {{
            let input = document.getElementById('search').value.toLowerCase().replace(/[^a-z0-9]/g, '');
            let elements = document.getElementsByClassName('searchable');
            let details = document.getElementsByTagName('details');
            
            let isSearching = input.length > 0;
            
            // Auto-expand folders if the user is typing
            for (let i = 0; i < details.length; i++) {{
                if (isSearching) {{
                    details[i].open = true;
                }} else {{
                    if (details[i].classList.contains('sub-details')) details[i].open = false;
                    if (details[i].classList.contains('main-details')) details[i].open = true;
                }}
            }}

            for (let i = 0; i < elements.length; i++) {{
                let searchData = elements[i].getAttribute('data-search');
                if (searchData.includes(input)) {{
                    elements[i].classList.remove('hidden');
                }} else {{
                    elements[i].classList.add('hidden');
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
print("\nAll Done! Open index.html in your browser.")