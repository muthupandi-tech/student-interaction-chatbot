from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import os

app = Flask(__name__)

# ✅ Load faculty data from Excel
faculty_file = "ECE_Faculty_Details_VSBEC.xlsx"
faculty_data = []
if os.path.exists(faculty_file):
    df = pd.read_excel(faculty_file)
    faculty_data = df["Name"].dropna().tolist()

# ✅ Predefined static data
lab_details = """
<table border="1" cellspacing="0" cellpadding="6" style="width:100%; text-align:left;">
<tr><th>Semester</th><th>Lab Name</th><th>Details</th></tr>
<tr><td>2nd Sem</td><td>Electronic Devices and Circuits Lab</td><td>Practical experiments on diodes, transistors, and amplifiers.</td></tr>
<tr><td>2nd Sem</td><td>Digital Electronics Lab</td><td>Focuses on logic gates, multiplexers, and counters.</td></tr>
<tr><td>2nd Sem</td><td>Simulation Lab</td><td>Introduction to MATLAB & Multisim simulations.</td></tr>
</table>
"""

department_link = '<a href="https://vsbec.edu.in/ece/" target="_blank">Click here to visit the Department of ECE - VSBEC Website</a>'

club_event_html = f"""
<div style="text-align:center;">
  <img src="/static/club_event.jpg" alt="ECE Club Event" style="width:70%; border-radius:10px; box-shadow:0 4px 10px rgba(0,0,0,0.3); margin:10px 0;">
  <h3>🎉 Line Follower Robot Competition - LiRo 2K25</h3>
  <p><strong>Date:</strong> 28th Oct 2025<br>
  <strong>Venue:</strong> Dr. V.C.K. Auditorium, VSBEC<br>
  <strong>Organized by:</strong> Department of ECE & Electronics Club<br>
  <strong>Stages:</strong> Qualifying Race & Final Race<br>
  <strong>Registration Fee:</strong> ₹200 per person<br>
  <strong>Prizes:</strong> 1st – ₹4000 | 2nd – ₹3000 | 3rd – ₹2000</p>
  <p><a href="https://vsbec.edu.in/" target="_blank">Register Now (College Website)</a></p>
</div>
"""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get', methods=['POST'])
def get_bot_response():
    user_input = request.form['msg'].strip().lower()

    if "faculty" in user_input:
        if faculty_data:
            staff_html = "<div class='table-box'><strong>👩‍🏫 Faculty Members:</strong><ul>"
            for name in faculty_data:
                staff_html += f"<li>{name}</li>"
            staff_html += "</ul></div>"
            return jsonify({'reply': staff_html})
        else:
            return jsonify({'reply': "No faculty data found."})

    elif "lab" in user_input:
        return jsonify({'reply': lab_details})

    elif "department" in user_input:
        return jsonify({'reply': department_link})

    elif "club" in user_input or "event" in user_input:
        return jsonify({'reply': club_event_html})

    elif "notification" in user_input:
        return jsonify({'reply': "<p>📢 No new notifications found.</p>"})

    else:
        return jsonify({'reply': "Sorry, I couldn't find that. Try asking about faculty, labs, department, or events."})


if __name__ == '__main__':
    app.run(debug=True)
