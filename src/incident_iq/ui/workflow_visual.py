import os
from incident_iq.database.db.connection import get_connection
from incident_iq.database.models.incident_log import IncidentLogsModel
import streamlit as st
import time
from datetime import datetime
from pathlib import Path
import sys
import random

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
    
from incident_iq.ml_model.scripts import main_classifier
# from database.db.connection import get_connection
# from database.models.incident_log import IncidentLogsModel

# from models.incident_logs_model import IncidentLogsModel
# from db_connection import get_connection

# ----------------------------------------------
# Optional: Add project base path for imports
# ----------------------------------------------
# BASE_DIR = Path(__file__).resolve().parent.parent.parent
# if str(BASE_DIR) not in sys.path:
#     sys.path.append(str(BASE_DIR))

# ----------------------------------------------
# Mock backend actions — replace with real logic
# ----------------------------------------------
def data_ingestion():
    """Simulate ingestion + call insert_many()"""
    st.write("🔄 Inserting records into ActivityLog table...")
    # conn = get_connection()
    # model = IncidentLogsModel(conn)
    # model.bulk_insert()  # <-- hardcoded insert_many()
    time.sleep(2)
    return f"{datetime.now():%H:%M:%S} - ✅ Data ingestion complete (5 records inserted)."

def data_processing():
    time.sleep(2)
    return f"{datetime.now():%H:%M:%S} - ⚙️ Data cleaning and transformation done."

def model_training():
    main_classifier.main()
    time.sleep(5)
    return f"{datetime.now():%H:%M:%S} - 🧠 Model retraining completed."

def alert_generation():
    time.sleep(2)
    return f"{datetime.now():%H:%M:%S} - 🚨 Alerts triggered for 2 anomalies."

def report_summary():
    time.sleep(2)
    return f"{datetime.now():%H:%M:%S} - 📊 Summary report exported."

# ----------------------------------------------
# Step registry (like UC4 scheduler)
# ----------------------------------------------
WORKFLOW_STEPS = [
    {"name": "📥 Data Ingestion", "info": "Collect and validate raw input data", "note": "Ensures schema and quality checks", "action": data_ingestion},
    {"name": "⚙️ Data Processing", "info": "Clean and transform structured data", "note": "ETL tasks and feature extraction", "action": data_processing},
    {"name": "🧠 Model Training", "info": "Train ML models using updated data", "note": "Hyperparameter tuning in progress", "action": model_training},
    {"name": "🚨 Alert Generation", "info": "Detect anomalies and issue alerts", "note": "Real-time incident scoring", "action": alert_generation},
    {"name": "📊 Report Summary", "info": "Generate insights and reports", "note": "Exports dashboards and summaries", "action": report_summary},
]

# ----------------------------------------------
# Streamlit UI setup
# ----------------------------------------------
def show():
    st.title("⚙️ Cloud AI Agent Workflow Scheduler")

    st.markdown("""
    <style>
    .flow { display:flex; justify-content:center; align-items:center; gap:20px; margin-top:60px; flex-wrap:nowrap; overflow-x:auto; }
    .box { width:250px; height:200px; border-radius:15px; background:linear-gradient(145deg,#1f2937,#111827);
           color:white; text-align:center; display:flex; flex-direction:column; justify-content:center;
           box-shadow:8px 8px 20px #0f172a,-4px -4px 10px #334155; font-weight:600; padding:10px; transition:all .3s ease; }
    .active { border:3px solid #22c55e; box-shadow:0 0 25px #22c55e,inset 0 0 10px #22c55e; animation:pulse 1.5s infinite alternate; }
    @keyframes pulse { from { transform:scale(1);} to { transform:scale(1.05);} }
    .connector { width:80px; height:4px; background:linear-gradient(90deg,#22c55e,#16a34a,#22c55e); border-radius:2px; animation:flow 1s infinite alternate; }
    @keyframes flow { from{opacity:.3;} to{opacity:1;} }
    .logbox { background:#0a0a0a; color:#9ca3af; font-size:13px; padding:10px; border-radius:8px; margin-top:5px; font-family:monospace; }
    </style>
    """, unsafe_allow_html=True)

    # Session state
    if "logs" not in st.session_state:
        st.session_state.logs = []
    if "running" not in st.session_state:
        st.session_state.running = False

    # Start workflow button
    if st.button("▶️ Start Workflow", disabled=st.session_state.running):
        st.session_state.logs.clear()
        st.session_state.running = True
        st.rerun()

    if st.session_state.running:
        placeholder = st.empty()
        for i, step in enumerate(WORKFLOW_STEPS):
            with placeholder.container():
                st.markdown('<div class="flow">', unsafe_allow_html=True)
                for j, s in enumerate(WORKFLOW_STEPS):
                    cls = "box active" if j == i else "box"
                    st.markdown(f"""
                    <div class="{cls}">
                        <div style="font-size:24px;">{s["name"]}</div>
                        <div style="font-size:14px;margin-top:6px;color:#d1d5db;">{s["info"]}</div>
                        <div style="font-size:12px;margin-top:10px;color:#a5b4fc;">💡 {s["note"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if j < len(WORKFLOW_STEPS)-1:
                        st.markdown('<div class="connector"></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # Execute backend step
                with st.expander(f"🔍 Logs for {step['name']}"):
                    st.write(f"⏳ Executing: {step['name']} ...")
                    result = step["action"]()
                    st.session_state.logs.append(result)
                    st.markdown(f'<div class="logbox">{result}</div>', unsafe_allow_html=True)

            time.sleep(1)

        st.session_state.running = False
        st.success("✅ Workflow completed successfully!")
        st.balloons()

    # Show summary logs
    if st.session_state.logs:
        st.subheader("📜 Execution Summary")
        for log in st.session_state.logs:
            st.markdown(f'<div class="logbox">{log}</div>', unsafe_allow_html=True)