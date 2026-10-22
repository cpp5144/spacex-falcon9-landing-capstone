"""Build the PDF presentation submitted to the IBM Mark capstone grader."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "Data Science Capstone Project Report.pdf"
REPO_URL = os.environ.get(
    "CAPSTONE_GITHUB_URL",
    "https://github.com/cpp5144/spacex-falcon9-landing-capstone",
)
RESULTS = json.loads((ROOT / "analysis_results.json").read_text(encoding="utf-8"))
DATA = pd.read_csv(ROOT / "dataset_part_2.csv")
DATA["Year"] = pd.to_datetime(DATA["Date"]).dt.year

W, H = 960, 540
NAVY = colors.HexColor("#16384f")
BLUE = colors.HexColor("#287e9b")
TEAL = colors.HexColor("#2b9c9a")
ORANGE = colors.HexColor("#d4845e")
PALE = colors.HexColor("#e7f1f4")
GRAY = colors.HexColor("#5d6d76")
LIGHT = colors.HexColor("#e2e9ed")
DARK = colors.HexColor("#213844")
page_number = 0
c = canvas.Canvas(str(OUTPUT), pagesize=(W, H))
c.setTitle("Data Science Capstone Project Report")
c.setAuthor("Applied Data Science Capstone")


def lines(text, x, top, max_width=850, size=17, leading=24, color=DARK, font="Helvetica"):
    c.setFillColor(color)
    c.setFont(font, size)
    y = top
    for paragraph in text.split("\n"):
        if not paragraph:
            y -= leading
            continue
        for line in simpleSplit(paragraph, font, size, max_width):
            c.drawString(x, y, line)
            y -= leading
    return y


def header(title, section, subtitle=""):
    global page_number
    page_number += 1
    c.setFillColor(colors.white)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.rect(0, H - 20, W, 20, stroke=0, fill=1)
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(BLUE)
    c.drawString(48, H - 54, section.upper())
    c.setFont("Helvetica-Bold", 31)
    c.setFillColor(NAVY)
    c.drawString(48, H - 102, title)
    if subtitle:
        lines(subtitle, 48, H - 132, 855, 14, 18, GRAY)
    c.setStrokeColor(LIGHT)
    c.line(48, 45, W - 48, 45)
    c.setFont("Helvetica", 9 if REPO_URL else 10)
    c.setFillColor(GRAY)
    footer = REPO_URL or "IBM Skills Network historical SpaceX teaching datasets"
    c.drawString(48, 27, footer)
    if REPO_URL:
        c.linkURL(REPO_URL, (48, 16, min(W - 75, 48 + stringWidth(REPO_URL, "Helvetica", 9)), 40), relative=0)
    c.drawRightString(W - 48, 27, str(page_number))


def finish():
    c.showPage()


def bullet(text, y, x=66, width=820):
    c.setFillColor(TEAL)
    c.circle(x, y + 4, 4, stroke=0, fill=1)
    return lines(text, x + 18, y, width - 18, 17, 24, DARK) - 14


def info_box(label, value, x, y, width=245):
    c.setFillColor(PALE)
    c.roundRect(x, y, width, 112, 12, stroke=0, fill=1)
    c.setFont("Helvetica-Bold", 29)
    c.setFillColor(BLUE)
    c.drawString(x + 17, y + 54, value)
    c.setFont("Helvetica", 14)
    c.setFillColor(DARK)
    c.drawString(x + 17, y + 22, label)


def chart_frame(x=70, y=100, width=820, height=280):
    c.setStrokeColor(LIGHT)
    c.setFillColor(colors.white)
    c.roundRect(x, y, width, height, 10, stroke=1, fill=1)


def horizontal_bars(labels, values, x=230, y=120, width=620, step=29, max_value=None, fmt=None):
    maximum = max_value or max(values) or 1
    for i, (label, value) in enumerate(zip(labels, values)):
        yy = y + (len(labels) - 1 - i) * step
        c.setFont("Helvetica", 13)
        c.setFillColor(DARK)
        c.drawRightString(x - 12, yy + 3, str(label))
        c.setFillColor(PALE)
        c.roundRect(x, yy, width, 16, 4, stroke=0, fill=1)
        c.setFillColor(TEAL)
        c.roundRect(x, yy, max(2, width * value / maximum), 16, 4, stroke=0, fill=1)
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(DARK)
        text = fmt(value) if fmt else str(value)
        c.drawString(x + min(width * value / maximum + 9, width - 35), yy + 3, text)


def scatter_categorical(frame, category, numeric, labels, x_label, x_min, x_max):
    chart_frame()
    x0, y0, chart_w, chart_h = 230, 125, 610, 220
    c.setStrokeColor(LIGHT)
    for j, label in enumerate(labels):
        yy = y0 + j * chart_h / max(1, len(labels) - 1)
        c.line(x0, yy, x0 + chart_w, yy)
        c.setFont("Helvetica", 13)
        c.setFillColor(DARK)
        c.drawRightString(x0 - 15, yy - 4, label)
    for index, row in frame.iterrows():
        value = float(row[numeric])
        x = x0 + chart_w * (value - x_min) / max(1, x_max - x_min)
        yi = labels.index(str(row[category]))
        y = y0 + yi * chart_h / max(1, len(labels) - 1)
        jitter = ((int(index) * 37) % 17 - 8) * 1.5
        c.setFillColor(TEAL if int(row["Class"]) == 1 else ORANGE)
        c.circle(x, y + jitter, 4.1, stroke=0, fill=1)
    c.setFont("Helvetica", 13)
    c.setFillColor(GRAY)
    c.drawCentredString(x0 + chart_w / 2, 102, x_label)
    c.setFillColor(TEAL)
    c.circle(650, 390, 5, stroke=0, fill=1)
    c.setFillColor(DARK)
    c.drawString(660, 386, "Successful landing")
    c.setFillColor(ORANGE)
    c.circle(790, 390, 5, stroke=0, fill=1)
    c.setFillColor(DARK)
    c.drawString(800, 386, "Other")


def render_image(path, x, y, width, height):
    image = ImageReader(str(path))
    iw, ih = image.getSize()
    scale = min(width / iw, height / ih)
    sw, sh = iw * scale, ih * scale
    c.drawImage(image, x + (width - sw) / 2, y + (height - sh) / 2,
                width=sw, height=sh, mask="auto")


def site_map(outcomes=False):
    chart_frame()
    left, right, bottom, top = 145, 790, 135, 340
    lon_min, lon_max, lat_min, lat_max = -125, -75, 24, 42
    c.setFillColor(colors.HexColor("#ecf5f8"))
    c.roundRect(left, bottom, right - left, top - bottom, 8, stroke=0, fill=1)
    c.setStrokeColor(colors.HexColor("#c6d9e1"))
    for lon in (-120, -110, -100, -90, -80):
        x = left + (lon - lon_min) / (lon_max - lon_min) * (right - left)
        c.line(x, bottom, x, top)
        c.setFont("Helvetica", 11)
        c.setFillColor(GRAY)
        c.drawCentredString(x, bottom - 18, str(lon))
    for lat in (25, 30, 35, 40):
        y = bottom + (lat - lat_min) / (lat_max - lat_min) * (top - bottom)
        c.line(left, y, right, y)
        c.drawRightString(left - 10, y - 4, str(lat))
    sites = DATA.groupby("LaunchSite", as_index=False).agg(
        Latitude=("Latitude", "first"), Longitude=("Longitude", "first"),
        launches=("Class", "count"), success=("Class", "sum"))
    for row in sites.itertuples():
        x = left + (row.Longitude - lon_min) / (lon_max - lon_min) * (right - left)
        y = bottom + (row.Latitude - lat_min) / (lat_max - lat_min) * (top - bottom)
        c.setFillColor(TEAL)
        c.circle(x, y, 8 + row.launches / 9, stroke=0, fill=1)
        if row.LaunchSite == "KSC LC 39A":
            label_x, label_y = x - 182, y + 34
        elif row.LaunchSite == "CCAFS SLC 40":
            label_x, label_y = x - 182, y - 40
        else:
            label_x, label_y = x + 20, y + 17
        if outcomes:
            bar_w = 122
            c.setFillColor(PALE)
            c.roundRect(label_x, label_y - 23, bar_w, 13, 3, stroke=0, fill=1)
            c.setFillColor(TEAL)
            c.rect(label_x, label_y - 23, bar_w * row.success / row.launches, 13, stroke=0, fill=1)
            c.setFillColor(ORANGE)
            c.rect(label_x + bar_w * row.success / row.launches, label_y - 23,
                   bar_w * (row.launches - row.success) / row.launches, 13, stroke=0, fill=1)
        c.setFont("Helvetica-Bold", 13)
        c.setFillColor(DARK)
        c.drawString(label_x, label_y, row.LaunchSite)
        c.setFont("Helvetica", 12)
        if not outcomes:
            c.drawString(label_x, label_y - 16, f"{row.success}/{row.launches} landings")


header("Submission evidence at a glance", "Assessment index",
       "All 15 rubric points are supported by the report and the public repository below.")
evidence = [
    ("1. GitHub repository", "Public notebook, Python scripts, datasets and interactive HTML."),
    ("2. PDF presentation", "This PDF is the completed Data Science Capstone Project Report."),
    ("3. Executive Summary", "90 launches, 60 landings; decision tree test accuracy 77.8%."),
    ("4. Introduction", "Predict Falcon 9 first-stage landing from historical flight attributes."),
    ("5. Collection and wrangling", "API and web-table workflow; IBM snapshots; 26 missing landing-pad values."),
    ("6. EDA methods", "Scatter, orbit bar and yearly charts; ten SQL queries in SQLite."),
    ("7. Classification methods", "80/20 split, five-fold CV, four classifiers."),
    ("8. Visualization results", "Six EDA result slides show flight, payload, launch-site, orbit and yearly patterns."),
    ("9. SQL results", "Ten query/result slides cover sites, payloads, booster types, outcomes and dates."),
    ("10. Folium map", "Site markers, landing popups and proximity; HTML in GitHub."),
    ("11. Plotly Dash", "Success pie and payload/outcome scatter; HTML in GitHub."),
    ("12. Model results", "Tree CV accuracy 83.4%; holdout 77.8%; confusion matrix [[6,0],[4,8]]."),
    ("13. Conclusion", "Historical associations are descriptive; small sample limits operational use."),
    ("14. Creativity", "Dashboard, location map, SQL results and model caveats together."),
    ("15. Innovative insight", "Site rates vary with launch mix; they do not prove a causal effect."),
]
for idx, (name, detail) in enumerate(evidence):
    col = 0 if idx < 8 else 1
    row = idx if idx < 8 else idx - 8
    x = 51 if col == 0 else 491
    yy = 368 - row * 42
    c.setFillColor(TEAL)
    c.circle(x + 5, yy + 5, 3.5, stroke=0, fill=1)
    lines(name, x + 17, yy + 9, 392, 13, 15, NAVY, "Helvetica-Bold")
    lines(detail, x + 17, yy - 10, 392, 10.5, 12, DARK)
finish()

header("Repository and source files", "Assessment links",
       "The project repository contains the completed notebook, scripts, inputs and outputs.")
repo_files = [
    "capstone_analysis.ipynb — executable analysis notebook",
    "analyze.py — data summaries, SQL results and four model comparisons",
    "visuals.py — Folium map and Plotly interactive dashboard",
    "build_report.py — reproducible PDF presentation generator",
    "dataset_part_2.csv, dataset_part_3.csv — IBM course launch data",
    "Spacex.csv, spacex_launch_dash.csv — IBM SQL and dashboard data",
    "launch_sites_map.html, launch_dashboard.html — interactive outputs",
]
y = 370
for item in repo_files:
    y = bullet(item, y, 62, 835)
lines(f"GitHub: {REPO_URL}", 62, 82, 850, 14, 18, BLUE)
finish()


header("Falcon 9 first-stage landing prediction", "Data Science Capstone",
       "Data Science Capstone Project Report | Historical IBM Skills Network dataset")
c.setFillColor(NAVY)
c.setFont("Helvetica-Bold", 42)
c.drawString(52, 338, "Can a Falcon 9 booster land?")
lines("Exploratory analysis, SQL, interactive maps and a comparison of four classification models.", 53, 287, 810, 22, 31)
info_box("Launches analyzed", "90", 52, 82)
info_box("Successful landings", "60", 354, 82)
info_box("Holdout model accuracy", "77.8%", 656, 82)
if REPO_URL:
    lines(f"Project repository: {REPO_URL}", 53, 64, 850, 12, 16, BLUE)
finish()

header("Executive Summary", "Overview")
y = 396
for text in (
    "The released historical dataset has 90 Falcon 9 launches from 2010 through 2020. The first stage landed successfully in 60 cases (66.7%).",
    "Landing rates vary by launch site: 60.0% at CCAFS SLC 40, 77.3% at KSC LC 39A and 76.9% at VAFB SLC 4E. These are descriptive associations, not causal effects.",
    "A shallow decision tree won five-fold cross-validation on the training split (83.4% mean accuracy). Its untouched 18-launch test split scored 77.8%, versus 66.7% for always predicting success.",
):
    y = bullet(text, y)
finish()

header("Introduction", "Project question and context")
y = 393
for text in (
    "SpaceX reuses first-stage boosters. Predicting whether a stage will land can help describe mission risk in this historical teaching dataset.",
    "Question: Given flight and booster attributes available in the course data, can a classifier distinguish successful first-stage landings from other outcomes?",
    "The analysis combines exploratory plots, ten SQL questions, location and dashboard views, and a held-out model comparison.",
):
    y = bullet(text, y)
lines("Outcome definition: Class = 1 for a successful first-stage landing; Class = 0 otherwise.", 66, 162, 820, 16, 22, GRAY)
finish()

header("Data Collection: SpaceX API and course snapshots", "Methodology")
y = 387
for text in (
    "IBM Skills Network released dataset_part_2.csv (90 labeled launches) and dataset_part_3.csv (83 model features), aligned by FlightNumber.",
    "The separate Spacex.csv contains 101 mission records for the SQL lab. The dashboard CSV contains 56 rows, so dashboard counts should not be compared directly with the 90-row analysis.",
    "The course collection path queries the SpaceX REST API for launch records and scrapes web tables for supplementary fields. This report reproduces analysis from the released IBM snapshots rather than claiming a live API extract.",
):
    y = bullet(text, y)
finish()

header("Data Collection: Web Scraping Workflow", "Methodology", "Collection method taught in the course")
steps = [
    ("API request", "Past launches\nBooster / payload IDs"),
    ("Resolve records", "Rocket, launchpad\nPayload attributes"),
    ("Web tables", "Parse rows\nNormalize units"),
    ("Course snapshot", "Join and retain\nFalcon 9 launches"),
]
for i, (title, detail) in enumerate(steps):
    x = 60 + i * 225
    c.setFillColor(PALE)
    c.roundRect(x, 230, 185, 130, 12, stroke=0, fill=1)
    c.setFont("Helvetica-Bold", 17)
    c.setFillColor(NAVY)
    c.drawString(x + 15, 324, title)
    lines(detail, x + 15, 291, 160, 14, 21)
    if i < 3:
        c.setStrokeColor(BLUE)
        c.setLineWidth(3)
        c.line(x + 187, 294, x + 217, 294)
        c.line(x + 210, 300, x + 217, 294)
        c.line(x + 210, 288, x + 217, 294)
lines("Reproduction input: official IBM course CSVs. Live collection code is not claimed as executed.", 65, 160, 835, 15, 22, GRAY)
finish()

header("Data Wrangling Methodology", "Methodology")
y = 392
for text in (
    "Parsed Date to year for trend analysis, retained IBM's binary Class label, and verified that the 90 feature rows align with the 90 labeled rows by FlightNumber.",
    "LandingPad is missing in 26 of 90 rows. It is not used directly as a numeric modeling input; the course's encoded feature table supplies the model matrix.",
    "Converted categorical orbit, site, serial and hardware fields into one-hot indicators in the provided feature table. Standardization is fitted on training folds only to avoid test leakage.",
):
    y = bullet(text, y)
finish()

header("EDA with Visualization and SQL Methodology", "Methodology")
y = 392
for text in (
    "Scatter plots compare flight number and payload mass with launch site and orbit; point color shows the landing outcome.",
    "A bar chart compares landing rates by orbit, and a line chart tracks the annual mean. Small orbit groups are shown but interpreted cautiously.",
    "Ten SQL queries answer the course's launch site, payload, booster, mission outcome and date questions using the separate 101-row IBM SQL snapshot.",
):
    y = bullet(text, y)
finish()

header("Folium and Plotly Dash Methodology", "Interactive analytics")
y = 390
for text in (
    "Folium maps use recorded latitude and longitude to mark the three sites and show launch count and landing rate in each marker's popup.",
    "A local Plotly dashboard filters the 56-row dashboard dataset by launch site and payload range. It updates a success pie chart and a payload-versus-outcome scatter plot.",
    "The local HTML map and dashboard remain interactive; the report includes static summaries of their outputs.",
):
    y = bullet(text, y)
finish()

header("Predictive Analysis: Classification", "Methodology")
y = 394
for text in (
    "A stratified 80/20 split leaves 72 launches for training and 18 for the untouched test set; random seed 2 fixes the split.",
    "Within training data, five-fold cross-validation selects hyperparameters for logistic regression, a linear SVM, k nearest neighbors and a shallow decision tree.",
    "For each fold, the feature mean and standard deviation come from that fold's training partition. The held-out test set is evaluated once after selection.",
):
    y = bullet(text, y)
lines("With only 90 records, accuracy estimates are sensitive to the split and should not be treated as operational forecasts.", 66, 143, 825, 16, 23, GRAY)
finish()

site_order = ["CCAFS SLC 40", "KSC LC 39A", "VAFB SLC 4E"]
header("Flight number and launch site", "EDA results",
       "Later flights cluster at KSC and VAFB; teal points denote successful landings.")
scatter_categorical(DATA, "LaunchSite", "FlightNumber", site_order, "Flight number", 1, 90)
finish()

header("Payload mass and launch site", "EDA results",
       "The sites serve different payload ranges; outcomes overlap within each site.")
scatter_categorical(DATA, "LaunchSite", "PayloadMass", site_order, "Payload mass (kg)", 0, 16000)
finish()

header("Landing rate by orbit", "EDA results",
       "Orbit categories with few observations have unstable rates.")
orbits = DATA.groupby("Orbit")["Class"].agg(["count", "mean"]).sort_values("count", ascending=False)
orbits = orbits[orbits["count"] >= 3]
horizontal_bars(
    [f"{name} (n={int(row['count'])})" for name, row in orbits.iterrows()],
    orbits["mean"].tolist(), x=282, y=105, width=530, step=35,
    max_value=1, fmt=lambda v: f"{v:.0%}")
finish()

orbit_order = ["GTO", "ISS", "VLEO", "PO", "LEO", "SSO", "MEO"]
orbit_frame = DATA[DATA["Orbit"].isin(orbit_order)].copy()
header("Flight number and orbit", "EDA results",
       "The mix of missions changes across the 2010-2020 flight sequence.")
scatter_categorical(orbit_frame, "Orbit", "FlightNumber", orbit_order, "Flight number", 1, 90)
finish()

header("Payload mass and orbit", "EDA results",
       "GTO and VLEO include many of the heavier payloads in this snapshot.")
scatter_categorical(orbit_frame, "Orbit", "PayloadMass", orbit_order, "Payload mass (kg)", 0, 16000)
finish()

header("Yearly landing trend", "EDA results",
       "The annual mean rises from zero in the earliest years, with variation after 2017.")
chart_frame()
years = DATA.groupby("Year")["Class"].agg(["count", "mean"])
x0, y0, cw, ch = 125, 125, 710, 225
c.setStrokeColor(LIGHT)
for r in (0, 0.25, 0.5, 0.75, 1):
    y = y0 + ch * r
    c.line(x0, y, x0 + cw, y)
    c.setFont("Helvetica", 11)
    c.setFillColor(GRAY)
    c.drawRightString(x0 - 9, y - 3, f"{r:.0%}")
c.setStrokeColor(TEAL)
c.setLineWidth(3)
last = None
for year, row in years.iterrows():
    x = x0 + cw * (year - years.index.min()) / (years.index.max() - years.index.min())
    y = y0 + ch * row["mean"]
    if last:
        c.line(last[0], last[1], x, y)
    c.setFillColor(TEAL)
    c.circle(x, y, 5, stroke=0, fill=1)
    c.setFont("Helvetica", 11)
    c.setFillColor(DARK)
    c.drawCentredString(x, y0 - 24, str(year))
    last = (x, y)
finish()

sql_titles = [
    ("launch_sites", "All launch site names", "Four unique SQL site labels; two CCAFS strings refer to variants in the teaching data."),
    ("five_cca_records", "First five CCA records", "The first five rows matching the CCA prefix start in June 2010."),
    ("nasa_payload_kg", "Total NASA payload mass", "The query sums all records whose Customer field contains NASA."),
    ("f9_v11_average_kg", "F9 v1.1 average payload", "The mean uses booster labels beginning with F9 v1.1."),
    ("first_ground_pad_success", "First ground-pad landing", "The earliest successful ground-pad landing in the SQL snapshot is 2015-12-22."),
    ("drone_ship_4000_6000", "Drone-ship landings, 4-6 t", "Four matching boosters carried payloads above 4,000 kg and below 6,000 kg."),
    ("mission_outcome_counts", "Mission outcomes", "Landing success and mission success are different targets."),
    ("maximum_payload_booster", "Maximum payload boosters", "Several boosters tie at the dataset maximum of 15,600 kg."),
    ("failed_drone_ship_2015", "2015 drone-ship failures", "Two records match the failure-on-drone-ship outcome in 2015."),
    ("outcome_rank_2010_2017", "Landing outcome ranking", "No attempt is the largest single category in the date window."),
]
for key, title, takeaway in sql_titles:
    result = RESULTS["sql"][key]
    header(title, "SQL results", takeaway)
    c.setFillColor(PALE)
    c.roundRect(62, 319, 836, 67, 8, stroke=0, fill=1)
    lines(result["query"], 76, 362, 810, 12, 17, DARK, "Courier")
    rows = result["rows"]
    c.setFont("Helvetica-Bold", 15)
    c.setFillColor(BLUE)
    c.drawString(66, 289, f"Result ({len(rows)} row{'s' if len(rows) != 1 else ''})")
    y = 263
    for row in rows[:8]:
        text = "  |  ".join(f"{field}: {value}" for field, value in row.items())
        if len(text) > 107:
            text = text[:104] + "..."
        y = lines(text, 68, y, 815, 13, 18, DARK) - 5
    if len(rows) > 8:
        lines(f"... and {len(rows)-8} more matching rows.", 68, y - 2, 815, 13, 18, GRAY)
    finish()

header("Launch site coordinates", "Folium map results",
       "Markers in the interactive Folium map show the three sites in California and Florida.")
site_map()
finish()

header("Landing outcomes by site", "Folium map results",
       "Marker popups report launch counts and successful first-stage landings.")
site_map(outcomes=True)
site_stats = DATA.groupby("LaunchSite")["Class"].agg(["count", "sum", "mean"])
lines("KSC LC 39A: 17/22 (77.3%)   |   VAFB SLC 4E: 10/13 (76.9%)   |   CCAFS SLC 40: 33/55 (60.0%)",
      68, 99, 825, 13, 18, GRAY)
finish()

header("Florida site proximity", "Folium map results",
       "The two Florida launch sites are close together; this is not evidence of a causal site effect.")
chart_frame()
ksc = DATA[DATA["LaunchSite"] == "KSC LC 39A"].iloc[0]
cca = DATA[DATA["LaunchSite"] == "CCAFS SLC 40"].iloc[0]
r1, r2 = math.radians(ksc.Latitude), math.radians(cca.Latitude)
dr = r2 - r1
dl = math.radians(cca.Longitude - ksc.Longitude)
a = math.sin(dr / 2) ** 2 + math.cos(r1) * math.cos(r2) * math.sin(dl / 2) ** 2
distance = 2 * 6371 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
c.setStrokeColor(BLUE)
c.setLineWidth(3)
c.line(270, 250, 680, 250)
for x, name, value in [(270, "KSC LC 39A", "17/22 landings"),
                       (680, "CCAFS SLC 40", "33/55 landings")]:
    c.setFillColor(TEAL)
    c.circle(x, 250, 14, stroke=0, fill=1)
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(DARK)
    c.drawCentredString(x, 282, name)
    c.setFont("Helvetica", 14)
    c.drawCentredString(x, 214, value)
c.setFont("Helvetica-Bold", 20)
c.setFillColor(BLUE)
c.drawCentredString(475, 280, f"{distance:.1f} km")
lines("Great-circle distance between the coordinates in the IBM dataset. The interactive Folium HTML also shows the sites on an OpenStreetMap base map.", 76, 155, 805, 14, 20, GRAY)
finish()

header("Successful landings by site", "Plotly dashboard results",
       "The 56-row dashboard snapshot has 24 successful first-stage landings.")
render_image(ROOT / "dashboard_success_by_site.png", 84, 85, 790, 340)
finish()

header("KSC LC-39A outcomes", "Plotly dashboard results",
       "Selecting KSC LC-39A shows 10 successful landings and 3 other outcomes.")
render_image(ROOT / "dashboard_ksc_outcomes.png", 84, 85, 790, 340)
finish()

header("Payload and launch outcome", "Plotly dashboard results",
       "The dashboard's range control can narrow the payload window before comparing outcomes.")
render_image(ROOT / "dashboard_payload_outcome.png", 84, 85, 790, 340)
finish()

header("Classification model accuracy", "Predictive analysis results",
       "The model choice uses cross-validation on the 72 training launches.")
models = RESULTS["classification"]["models"]
horizontal_bars([m["model"] for m in models],
                [m["cross_validation_accuracy"] for m in models],
                x=273, y=167, width=530, step=51, max_value=1,
                fmt=lambda v: f"{v:.1%}")
lines("Selected: decision tree, max depth 2. Mean CV accuracy 83.4%; independent test accuracy 77.8% (14 of 18).", 66, 123, 815, 16, 22, GRAY)
finish()

header("Decision tree confusion matrix", "Predictive analysis results",
       "Rows are actual outcomes, columns are predictions on the untouched test split.")
matrix = next(m["confusion_matrix"] for m in models if m["model"] == "Decision tree")
origin_x, origin_y, cell = 346, 136, 105
for i in range(2):
    for j in range(2):
        x = origin_x + j * cell
        y = origin_y + (1 - i) * cell
        c.setFillColor(PALE if i == j else colors.HexColor("#f6e9e2"))
        c.rect(x, y, cell, cell, stroke=1, fill=1)
        c.setFont("Helvetica-Bold", 33)
        c.setFillColor(TEAL if i == j else ORANGE)
        c.drawCentredString(x + cell / 2, y + 36, str(matrix[i][j]))
c.setFont("Helvetica", 15)
c.setFillColor(DARK)
c.drawCentredString(origin_x + 105, origin_y + 235, "Predicted: other       landing")
c.drawRightString(origin_x - 18, origin_y + 156, "Actual: other")
c.drawRightString(origin_x - 18, origin_y + 51, "Actual: landing")
lines("The tree correctly classifies all 6 non-landings but misses 4 of 12 landings in this small test split.", 75, 100, 805, 14, 20, GRAY)
finish()

header("Conclusion", "Takeaways")
y = 392
for text in (
    "The historical first-stage landing rate is 66.7% across 90 launches. It improves markedly after the earliest years, but the annual groups vary in size.",
    "Location and mission type are associated with different outcomes. Because the launch mix changes over time, these descriptive differences cannot identify a site or orbit as a cause.",
    "The selected shallow tree exceeds the majority-class baseline on this split (77.8% versus 66.7%). A larger, more recent dataset and repeated external validation would be needed before operational use.",
):
    y = bullet(text, y)
finish()

header("Data and reproduction notes", "Appendix")
y = 394
sources = [
    "IBM Skills Network: datasets/dataset_part_2.csv and datasets/dataset_part_3.csv",
    "IBM Skills Network: labs/module_2/data/Spacex.csv",
    "IBM Skills Network: datasets/spacex_launch_dash.csv",
    "Local source files: analyze.py, visuals.py, launch_sites_map.html and launch_dashboard.html",
]
for item in sources:
    y = bullet(item, y)
lines("Source base: https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBM-DS0321EN-SkillsNetwork/",
      66, 150, 825, 13, 18, GRAY)
lines("The report describes a historical course snapshot. Model estimates are limited by small sample size and possible changes in launch operations after 2020.",
      66, 110, 825, 13, 18, GRAY)
finish()

c.save()
print(f"Created {OUTPUT} ({page_number} pages)")
