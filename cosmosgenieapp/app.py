"""CosmosGenie — a Genie Agent in front of space & astronomy data.

Design principle (borrowed from the bushfire app): the chat is the product.
Everything else on screen exists to help a first-time visitor ask a good
question and trust the answer. Keep it calm: let the theme (.streamlit/
config.toml) do the styling, and write CSS only to fix specific Streamlit warts.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Optional

import pandas as pd
import streamlit as st
from databricks.sdk import WorkspaceClient

import sky_view
from genie_client import GenieClient, GenieError, GenieTurn, rows_to_records

# --------------------------------------------------------------------------
# Config & logging
# --------------------------------------------------------------------------
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout, force=True,
)
log = logging.getLogger("cosmos.app")

GENIE_SPACE_ID = os.environ.get("GENIE_SPACE_ID", "")
WAREHOUSE_ID = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
CATALOG = os.environ.get("UC_CATALOG", "cosmos")
SCHEMA = os.environ.get("UC_SCHEMA", "space")

SUGGESTED_QUESTIONS = [
    "When is the next total solar eclipse and where is it visible?",
    "Which potentially hazardous asteroids approach Earth in the next 30 days?",
    "What planetary conjunctions are coming up in 2026 and 2027?",
    "Which upcoming eclipse has the longest totality?",
    "What are the strongest solar flares on record this year?",
]

# Kid-friendly glossary — reuse the analogies from the Genie instructions so the
# explanation lives in the UI, not just in the semantic layer.
GLOSSARY = [
    ("Opposition", "Earth sits right between the Sun and a planet, so the planet "
                   "looks biggest and brightest — like a streetlight glowing "
                   "brightest when you stand right under it."),
    ("Conjunction", "Two planets look like they're side by side in the sky, even "
                    "though they're really far apart — two friends lining up so "
                    "one appears right behind the other."),
    ("Blood Moon", "A total lunar eclipse. Earth's shadow falls on the Moon and "
                   "paints it red — the Moon stepping into Earth's shadow and blushing."),
    ("Potentially Hazardous Asteroid", "A space rock big enough (>140 m) and close "
                   "enough (<0.05 AU) to keep an eye on. Watched, not feared."),
    ("Lunar distance (LD)", "One Earth-to-Moon trip. '15 lunar distances away' means "
                   "15 Moon-trips away."),
]

st.set_page_config(
    page_title="CosmosGenie",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Minimal, surgical CSS. Only what the theme can't do: make the chat input
# (the product) stand out, and tidy the metric labels.
st.markdown(
    """
    <style>
      /* Clean Aurora theme - static background */
      .stApp {
        background: #0B1426;
      }
      .block-container { padding-top: 1.4rem; max-width: 1320px; }
      div[data-testid="stMetricValue"] { font-size: 1.85rem; font-weight: 700; color: #64FFDA; }
      div[data-testid="stMetricLabel"] { text-transform: uppercase; letter-spacing: .04em;
        font-size: .78rem; color: #9aa6ba; }
      div[data-testid="stChatInput"] {
        border: 2px solid #64FFDA; border-radius: 14px; background: #131F33;
        box-shadow: 0 0 22px rgba(100,255,218,.16); }
      div[data-testid="stChatInput"]:focus-within {
        border-color: #64FFDA; box-shadow: 0 0 0 3px rgba(100,255,218,.26); }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Clients (cached)
# --------------------------------------------------------------------------
@st.cache_resource
def get_workspace_client() -> WorkspaceClient:
    return WorkspaceClient()


@st.cache_resource
def get_genie_client() -> Optional[GenieClient]:
    if not GENIE_SPACE_ID:
        log.error("GENIE_SPACE_ID is not set")
        return None
    try:
        return GenieClient(space_id=GENIE_SPACE_ID, workspace_client=get_workspace_client())
    except Exception:
        log.exception("Could not create Genie client")
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def run_sql(statement: str) -> list[list[Any]]:
    """Small statement against the warehouse. Used only for header stats."""
    if not WAREHOUSE_ID:
        return []
    try:
        w = get_workspace_client()
        resp = w.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID, statement=statement, wait_timeout="30s")
        result = getattr(resp, "result", None)
        return [list(r) for r in (getattr(result, "data_array", None) or [])]
    except Exception:
        log.exception("Header stats query failed")
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def header_stats() -> dict[str, Optional[int]]:
    """A few figures that establish the domain before anyone asks anything.
    Point these at your real tables/views."""
    rows = run_sql(
        f"""
        SELECT
          asteroids_this_week,
          hazardous_count,
          days_to_eclipse,
          days_to_alignment
        FROM {CATALOG}.{SCHEMA}.gold_cosmic_kpis
        LIMIT 1
        """
    )

    def as_int(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    if not rows or len(rows[0]) < 4:
        return {"asteroids_week": None, "hazardous": None, "days_eclipse": None, "days_alignment": None}
    r = rows[0]
    return {"asteroids_week": as_int(r[0]), "hazardous": as_int(r[1]),
            "days_eclipse": as_int(r[2]), "days_alignment": as_int(r[3])}


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
def render_header() -> None:
    st.title("🔭 CosmosGenie")
    st.caption("Ask anything about asteroids, eclipses, planetary events, moon "
               "phases and space weather. Genie writes the SQL.")
    s = header_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Asteroids this week", f"{s['asteroids_week']:,}" if s["asteroids_week"] is not None else "—")
    c2.metric("Potentially hazardous", f"{s['hazardous']:,}" if s["hazardous"] is not None else "—",
              help="Within 0.05 AU and larger than 140 m.")
    c3.metric("Days to next eclipse", f"{s['days_eclipse']:,}" if s["days_eclipse"] is not None else "—")
    c4.metric("Days to next alignment", f"{s['days_alignment']:,}" if s["days_alignment"] is not None else "—")
    st.divider()


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(sky_view.current_moon_svg(), unsafe_allow_html=True)
        st.subheader("How this works")
        st.markdown(
            "Every question goes to a **Genie Agent**, which writes the SQL "
            "itself. Nothing here is a pre-built report — ask anything the data "
            "can answer.")
        with st.expander("What data is available"):
            st.markdown(
                "- **Asteroids & close approaches** (NASA NeoWs)\n"
                "- **Eclipses** (NASA Five Millennium Catalog)\n"
                "- **Planetary events** — oppositions, conjunctions, meteor showers\n"
                "- **Moon phases** and **space weather** (solar flares, storms)\n"
                "- **Space news** and **mission launches**")
        with st.expander("Space terms, explained simply"):
            st.markdown("\n\n".join(f"**{t}**  \n{d}" for t, d in GLOSSARY))
        st.divider()
        st.caption("Powered by Databricks Genie")


def maybe_chart(df: pd.DataFrame) -> Optional[str]:
    """Only chart when it clearly helps. A bad chart is worse than none."""
    if df.empty or len(df.columns) < 2 or len(df) > 30:
        return None
    numeric = df.select_dtypes(include="number").columns
    if len(numeric) == 0 or df.columns[0] in numeric:
        return None
    return "line" if any(k in str(df.columns[0]).lower()
                         for k in ("date", "year", "month")) else "bar"


def render_turn(turn: GenieTurn, key: str) -> None:
    if turn.sql:
        with st.expander("Show the SQL Genie wrote"):
            if turn.sql_description:
                st.caption(turn.sql_description)
            st.code(turn.sql, language="sql")

    if not turn.has_data:
        return

    df = pd.DataFrame(rows_to_records(turn))
    for col in df.columns:  # convert genuinely-numeric string columns
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().all():
            df[col] = converted

    # Prefer a tailored space visual (eclipse map, asteroid scatter, timeline).
    # Show it alongside the table so the data is always inspectable.
    drew_visual = False
    try:
        drew_visual = sky_view.render_result_visual(df, CATALOG, SCHEMA)
    except Exception:
        log.exception("result visual failed")

    if drew_visual:
        st.dataframe(df, use_container_width=True, hide_index=True)
    elif (kind := maybe_chart(df)):
        tab_table, tab_chart = st.tabs(["Table", "Chart"])
        tab_table.dataframe(df, use_container_width=True, hide_index=True)
        with tab_chart:
            indexed = df.set_index(df.columns[0]).select_dtypes("number")
            (st.line_chart if kind == "line" else st.bar_chart)(indexed)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.caption(f"{turn.row_count:,} rows · {turn.elapsed_seconds}s")
    st.download_button("Download CSV", df.to_csv(index=False).encode(),
                       file_name=f"cosmos_{key}.csv", mime="text/csv", key=f"dl_{key}")


def ask_genie(question: str) -> None:
    client = get_genie_client()
    if client is None:
        st.error("Genie is not configured. Check GENIE_SPACE_ID in app.yaml and "
                 "that the app's service principal has 'Can Run' on the Genie space.")
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        status = st.status("Sending your question", expanded=False)
        try:
            turn = client.ask(question,
                              conversation_id=st.session_state.conversation_id,
                              on_status=lambda _s, label: status.update(label=label))
        except Exception as exc:  # never fail silently
            log.exception("Genie call failed")
            status.update(label="Failed", state="error")
            st.session_state.messages.append(
                {"role": "assistant", "content": f"Error: {exc}", "turn": None})
            return
        status.update(label=f"Answered in {turn.elapsed_seconds}s", state="complete")

    st.session_state.conversation_id = turn.conversation_id
    st.session_state.messages.append(
        {"role": "assistant", "content": turn.text or turn.error or "", "turn": turn})


def replay_history() -> None:
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            if msg["role"] == "user":
                st.markdown(msg["content"])
                continue
            turn: Optional[GenieTurn] = msg.get("turn")
            if turn and turn.follow_up:
                st.info(turn.follow_up)
            if msg["content"]:
                st.markdown(msg["content"])
            if turn:
                render_turn(turn, key=f"{turn.message_id}_{i}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("conversation_id", None)

    render_header()
    render_sidebar()

    pending: Optional[str] = None

    # Hero visual + starter questions in one collapsible block. Collapsing it
    # hands the conversation the full page once you're a few questions in.
    with st.expander("Upcoming Events", expanded=True):
        hero_col, ask_col = st.columns([3, 2], gap="large")
        clicked_event = None
        with hero_col:
            try:
                clicked_event = sky_view.render_sky_hero(run_sql, CATALOG, SCHEMA)
            except Exception:
                log.exception("hero visual failed")
                st.info("Sky view unavailable. Ask a question on the right.")
        
        # Show contextual question if user clicked an event
        if clicked_event:
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(135deg, #64FFDA 0%, #82B1FF 100%);
                    padding: 1.2rem;
                    border-radius: 12px;
                    margin: 1rem 0;
                    box-shadow: 0 4px 16px rgba(100, 255, 218, 0.3);
                    border: 2px solid #64FFDA;
                ">
                    <p style="color: #0B1426; font-weight: 700; font-size: 1.1rem; margin: 0 0 0.5rem 0;">
                        🌟 {clicked_event['label']} — {clicked_event['date']}
                    </p>
                    <p style="color: #131F33; font-size: 0.95rem; margin: 0; font-style: italic;">
                        {clicked_event['description']}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            suggested_q = f"Tell me more about the {clicked_event['label'].lower()} on {clicked_event['date']}"
            if st.button(f"🔍 Ask: {suggested_q}", key="clicked_event_q", use_container_width=True, type="primary"):
                pending = suggested_q
            st.divider()
        
        with ask_col:
            st.markdown(
                """
                <div style="
                    background: linear-gradient(135deg, #64FFDA 0%, #82B1FF 100%);
                    padding: 1rem 1.2rem;
                    border-radius: 12px;
                    margin-bottom: 1rem;
                    box-shadow: 0 4px 16px rgba(100, 255, 218, 0.3);
                    border: 2px solid #64FFDA;
                ">
                    <p style="color: #0B1426; font-weight: 700; font-size: 1.2rem; margin: 0 0 0.3rem 0;">
                        🔮 Ask the data a question
                    </p>
                    <p style="color: #131F33; font-size: 0.9rem; margin: 0;">
                        Genie writes the SQL. Nothing here is pre-built.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            for i, q in enumerate(SUGGESTED_QUESTIONS):
                if st.button(q, key=f"sq_{i}", use_container_width=True):
                    pending = q
            st.caption("Or type your own below. Follow-ups keep the thread.")

    if st.session_state.messages:
        st.divider()
        head, clear = st.columns([5, 1])
        head.markdown("#### Conversation")
        if clear.button("Clear", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_id = None
            st.rerun()
        replay_history()

    typed = st.chat_input("Ask about asteroids, eclipses, planets, the Moon…")
    if typed:
        pending = typed

    if pending:
        ask_genie(pending)
        st.rerun()  # redraw so the answer renders from history, not inline


if __name__ == "__main__":
    main()
