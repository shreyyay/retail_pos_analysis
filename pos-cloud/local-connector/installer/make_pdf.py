"""
Generate TallySync Installation Guide PDF using reportlab.
Run: python make_pdf.py
Output: TallySync_Installation_Guide.pdf (in the same directory)
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "TallySync_Installation_Guide.pdf")

# ── Colour palette ─────────────────────────────────────────────────────────────
BLUE       = colors.HexColor("#1e40af")
LIGHT_BLUE = colors.HexColor("#dbeafe")
GREEN      = colors.HexColor("#166534")
LIGHT_GRN  = colors.HexColor("#dcfce7")
ORANGE     = colors.HexColor("#92400e")
LIGHT_ORG  = colors.HexColor("#fef3c7")
GRAY_BG    = colors.HexColor("#f8fafc")
GRAY_BDR   = colors.HexColor("#cbd5e1")
DARK       = colors.HexColor("#1e293b")
MID        = colors.HexColor("#475569")
CODE_BG    = colors.HexColor("#0f172a")
CODE_FG    = colors.white

# ── Styles ────────────────────────────────────────────────────────────────────
ss = getSampleStyleSheet()

def S(name, **kw):
    base = ss[name]
    return ParagraphStyle(name + "_custom_" + str(id(kw)),
                          parent=base, **kw)

title_style = S("Title",
                fontSize=24, textColor=BLUE, leading=30,
                spaceAfter=4, alignment=TA_CENTER)

subtitle_style = S("Normal",
                   fontSize=11, textColor=MID, alignment=TA_CENTER,
                   spaceAfter=2)

h1_style = S("Heading1",
             fontSize=15, textColor=colors.white, leading=20,
             spaceBefore=14, spaceAfter=0,
             backColor=BLUE, leftIndent=-12, rightIndent=-12,
             borderPadding=(6, 12, 6, 12))

h2_style = S("Heading2",
             fontSize=12, textColor=BLUE, leading=16,
             spaceBefore=10, spaceAfter=2,
             borderPadding=(0, 0, 2, 0))

body_style = S("Normal",
               fontSize=10, textColor=DARK, leading=15,
               spaceBefore=2, spaceAfter=2)

note_style = S("Normal",
               fontSize=9, textColor=ORANGE, leading=13,
               spaceBefore=2, spaceAfter=2)

code_style = S("Normal",
               fontSize=9, textColor=CODE_FG,
               fontName="Courier", leading=14,
               backColor=CODE_BG, leftIndent=6, rightIndent=6,
               borderPadding=(5, 8, 5, 8))

step_num_style = S("Normal",
                   fontSize=10, textColor=colors.white,
                   fontName="Helvetica-Bold", alignment=TA_CENTER)

bullet_style = S("Normal",
                 fontSize=10, textColor=DARK, leading=15,
                 leftIndent=14, spaceBefore=1, spaceAfter=1,
                 bulletIndent=4)


def P(text, style=None):
    return Paragraph(text, style or body_style)


def SP(n=6):
    return Spacer(1, n)


def HR():
    return HRFlowable(width="100%", thickness=0.5,
                      color=GRAY_BDR, spaceAfter=4, spaceBefore=4)


def step_row(num, title, detail, bg=LIGHT_BLUE, num_bg=BLUE):
    """A numbered step rendered as a table row."""
    num_cell = Table([[Paragraph(str(num), step_num_style)]],
                     colWidths=[0.7*cm], rowHeights=[0.7*cm])
    num_cell.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), num_bg),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [4]),
    ]))
    body_text = f"<b>{title}</b><br/><font size=9 color='#475569'>{detail}</font>"
    data = [[num_cell, Paragraph(body_text, body_style)]]
    t = Table(data, colWidths=[1.0*cm, 15.2*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), bg),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",(0, 0), (-1, -1), 6),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("ROUNDEDCORNERS", [6]),
        ("BOX", (0, 0), (-1, -1), 0.5, GRAY_BDR),
    ]))
    return KeepTogether([t, SP(5)])


def info_box(title, lines, bg=LIGHT_GRN, title_color=GREEN):
    header = Paragraph(f"<b>{title}</b>", S("Normal", fontSize=10,
                       textColor=title_color))
    paras  = [header, SP(3)]
    for line in lines:
        paras.append(Paragraph(f"• {line}", bullet_style))
    box = Table([[paras]], colWidths=[16.2*cm])
    box.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), bg),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("BOX",          (0, 0), (-1, -1), 0.5, GRAY_BDR),
    ]))
    return KeepTogether([box, SP(6)])


def code_block(*lines):
    text = "<br/>".join(lines)
    return KeepTogether([
        Paragraph(text, code_style),
        SP(5)
    ])


def h1(text):
    return KeepTogether([
        SP(4),
        Paragraph(text, h1_style),
        SP(8),
    ])


def h2(text):
    return KeepTogether([
        SP(4),
        Paragraph(f"<b>{text}</b>", h2_style),
        HRFlowable(width="100%", thickness=1, color=BLUE,
                   spaceAfter=4, spaceBefore=0),
    ])


# ── Document ──────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUT,
    pagesize=A4,
    leftMargin=2.0*cm, rightMargin=2.0*cm,
    topMargin=2.0*cm,  bottomMargin=2.0*cm,
    title="TallySync Installation Guide",
    author="TallySync",
)

story = []

# ── Cover / title block ───────────────────────────────────────────────────────
story += [
    SP(20),
    Paragraph("TallySync", title_style),
    Paragraph("Installation &amp; Build Guide", subtitle_style),
    SP(4),
    Paragraph("v 1.1 &nbsp;·&nbsp; For Windows 10 / 11 (64-bit) with Tally Prime",
              subtitle_style),
    SP(10),
    HR(),
    SP(6),
    info_box(
        "What TallySync does",
        [
            "Automatically pushes Tally Prime sales data to your cloud dashboard "
            "3 times a day (11 AM, 3 PM, 6 PM).",
            "Lets you drop a supplier PDF bill and save it directly into Tally "
            "with one click — no manual data entry.",
        ],
        bg=LIGHT_BLUE, title_color=BLUE,
    ),
    SP(20),
]

# ── Part A: Build steps (developer) ──────────────────────────────────────────
story.append(h1("Part A — Build the Installer  (Developer / One-Time)"))

story += [
    P("Run these steps once on <b>your Windows development machine</b> to produce "
      "<b>TallySyncInstaller.exe</b>. You then send that single file to each client."),
    SP(6),
]

prereqs = [
    ("Pre-requisite", "Python 3.11 or newer",
     "Download from python.org — tick 'Add Python to PATH' during install."),
    ("Pre-requisite", "Inno Setup 6",
     "Download from jrsoftware.org/isdl.php and install with default options."),
    ("Pre-requisite", "Git (optional)",
     "To clone the repo. Or copy the local-connector\\ folder to the build machine."),
]
for kind, title, detail in prereqs:
    box = Table(
        [[Paragraph(f"<b>{kind}</b>", S("Normal", fontSize=8, textColor=MID)),
          Paragraph(f"<b>{title}</b><br/>"
                    f"<font size=9 color='#475569'>{detail}</font>", body_style)]],
        colWidths=[2.2*cm, 14.0*cm]
    )
    box.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (0, 0), GRAY_BG),
        ("BACKGROUND",   (1, 0), (1, 0), colors.white),
        ("BOX",          (0, 0), (-1, -1), 0.5, GRAY_BDR),
        ("INNERGRID",    (0, 0), (-1, -1), 0.3, GRAY_BDR),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
    ]))
    story += [box, SP(3)]

story.append(SP(6))
story.append(h2("Build commands"))

story += [
    P("Open a <b>Command Prompt</b> (or PowerShell) and run:"),
    SP(4),
    code_block(
        "cd path\\to\\retail_pos_analysis\\pos-cloud\\local-connector",
        "installer\\build.bat",
    ),
    P("The script runs 5 steps automatically:"),
    SP(3),
    step_row(1, "pip install",
             "Installs pyinstaller, psycopg2, requests, pdfplumber, groq, streamlit and all "
             "other required packages into your Python environment."),
    step_row(2, "Build tally_sync.exe",
             "Freezes the daily Tally → cloud sync engine using PyInstaller."),
    step_row(3, "Build TallySyncSetup.exe",
             "Freezes the setup wizard GUI (collects credentials, schedules tasks)."),
    step_row(4, "Build SupplierBillTool.exe",
             "Freezes the PDF import tool (streamlit + pdfplumber + groq bundled). "
             "This step takes 5 – 15 minutes."),
    step_row(5, "Run Inno Setup",
             "Packages all three exes into a single TallySyncInstaller.exe."),
    info_box(
        "Output",
        [
            "installer\\Output\\TallySyncInstaller.exe  — send this to the client.",
            "The file will be roughly 80 – 150 MB after LZMA compression.",
        ],
        bg=LIGHT_GRN, title_color=GREEN,
    ),
]

# ── Part B: Client PC installation ───────────────────────────────────────────
story.append(h1("Part B — Install on the Client PC  (Retail Shop)"))

story += [
    P("Do this once on <b>each shop's Tally PC</b>. "
      "Tally Prime must be installed and open on that PC."),
    SP(6),
    info_box(
        "What you need before starting",
        [
            "TallySyncInstaller.exe  (the file built in Part A).",
            "Supabase connection string — from Supabase dashboard → "
            "Connect → Session pooler → copy the URL.",
            "Store ID — a short code for this shop, e.g. STORE001.",
            "Groq API key — free from console.groq.com → API Keys → Create.  "
            "It starts with 'gsk_'.",
        ],
        bg=LIGHT_ORG, title_color=ORANGE,
    ),
]

story.append(h2("Installation steps"))

client_steps = [
    ("Copy the installer",
     "Copy TallySyncInstaller.exe to the Tally PC (USB drive, WhatsApp, email, etc.)."),
    ("Run as Administrator",
     "Right-click TallySyncInstaller.exe → Run as administrator. "
     "Click Yes on the UAC prompt."),
    ("Follow the Inno Setup wizard",
     "Click Next → Next → Install.  Default install folder is fine "
     "(C:\\Program Files\\TallySync)."),
    ("Setup wizard opens automatically",
     "After installation finishes, the TallySync Setup window appears."),
    ("Step 1 of 3 — Enter your details",
     "Fill in: Supabase Database URL · Store ID · Groq AI Key · Tally Port (leave as 9000). "
     "Click Next → Test Connection."),
    ("Step 2 of 3 — Test connection",
     "Click Test Connection.  You should see a green tick. "
     "If it fails, double-check the Supabase URL and your internet connection. "
     "Click Next → Schedule Tasks."),
    ("Step 3 of 3 — Install",
     "Click Install.  The wizard writes config.ini, creates 3 Task Scheduler entries "
     "(11 AM, 3 PM, 6 PM) and adds a Supplier Bill Tool shortcut to the Desktop."),
    ("Click Finish",
     "Setup is complete.  TallySync will now sync automatically at 11 AM, 3 PM, 6 PM."),
]
for i, (title, detail) in enumerate(client_steps, 1):
    story.append(step_row(i, title, detail))

# ── Part C: Using the Supplier Bill Tool ─────────────────────────────────────
story.append(h1("Part C — Using the Supplier Bill Tool"))

story += [
    P("The Supplier Bill Tool lets you scan a supplier PDF invoice and push it "
      "into Tally Prime with one click."),
    SP(6),
    step_row(1, "Open Tally Prime",
             "Make sure Tally Prime is open and running on the same PC.",
             bg=LIGHT_GRN, num_bg=GREEN),
    step_row(2, "Double-click the Desktop shortcut",
             "Click the 'Supplier Bill Tool' icon on the Desktop.  "
             "A small window appears — wait for the green tick.",
             bg=LIGHT_GRN, num_bg=GREEN),
    step_row(3, "Upload the PDF",
             "The browser opens automatically.  Click 'Choose a supplier PDF bill' "
             "and select the invoice file.",
             bg=LIGHT_GRN, num_bg=GREEN),
    step_row(4, "Check the details",
             "The tool reads the bill with AI.  Review the supplier name, items, "
             "quantities and amounts shown on screen.",
             bg=LIGHT_GRN, num_bg=GREEN),
    step_row(5, "Click Save to Tally",
             "One click sends the purchase voucher directly into Tally Prime. "
             "A success message confirms it was created.",
             bg=LIGHT_GRN, num_bg=GREEN),
    step_row(6, "Close when done",
             "Click Stop in the small launcher window, or just close it.  "
             "The browser tab closes too.",
             bg=LIGHT_GRN, num_bg=GREEN),
]

# ── Troubleshooting ───────────────────────────────────────────────────────────
story.append(h1("Troubleshooting"))

troubles = [
    ("Connection failed in Step 2",
     ["Paste the Supabase URL again carefully — it must start with postgresql://",
      "Make sure the PC has an internet connection.",
      "Check that you used the Session Pooler URL (port 5432), not the direct URL."]),
    ("Tally Closed / Cannot connect to Tally",
     ["Open Tally Prime before clicking Save to Tally.",
      "In Tally: F12 → Advanced Configuration → Enable Tally.Developer "
      "(or confirm port is 9000).",
      "Firewall: allow port 9000 for localhost connections."]),
    ("Supplier Bill Tool takes too long to start",
     ["First launch is slower — wait up to 60 seconds.",
      "If it fails, close and re-open the shortcut.",
      "Check that setup wizard was completed and config.ini exists in the install folder."]),
    ("Task Scheduler tasks not created (error in Step 3)",
     ["Close the setup wizard, right-click its icon → Run as administrator, "
      "and re-run from Step 3.",
      "The tasks need admin rights to be registered."]),
    ("Sync log location",
     ["Logs are written to:  C:\\Program Files\\TallySync\\tally_sync\\logs\\sync.log",
      "Open this file to see the last sync result and any errors."]),
]
for title, bullets in troubles:
    story.append(info_box(title, bullets, bg=GRAY_BG, title_color=DARK))

# ── Footer note ───────────────────────────────────────────────────────────────
story += [
    HR(),
    P("<i>Confidential — for internal use only.  "
      "Do not share credentials or this document with unauthorised persons.</i>",
      S("Normal", fontSize=8, textColor=MID, alignment=TA_CENTER)),
]

# ── Build ─────────────────────────────────────────────────────────────────────
doc.build(story)
print(f"PDF written to: {OUT}")
