"""
IAI & Rafael IPO Executive Dashboard
=====================================
Source files (read-only, in parent folder):
  - rafael_ipo_analysis.pdf
  - Rafael_Strategic_Intelligence_Briefing.pdf
  - iai_ipo_2026_strategic_analysis_20260503180732.pdf

To update data: edit the RAFAEL_DATA or IAI_DATA dictionaries below.
To run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json, os
from datetime import datetime
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IAI & Rafael IPO Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Base ── */
  .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
  body, .stApp { background-color: #f4f6f9; font-family: 'Segoe UI', sans-serif; }

  /* ── Header ── */
  .dash-header {
    background: #0f172a;
    color: white; padding: 24px 32px; border-radius: 14px; margin-bottom: 24px;
    border-left: 5px solid #3b82f6;
  }
  .dash-header h1 { margin: 0; color: white; font-size: 1.65em; font-weight: 700; letter-spacing: -0.3px; }
  .dash-header p  { margin: 5px 0 0 0; color: #94a3b8; font-size: 0.88em; }

  /* ── Section titles ── */
  .sec-title {
    display: flex; align-items: center; gap: 10px;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 8px; margin: 28px 0 16px 0;
    font-size: 1.05em; font-weight: 700; color: #1e293b;
    letter-spacing: -0.2px;
  }
  .sec-title .sec-icon {
    width: 30px; height: 30px; border-radius: 8px;
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 0.9em; flex-shrink: 0;
  }

  /* ── KPI cards ── */
  .kpi-card {
    background: white; padding: 20px 16px 16px; border-radius: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07), 0 0 0 1px #e8ecf0;
    text-align: center; height: 100%;
  }
  .kpi-val   { font-size: 2em; font-weight: 800; letter-spacing: -0.5px; line-height: 1.1; }
  .kpi-lbl   { font-size: 0.75em; color: #64748b; margin-top: 5px; text-transform: uppercase; letter-spacing: 0.5px; }
  .kpi-delta { font-size: 0.78em; color: #16a34a; margin-top: 3px; font-weight: 600; }

  /* ── Insight cards ── */
  .insight-card {
    background: white;
    border-left: 3px solid #3b82f6;
    padding: 11px 14px; margin: 6px 0; border-radius: 0 10px 10px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    font-size: 0.92em; line-height: 1.5; color: #1e293b;
  }
  .insight-num { font-weight: 700; margin-right: 6px; }
  .src-tag {
    background: #f1f5f9; padding: 2px 7px; border-radius: 4px;
    font-size: 0.72em; color: #64748b; margin-top: 5px; display: inline-block;
  }

  /* ── Status banner ── */
  .status-banner {
    padding: 10px 18px; border-radius: 8px;
    font-size: 0.9em; font-weight: 600; margin-bottom: 16px;
    display: flex; align-items: center; gap: 8px;
  }

  /* ── Info boxes ── */
  .info-box {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 14px 16px; font-size: 0.88em; color: #334155; line-height: 1.6;
  }

  /* ── Risk cards ── */
  .risk-card {
    background: white; border-radius: 10px; padding: 14px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px #e8ecf0;
    margin-bottom: 10px; border-left: 4px solid #ccc;
  }
  .risk-title { font-weight: 700; font-size: 0.92em; color: #1e293b; margin-bottom: 5px; }
  .risk-desc  { font-size: 0.82em; color: #475569; line-height: 1.5; margin-bottom: 8px; }
  .pill {
    display: inline-block; padding: 2px 9px; border-radius: 20px;
    font-size: 0.72em; font-weight: 700; color: white; margin-right: 5px;
  }

  /* ── Stakeholder cards ── */
  .stk-card {
    background: white; border-radius: 10px; padding: 12px 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 0 0 1px #e8ecf0;
    margin-bottom: 8px; display: flex; align-items: flex-start; gap: 12px;
  }
  .stk-avatar {
    width: 38px; height: 38px; border-radius: 50%; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 0.85em; color: white;
  }
  .stk-name  { font-weight: 700; font-size: 0.9em; color: #1e293b; }
  .stk-role  { font-size: 0.78em; color: #64748b; margin-top: 2px; }
  .stk-group { font-size: 0.7em; color: #94a3b8; margin-top: 1px; text-transform: uppercase; letter-spacing: 0.4px; }

  /* ── Structure table ── */
  .struct-row {
    display: flex; padding: 10px 0; border-bottom: 1px solid #f1f5f9;
    font-size: 0.88em;
  }
  .struct-label { width: 170px; flex-shrink: 0; font-weight: 600; color: #475569; }
  .struct-value { color: #1e293b; flex: 1; line-height: 1.5; }

  /* ── Timeline ── */
  .tl-row {
    display: flex; align-items: flex-start; gap: 14px;
    padding: 10px 0; border-bottom: 1px solid #f1f5f9; font-size: 0.87em;
  }
  .tl-date  { width: 110px; flex-shrink: 0; font-weight: 700; color: #475569; }
  .tl-event { flex: 1; color: #1e293b; font-weight: 600; }
  .tl-sig   { flex: 1.2; color: #64748b; }

  /* ── Sentiment ── */
  .sent-banner {
    border-radius: 10px; padding: 16px 20px; margin-bottom: 16px;
    font-size: 1.0em; font-weight: 700;
  }
  .cond-item, .concern-item {
    padding: 7px 12px; border-radius: 7px; margin: 5px 0;
    font-size: 0.87em; line-height: 1.5;
  }
  .cond-item    { background: #f0fdf4; color: #166534; border-left: 3px solid #16a34a; }
  .concern-item { background: #fff7ed; color: #9a3412; border-left: 3px solid #ea580c; }

  /* ── Source table ── */
  .src-footer {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;
    padding: 10px 14px; font-size: 0.82em; color: #64748b; margin-top: 10px;
  }

  /* ── Main tabs — bigger, always-visible labels ── */
  .stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: white;
    border-radius: 12px;
    padding: 6px 8px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 0 0 1px #e2e8f0;
    margin-bottom: 20px;
  }
  .stTabs [data-baseweb="tab"] {
    font-size: 1.05em !important;
    font-weight: 600 !important;
    color: #475569 !important;
    padding: 12px 26px !important;
    border-radius: 8px !important;
    border: none !important;
    background: transparent !important;
    white-space: nowrap;
    transition: background 0.15s, color 0.15s;
  }
  .stTabs [data-baseweb="tab"]:hover {
    background: #f1f5f9 !important;
    color: #1e293b !important;
  }
  .stTabs [aria-selected="true"] {
    background: #0f172a !important;
    color: white !important;
  }
  .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
  .stTabs [data-baseweb="tab-border"]    { display: none !important; }

  /* ── Sub-navigation segmented control ── */
  .stSegmentedControl {
    margin-bottom: 20px !important;
  }
  .stSegmentedControl [data-testid="stSegmentedControlContainer"] {
    background: #f1f5f9 !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid #e2e8f0 !important;
    gap: 3px !important;
  }
  .stSegmentedControl button {
    font-size: 0.93em !important;
    font-weight: 600 !important;
    padding: 8px 18px !important;
    border-radius: 8px !important;
    color: #475569 !important;
    white-space: nowrap;
  }
  .stSegmentedControl button[aria-pressed="true"],
  .stSegmentedControl button[aria-selected="true"] {
    background: #0f172a !important;
    color: white !important;
  }
  /* hide the group label */
  .stSegmentedControl > label { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# DATA — sourced exclusively from PDFs in the parent folder.
# If a field was not present in any source file, it reads:
#   "Not specified in the source files"
# ═══════════════════════════════════════════════════════════════════════════════

# ── RAFAEL ────────────────────────────────────────────────────────────────────
RAFAEL = {
    # ── Executive summary ──────────────────────────────────────────
    "exec": {
        "status": "Active — Pre-IPO Preparation",
        "why_now": (
            "Record financial results post-Iron Swords war; global defense-spending surge; "
            "peak valuation window; fiscal pressure on state to finance war costs "
            "(war expenditure >NIS 1 trillion)."
        ),
        "insights": [
            ("2025 revenue reached $6.28B (+12.5% YoY) — record high; order backlog $23.3B (+18.2%).",
             "rafael_ipo_analysis.pdf"),
            ("IPO structured as private placement (Section 15A) — NOT a public offering. "
             "Avoids ISA full-disclosure requirement.",
             "rafael_ipo_analysis.pdf"),
            ("First phase targets late 2026; state retains >50% (golden share + 'tzō interss' mechanism).",
             "rafael_ipo_analysis.pdf"),
            ("Advisory team (Aminach, Quint, Hauser) formally authorized by Board — April 2026.",
             "Rafael_Strategic_Intelligence_Briefing.pdf"),
            ("Key internal dispute: MoD wants ≤30% cap; GCA pushes for up to 49%.",
             "rafael_ipo_analysis.pdf"),
            ("Wage-cap demand (Budget Foundations Law amendment) and employee equity claim (10% at 30% discount) "
             "are critical labor blockers.",
             "Rafael_Strategic_Intelligence_Briefing.pdf"),
        ],
        "drivers": [
            "Fiscal: financing war costs — state needs >NIS 1 trillion in liquidity",
            "Strategic: compete with listed peers (Elbit), attract top talent, enable M&A",
            "Political: government achievement ahead of elections",
            "Market: peak defense-sector valuations globally post-Oct 7 & Ukraine war",
        ],
        "blockers": [
            "Security: Malmab limits disclosure of classified programs (Iron Dome, Spike, Barak)",
            "Regulatory: ISA full-transparency requirement vs. classified prospectus",
            "Labor: union demands wage-cap relief + 10% equity stake at 30% discount",
            "Structural: MoD (≤30%) vs. GCA (up to 49%) stake-size dispute",
            "Timing: election cycle could freeze senior appointments & key decisions",
        ],
    },

    # ── IPO structure ──────────────────────────────────────────────
    "structure": {
        "float":       "25–49% (GCA draft proposes 10% in first phase; board targets 25–49% total)",
        "type":        "Private Placement — Section 15A (institutional investors only; no public float)",
        "valuation":   "$10B – $20B+  (NIS 60–70B)",
        "stage":       "Pre-mandate — advisors engaged; underwriters not yet formally appointed",
        "state":       "State retains >50% with golden share + 'tzō interss' mechanism. "
                       "Sale in tranches. No foreign investor may exceed 50%. "
                       "Absolute state control preserved.",
        "underwriters":"Poalim IBI / Leumi considered likely pool for TASE underwriting "
                       "(not yet formally signed).",
        "exchange":    "TASE (Tel Aviv Stock Exchange)",
        "source":      "rafael_ipo_analysis.pdf; Rafael_Strategic_Intelligence_Briefing.pdf",
    },

    # ── Financials ─────────────────────────────────────────────────
    "fin": {
        "revenue":        6.28,
        "revenue_delta":  "+12.5% vs 2024",
        "net_profit":     0.391,
        "profit_delta":   "+8.3% vs 2024",
        "backlog":        23.3,
        "backlog_delta":  "+18.2% vs 2024",
        "ebitda":         0.892,
        "ebitda_delta":   "Not specified in the source files",
        "gross_margin":   "28.5%",
        "roe":            "14.2%",
        "debt_equity":    "0.45",
        "current_ratio":  "1.85",
        "cash_flow":      0.456,
        "val_low":        10,
        "val_mid":        15,
        "val_high":       20,
        "bonds":          "Series A & B bonds; Series B NIS 500M issued 2012. "
                          "Midroog credit rating: Aaa.il (upgraded 2011).",
        "debt_notes":     "Debt/Equity ratio 0.45 — moderate leverage",
        # approximate historical trend extracted from chart visuals in the PDF
        "trend_years":  [2020, 2021, 2022, 2023, 2024, 2025],
        "trend_rev":    [3.50, 3.90, 4.50, 5.10, 5.58, 6.28],
        "trend_profit": [0.18, 0.22, 0.27, 0.31, 0.36, 0.391],
        "source":       "rafael_ipo_analysis.pdf",
    },

    # ── Timeline ───────────────────────────────────────────────────
    "timeline": [
        ("Mar 2010",  "Bondholder meeting for Series A/B bonds",
         "First bond issuance — early capital-market access", "Completed",
         "rafael_ipo_analysis.pdf"),
        ("2011",      "Midroog upgrades Rafael to Aaa.il",
         "Highest Israeli credit rating achieved", "Completed",
         "rafael_ipo_analysis.pdf"),
        ("2011",      "Steinitz tax reform: exempts defense companies",
         "Policy foundation for privatization framework", "Completed",
         "Rafael_Strategic_Intelligence_Briefing.pdf"),
        ("2012",      "Series B bonds issued (NIS 500M)",
         "Capital-market infrastructure established", "Completed",
         "rafael_ipo_analysis.pdf"),
        ("2014",      "Cabinet approves 25–49% privatization framework",
         "First formal government authorization for partial IPO", "Completed",
         "Rafael_Strategic_Intelligence_Briefing.pdf"),
        ("Nov 2020",  "IAI privatization approved — establishes blueprint for Rafael",
         "Legal/structural precedent for Rafael IPO", "Completed",
         "rafael_ipo_analysis.pdf"),
        ("2022",      "Ukraine war triggers global defense-spending surge",
         "Valuation window opens; defense-stock appetite grows", "Completed",
         "rafael_ipo_analysis.pdf"),
        ("Oct 2023",  "Iron Swords war begins (Oct 7)",
         "Rafael demand surges; record financials follow", "Completed",
         "rafael_ipo_analysis.pdf"),
        ("Sep–Oct 2025", "PMO grants 60-day mandate to present IPO plan",
         "Political re-authorization at highest level", "Completed",
         "Rafael_Strategic_Intelligence_Briefing.pdf"),
        ("2025",      "Record results: $6.28B revenue, $23.3B backlog",
         "Strongest financial position in company history", "Completed",
         "rafael_ipo_analysis.pdf"),
        ("Jan 2026",  "GCA announces IAI IPO; Rafael to follow",
         "Formal public signal of Rafael IPO track", "Completed",
         "rafael_ipo_analysis.pdf"),
        ("Feb 2026",  "Steinitz confirms first phase late 2026/early 2027",
         "Board chairman sets public timeline expectations", "Completed",
         "rafael_ipo_analysis.pdf"),
        ("Mar 2026",  "Record 2025 results published; GCA draft proposes 10% equity",
         "Financial case confirmed; first structural proposal made public", "Completed",
         "rafael_ipo_analysis.pdf"),
        ("Apr 2026",  "Board authorizes advisory team: Aminach, Quint, Hauser",
         "Official advisory mandate — process formally begins", "Active",
         "rafael_ipo_analysis.pdf"),
        ("Late 2026", "Target: first-phase privatization (25–49% equity float)",
         "First institutional private placement", "Upcoming",
         "rafael_ipo_analysis.pdf"),
        ("2027+",     "Full implementation — complete privatization process",
         "Full market integration and strategic expansion", "Upcoming",
         "rafael_ipo_analysis.pdf"),
    ],

    # ── Stakeholders ───────────────────────────────────────────────
    "stakeholders": [
        ("Benjamin Netanyahu", "Government",    "Prime Minister; chairs Privatization Committee",
         "Very High", "Pro — Active",          "rafael_ipo_analysis.pdf"),
        ("Israel Katz",        "Government",    "Defense Minister; co-signatory on IPO conditions",
         "High",      "Pro, conditional",      "rafael_ipo_analysis.pdf"),
        ("David Amsalem",      "Government",    "Minister for Regional Cooperation",
         "Medium",    "Pro, accelerationist",  "rafael_ipo_analysis.pdf"),
        ("Roi Kahlon",         "Government",    "Director, Government Companies Authority (GCA)",
         "High",      "Strongly Pro",          "rafael_ipo_analysis.pdf"),
        ("Amir Baram",         "Government",    "Director-General, Ministry of Defense",
         "High",      "Pro, with conditions (30% cap)",  "rafael_ipo_analysis.pdf"),
        ("Yuval Shimoni",      "Government",    "Director, Malmab (Security)",
         "Medium",    "Cautious / Skeptical",  "rafael_ipo_analysis.pdf"),
        ("Dr. Yuval Steinitz", "Rafael Internal","Chairman of the Board — Deal Architect",
         "Critical",  "Maximally Pro",         "rafael_ipo_analysis.pdf"),
        ("Yoav Tourgeman",     "Rafael Internal","CEO",
         "High",      "Pro, publicly cautious","rafael_ipo_analysis.pdf"),
        ("Rafael Board",       "Rafael Internal","Corporate authority",
         "High",      "Pro",                   "rafael_ipo_analysis.pdf"),
        ("Victor Hasson",      "Rafael Internal","Chair, Rafael Engineers & Technicians Union",
         "High",      "Conditional Pro (wage cap + 10% equity demand)",
         "rafael_ipo_analysis.pdf"),
        ("Ram Aminach",        "Advisors",      "Head of Advisory Team; Ex-IDF Financial Adviser",
         "High",      "Pro — MoD financial-flows expert",
         "rafael_ipo_analysis.pdf"),
        ("Shmuel Hauser",      "Advisors",      "Regulatory Advisor; Ex-ISA Chairman",
         "High",      "Pro — negotiating ISA exemption",
         "rafael_ipo_analysis.pdf"),
        ("Yankee Quint",       "Advisors",      "Strategic Advisor; Ex-Director ILA & GCA",
         "Medium",    "Pro — real-estate/GCA strategy",
         "rafael_ipo_analysis.pdf"),
        ("Gornitzky & Co.",    "Legal",         "Law firm retained by GCA",
         "Medium",    "Pro — executing legal framework",
         "rafael_ipo_analysis.pdf"),
        ("Yair Katz",          "IAI Cross-ref", "Chair, IAI Workers' Council (simultaneity context)",
         "Medium",    "Conditional Pro",
         "rafael_ipo_analysis.pdf"),
    ],

    # ── Risks ──────────────────────────────────────────────────────
    "risks": [
        ("Security",   "Malmab Classified-Programs Disclosure",
         "Malmab limits disclosure for Mossad/Air Force tech (Iron Dome, Spike, Barak). "
         "Prevents standard public prospectus. No local or international precedent for "
         "an offering of this size with a classified/redacted prospectus.",
         "High",   "Open",           "rafael_ipo_analysis.pdf"),
        ("Regulation", "ISA Disclosure vs. Private Placement",
         "ISA mandates full transparency for listed equity. Rafael seeks Section 15A "
         "private-placement loophole to bypass this requirement.",
         "High",   "In Progress",    "rafael_ipo_analysis.pdf"),
        ("Regulation", "Redacted Prospectus Negotiation",
         "Negotiating disclosure perimeter for classified information. Progress ~45%.",
         "Medium", "In Progress",    "rafael_ipo_analysis.pdf"),
        ("Labor",      "Wage-Cap Relief Demand",
         "Unions demand Budget Foundations Law amendment to lift salary caps. "
         "Without resolution, talent-retention and competitiveness are at risk.",
         "High",   "Open",           "Rafael_Strategic_Intelligence_Briefing.pdf"),
        ("Labor",      "Employee Equity Demand",
         "Workers demand 10% equity at 30% discount + cash bonuses. "
         "Could dilute institutional-investor returns significantly. Progress ~55%.",
         "Medium", "In Progress",    "Rafael_Strategic_Intelligence_Briefing.pdf"),
        ("Political",  "Election-Cycle Freeze",
         "Israeli election cycle could freeze senior appointments and key government "
         "decisions at critical execution points in Q3–Q4 2026.",
         "High",   "Open",           "rafael_ipo_analysis.pdf"),
        ("Political",  "Stake-Size Dispute (MoD vs. GCA)",
         "MoD: hard ≤30% cap. GCA: up to 49%. Unresolved inter-ministry conflict "
         "that could limit offering size and investor returns. Progress ~65%.",
         "Medium", "In Progress",    "rafael_ipo_analysis.pdf"),
        ("Market",     "Market Timing & Investor Appetite",
         "Optimal IPO window is late 2026/early 2027. "
         "Depends on geopolitical stability, global interest rates, "
         "and defense-sector investor sentiment. Progress ~70%.",
         "Medium", "Monitored",      "rafael_ipo_analysis.pdf"),
        ("Execution",  "Underwriter Selection",
         "No underwriter formally appointed. Poalim IBI / Leumi considered likely. "
         "Delay compresses execution timeline. Progress ~90%.",
         "Low",    "In Progress",    "rafael_ipo_analysis.pdf"),
        ("Regulation", "Legislative Approval (Budget Foundations Law)",
         "Budget Foundations Law amendment required for employee wage-cap changes. "
         "Needs Knesset vote. Progress ~80%.",
         "Low",    "In Progress",    "Rafael_Strategic_Intelligence_Briefing.pdf"),
    ],

    # ── Sentiment ──────────────────────────────────────────────────
    "sentiment": {
        "overall":   "Mixed — Cautiously Optimistic",
        "narrative": (
            "Strong financial fundamentals and political will at the highest level exist, "
            "but structural barriers — security disclosure, union demands, and inter-ministry "
            "stake-size dispute — create meaningful execution uncertainty. "
            "The shift from 'public IPO' to 'private placement' reflects pragmatic adaptation "
            "to classification constraints rather than lack of ambition."
        ),
        "conditions": [
            "ISA disclosure resolved via Section 15A private-placement route",
            "Wage-cap amendment passed through Knesset before election period",
            "MoD–GCA agreement on stake size (30% vs. 49%)",
            "Union acceptance of equity-allocation terms",
            "No election freeze during Q3–Q4 2026 execution window",
        ],
        "concerns": [
            "Classified programs cannot be disclosed in a standard prospectus",
            "No precedent for an IPO of this scale with a classified/redacted prospectus",
            "Union wage-law demands could derail the entire process",
            "Political urgency before elections may force a suboptimal deal",
            "Foreign-investor restrictions limit the pool of potential buyers",
        ],
        "source": "rafael_ipo_analysis.pdf; Rafael_Strategic_Intelligence_Briefing.pdf",
    },

    # ── Sources ────────────────────────────────────────────────────
    "sources": [
        ("rafael_ipo_analysis.pdf",
         "Strategic Analysis — English slides (6 pages)",
         "Rafael",
         "Executive summary, financial highlights, stakeholder map, "
         "IPO structure, timeline, structural challenges"),
        ("Rafael_Strategic_Intelligence_Briefing.pdf",
         "Strategic Intelligence Briefing — Hebrew slides (14 pages)",
         "Rafael",
         "Detailed timeline, forces/blockers balance, deal structure detail, "
         "risk matrix, government/state position, strategic context (Hebrew RTL)"),
    ],
}

# ── IAI ───────────────────────────────────────────────────────────────────────
IAI = {
    # ── Executive summary ──────────────────────────────────────────
    "exec": {
        "status": "Active — Advanced Advisory Phase",
        "why_now": (
            "Fiscal deficit relief post-Oct 7 war (NIS 20–30B target); "
            "peak defense-sector valuations; IAI capital/M&A agility needs; "
            "political momentum for government achievement before elections."
        ),
        "insights": [
            ("FY2025 revenue $7.38B (+12.5% YoY); order backlog $29–30B — largest in company history.",
             "Defence Industry Europe",
             "https://defence-industry.eu/israel-aerospace-industries-reports-record-2025-financial-results-with-strong-growth-and-order-backlog-nearing-30-billion/"),
            ("GCA valuation estimate: NIS 80–100B ($25–32B USD) — comparable to Elbit Systems.",
             "Ynet",
             "https://www.ynetnews.com/business/article/byqqynnbbe"),
            ("Critical blocker: union (Yair Katz) demands Budget Foundations Law wage amendment "
             "before supporting IPO.",
             "Calcalist",
             "https://www.calcalistech.com/ctechnews/article/bknrsithbe"),
            ("Stake conflict: GCA seeks 49% vs. MoD's hard 30% cap — unresolved as of May 2026.",
             "Times of Israel",
             "https://www.timesofisrael.com/israel-eyes-privatization-of-defense-giants-iai-and-rafael-via-public-share-sale/"),
            ("MoD requires simultaneous listing with Rafael, which is 18–30 months behind IAI.",
             "Jerusalem Post",
             "https://www.jpost.com/defense-and-tech/article-883293"),
            ("Board Chair position vacant >1 year — critical governance gap for an imminent IPO.",
             "Calcalist",
             "https://www.calcalistech.com/ctechnews/article/sjftmg11hbl"),
        ],
        "drivers": [
            "Fiscal: state revenue need — NIS 20–30B IPO proceeds reduce debt-to-GDP",
            "Strategic: IAI capital/M&A agility vs. global defense peers",
            "Market: peak defense valuations post-Oct 7 — historical window",
            "Political: government achievement target before elections",
        ],
        "blockers": [
            "Labor: wage-law standoff with union — Budget Foundations Law amendment demanded",
            "MoD simultaneity requirement with Rafael (18–30 months behind)",
            "Governance: Board Chair vacant >1 year",
            "Regulatory: GCA (49%) vs. MoD (30%) stake conflict",
            "Execution: underwriting syndicate not yet appointed",
        ],
    },

    # ── IPO structure ──────────────────────────────────────────────
    "structure": {
        "float":       "25–30% in 3 tranches: Tranche 1 (10%) + Tranche 2 (8%) + Tranche 3 (7%)",
        "type":        "TASE listing — phased tranches; institutional primary with potential public component",
        "valuation":   "NIS 80–100B  ($25–32B USD)",
        "stage":       "Advanced Advisory Phase — legal counsel (Gornitzky & Co.) retained; "
                       "underwriters pending",
        "state":       "State retains 70–75%. MoD hard cap: max 30% sold. "
                       "No foreign investor control permitted.",
        "underwriters":"Not yet appointed — beauty contest to begin at Week 6–8 of critical path.",
        "exchange":    "TASE (Tel Aviv Stock Exchange)",
        "source":      "iai_ipo_2026_strategic_analysis_20260503180732.pdf",
    },

    # ── Financials ─────────────────────────────────────────────────
    "fin": {
        "revenue":       7.38,
        "revenue_delta": "+12.5% YoY",
        "net_profit":    0.712,
        "profit_delta":  "+8.3% YoY",
        "backlog_label": "$29–30B",
        "backlog":       29.5,
        "backlog_delta": "Not specified in the source files",
        "ebitda":        1.08,
        "ebitda_delta":  "+15.2% YoY",
        "ebitda_margin": "14.6%",
        "net_margin":    "9.6%",
        "cash":          3.9,
        "cash_delta":    "+5.1% YoY",
        "dividend":      0.242,
        "debt_equity":   "Not specified in the source files",
        "current_ratio": "Not specified in the source files",
        "cash_flow":     None,
        "val_low":       25,
        "val_mid":       28,
        "val_high":      32,
        "bonds":         "Not specified in the source files",
        "debt_notes":    "Minimal / Net Cash position (as stated in source)",
        "trend_years":   None,
        "source":        "iai_ipo_2026_strategic_analysis_20260503180732.pdf",
    },

    # ── Timeline ───────────────────────────────────────────────────
    "timeline": [
        ("2003–2010",    "Recurring Knesset debates on privatization; MoD opposed",
         "Long history of failed privatization attempts — establishes political complexity",
         "Completed",    "Wikipedia",
         "https://en.wikipedia.org/wiki/Israel_Aerospace_Industries"),
        ("Nov 2020",     "Ministerial Committee approves sale of up to 49%",
         "First formal government approval for IAI IPO", "Completed",
         "Times of Israel",
         "https://www.timesofisrael.com/israel-eyes-privatization-of-defense-giants-iai-and-rafael-via-public-share-sale/"),
        ("H1 2021",      "IPO process stalls due to security concerns",
         "First failed attempt — disclosure barrier identified as key obstacle", "Completed",
         "IsraelDesks",
         "https://israeldesks.com/iai-eyes-tase-ipo-in-2025/"),
        ("Oct 7, 2023",  "Gaza War begins — global defense demand surges",
         "Demand explosion accelerates IPO urgency and peak valuation timing", "Completed",
         "Ynet",
         "https://www.ynetnews.com/business/article/by1omdr5ze"),
        ("Oct–Nov 2025", "PMO political re-authorization of IPO process",
         "IPO track revived at highest political level", "Completed",
         "Jerusalem Post",
         "https://www.jpost.com/defense-and-tech/article-883293"),
        ("Jan 2026",     "GCA formalizes 25–30% stake-sale target",
         "Operational target set; first public announcement of current phase", "Completed",
         "Haaretz",
         "https://www.haaretz.com/israel-news/2026-01-12/ty-article/.premium/israel-to-privatise-two-key-defense-firms-within-months-government-official-says/0000019b-b328-d352-afbb-b7eb5abd0000"),
        ("Mar 2026",     "MoD conditional approval — 30% hard cap imposed",
         "MoD sets hard limit; creates stake conflict with GCA's 49% target", "In Progress",
         "Jerusalem Post",
         "https://www.jpost.com/defense-and-tech/article-883293"),
        ("May 2026",     "Current phase: Advanced Advisory — Gornitzky & Co. retained",
         "Legal framework being built; critical path defined (IPO prep 85% complete)", "Active",
         "Calcalist",
         "https://www.calcalistech.com/ctechnews/article/sjftmg11hbl"),
        ("Week 1–2",     "Broker compromise on wage framework (critical path)",
         "Union deal must precede IPO — single highest-probability blocker", "Upcoming",
         "Calcalist",
         "https://www.calcalistech.com/ctechnews/article/bknrsithbe"),
        ("Week 2–4",     "Resolve stake-size policy conflict (GCA 49% vs. MoD 30%)",
         "Determines actual float size and proceeds allocation", "Upcoming",
         "Times of Israel",
         "https://www.timesofisrael.com/israel-eyes-privatization-of-defense-giants-iai-and-rafael-via-public-share-sale/"),
        ("Week 4–6",     "Appoint permanent Board Chair",
         "Closes 1+ year governance gap; prerequisite for stock-exchange listing", "Upcoming",
         "Calcalist",
         "https://www.calcalistech.com/ctechnews/article/sjftmg11hbl"),
        ("Week 6–8",     "Begin underwriter beauty contest",
         "Selecting lead managers for TASE listing", "Upcoming",
         "Ynet",
         "https://www.ynetnews.com/business/article/byqqynnbbe"),
        ("Week 8–10",    "TASE investor education roadshow begins",
         "Market preparation for institutional investors", "Upcoming",
         "Ynet",
         "https://www.ynetnews.com/business/article/byqqynnbbe"),
        ("Q2 2026",      "IPO launch — first tranche (10%)",
         "Historic first public listing of IAI on TASE", "Upcoming",
         "Ynet",
         "https://www.ynetnews.com/business/article/byqqynnbbe"),
    ],

    # ── Stakeholders ───────────────────────────────────────────────
    "stakeholders": [
        ("Benjamin Netanyahu", "Government",     "Prime Minister — final political authority & IPO sponsor",
         "Critical",  "Champion — Active",
         "iai_ipo_2026_strategic_analysis_20260503180732.pdf"),
        ("David Amsalem",      "Government",     "GCA Chair; Privatization Committee",
         "Very High", "Champion — Active",
         "iai_ipo_2026_strategic_analysis_20260503180732.pdf"),
        ("Roi Kahlon",         "Government",     "GCA Director — operational driver & public spokesperson",
         "High",      "Champion",
         "iai_ipo_2026_strategic_analysis_20260503180732.pdf"),
        ("Israel Katz",        "Government",     "Defense Minister",
         "High",      "Conditional — security conditions",
         "iai_ipo_2026_strategic_analysis_20260503180732.pdf"),
        ("Amir Baram",         "Government",     "MoD Director-General — enforces 30% cap & simultaneity",
         "High",      "Conditional — 30% cap + simultaneity with Rafael",
         "iai_ipo_2026_strategic_analysis_20260503180732.pdf"),
        ("Boaz Levy",          "IAI Internal",   "CEO — public advocate & operational preparation (85% complete)",
         "High",      "Enabler — Active",
         "iai_ipo_2026_strategic_analysis_20260503180732.pdf"),
        ("Vacant Board Chair", "IAI Internal",   "Board governance — position vacant >1 year",
         "High",      "Blocker — Governance gap",
         "iai_ipo_2026_strategic_analysis_20260503180732.pdf"),
        ("Yair Katz",          "Labor",          "IAI Workers' Union Chair — wage amendment demand",
         "High",      "Blocker — wage law amendment demanded",
         "iai_ipo_2026_strategic_analysis_20260503180732.pdf"),
        ("Gornitzky & Co.",    "Legal/Advisors", "Legal counsel retained by IAI/GCA",
         "Medium",    "Enabler — building legal framework",
         "iai_ipo_2026_strategic_analysis_20260503180732.pdf"),
        ("Underwriting Syndicate", "Financial/Advisors", "Lead managers for TASE listing — not yet appointed",
         "Medium",    "Pending — beauty contest not started",
         "iai_ipo_2026_strategic_analysis_20260503180732.pdf"),
    ],

    # ── Risks ──────────────────────────────────────────────────────
    "risks": [
        ("Labor",      "Wage-Law Amendment Standoff",
         "Union demands amendment to Budget Foundations Law to lift salary caps. "
         "Without this, union will not support IPO. "
         "Described as the single highest-probability blocker.",
         "High",   "Open — Blocking IPO",
         "Calcalist",
         "https://www.calcalistech.com/ctechnews/article/bknrsithbe"),
        ("Regulation", "Stake-Size Conflict (GCA 49% vs. MoD 30%)",
         "GCA seeks 49% stake sale; MoD imposes hard 30% cap. "
         "Directly impacts proceeds (NIS 80–100B vs ~50B) and investor appetite.",
         "High",   "Open",
         "Times of Israel",
         "https://www.timesofisrael.com/israel-eyes-privatization-of-defense-giants-iai-and-rafael-via-public-share-sale/"),
        ("Security",   "MoD Simultaneity Requirement with Rafael",
         "MoD requires IAI to list simultaneously with Rafael, "
         "which is 18–30 months behind IAI in readiness. "
         "Could delay an otherwise-ready process by up to 2.5 years.",
         "High",   "Open",
         "Jerusalem Post",
         "https://www.jpost.com/defense-and-tech/article-883293"),
        ("Political",  "Vacant Board Chair — Governance Gap",
         "IAI Board Chair vacant >1 year. "
         "Critical governance prerequisite for a public company listing. "
         "On critical path: appointment at Week 4–6.",
         "High",   "Open — Critical",
         "Calcalist",
         "https://www.calcalistech.com/ctechnews/article/sjftmg11hbl"),
        ("Security",   "ISA Disclosure vs. Classified Programs",
         "Full public disclosure requirements conflict with classified defense programs. "
         "ISA framework noted as 'Resolved' in source — structural tension remains.",
         "Medium", "In Progress",
         "Ynet",
         "https://www.ynetnews.com/business/article/byqqynnbbe"),
        ("Market",     "TASE Absorption Capacity & Geopolitical Risk",
         "Israeli market capacity to absorb NIS 80–100B offering is uncertain. "
         "Geopolitical escalation could damage investor sentiment.",
         "Medium", "Monitored",
         "Ynet",
         "https://www.ynetnews.com/business/article/by1omdr5ze"),
        ("Execution",  "Underwriting Syndicate Not Appointed",
         "No underwriters formally selected. Beauty contest not yet started. "
         "Critical path: Week 6–8 — tight for a Q2 2026 target.",
         "Medium", "Open",
         "Calcalist",
         "https://www.calcalistech.com/ctechnews/article/sjftmg11hbl"),
        ("Political",  "Coalition & Election Dynamics",
         "Vacant Board Chair + coalition instability. "
         "Political pressure to complete before elections may force "
         "a rushed or suboptimal deal structure.",
         "Medium", "Open",
         "Jerusalem Post",
         "https://www.jpost.com/defense-and-tech/article-883293"),
    ],

    # ── Sentiment ──────────────────────────────────────────────────
    "sentiment": {
        "overall":   "Cautiously Positive — Strong Fundamentals, Multiple Structural Blockers",
        "narrative": (
            "IAI enters the IPO process with the strongest financial position in its history "
            "and unambiguous political sponsorship (PM Netanyahu, GCA). "
            "However, three structural blockers — wage-law standoff, MoD simultaneity requirement, "
            "and vacant Board Chair — create genuine uncertainty around the Q2 2026 timeline. "
            "Operational readiness is 85%; political readiness is only 60%."
        ),
        "conditions": [
            "Wage-law amendment resolved — broker compromise between union and government",
            "MoD simultaneity requirement waived or Rafael IPO accelerated",
            "Permanent Board Chair appointed (critical path: Week 4–6)",
            "Stake-size conflict resolved (30% vs. 49%)",
            "Underwriting syndicate selected and formally engaged",
        ],
        "concerns": [
            "Simultaneity clause could delay IAI by up to 18–30 months for political, not financial, reasons",
            "Union wage-law standoff is the most-cited blocker across all source documents",
            "Vacant Board Chair is an unusual governance risk for an imminent IPO",
            "TASE may struggle to absorb a NIS 80–100B offering domestically",
            "Q2 2026 target may be too aggressive given the number of unresolved dependencies",
        ],
        "source": "iai_ipo_2026_strategic_analysis_20260503180732.pdf",
    },

    # ── Sources ────────────────────────────────────────────────────
    "sources": [
        ("iai_ipo_2026_strategic_analysis_20260503180732.pdf",
         "Strategic Analysis — English slides (9 pages, text-extractable)",
         "IAI",
         "Executive summary, financial metrics, stakeholder matrix, "
         "timeline, IPO structure, risk assessment, government dynamics, "
         "critical path, analyst assessment"),
        ("IAI_IPO_Strategic_Analysis.pdf",
         "Strategic Analysis — image-based PDF (15 pages, text not extractable)",
         "IAI",
         "Visual slides only — superseded by timestamped file above. "
         "Not used as primary data source."),
    ],
}

# ── TASE ──────────────────────────────────────────────────────────────────────
TASE = {
    "kpis": [
        ("2025 IPOs",        "21",        "Historic record"),
        ("2025 Capital",     "NIS 21B",   "All-time high"),
        ("TA-125 Return",    "+51%",      "2025 index performance"),
        ("Foreign Inflows",  "NIS 4.4B",  "2025 net foreign capital"),
        ("Avg Daily Volume", "NIS 3.4B",  "+57% vs 2024"),
        ("TASE Revenue",     "NIS 563M",  "All-time record; EBITDA 52%"),
    ],

    "annual": [
        (2021, 97,   10.5,  "PEAK — early-stage 'dream' companies; many later delisted"),
        (2022, 13,   15.0,  "Slowdown; judicial reform protests; governance risk premium rises"),
        (2023, 1,    2.0,   "NEAR-FREEZE — worst since 2008; Oct 7 war in Q4"),
        (2024, 8,    8.4,   "Wartime resilience; TA-35 +28%, TA-125 +29% — both beat S&P 500"),
        (2025, 21,   21.0,  "HISTORIC — 200K new retail accounts; NIS 4.4B foreign inflows"),
        (2026, 5,    3.0,   "Q1+ momentum continues; Palo Alto dual-listed; defense pipeline building"),
    ],

    "routes": [
        ("IPO — Full Public Offering",
         "Prospectus to ISA + TASE. Price discovery via bookbuild. Open to retail + institutional.",
         "Most rigorous; full disclosure required",
         "#dc2626"),
        ("Private Placement (Sec. 15A)",
         "Institutional sophisticated investors only. No full prospectus. Can close in days.",
         "Preferred for defense/classified assets — Rafael route",
         "#d97706"),
        ("Dual Listing",
         "Foreign-listed company joins TASE. Often no new capital raised.",
         "Palo Alto Networks Feb 2026 — landmark",
         "#2563eb"),
        ("TASE UP Platform",
         "Pre-IPO; companies remain private. Raise from accredited investors.",
         "Ideal path for early-stage companies",
         "#16a34a"),
    ],

    "sectors": [
        ("Defense",           "STRONGLY BULLISH", "#16a34a",
         "Record exports ($14.8B, 2024); battle-proven products; European rearmament; war-driven backlog"),
        ("Financials / Banks","BULLISH",           "#2563eb",
         "Rate environment beneficial; strong earnings; recovered from war-period discount"),
        ("Technology",        "CAUTIOUSLY POSITIVE","#0891b2",
         "Lagged global peers during war; recovering 2025; Palo Alto dual-listing a landmark"),
        ("Real Estate",       "CAUTION / BEARISH", "#d97706",
         "Rising rates + construction costs; but Tadhar, Rami Levy RE IPOs planned"),
        ("Food / Consumer",   "MIXED-POSITIVE",    "#7c3aed",
         "Sugat, Tnuva, Mivne — consumer staples showing strong institutional demand"),
        ("Clean Energy",      "DIFFICULT",         "#dc2626",
         "Pre-revenue companies face headwinds; 2021 multiples gone; narrative alone insufficient"),
    ],

    "cases": [
        {
            "id": 1, "name": "NextVision Stabilized Systems (NXSN)",
            "sector": "Defense-Adjacent Tech", "year": "~2021", "status": "Completed",
            "valuation": "Low at IPO → NIS 17–35B (2025)",
            "performance": "+2,600% since IPO",
            "highlights": [
                "Stabilized day/night cameras for drones, ground & aerial military platforms",
                "Revenue growth +664% from 2021 to 2024",
                "Gross margin 72%+ (Q4 2025: revenue $168M, net profit $103M)",
                "Added to TA-35 index in November 2025 — under 4.5 years from IPO",
                "Backlog 2026: NIS 280M+, 80% deliverable within 12 months",
            ],
            "lesson": "Definitive example of Israeli 'defense tech' premium — battle-tested products validated on multiple fronts simultaneously. Investors who held since IPO achieved extraordinary returns.",
            "color": "#16a34a",
        },
        {
            "id": 2, "name": "Aryt Industries (ARYT)",
            "sector": "Defense Components — Fuzes & Explosives", "year": "Long-standing", "status": "War Beneficiary",
            "valuation": "NIS multi-billion (from near-zero pre-war)",
            "performance": "+2,212% since Oct 7 / +408% in 2025 alone",
            "highlights": [
                "Fuzes, detonators, explosive components — 'picks & shovels' defense",
                "Supplier to IAI, Rafael, Elbit, and export markets",
                "TA-90 top performer in 2025",
                "Emergency war procurement of munitions; global ammunition shortage driver",
                "Cyclical risk: tied to wartime demand; normalization risk post-ceasefire",
            ],
            "lesson": "Defense premium on TASE applies across the full value chain. Second-tier suppliers can deliver superior returns to primes due to lower starting valuations and operating leverage.",
            "color": "#dc2626",
        },
        {
            "id": 3, "name": "Mivne Real Estate (MVNE)",
            "sector": "Commercial Real Estate", "year": "2024", "status": "Completed",
            "valuation": "Part of NIS 8.4B total 2024 IPO raise",
            "performance": "Continued trading; no significant post-listing distress",
            "highlights": [
                "Commercial real estate — industrial, logistics, office parks",
                "Spinoff from listed parent entity",
                "Listed during wartime — demonstrated market resilience",
                "Primarily institutional investor base; pension funds seeking real assets",
                "2024: TA-125 +29% — strong tailwind for new listings",
            ],
            "lesson": "Not all successful IPOs are defense. Quality real assets attract capital even in wartime. Precise IPO pricing not publicly disclosed — verify via TASE MAYA portal.",
            "color": "#d97706",
        },
        {
            "id": 4, "name": "Altshuler Shaham Finance (ALTF)",
            "sector": "Financial Services — Asset Management", "year": "2022", "status": "Completed",
            "valuation": "Not specified in source",
            "performance": "Stock appreciated; expanding trading capabilities",
            "highlights": [
                "AUM ~NIS 190B on behalf of 2.3 million clients at IPO",
                "Partial listing of subsidiary; parent remains private",
                "In 2023, joined TASE as full member — executes trades directly",
                "Among Israel's leading investment houses by AUM",
                "Supervised by Capital Markets Authority; established governance",
            ],
            "lesson": "Non-tech, non-defense established businesses can successfully IPO in Israel. Quality and AUM scale matter more than growth narrative in post-2021 markets.",
            "color": "#2563eb",
        },
        {
            "id": 5, "name": "TASE Secondary Offering (TASE.TA)",
            "sector": "Financial Infrastructure — Exchange", "year": "2024", "status": "Completed",
            "valuation": "NIS 353M (~$95M) — 18.5% shares at NIS 20.60/share",
            "performance": "TASE revenue +29% (2025); net profit +79% (2025); ADV +57%",
            "highlights": [
                "Anchor buyer: Bill Ackman (Pershing Square) + Neri Oxman — 4.9% stake",
                "Described as 'most prominent bet on Israel since Oct 7 escalated'",
                "Strongly oversubscribed; multiple institutional buyers",
                "TASE 2025: NIS 563M revenue — all-time record; EBITDA margin 52%",
                "Ackman's purchase shifted global narrative: 'Israel's market is open for business'",
            ],
            "lesson": "When a globally recognized activist investor buys into the exchange itself during active war, the signaling effect on foreign investors is profound. Materially contributed to NIS 4.4B foreign inflow in 2025.",
            "color": "#7c3aed",
        },
        {
            "id": 6, "name": "Sugat (IIII)",
            "sector": "Food & Consumer Staples", "year": "2025", "status": "Completed",
            "valuation": "Not precisely disclosed — part of NIS 21B 2025 raise",
            "performance": "Continued trading; no significant distress",
            "highlights": [
                "Sugar, flour, basic food commodities — established consumer brand",
                "Listed as TA-125 reached record highs — favorable pricing window",
                "Institutional-led; retail via mutual funds",
                "'Quality staples' theme — recession-resilient, pricing power",
                "Listed alongside Mivne Gad — food sector wave in 2025",
            ],
            "lesson": "Representative of 2025 food-sector IPO wave. Exact valuation/subscription data not publicly detailed. Verify via TASE MAYA for complete filings.",
            "color": "#0891b2",
        },
        {
            "id": 7, "name": "Mivne Gad Dairies (GAD)",
            "sector": "Food Manufacturing — Premium Dairy", "year": "Sep 7, 2025", "status": "Completed",
            "valuation": "NIS 725M pre-money → NIS 935M post-money",
            "performance": "Revenue NIS 720M (+6.6%); net income NIS 46M (+19%); debt fully repaid",
            "highlights": [
                "4th largest Israeli dairy, founded 1982 — 3.2x oversubscribed",
                "Capital raised: NIS 280M (NIS 210M primary + NIS 70M secondary)",
                "Float ~30%; founder Ezra Cohen retains 40%",
                "Lead underwriters: Discount Capital + Barak Capital + Hunter",
                "Use of proceeds: new factory in Timorim; 51% stake in Vayler Tofu",
            ],
            "lesson": "3.2x oversubscription for a profitable 40-year-old dairy company signals institutional appetite for proven, cash-generative businesses — not speculative tech. Post-IPO debt repayment improved credit profile immediately.",
            "color": "#16a34a",
        },
        {
            "id": 8, "name": "Smart Shooter — SMASH (SSHT)",
            "sector": "Defense Tech — AI Fire Control", "year": "Mar 2, 2026", "status": "Completed",
            "valuation": "NIS 900M post-money",
            "performance": "2025 revenue $36.5M (+49%); EBITDA $6.5–7.5M (+500%)",
            "highlights": [
                "AI-based fire control systems (SMASH 3000) — precision targeting, anti-drone",
                "Founders: Dr. Michal Mor + Avshalom Arlich (both Rafael veterans)",
                "Capital raised: NIS 260M (NIS 200M primary + NIS 60M secondary)",
                "Clients: 25+ countries; IDF 36%, Europe 40%, Abraham Accords 20%",
                "Phoenix Finance, Altshuler Shaham, Hachshara did NOT sell at IPO",
            ],
            "lesson": "Priced at ~25x 2025 revenues — premium reflects AI + defense narrative, not earnings maturity. IDF = 36% of revenue is single-customer concentration risk. Post-IPO lock-up expiry and backlog execution are key watch items.",
            "color": "#dc2626",
        },
        {
            "id": 9, "name": "DSIT Solutions (DSIT)",
            "sector": "Defense — Underwater Acoustic Systems", "year": "Mar 2026", "status": "Completed",
            "valuation": "NIS 260M post-money",
            "performance": "Revenue +70% H1 2025; operating profit tripled H1 2025",
            "highlights": [
                "Underwater acoustic detection — ports, gas rigs, submarines, maritime infrastructure",
                "Parent: Rafael Advanced Defense Systems — direct subsidiary spinoff",
                "~NIS 50M acquired by public; priced at 26x annualized operating profit",
                "Revenue +70% YoY in H1 2025; operating profit tripled",
                "Rafael using DSIT as partial IPO 'rehearsal' before its own listing",
            ],
            "lesson": "Most significant structural precedent for Rafael's own IPO. DSIT serves as: (1) capital-raising for a subsidiary; (2) governance/disclosure dry run; (3) market signal of Rafael ecosystem quality. Watch DSIT as proxy for Rafael privatization thesis.",
            "color": "#1e40af",
        },
        {
            "id": 10, "name": "Palo Alto Networks (PANW)",
            "sector": "Cybersecurity — Global Fortune 500", "year": "Feb 23, 2026", "status": "Dual Listing",
            "valuation": "~$120B+ (NASDAQ market cap)",
            "performance": "No capital raised; liquidity event for Israeli investors",
            "highlights": [
                "First Fortune 500-scale company to dual-list on TASE in modern era",
                "NASDAQ primary, TASE secondary — no new capital raised",
                "Significant Israeli R&D; key Israeli founders and engineering teams",
                "Listed after TASE Mon-Fri trading reform (January 2026)",
                "Part of TASE strategy for MSCI index inclusion",
            ],
            "lesson": "Not every IPO is about raising capital. Signals to global companies that TASE is a serious secondary market. More Fortune 500 dual listings would follow if TASE achieves MSCI inclusion — generating $1–3B annual passive inflows.",
            "color": "#7c3aed",
        },
    ],

    "pipeline": [
        ("Israel Aerospace Industries (IAI)", "Defense",      "NIS 80–100B", "H2 2026 target",
         "Wage law amendment is binary gate; board chair vacancy unresolved"),
        ("Rafael Advanced Defense Systems",  "Defense",      "NIS 60–70B",  "2027 likely",
         "Private placement structure; classified disclosure challenge; IAI simultaneity condition"),
        ("Tadhar",                            "Real Estate",  "NIS 4.5B",    "2026",
         "Large residential/commercial developer; one of Israel's largest RE IPOs planned"),
        ("Rami Levy Real Estate",             "Real Estate",  "NIS 3.6B",    "2026",
         "Diversified RE assets; less exposed to residential slowdown"),
        ("Tnuva",                             "Food",         "NIS 9–10B",   "2026–2027",
         "Israel's largest dairy — would be one of TASE's biggest-ever food IPOs"),
        ("Begirah Systems",                   "Defense / Simulators", "NIS 2.5B", "2026",
         "Military training simulators; 40 countries; in active underwriter discussions"),
        ("Palsan / Carmoochrome",             "Defense",      "~NIS 1.25B",  "2026",
         "Vehicle protection systems; pursuing merger route rather than standalone IPO"),
    ],

    "conclusions": [
        ("Is the market open?",         "YES — most open since 2021–22; capacity constraints exist for mega-offerings"),
        ("Best performing sector?",     "Defense — by wide margin across returns, subscriptions, and pipeline"),
        ("Quality shift vs. 2021?",     "Significant — profitable, established companies replacing loss-making start-ups"),
        ("Foreign investor role?",      "Growing — NIS 4.4B net inflows 2025; Ackman/Palo Alto shifting sentiment"),
        ("Defense premium duration?",   "Time-limited — European rearmament cycle will plateau by 2028–2030"),
        ("Single biggest risk?",        "IAI/Rafael: Budget Foundations Law amendment — legislative, not technical"),
        ("Market depth concern?",       "IAI at NIS 80–100B requires foreign co-investment; TASE domestic capacity alone insufficient"),
        ("MSCI inclusion upside?",      "Friday trading reform enables eligibility; would generate $1–3B annual passive inflows"),
        ("Best IPO archetype (2025)?",  "Profitable, established, 10%+ EBITDA margin, real backlog, dual-use defense narrative"),
        ("Verdict TASE 2026?",          "SELECTIVELY BULLISH — defense + quality industrials; cautious on pre-revenue and real estate"),
    ],

    "sources": [
        ("TASE_IPO_Market_Overview.pdf",
         "Market Analysis — English (10 pages, text-extractable)",
         "TASE / Market",
         "Market framework, 10 case studies, annual IPO activity 2021–2026, sector sentiment, pipeline, strategic conclusions"),
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def section(title):
    st.markdown(f'<div class="section-bar">{title}</div>', unsafe_allow_html=True)


def pill(text, color):
    return (f'<span class="status-pill" style="background:{color}">{text}</span>')


# ── Colour helpers ────────────────────────────────────────────────────────────

def _rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

def severity_color(s):
    return {"High":"#dc2626","Medium":"#d97706","Low":"#16a34a","Critical":"#7c3aed"}.get(s,"#64748b")

def severity_bg(s):
    return {"High":"#fef2f2","Medium":"#fffbeb","Low":"#f0fdf4","Critical":"#f5f3ff"}.get(s,"#f8fafc")

def position_color(p):
    t = p.lower()
    if "block" in t:                                    return "#dc2626"
    if "champion" in t or "maximally" in t or "strongly" in t: return "#16a34a"
    if "conditional" in t or "cautious" in t or "pending" in t: return "#d97706"
    if "enabler" in t or "pro" in t:                   return "#2563eb"
    return "#64748b"

def status_color(s):
    t = s.lower()
    if "active" in t:    return "#2563eb"
    if "completed" in t: return "#16a34a"
    if "upcoming" in t:  return "#d97706"
    if "progress" in t:  return "#0891b2"
    if "open" in t or "block" in t: return "#dc2626"
    return "#64748b"

def initials(name):
    parts = name.split()
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


# ── Section title ─────────────────────────────────────────────────────────────

def section(label, icon, accent):
    bg = _rgba(accent, 0.10)
    st.markdown(
        f'<div class="sec-title">'
        f'<span class="sec-icon" style="background:{bg};color:{accent}">{icon}</span>'
        f'{label}</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION RENDERERS
# ═══════════════════════════════════════════════════════════════════════════════

def render_exec(d, accent):
    section("Executive Summary", "📊", accent)
    e = d["exec"]

    # Status banner
    st.markdown(
        f'<div class="status-banner" style="background:{_rgba(accent,0.08)};'
        f'color:{accent};border:1px solid {_rgba(accent,0.25)}">'
        f'<span style="font-size:1.1em">●</span>&nbsp;IPO Status: {e["status"]}</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        st.markdown(
            f'<div style="font-size:0.78em;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.6px;color:#64748b;margin-bottom:10px">Key Insights</div>',
            unsafe_allow_html=True,
        )
        for i, item in enumerate(e["insights"], 1):
            txt = item[0]
            src = item[1] if len(item) > 1 else ""
            url = item[2] if len(item) > 2 else ""
            link = (f'<a href="{url}" target="_blank" rel="noopener noreferrer" '
                    f'style="color:#3b82f6;font-size:0.78em;margin-left:6px;text-decoration:none;'
                    f'font-weight:700;vertical-align:middle;opacity:0.8" title="{src}">↗</a>') if url else ""
            st.markdown(
                f'<div class="insight-card" style="border-left-color:{accent}">'
                f'<span class="insight-num" style="color:{accent}">{i}.</span>{txt}{link}'
                f'</div>',
                unsafe_allow_html=True,
            )

    with c2:
        st.markdown(
            f'<div style="font-size:0.78em;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.6px;color:#64748b;margin-bottom:8px">Why Now?</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="info-box">{e["why_now"]}</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:0.78em;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.6px;color:#64748b;margin-bottom:8px">Main Drivers</div>',
            unsafe_allow_html=True,
        )
        for x in e["drivers"]:
            st.markdown(
                f'<div class="cond-item">✅ {x}</div>', unsafe_allow_html=True
            )
        st.markdown(
            f'<div style="font-size:0.78em;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.6px;color:#64748b;margin:12px 0 8px">Main Blockers</div>',
            unsafe_allow_html=True,
        )
        for x in e["blockers"]:
            st.markdown(
                f'<div class="concern-item">⚠️ {x}</div>', unsafe_allow_html=True
            )


def render_structure(d, accent):
    section("IPO Structure", "🏗️", accent)
    s = d["structure"]

    c1, c2, c3 = st.columns(3, gap="medium")
    for col, lbl, val in [
        (c1, "Float Target",       s["float"][:35] + "…" if len(s["float"]) > 35 else s["float"]),
        (c2, "Expected Valuation", s["valuation"]),
        (c3, "Exchange",           s["exchange"]),
    ]:
        with col:
            st.markdown(
                f'<div class="kpi-card">'
                f'<div class="kpi-lbl">{lbl}</div>'
                f'<div class="kpi-val" style="color:{accent};font-size:1.35em">{val}</div>'
                f'</div>', unsafe_allow_html=True,
            )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    fields = [
        ("Offering Type",        s["type"]),
        ("Current Stage",        s["stage"]),
        ("Underwriters",         s["underwriters"]),
        ("Float Target (full)",  s["float"]),
        ("State Control",        s["state"]),
    ]
    html = '<div style="background:white;border-radius:12px;padding:4px 20px;box-shadow:0 1px 4px rgba(0,0,0,0.06),0 0 0 1px #e8ecf0;">'
    for lbl, val in fields:
        html += (f'<div class="struct-row">'
                 f'<span class="struct-label">{lbl}</span>'
                 f'<span class="struct-value">{val}</span></div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_financials(d, accent):
    section("Financial Overview", "💰", accent)
    f = d["fin"]

    backlog_disp = f.get("backlog_label") or f"${f['backlog']}B"
    kpis = [
        ("Revenue 2025",  f"${f['revenue']}B",   f.get("revenue_delta","")),
        ("Net Profit",    f"${f['net_profit']}B", f.get("profit_delta","")),
        ("Order Backlog", backlog_disp,            f.get("backlog_delta","")),
        ("EBITDA",        f"${f['ebitda']}B",      f.get("ebitda_delta","")),
    ]
    cols = st.columns(4, gap="medium")
    for col, (lbl, val, delta) in zip(cols, kpis):
        with col:
            st.markdown(
                f'<div class="kpi-card">'
                f'<div class="kpi-val" style="color:{accent}">{val}</div>'
                f'<div class="kpi-lbl">{lbl}</div>'
                f'<div class="kpi-delta">{delta if "Not specified" not in delta else ""}</div>'
                f'</div>', unsafe_allow_html=True,
            )

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1], gap="large")

    with c1:
        # Valuation bar chart — clean minimal style
        vals = [f["val_low"], f["val_mid"], f["val_high"]]
        labels = ["Conservative", "Mid-Range", "Optimistic"]
        colors = [_rgba(accent, a) for a in [0.40, 0.65, 1.0]]
        fig = go.Figure(go.Bar(
            x=labels, y=vals,
            marker_color=colors, marker_line_width=0,
            text=[f"${v}B" for v in vals],
            textposition="outside",
            textfont=dict(size=13, color="#1e293b", family="Segoe UI"),
            width=0.42,
        ))
        fig.update_layout(
            title=dict(text="Valuation Scenarios", font=dict(size=13, color="#1e293b"), x=0),
            height=260,
            margin=dict(t=38, b=8, l=8, r=8, pad=0),
            plot_bgcolor="white", paper_bgcolor="white",
            yaxis=dict(range=[0, max(vals)*1.3], showgrid=True,
                       gridcolor="#f1f5f9", tickfont=dict(size=10),
                       title=dict(text="$B USD", font=dict(size=10, color="#94a3b8"))),
            xaxis=dict(showgrid=False, tickfont=dict(size=11)),
            font=dict(family="Segoe UI"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with c2:
        # Metrics as styled HTML rows
        rows = []
        for lbl, key in [
            ("Gross Margin",  "gross_margin"), ("EBITDA Margin", "ebitda_margin"),
            ("Net Margin",    "net_margin"),   ("ROE",            "roe"),
            ("Debt / Equity", "debt_equity"),  ("Current Ratio",  "current_ratio"),
        ]:
            v = f.get(key)
            if v and "Not specified" not in str(v):
                rows.append((lbl, v))
        if f.get("cash"):      rows.append(("Cash",              f"${f['cash']}B"))
        if f.get("cash_flow"): rows.append(("Operating CF",      f"${f['cash_flow']}B"))
        if f.get("dividend"):  rows.append(("Dividend Declared", f"${f['dividend']}B"))

        html = '<div style="background:white;border-radius:12px;padding:4px 16px;box-shadow:0 1px 4px rgba(0,0,0,0.06),0 0 0 1px #e8ecf0;height:100%">'
        for lbl, val in rows:
            html += (f'<div class="struct-row">'
                     f'<span class="struct-label">{lbl}</span>'
                     f'<span class="struct-value" style="font-weight:600">{val}</span></div>')
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    # Revenue trend
    if f.get("trend_years"):
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=f["trend_years"], y=f["trend_rev"], name="Revenue ($B)",
            mode="lines+markers",
            line=dict(color=accent, width=2.5),
            marker=dict(size=7, color="white", line=dict(color=accent, width=2)),
            fill="tozeroy", fillcolor=_rgba(accent, 0.07),
        ))
        fig2.add_trace(go.Scatter(
            x=f["trend_years"], y=f["trend_profit"], name="Net Profit ($B)",
            mode="lines+markers",
            line=dict(color="#16a34a", width=2.5, dash="dot"),
            marker=dict(size=7, color="white", line=dict(color="#16a34a", width=2)),
            yaxis="y2",
        ))
        fig2.update_layout(
            title=dict(text="Revenue & Net Profit Trend 2020–2025", font=dict(size=13, color="#1e293b"), x=0),
            height=260,
            margin=dict(t=38, b=8, l=8, r=8),
            plot_bgcolor="white", paper_bgcolor="white",
            yaxis=dict(title="Revenue ($B)", showgrid=True, gridcolor="#f1f5f9",
                       tickfont=dict(size=10)),
            yaxis2=dict(title="Net Profit ($B)", overlaying="y", side="right",
                        tickfont=dict(size=10), showgrid=False),
            legend=dict(orientation="h", x=0, y=1.12, font=dict(size=11)),
            font=dict(family="Segoe UI"),
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        st.caption("ℹ️ Revenue figures approximated from chart visuals in source PDF")
    else:
        st.caption("ℹ️ Historical revenue trend: not specified in source files for IAI")

    st.markdown(
        f'<div class="info-box" style="margin-top:12px">'
        f'<b>Bonds / Credit Rating:</b> {f.get("bonds","Not specified in the source files")}<br>'
        f'<b>Debt Notes:</b> {f.get("debt_notes","Not specified in the source files")}'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_timeline(d, accent):
    section("Timeline", "📅", accent)
    status_cfg = {
        "Completed":   ("#16a34a", "#f0fdf4"),
        "Active":      ("#2563eb", "#eff6ff"),
        "In Progress": ("#0891b2", "#f0f9ff"),
        "Upcoming":    ("#d97706", "#fffbeb"),
    }
    html = '<div style="background:white;border-radius:12px;padding:4px 20px;box-shadow:0 1px 4px rgba(0,0,0,0.06),0 0 0 1px #e8ecf0;">'
    for t in d["timeline"]:
        date, event, sig, status, src = t[0], t[1], t[2], t[3], t[4]
        url = t[5] if len(t) > 5 else ""
        tc, tbg = status_cfg.get(status, ("#64748b", "#f8fafc"))
        link = (f'<a href="{url}" target="_blank" rel="noopener noreferrer" '
                f'style="color:#3b82f6;font-size:0.78em;margin-left:6px;text-decoration:none;'
                f'font-weight:700;opacity:0.8" title="{src}">↗</a>') if url else ""
        html += f"""
        <div style="display:flex;align-items:flex-start;gap:14px;padding:11px 0;
                    border-bottom:1px solid #f1f5f9;font-size:0.87em">
          <div style="width:100px;flex-shrink:0;font-weight:700;color:#475569;
                      padding-top:2px">{date}</div>
          <div style="flex:1;min-width:0">
            <div style="font-weight:600;color:#1e293b;margin-bottom:3px">{event}{link}</div>
            <div style="color:#64748b;font-size:0.93em;line-height:1.45">{sig}</div>
          </div>
          <div style="flex-shrink:0">
            <span style="background:{tbg};color:{tc};border:1px solid {_rgba(tc,0.3)};
                         padding:2px 9px;border-radius:20px;font-size:0.75em;
                         font-weight:700;white-space:nowrap">{status}</span>
          </div>
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_stakeholders(d, accent):
    section("Stakeholders", "👥", accent)

    rows = [{"Actor":s[0],"Group":s[1],"Role":s[2],
             "Influence":s[3],"Position":s[4],"Source":s[5]}
            for s in d["stakeholders"]]
    df = pd.DataFrame(rows)

    groups = ["All"] + sorted(df["Group"].unique().tolist())
    sel = st.selectbox("Filter by Group", groups, key=f"sg_{accent}")
    view = df if sel == "All" else df[df["Group"] == sel]

    # Card grid — 3 per row
    html = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px">'
    for _, row in view.iterrows():
        pc = position_color(row["Position"])
        bg = _rgba(pc, 0.10)
        html += f"""
        <div class="stk-card">
          <div class="stk-avatar" style="background:{pc}">{initials(row['Actor'])}</div>
          <div style="min-width:0">
            <div class="stk-name">{row['Actor']}</div>
            <div class="stk-group">{row['Group']}</div>
            <div class="stk-role">{row['Role']}</div>
            <div style="margin-top:6px;display:flex;flex-wrap:wrap;gap:4px">
              <span style="background:{bg};color:{pc};border:1px solid {_rgba(pc,0.25)};
                           padding:2px 8px;border-radius:20px;font-size:0.7em;font-weight:700">
                {row['Position'][:30]}</span>
              <span style="background:#f1f5f9;color:#64748b;padding:2px 7px;
                           border-radius:20px;font-size:0.7em">{row['Influence']}</span>
            </div>
          </div>
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    # Influence chart — clean lollipop style
    influence_map = {"Critical":5,"Very High":4,"High":3,"Medium":2,"Low":1}
    df["inf_num"] = df["Influence"].map(influence_map).fillna(2)
    df_s = df.sort_values("inf_num", ascending=True).copy()
    colors = [position_color(p) for p in df_s["Position"]]

    fig = go.Figure()
    # stem lines
    for i, (_, row) in enumerate(df_s.iterrows()):
        fig.add_shape(type="line",
            x0=0, x1=row["inf_num"], y0=i, y1=i,
            line=dict(color="#e2e8f0", width=10))
    # dots
    fig.add_trace(go.Scatter(
        x=df_s["inf_num"], y=list(range(len(df_s))),
        mode="markers+text",
        marker=dict(color=colors, size=14, line=dict(color="white", width=2)),
        text=df_s["inf_num"].astype(int).astype(str),
        textfont=dict(color="white", size=9),
        textposition="middle center",
        hovertemplate="<b>%{customdata[0]}</b><br>Influence: %{x}/5<br>%{customdata[1]}<extra></extra>",
        customdata=list(zip(df_s["Actor"], df_s["Position"])),
    ))
    fig.update_layout(
        title=dict(text="Influence Level by Stakeholder", font=dict(size=13, color="#1e293b"), x=0),
        height=max(280, len(df_s)*32),
        margin=dict(t=38, b=8, l=190, r=20),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(range=[0,5.5], tickvals=[1,2,3,4,5],
                   ticktext=["Low","Medium","High","Very High","Critical"],
                   showgrid=True, gridcolor="#f1f5f9", tickfont=dict(size=11)),
        yaxis=dict(tickvals=list(range(len(df_s))), ticktext=df_s["Actor"].tolist(),
                   tickfont=dict(size=11), showgrid=False),
        showlegend=False, font=dict(family="Segoe UI"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_risks(d, accent):
    section("Risks & Constraints", "⚠️", accent)

    rows = [{"Category":r[0],"Risk":r[1],"Description":r[2],
             "Severity":r[3],"Status":r[4],"Source":r[5],
             "URL": r[6] if len(r) > 6 else ""}
            for r in d["risks"]]
    df = pd.DataFrame(rows)

    cats = ["All"] + sorted(df["Category"].unique().tolist())
    sel = st.selectbox("Filter by Category", cats, key=f"rc_{accent}")
    view = df if sel == "All" else df[df["Category"] == sel]

    # 2-column card grid
    col_a, col_b = st.columns(2, gap="medium")
    for i, (_, row) in enumerate(view.iterrows()):
        sc  = severity_color(row["Severity"])
        sbg = severity_bg(row["Severity"])
        stc = status_color(row["Status"])
        url = row.get("URL", "")
        link = (f'<a href="{url}" target="_blank" rel="noopener noreferrer" '
                f'style="color:#3b82f6;font-size:0.78em;margin-left:6px;text-decoration:none;'
                f'font-weight:700;opacity:0.8" title="{row[\"Source\"]}">↗</a>') if url else ""
        card = f"""
        <div class="risk-card" style="border-left-color:{sc}">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px">
            <span class="risk-title">{row['Risk']}{link}</span>
          </div>
          <div class="risk-desc">{row['Description']}</div>
          <div style="display:flex;flex-wrap:wrap;gap:5px;align-items:center">
            <span class="pill" style="background:{sc}">{row['Severity']}</span>
            <span class="pill" style="background:{stc}">{row['Status']}</span>
            <span style="background:#f1f5f9;color:#64748b;padding:2px 7px;border-radius:10px;
                         font-size:0.7em">{row['Category']}</span>
          </div>
        </div>"""
        (col_a if i % 2 == 0 else col_b).markdown(card, unsafe_allow_html=True)

    # Summary donut by severity
    sev_counts = df.groupby("Severity").size().reset_index(name="Count")
    fig = go.Figure(go.Pie(
        labels=sev_counts["Severity"],
        values=sev_counts["Count"],
        hole=0.6,
        marker_colors=[severity_color(s) for s in sev_counts["Severity"]],
        textinfo="label+value",
        textfont=dict(size=12, family="Segoe UI"),
        hovertemplate="<b>%{label}</b>: %{value} risk(s)<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Risk Distribution by Severity", font=dict(size=13, color="#1e293b"), x=0),
        height=240,
        margin=dict(t=38, b=8, l=8, r=8),
        paper_bgcolor="white",
        showlegend=True,
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.05,
                    font=dict(size=11)),
        font=dict(family="Segoe UI"),
        annotations=[dict(text=f"<b>{len(df)}</b><br><span style='font-size:10'>risks</span>",
                          x=0.5, y=0.5, xref="paper", yref="paper",
                          showarrow=False, font=dict(size=18, color="#1e293b"))],
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_sentiment(d, accent):
    section("Media / Sentiment View", "📰", accent)
    s = d["sentiment"]

    sent_cfg = {
        "mixed":               ("#d97706", "#fffbeb", "#fef3c7"),
        "cautiously optimistic": ("#2563eb", "#eff6ff", "#dbeafe"),
        "cautiously positive":   ("#2563eb", "#eff6ff", "#dbeafe"),
        "positive":            ("#16a34a", "#f0fdf4", "#dcfce7"),
        "negative":            ("#dc2626", "#fef2f2", "#fee2e2"),
    }
    sc, sbg, sborder = next(
        ((v) for k, v in sent_cfg.items() if k in s["overall"].lower()),
        ("#64748b", "#f8fafc", "#e2e8f0"),
    )
    st.markdown(
        f'<div class="sent-banner" style="background:{sbg};color:{sc};border:1px solid {sborder}">'
        f'Overall Sentiment: {s["overall"]}</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        st.markdown(
            '<div style="font-size:0.78em;font-weight:700;text-transform:uppercase;'
            'letter-spacing:0.6px;color:#64748b;margin-bottom:8px">Main Narrative</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="info-box">{s["narrative"]}</div>', unsafe_allow_html=True)
        st.markdown(
            '<div style="font-size:0.78em;font-weight:700;text-transform:uppercase;'
            'letter-spacing:0.6px;color:#64748b;margin:14px 0 8px">Conditions for Success</div>',
            unsafe_allow_html=True,
        )
        for x in s["conditions"]:
            st.markdown(f'<div class="cond-item">✅ {x}</div>', unsafe_allow_html=True)

    with c2:
        st.markdown(
            '<div style="font-size:0.78em;font-weight:700;text-transform:uppercase;'
            'letter-spacing:0.6px;color:#64748b;margin-bottom:8px">Key Concerns</div>',
            unsafe_allow_html=True,
        )
        for x in s["concerns"]:
            st.markdown(f'<div class="concern-item">⚠️ {x}</div>', unsafe_allow_html=True)


def render_sources(d, accent):
    section("Sources", "📚", accent)
    html = '<div style="background:white;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.06),0 0 0 1px #e8ecf0;">'
    html += ('<div style="display:grid;grid-template-columns:2fr 1.5fr 0.6fr 2.5fr;'
             'background:#f8fafc;padding:10px 16px;font-size:0.75em;font-weight:700;'
             'text-transform:uppercase;letter-spacing:0.5px;color:#64748b;'
             'border-bottom:1px solid #e2e8f0">'
             '<div>File Name</div><div>Document Type</div><div>Company</div><div>Key Contribution</div></div>')
    for row in d["sources"]:
        fn, dt, co, kc = row
        html += (f'<div style="display:grid;grid-template-columns:2fr 1.5fr 0.6fr 2.5fr;'
                 f'padding:10px 16px;border-bottom:1px solid #f1f5f9;font-size:0.83em;'
                 f'color:#1e293b;align-items:start">'
                 f'<div style="font-weight:600;color:#2563eb">{fn}</div>'
                 f'<div style="color:#475569">{dt}</div>'
                 f'<div><span style="background:#eff6ff;color:#1d4ed8;padding:2px 8px;'
                 f'border-radius:10px;font-size:0.85em;font-weight:600">{co}</span></div>'
                 f'<div style="color:#64748b;line-height:1.45">{kc}</div></div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
    st.markdown(
        '<div class="src-footer">'
        "📁 Source files: <code>Desktop / Cloude Code folder / KOBI REPORT / IAI and Rafael /</code>"
        " &nbsp;·&nbsp; 🔄 To update: edit data dictionaries in <code>app.py</code> and refresh."
        "</div>",
        unsafe_allow_html=True,
    )


def render_tab(d, company, accent):
    SECTION_LABELS = [
        "📋 Executive Summary",
        "🏛️ IPO Structure",
        "📊 Financials",
        "⏱️ Timeline",
        "👥 Stakeholders",
        "⚠️ Risks",
        "🎯 Sentiment",
    ]
    selected = st.segmented_control(
        "Section", SECTION_LABELS,
        default=SECTION_LABELS[0],
        key=f"subnav_{company}",
    )
    if selected is None:
        selected = SECTION_LABELS[0]
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if selected == "📋 Executive Summary":
        render_exec(d, accent)
    elif selected == "🏛️ IPO Structure":
        render_structure(d, accent)
    elif selected == "📊 Financials":
        render_financials(d, accent)
    elif selected == "⏱️ Timeline":
        render_timeline(d, accent)
    elif selected == "👥 Stakeholders":
        render_stakeholders(d, accent)
    elif selected == "⚠️ Risks":
        render_risks(d, accent)
    elif selected == "🎯 Sentiment":
        render_sentiment(d, accent)


# ═══════════════════════════════════════════════════════════════════════════════
# TASE TAB RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

TASE_ACCENT = "#0f4c81"

def sp():
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)


def _tase_market(t):
    section("Market at a Glance — TASE 2025–2026", "📈", TASE_ACCENT)
    cols = st.columns(6, gap="small")
    for col, (lbl, val, delta) in zip(cols, t["kpis"]):
        with col:
            st.markdown(
                f'<div class="kpi-card">'
                f'<div class="kpi-val" style="color:{TASE_ACCENT};font-size:1.5em">{val}</div>'
                f'<div class="kpi-lbl">{lbl}</div>'
                f'<div class="kpi-delta">{delta}</div>'
                f'</div>', unsafe_allow_html=True,
            )
    sp()
    section("Annual IPO Activity 2021–2026", "📊", TASE_ACCENT)
    years  = [r[0] for r in t["annual"]]
    n_ipos = [r[1] for r in t["annual"]]
    capital= [r[2] for r in t["annual"]]
    notes  = [r[3] for r in t["annual"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[str(y) for y in years], y=n_ipos,
        name="# IPOs",
        marker_color=[_rgba(TASE_ACCENT, a) for a in [0.5,0.5,0.3,0.65,1.0,0.75]],
        marker_line_width=0,
        text=n_ipos, textposition="outside",
        textfont=dict(size=12, color="#1e293b"),
        width=0.4, yaxis="y1",
        hovertemplate="<b>%{x}</b><br># IPOs: %{y}<br>%{customdata}<extra></extra>",
        customdata=notes,
    ))
    fig.add_trace(go.Scatter(
        x=[str(y) for y in years], y=capital,
        name="Capital Raised (NIS B)",
        mode="lines+markers",
        line=dict(color="#d97706", width=2.5),
        marker=dict(size=9, color="white", line=dict(color="#d97706", width=2.5)),
        yaxis="y2",
        hovertemplate="<b>%{x}</b><br>Capital: NIS %{y}B<extra></extra>",
    ))
    fig.update_layout(
        height=300, margin=dict(t=20, b=10, l=8, r=8),
        plot_bgcolor="white", paper_bgcolor="white",
        yaxis=dict(title="# IPOs", showgrid=True, gridcolor="#f1f5f9", tickfont=dict(size=11)),
        yaxis2=dict(title="Capital (NIS B)", overlaying="y", side="right",
                    tickfont=dict(size=11), showgrid=False),
        legend=dict(orientation="h", x=0, y=1.08, font=dict(size=11)),
        bargap=0.35, font=dict(family="Segoe UI"),
        xaxis=dict(tickfont=dict(size=12)),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _tase_routes(t):
    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        section("Listing Routes", "🏛️", TASE_ACCENT)
        for route, desc, best, color in t["routes"]:
            st.markdown(
                f'<div class="risk-card" style="border-left-color:{color}">'
                f'<div class="risk-title" style="color:{color}">{route}</div>'
                f'<div class="risk-desc">{desc}</div>'
                f'<span class="pill" style="background:{_rgba(color,0.12)};color:{color};'
                f'border:1px solid {_rgba(color,0.3)}">{best}</span>'
                f'</div>', unsafe_allow_html=True,
            )
    with c2:
        section("Sector Sentiment (May 2026)", "🎯", TASE_ACCENT)
        for sector, sent, color, driver in t["sectors"]:
            st.markdown(
                f'<div class="risk-card" style="border-left-color:{color}">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">'
                f'<span class="risk-title">{sector}</span>'
                f'<span class="pill" style="background:{color}">{sent}</span></div>'
                f'<div class="risk-desc">{driver}</div>'
                f'</div>', unsafe_allow_html=True,
            )


def _tase_cases(t):
    section("10 Case Studies — Recent TASE IPOs", "🔍", TASE_ACCENT)
    for i in range(0, len(t["cases"]), 2):
        col_a, col_b = st.columns(2, gap="medium")
        for col, case in zip([col_a, col_b], t["cases"][i:i+2]):
            c = case["color"]
            highlights_html = "".join(
                f'<div style="padding:2px 0;font-size:0.8em;color:#475569">• {h}</div>'
                for h in case["highlights"]
            )
            col.markdown(
                f'<div style="background:white;border-radius:12px;padding:16px 18px;'
                f'box-shadow:0 1px 4px rgba(0,0,0,0.07),0 0 0 1px #e8ecf0;'
                f'border-top:3px solid {c};margin-bottom:12px">'
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">'
                f'<span style="background:{c};color:white;font-weight:800;font-size:0.8em;'
                f'padding:3px 9px;border-radius:20px">#{case["id"]}</span>'
                f'<span style="font-weight:700;font-size:0.93em;color:#1e293b">{case["name"]}</span>'
                f'</div>'
                f'<div style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:10px">'
                f'<span class="pill" style="background:{_rgba(c,0.12)};color:{c};border:1px solid {_rgba(c,0.3)}">{case["sector"]}</span>'
                f'<span class="pill" style="background:#f1f5f9;color:#475569">{case["year"]}</span>'
                f'<span class="pill" style="background:{_rgba(c,0.85)}">{case["status"]}</span>'
                f'</div>'
                f'<div style="display:flex;gap:16px;margin-bottom:10px">'
                f'<div><div style="font-size:0.7em;text-transform:uppercase;letter-spacing:0.5px;color:#94a3b8">Valuation</div>'
                f'<div style="font-weight:700;font-size:0.88em;color:{c}">{case["valuation"]}</div></div>'
                f'<div><div style="font-size:0.7em;text-transform:uppercase;letter-spacing:0.5px;color:#94a3b8">Performance</div>'
                f'<div style="font-weight:700;font-size:0.88em;color:#16a34a">{case["performance"]}</div></div>'
                f'</div>'
                f'{highlights_html}'
                f'<div style="margin-top:10px;padding:8px 10px;background:#f8fafc;border-radius:7px;'
                f'font-size:0.78em;color:#64748b;line-height:1.45;border-left:3px solid {c}">'
                f'<b>Lesson:</b> {case["lesson"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def _tase_pipeline(t):
    section("2026 IPO Pipeline", "🚀", TASE_ACCENT)
    pipeline_color = {
        "Defense": "#dc2626", "Real Estate": "#d97706",
        "Food": "#16a34a", "Defense / Simulators": "#7c3aed",
    }
    html = ('<div style="background:white;border-radius:12px;overflow:hidden;'
            'box-shadow:0 1px 4px rgba(0,0,0,0.06),0 0 0 1px #e8ecf0;">'
            '<div style="display:grid;grid-template-columns:2fr 1fr 1fr 0.9fr 3fr;'
            'background:#f8fafc;padding:10px 16px;font-size:0.73em;font-weight:700;'
            'text-transform:uppercase;letter-spacing:0.5px;color:#64748b;'
            'border-bottom:1px solid #e2e8f0">'
            '<div>Company</div><div>Sector</div><div>Valuation</div>'
            '<div>Timeline</div><div>Key Notes</div></div>')
    for company, sector, val, timeline, notes in t["pipeline"]:
        sc = pipeline_color.get(sector, "#64748b")
        html += (f'<div style="display:grid;grid-template-columns:2fr 1fr 1fr 0.9fr 3fr;'
                 f'padding:10px 16px;border-bottom:1px solid #f1f5f9;font-size:0.85em;'
                 f'color:#1e293b;align-items:center">'
                 f'<div style="font-weight:700">{company}</div>'
                 f'<div><span style="background:{_rgba(sc,0.1)};color:{sc};border:1px solid {_rgba(sc,0.25)};'
                 f'padding:2px 8px;border-radius:10px;font-size:0.82em;font-weight:600">{sector}</span></div>'
                 f'<div style="font-weight:700;color:{TASE_ACCENT}">{val}</div>'
                 f'<div style="color:#475569">{timeline}</div>'
                 f'<div style="color:#64748b;font-size:0.85em;line-height:1.4">{notes}</div>'
                 f'</div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def _tase_conclusions(t):
    section("Strategic Conclusions", "💡", TASE_ACCENT)
    c1, c2 = st.columns(2, gap="medium")
    for i, (q, a) in enumerate(t["conclusions"]):
        col = c1 if i % 2 == 0 else c2
        col.markdown(
            f'<div style="background:white;border-radius:10px;padding:12px 14px;'
            f'box-shadow:0 1px 3px rgba(0,0,0,0.06),0 0 0 1px #e8ecf0;margin-bottom:8px">'
            f'<div style="font-size:0.73em;text-transform:uppercase;letter-spacing:0.5px;'
            f'color:#94a3b8;margin-bottom:4px">{q}</div>'
            f'<div style="font-size:0.88em;font-weight:600;color:#1e293b;line-height:1.45">{a}</div>'
            f'</div>', unsafe_allow_html=True,
        )


def render_tase_tab():
    t = TASE
    TASE_SECTIONS = [
        "📈 Market Overview",
        "🏛️ Listing Routes",
        "🔍 Case Studies",
        "🚀 2026 Pipeline",
        "💡 Conclusions",
    ]
    selected = st.segmented_control(
        "Section", TASE_SECTIONS,
        default=TASE_SECTIONS[0],
        key="subnav_tase",
    )
    if selected is None:
        selected = TASE_SECTIONS[0]
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if selected == "📈 Market Overview":
        _tase_market(t)
    elif selected == "🏛️ Listing Routes":
        _tase_routes(t)
    elif selected == "🔍 Case Studies":
        _tase_cases(t)
    elif selected == "🚀 2026 Pipeline":
        _tase_pipeline(t)
    elif selected == "💡 Conclusions":
        _tase_conclusions(t)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ═══════════════════════════════════════════════════════════════════════════════
# NOTES TAB — persistence + renderer
# ═══════════════════════════════════════════════════════════════════════════════

NOTES_FILE = Path(__file__).parent / "notes.json"
NOTES_ACCENT = "#6d28d9"

NOTE_TYPES = ["📰 מאמר / כתבה", "📝 הערה פנימית", "⚠️ התראה / עדכון", "💡 תובנה אנליטית", "📞 פגישה / שיחה"]
NOTE_TAGS  = ["Rafael", "IAI", "TASE", "כללי"]

NOTE_TYPE_COLOR = {
    "📰 מאמר / כתבה":    "#2563eb",
    "📝 הערה פנימית":    "#16a34a",
    "⚠️ התראה / עדכון": "#dc2626",
    "💡 תובנה אנליטית":  "#d97706",
    "📞 פגישה / שיחה":   "#7c3aed",
}
TAG_COLOR = {
    "Rafael": "#1e40af", "IAI": "#15803d",
    "TASE": "#0f4c81",   "כללי": "#64748b",
}


SHEET_COLS = ["id", "title", "type", "tag", "source", "date", "content"]
SHEET_ID   = "16-1tYD1gHiMeo44Gge_b5BX9Ss2C6Q1dOKRwmGuexH0"

@st.cache_resource
def _gspread_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return gspread.authorize(creds)

def _get_sheet():
    return _gspread_client().open_by_key(SHEET_ID).sheet1

def load_notes():
    try:
        records = _get_sheet().get_all_records()
        return records
    except Exception:
        return []

def save_notes(notes):
    try:
        sheet = _get_sheet()
        sheet.clear()
        sheet.append_row(SHEET_COLS)
        for n in notes:
            sheet.append_row([n.get(c, "") for c in SHEET_COLS])
    except Exception as e:
        st.error(f"שגיאה בשמירה: {e}")


def render_notes_tab():
    NA = NOTES_ACCENT

    # ── Add new note form ─────────────────────────────────────────
    section("הוסף הערה / מאמר חדש", "✍️", NA)

    with st.form("add_note_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            title = st.text_input("כותרת *", placeholder="לדוגמה: כלכליסט — פרטי הנפקת רפאל")
        with c2:
            note_type = st.selectbox("סוג", NOTE_TYPES)
        with c3:
            tag = st.selectbox("תיוג", NOTE_TAGS)

        c4, c5 = st.columns([3, 1])
        with c4:
            source = st.text_input("מקור / כותב", placeholder="כלכליסט, TheMarker, שם עמית...")
        with c5:
            note_date = st.date_input("תאריך", value=datetime.today())

        content = st.text_area(
            "תוכן *",
            height=160,
            placeholder="הכנס את תוכן המאמר, הערה פנימית, עדכון, תובנה...",
        )

        submitted = st.form_submit_button("💾  שמור", use_container_width=True,
                                          type="primary")
        if submitted:
            if not title.strip() or not content.strip():
                st.error("כותרת ותוכן הם שדות חובה.")
            else:
                notes = load_notes()
                notes.insert(0, {
                    "id":      int(datetime.now().timestamp() * 1000),
                    "title":   title.strip(),
                    "type":    note_type,
                    "tag":     tag,
                    "source":  source.strip() or "—",
                    "date":    str(note_date),
                    "content": content.strip(),
                })
                save_notes(notes)
                st.success("✅ נשמר בהצלחה!")
                st.rerun()

    sp()
    # ── Filter bar ───────────────────────────────────────────────
    notes = load_notes()

    if not notes:
        st.markdown(
            '<div style="text-align:center;padding:60px 20px;color:#94a3b8;font-size:1.1em">'
            '📋 אין הערות עדיין. הוסף את הראשונה למעלה.</div>',
            unsafe_allow_html=True,
        )
        return

    section(f"הערות שמורות  ({len(notes)})", "📋", NA)

    fc1, fc2, fc3 = st.columns([1, 1, 2])
    with fc1:
        filter_tag  = st.selectbox("סנן לפי תיוג",  ["הכל"] + NOTE_TAGS, key="nf_tag")
    with fc2:
        filter_type = st.selectbox("סנן לפי סוג",  ["הכל"] + NOTE_TYPES, key="nf_type")
    with fc3:
        search = st.text_input("🔍 חיפוש חופשי", placeholder="חפש בכותרת ותוכן...", key="nf_search")

    # Apply filters
    visible = [
        n for n in notes
        if (filter_tag  == "הכל" or n["tag"]  == filter_tag)
        and (filter_type == "הכל" or n["type"] == filter_type)
        and (not search or search.lower() in n["title"].lower() or search.lower() in n["content"].lower())
    ]

    if not visible:
        st.info("אין תוצאות לפילטר הנוכחי.")
        return

    st.markdown(f"<div style='color:#94a3b8;font-size:0.82em;margin-bottom:12px'>{len(visible)} מתוך {len(notes)} הערות</div>",
                unsafe_allow_html=True)

    # ── Notes cards ───────────────────────────────────────────────
    for note in visible:
        tc = NOTE_TYPE_COLOR.get(note["type"], "#64748b")
        gc = TAG_COLOR.get(note["tag"], "#64748b")
        note_id = note["id"]

        # Truncate preview
        preview = note["content"][:280] + ("…" if len(note["content"]) > 280 else "")

        with st.container():
            st.markdown(
                f'<div style="background:white;border-radius:12px;padding:16px 18px;'
                f'box-shadow:0 1px 4px rgba(0,0,0,0.06),0 0 0 1px #e8ecf0;'
                f'border-left:4px solid {tc};margin-bottom:10px">'

                # Header row
                f'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">'
                f'<span style="font-weight:700;font-size:0.97em;color:#1e293b">{note["title"]}</span>'
                f'<span style="color:#94a3b8;font-size:0.78em;flex-shrink:0;margin-left:12px">{note["date"]}</span>'
                f'</div>'

                # Badges row
                f'<div style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:10px">'
                f'<span class="pill" style="background:{tc}">{note["type"]}</span>'
                f'<span class="pill" style="background:{gc}">{note["tag"]}</span>'
                f'<span style="background:#f1f5f9;color:#475569;padding:2px 9px;border-radius:10px;font-size:0.72em">מקור: {note["source"]}</span>'
                f'</div>'

                # Content preview
                f'<div style="font-size:0.87em;color:#334155;line-height:1.6;'
                f'white-space:pre-wrap">{preview}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Expand full + Delete in columns
            ea, eb = st.columns([5, 1])
            with ea:
                if len(note["content"]) > 280:
                    with st.expander("קרא הכל"):
                        st.markdown(
                            f'<div style="font-size:0.88em;color:#334155;line-height:1.7;white-space:pre-wrap">{note["content"]}</div>',
                            unsafe_allow_html=True,
                        )
            with eb:
                if st.button("🗑️ מחק", key=f"del_{note_id}", use_container_width=True):
                    updated = [n for n in notes if n["id"] != note_id]
                    save_notes(updated)
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="dash-header">
  <h1>🛡️ IAI &amp; Rafael — IPO Executive Dashboard</h1>
  <p>Strategic Analysis &nbsp;·&nbsp; May 2026 &nbsp;·&nbsp; Based exclusively on source documents &nbsp;·&nbsp; Confidential</p>
</div>
""", unsafe_allow_html=True)

# ── Top comparison strip ──────────────────────────────────────────────────────
RAFAEL_ACCENT = "#1e40af"
IAI_ACCENT    = "#15803d"

top_kpis = [
    ("Rafael", "Revenue 2025",   "$6.28B",   "+12.5%",  RAFAEL_ACCENT),
    ("Rafael", "Order Backlog",  "$23.3B",   "+18.2%",  RAFAEL_ACCENT),
    ("Rafael", "Valuation",      "$10–20B+", "NIS 60–70B", RAFAEL_ACCENT),
    ("IAI",    "Revenue 2025",   "$7.38B",   "+12.5%",  IAI_ACCENT),
    ("IAI",    "Order Backlog",  "$29–30B",  "FY2025",  IAI_ACCENT),
    ("IAI",    "Valuation",      "$25–32B",  "NIS 80–100B", IAI_ACCENT),
]
cols = st.columns(6, gap="small")
for col, (co, lbl, val, delta, ac) in zip(cols, top_kpis):
    with col:
        st.markdown(
            f'<div class="kpi-card" style="border-top:3px solid {ac}">'
            f'<div class="kpi-lbl" style="color:{ac};font-weight:700">{co}</div>'
            f'<div class="kpi-val" style="color:#1e293b;font-size:1.5em">{val}</div>'
            f'<div class="kpi-lbl">{lbl}</div>'
            f'<div class="kpi-delta">{delta}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_r, tab_i, tab_t = st.tabs(["🛡️  Rafael IPO", "✈️  IAI IPO", "📈  TASE Market"])

with tab_r:
    render_tab(RAFAEL, "Rafael", RAFAEL_ACCENT)

with tab_i:
    render_tab(IAI, "IAI", IAI_ACCENT)

with tab_t:
    render_tase_tab()
