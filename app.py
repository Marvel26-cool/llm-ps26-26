"""Streamlit UI for the Math Word Problem Solver."""
import streamlit as st

from config import EXAMPLE_PROBLEMS
from solver import solve_problem, MathSolverError

st.set_page_config(
    page_title="Math Word Problem Solver",
    page_icon="🧮",
    layout="wide",
)

st.markdown(
    """
    <style>
    .final-answer {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 1.6rem 2rem; border-radius: 14px;
        font-size: 1.7rem; font-weight: 700; text-align: center;
        box-shadow: 0 10px 30px rgba(102,126,234,0.35); margin: 1rem 0;
    }
    .badge-ok {
        display: inline-block; background: #d1fae5; color: #065f46;
        padding: 0.45rem 1rem; border-radius: 999px;
        font-weight: 600; font-size: 0.9rem; margin: 0.4rem 0;
    }
    .badge-warn {
        display: inline-block; background: #fef3c7; color: #92400e;
        padding: 0.45rem 1rem; border-radius: 999px;
        font-weight: 600; font-size: 0.9rem; margin: 0.4rem 0;
    }
    .step-title {
        font-weight: 700; color: #4c1d95;
        margin-bottom: 0.35rem; font-size: 1.02rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

col_icon, col_text = st.columns([1, 7])
with col_icon:
    st.markdown("# 🧮")
with col_text:
    st.title("Math Word Problem Solver")
    st.caption("Step-by-step solutions with explanations — powered by Google Gemini")

st.divider()

if "problem_text" not in st.session_state:
    st.session_state.problem_text = ""
if "history" not in st.session_state:
    st.session_state.history = []

with st.expander("📚 Need inspiration? Try an example", expanded=False):
    for i, ex in enumerate(EXAMPLE_PROBLEMS):
        if st.button(f"▶  {ex['label']}", key=f"ex_{i}", use_container_width=True):
            st.session_state.problem_text = ex["problem"]
            st.rerun()

st.markdown("**Enter your math word problem**")
problem = st.text_area(
    label="Problem input",
    key="problem_text",
    height=140,
    placeholder="e.g., A shopkeeper had 120 chocolates. He sold 45 in the morning and 30 in the evening. How many are left?",
    label_visibility="collapsed",
)

col_solve, col_clear = st.columns([3, 1])
with col_solve:
    solve_clicked = st.button("✨  Solve step by step", type="primary", use_container_width=True)
with col_clear:
    if st.button("🗑️  Clear", use_container_width=True):
        st.session_state.problem_text = ""
        if "last_result" in st.session_state:
            del st.session_state["last_result"]
        st.rerun()

if solve_clicked:
    if not problem.strip():
        st.warning("⚠️ Please enter a problem first.")
    else:
        with st.spinner("🧠 Thinking step by step..."):
            try:
                result = solve_problem(problem)
                st.session_state.last_result = result
                st.session_state.history.insert(
                    0, {"problem": problem.strip(), "result": result}
                )
            except MathSolverError as e:
                st.error(f"❌ {e}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")

if "last_result" in st.session_state:
    result = st.session_state.last_result
    st.divider()
    st.subheader("📘 Step-by-Step Solution")

    steps = result.get("steps") or []
    if steps:
        for i, step in enumerate(steps, 1):
            with st.container(border=True):
                title = step.get("title") or f"Step {i}"
                detail = step.get("detail") or ""
                st.markdown(
                    f"<div class='step-title'>{title}</div>", unsafe_allow_html=True
                )
                st.write(detail)
    else:
        st.info("The model did not return any steps for this input.")

    st.subheader("🎯 Final Answer")
    st.markdown(
        f"<div class='final-answer'>{result['final_answer']}</div>",
        unsafe_allow_html=True,
    )

    v = result.get("verified")
    if v and v.get("ok"):
        st.markdown(
            f"<div class='badge-ok'>✅ Python verified: "
            f"<code>{v['expression']}</code> = {v['computed']:g}</div>",
            unsafe_allow_html=True,
        )
    elif v and not v.get("ok"):
        st.markdown(
            f"<div class='badge-warn'>⚠️ Auto-check: {v.get('reason', 'mismatch')}</div>",
            unsafe_allow_html=True,
        )
    else:
        st.caption(
            "ℹ️ Automated arithmetic verification was not possible for this problem."
        )

if len(st.session_state.history) > 1:
    st.divider()
    with st.expander(
        f"📜 History ({len(st.session_state.history)} problems solved)",
        expanded=False,
    ):
        for idx, item in enumerate(st.session_state.history):
            preview = item["problem"]
            if len(preview) > 90:
                preview = preview[:90] + "..."
            st.markdown(f"**{idx + 1}. {preview}**")
            st.caption(f"Answer: {item['result']['final_answer']}")
            if st.button("Load this problem", key=f"hist_load_{idx}"):
                st.session_state.problem_text = item["problem"]
                st.session_state.last_result = item["result"]
                st.rerun()
            st.markdown("---")