import os
import html
from datetime import datetime
import random
import uuid
from modules.config import TICKET_TEMPLATE, AI_REMARKS_POOL
from modules.utils import print_event

def generate_html_ticket(total_points, sessions_folder, log_file):
    print_event("[Ticket Gen] Reading violation log...")
    if not os.path.exists(log_file):
        print_event(f"[Ticket Gen] Error: Log file '{log_file}' not found.")
        return

    violations_html = "<ul>\n"
    session_end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    violation_count = 0
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            # Skip header if it exists
            try:
                next(f)
            except StopIteration:
                pass # File is empty

            for line in f:
                if not line.strip():
                    continue
                try:
                    parts = line.strip().split(' | ')
                    if len(parts) < 4:
                        print_event(f"[Ticket Gen] Warning: Skipping malformed log line: {line.strip()}")
                        continue

                    timestamp, violation_msg, points, context = parts[0], parts[1], parts[2], parts[3]
                    
                    if violation_count == 0:
                        session_end_time = timestamp
                    
                    violations_html += f"<li><strong>{html.escape(timestamp)}:</strong> {html.escape(violation_msg)} ({html.escape(points)} points)"
                    
                    if context and context != 'N/A':
                        violations_html += f'<p class="context-text"><strong>Telemetry:</strong> {html.escape(context)}</p>'
                    
                    violations_html += "</li>\n"
                    session_end_time = timestamp
                    violation_count += 1
                except Exception as e:
                    print_event(f"[Ticket Gen] Warning: Skipping malformed log line: {line.strip()} ({e})")
        
        violations_html += "</ul>"

        if violation_count == 0:
            print_event("[Ticket Gen] No violations logged. No ticket will be issued. Good job?")
            # Clean up the empty log file
            open(log_file, 'w').close()
            return
            
        # --- Generate Funny AI Content ---
        print_event("[Ticket Gen] Consulting the AI Examiner for remarks...")
        num_remarks = min(len(AI_REMARKS_POOL), random.randint(2, 4))
        selected_remarks = random.sample(AI_REMARKS_POOL, num_remarks)
        
        ai_remarks_html = ""
        for remark in selected_remarks:
            ai_remarks_html += f"<p>{html.escape(remark)}</p>\n"

        ai_remarks_html += "<p><strong>RECOMMENDATION:</strong> Driver requires immediate re-education. My circuits are weeping.</p>\n<p>-- A.I. Examiner Unit 734</p>"
        
        session_id = f"{str(uuid.uuid4()).split('-')[0].upper()}-{str(uuid.uuid4()).split('-')[1].upper()}"
        passcode = f"JUDGE-SMASH-{random.randint(100, 999)}"
        
        print_event("[Ticket Gen] Assembling final citation...")
        final_html = TICKET_TEMPLATE
        
        # Inject CSS for context
        style_injection = """
<style>
    .context-text {
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.9em;
        color: #333;
        background-color: #f5f5f5;
        padding: 5px 10px;
        margin-top: 5px;
        margin-bottom: 5px;
        border-left: 3px solid #ddd;
    }
</style>
</head>
"""
        final_html = final_html.replace("</head>", style_injection)
        
        final_html = final_html.replace("<!-- VIOLATIONS_HERE -->", violations_html)
        final_html = final_html.replace("[TOTAL_POINTS_HERE]", str(total_points))
        final_html = final_html.replace("[SESSION_END_HERE]", session_end_time)
        final_html = final_html.replace("<!-- AI_REMARKS_HERE -->", ai_remarks_html)
        final_html = final_html.replace("[SESSION_ID_HERE]", session_id)
        final_html = final_html.replace("[PASSCODE_HERE]", passcode)
        
        ticket_filename = f"court_session_{session_id}.html"
        ticket_path = os.path.join(sessions_folder, ticket_filename)
        
        with open(ticket_path, 'w', encoding='utf-8') as f:
            f.write(final_html)
            
        print_event(f"\n[Ticket Generated] Court session file saved to: {ticket_path}")

    except Exception as e:
        print_event(f"[Ticket Gen] CRITICAL ERROR: Could not generate ticket: {e}")