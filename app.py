from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import traceback

# Optional: used only if Excel is missing and internet is available
# Do a non-import check so static analyzers don't complain about missing packages.
import importlib

req_spec = importlib.util.find_spec("requests")
bs4_spec = importlib.util.find_spec("bs4")
HAS_REQUESTS = bool(req_spec and bs4_spec)

app = Flask(__name__)

FACULTY_EXCEL = "ECE_Faculty_Details_VSBEC.xlsx"   # expected file in project root
FACULTY_SHEET = None  # if your excel has a specific sheet name, set it here

def load_faculty_from_excel(path=FACULTY_EXCEL):
    """Load faculty data safely from Excel."""
    if not os.path.exists(path):
        return []

    try:
        df = pd.read_excel(path)
        if not isinstance(df, pd.DataFrame):
            return []

        # Clean headers (strip + lowercase)
        df.columns = [str(c).strip().lower() for c in df.columns]

        # Detect possible headers dynamically
        name_col = next((c for c in df.columns if "name" in c), None)
        desig_col = next((c for c in df.columns if "design" in c), None)
        spec_col = next((c for c in df.columns if "special" in c or "area" in c), None)
        doj_col = next((c for c in df.columns if "join" in c or "doj" in c), None)
        exp_col = next((c for c in df.columns if "exp" in c), None)

        rows = []
        for _, row in df.iterrows():
            name = str(row.get(name_col, "")).strip()
            if not name or name.lower() in ["nan", "none", ""]:
                continue

            desig = str(row.get(desig_col, "")).strip() if desig_col else ""
            spec = str(row.get(spec_col, "")).strip() if spec_col else ""
            doj = str(row.get(doj_col, "")).strip() if doj_col else ""
            exp = str(row.get(exp_col, "")).strip() if exp_col else ""

            rows.append({
                "Name": name,
                "Designation": desig,
                "Specialization": spec,
                "DateOfJoining": doj,
                "Experience": exp
            })

        print(f"[INFO] Loaded {len(rows)} faculty entries from Excel")
        return rows

    except Exception as e:
        print(f"❌ Error reading faculty Excel: {e}")
        return []



def fetch_faculty_from_site():
    """Try fetching ECE faculty list from https://vsbec.edu.in/ece/ (best-effort).
       Requires requests and bs4. Returns same row format as load_faculty_from_excel."""
    if not HAS_REQUESTS:
        return None

    # Import lazily to avoid top-level import resolution errors in environments
    # where requests/bs4 may not be installed.
    import importlib
    try:
        requests = importlib.import_module('requests')
        bs4 = importlib.import_module('bs4')
        BeautifulSoup = getattr(bs4, 'BeautifulSoup')
    except Exception:
        # If imports fail at runtime, bail out so function can return None gracefully.
        return None

    url = "https://vsbec.edu.in/ece/"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")

        # Best-effort: find faculty section or table items; site structure can change.
        # We'll look for common patterns: lists, tables, cards with faculty names + designation.
        rows = []

        # Try to find elements with 'faculty' in class or id
        faculty_section = soup.find(lambda tag: tag.name in ['div','section'] and 'faculty' in (tag.get('class') or []) )
        if not faculty_section:
            # fallback: look for links or headings that look like faculty names (h3/h4)
            faculty_section = soup

        # find possible name tags inside
        candidates = faculty_section.find_all(['h2','h3','h4','p','li','td','span','div'])
        # naive extraction: pick texts that look like "Dr." or contain initials and title words
        for tag in candidates:
            text = tag.get_text(separator=' ', strip=True)
            if not text:
                continue
            # Heuristics to detect a faculty line:
            if ('dr ' in text.lower() or text.count(' ') <= 5) and any(x in text.lower() for x in ['prof', 'assistant', 'associate', 'dr.', 'mr.', 'ms.','mrs.']):
                # attempt to split name / designation
                parts = text.split('-')
                name = parts[0].strip()
                desig = parts[1].strip() if len(parts) > 1 else ''
                rows.append({
                    'Name': name,
                    'Designation': desig,
                    'DateOfJoining': '',
                    'Experience': '',
                    'Specialization': ''
                })
        # Remove duplicates by name
        seen = set()
        uniq = []
        for r in rows:
            nm = r['Name'].lower()
            if nm not in seen and nm not in ['','faculty']:
                seen.add(nm)
                uniq.append(r)
        return uniq if uniq else None
    except Exception:
        # any error -> return None
        return None

# Load faculty data at startup (first try excel, then try web)
faculty_rows = load_faculty_from_excel()
if not faculty_rows:
    faculty_rows = fetch_faculty_from_site()

# For debugging: print how many loaded
print(f"[INFO] Loaded faculty rows: {len(faculty_rows) if faculty_rows else 0}")

# Simple helper to build HTML table or list
def faculty_html(rows):
    if not rows:
        return "<p>❌ No faculty data available.</p>"

    html = [
        "<div class='table-box'>",
        "<div style='overflow-x:auto;'>",
        "<table class='faculty-table'>",
        "<thead><tr><th>Name</th><th>Designation</th><th>Specialization</th><th>Qualification</th><th>Experience</th></tr></thead>",
        "<tbody>"
    ]

    for r in rows:
        name = r.get('Name', '')
        desig = r.get('Designation', '')
        spec = r.get('Specialization', '')
        qual = r.get('Qualification', '')
        exp = r.get('Experience', '')
        html.append(f"<tr><td>{name}</td><td>{desig}</td><td>{spec}</td><td>{qual}</td><td>{exp}</td></tr>")

    html.append("</tbody></table></div></div>")
    return ''.join(html)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get', methods=['POST'])
def get_bot_response():
    try:
        user_input = request.form.get('msg','').strip().lower()
        if not user_input:
            return jsonify({'reply': "Please type a question."})

        # Faculty queries (broad matching)
        if any(k in user_input for k in ['faculty','staff','teacher','professor','who is','list of faculty','faculty details']):
            return jsonify({'reply': faculty_html(faculty_rows)})


        # Labs
        if 'lab' in user_input:
            # you can later load from excel; for now a sample HTML table
            lab_html = """
            <div class='table-box'>
            <table class='faculty-table'>
            <thead><tr><th>Semester</th><th>Lab Name</th><th>Details</th></tr></thead>
            <tbody>
            <tr><td>2nd Sem</td><td>Electronic Devices & Circuits Lab</td><td>Practical on diodes, BJT, FET amplifiers.</td></tr>
            <tr><td>2nd Sem</td><td>Digital Electronics Lab</td><td>Combinational & sequential logic experiments.</td></tr>
            <tr><td>2nd Sem</td><td>Simulation Lab</td><td>MATLAB & Multisim based experiments.</td></tr>
            </tbody></table></div>
            """
            return jsonify({'reply': lab_html})

        # Department
        if 'department' in user_input or 'ece' in user_input:
            return jsonify({'reply': '<a href="https://vsbec.edu.in/ece/" target="_blank">Visit ECE Department - VSBEC</a>'})

        # Club / event
        if any(k in user_input for k in ['club','event','events','competition','line follower']):
            club_html = """
            <div style="text-align:center;">
              <img src="/static/club_event.jpg" alt="ECE Club Event" style="width:70%; border-radius:10px; box-shadow:0 4px 10px rgba(0,0,0,0.3); margin:10px 0;">
              <h3>Line Follower Robot Competition - LiRo 2K25</h3>
              <p><strong>Date:</strong> 28th Oct 2025 | <strong>Venue:</strong> Dr. V.C.K. Auditorium, VSBEC</p>
              <p><strong>Registration Fee:</strong> ₹200 per person</p>
            </div>
            """
            return jsonify({'reply': club_html})

        # Notifications
        if 'notification' in user_input or 'notifications' in user_input or 'news' in user_input:
            return jsonify({'reply': "<p>📢 No new notifications found.</p>"})

        # Fallback: try to match exact question keys in a small KB (if you have one)
        return jsonify({'reply': "Sorry, I couldn't find that. Try: 'faculty', 'labs', 'department', 'club events', or 'notifications'."})
    except Exception:
        traceback.print_exc()
        return jsonify({'reply': "An internal error occurred. Check server logs."})

if __name__ == '__main__':
    app.run(debug=True)
