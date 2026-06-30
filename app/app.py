"""
CV-Diz Prototype v0.6
Adds Evidence Library and Interview Prep Engine.
"""

import os
import hashlib
from services.config_service import get_neo4j_uri, get_neo4j_username, get_neo4j_password

pwd = get_neo4j_password() or ""

st.sidebar.write("URI:", get_neo4j_uri())
st.sidebar.write("User:", get_neo4j_username())
st.sidebar.write("Password length:", len(pwd))
st.sidebar.write("Password hash:", hashlib.sha256(pwd.encode()).hexdigest()[:12])

from dataclasses import dataclass
import streamlit as st
from dotenv import load_dotenv
from services.neo4j_service import Neo4jService
from services.config_service import (
    get_openai_api_key,
    get_neo4j_uri,
    get_neo4j_username,
    get_neo4j_password,
)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None

try:
    from services.neo4j_service import Neo4jService
except ImportError:
    Neo4jService = None

load_dotenv()

APP_TITLE = "CV-Diz: Media Application Coach"
MODEL_NAME = "gpt-4.1-mini"


@dataclass
class ApplicationInputs:
    candidate_profile: str
    evidence_context: str
    research_context: str
    cv_text: str
    job_text: str
    company_name: str
    role_title: str
    application_draft: str
    notes: str
    review_mode: str


def extract_pdf_text(uploaded_file) -> str:
    if PdfReader is None:
        return "[PDF parser not installed. Run: pip install pypdf]"
    reader = PdfReader(uploaded_file)
    return "\n\n".join((page.extract_text() or "") for page in reader.pages).strip()


def extract_docx_text(uploaded_file) -> str:
    if docx is None:
        return "[DOCX parser not installed. Run: pip install python-docx]"
    document = docx.Document(uploaded_file)
    return "\n".join(p.text for p in document.paragraphs).strip()


def extract_uploaded_text(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return extract_pdf_text(uploaded_file)
    if name.endswith(".docx"):
        return extract_docx_text(uploaded_file)
    if name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="ignore")
    return "[Unsupported file type. Please upload PDF, DOCX or TXT.]"


def get_neo4j_service():
    if Neo4jService is None:
        return None, "Neo4j service not found. Check app/services/neo4j_service.py exists."
    uri = get_neo4j_uri()
    username = get_neo4j_username()
    password = get_neo4j_password()
    if not password:
        return None, "NEO4J_PASSWORD not found. Add it to your .env file."
    try:
        service = Neo4jService(uri=uri, username=username, password=password)
        service.verify_connectivity()
        return service, None
    except Exception as exc:
        return None, f"Neo4j connection failed: {exc}"


def call_openai_text(prompt: str, system_prompt: str, use_web_search: bool = False) -> str:
    if OpenAI is None:
        return "OpenAI package not installed. Run: pip install openai"
    api_key = get_openai_api_key()
    if not api_key:
        return "OPENAI_API_KEY not found. Add it to your .env file in the project root."
    client = OpenAI(api_key=api_key)
    kwargs = {
        "model": MODEL_NAME,
        "input": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    }
    if use_web_search:
        kwargs["tools"] = [{"type": "web_search_preview"}]
    response = client.responses.create(**kwargs)
    return response.output_text


def system_prompt() -> str:
    return """
You are CV-Diz, a rigorous but supportive media-industry career agent.

You help a 27-year-old screen-acting graduate apply for media, film, TV,
production, casting, talent agency, development, runner, assistant, project
coordination and entry-level creative-industry roles.

You review like a practical industry insider, not a generic CV bot.
Be honest, commercially realistic and specific.

Use:
- Candidate Profile as standing background.
- Evidence Library as factual reusable proof.
- Company/Role Research as strategy input.
- CV/application/job advert as specific application evidence.

Do not invent experience. Translate background into employability evidence.
Use a direct, helpful UK professional tone.
""".strip()


def research_prompt(company_name, role_title, job_text, notes) -> str:
    return f"""
Company / organisation:
{company_name or "[Not provided]"}

Role title:
{role_title or "[Not provided]"}

Job advert / source details:
{job_text or "[Not provided]"}

Manual notes / links / observations:
{notes or "[Not provided]"}

Produce a concise company and role intelligence brief:

1. Organisation snapshot
2. Likely hiring psychology
3. Useful language to mirror
4. Likely hidden requirements
5. Role-fit implications for a screen-acting graduate
6. Application strategy
7. Evidence to find or add
8. Cautions

If uncertain, say so clearly. Do not invent facts.
""".strip()


def review_prompt(inputs: ApplicationInputs) -> str:
    return f"""
Review mode:
{inputs.review_mode}

Candidate Profile:
{inputs.candidate_profile or "[Not provided]"}

Evidence Library:
{inputs.evidence_context or "[Not provided]"}

Company / Role Research:
{inputs.research_context or "[Not provided]"}

Company:
{inputs.company_name or "[Not provided]"}

Role title:
{inputs.role_title or "[Not provided]"}

Job advert / application details:
{inputs.job_text or "[Not provided]"}

CV:
{inputs.cv_text or "[Not provided]"}

Draft application:
{inputs.application_draft or "[Not provided]"}

Additional notes:
{inputs.notes or "[Not provided]"}

Produce:

1. Overall fit score out of 100
2. What the employer is probably really looking for
3. Best candidate-positioning angle
4. Application strategy
5. Strongest selling points
6. Best evidence to use from the Evidence Library
7. Missing evidence to add
8. Red flags or risks
9. CV edits
10. Cover letter / application critique
11. Rewritten cover note
12. Short email version
13. Interview preparation — 8 likely questions and answer angles
14. Final agent verdict
""".strip()


def interview_prompt(candidate_profile, evidence_context, research_context, company_name, role_title, job_text, review_text, mode) -> str:
    return f"""
Interview mode:
{mode}

Candidate Profile:
{candidate_profile or "[Not provided]"}

Evidence Library:
{evidence_context or "[Not provided]"}

Company / Role Research:
{research_context or "[Not provided]"}

Company:
{company_name or "[Not provided]"}

Role title:
{role_title or "[Not provided]"}

Job advert:
{job_text or "[Not provided]"}

Most recent agent review:
{review_text or "[Not provided]"}

Create an interview preparation pack:

1. Interview strategy
2. Opening answer to “Tell me about yourself”
3. Why this role / why this company
4. Why moving from screen acting into production/media support
5. 10 likely interview questions
6. Strong answer outline for each question
7. 5 STAR stories to prepare, using the evidence library
8. Weak answers to avoid
9. Practical questions Diz should ask them
10. Final rehearsal checklist
""".strip()


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title("CV-Diz")
    st.caption("Private media-industry CV, application, evidence and interview coach.")

    with st.sidebar:
        st.header("Settings")
        review_mode = st.selectbox(
            "Review mode",
            [
                "Agent mode - tough career positioning review",
                "Production office mode - runner / assistant / coordinator focus",
                "Talent agency mode - discretion, organisation and client-facing focus",
                "Casting / development mode - story, taste and communication focus",
                "Rewrite mode - improve the application pack",
            ],
        )
        interview_mode = st.selectbox(
            "Interview mode",
            [
                "Friendly recruiter",
                "Busy production coordinator",
                "Tough line producer",
                "Talent agency assistant interview",
                "Casting office interview",
            ],
        )
        use_web_search = st.checkbox("Use OpenAI web search if available", value=False)

        st.markdown("---")
        service, error = get_neo4j_service()
        if error:
            st.warning(error)
        else:
            st.success("Neo4j connected")
            service.close()
        st.write("v0.6: Evidence + Interview")

    tab_app, tab_evidence, tab_interview, tab_history = st.tabs(
        ["Application Review", "Evidence Library", "Interview Prep", "History"]
    )

    with tab_app:
        st.subheader("0. Candidate Profile / Background")
        profile_file = st.file_uploader("Upload Candidate Profile", type=["pdf", "docx", "txt"], key="profile_file")
        candidate_profile = st.text_area("Candidate Profile / background notes", value=extract_uploaded_text(profile_file), height=150)

        if st.button("Save Candidate Profile"):
            if not candidate_profile.strip():
                st.warning("Add candidate profile content before saving.")
            else:
                service, error = get_neo4j_service()
                if error:
                    st.error(error)
                else:
                    try:
                        service.upsert_candidate_profile("diz", "Diz", candidate_profile)
                        st.success("Candidate Profile saved.")
                    finally:
                        service.close()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("1. CV")
            cv_file = st.file_uploader("Upload CV", type=["pdf", "docx", "txt"], key="cv_file")
            cv_text = st.text_area("CV text", value=extract_uploaded_text(cv_file), height=220)

            st.subheader("2. Role details / advert")
            company_name = st.text_input("Company / organisation")
            role_title = st.text_input("Role title")
            job_text = st.text_area("Job advert / application brief / source details", height=240)

        with col2:
            st.subheader("3. Company / Role Research")
            extra_research_notes = st.text_area("Manual research notes / links / observations", height=100)

            if st.button("Research Company & Role"):
                with st.spinner("Preparing research brief..."):
                    try:
                        st.session_state["research_context"] = call_openai_text(
                            research_prompt(company_name, role_title, job_text, extra_research_notes),
                            "You are a careful media-industry research assistant. Separate evidence from inference. Do not invent facts.",
                            use_web_search=use_web_search,
                        )
                    except Exception as exc:
                        st.error(f"Research failed: {exc}")
                        st.info("Try unticking web search and paste manual notes instead.")

            research_context = st.text_area(
                "Research context used in review",
                value=st.session_state.get("research_context", ""),
                height=220,
            )

            if st.button("Save Research to Neo4j"):
                service, error = get_neo4j_service()
                if error:
                    st.error(error)
                elif not research_context.strip():
                    st.warning("No research to save.")
                else:
                    try:
                        research_id = service.save_company_research(company_name, role_title, job_text, research_context, extra_research_notes)
                        st.success(f"Research saved: {research_id}")
                    finally:
                        service.close()

            st.subheader("4. Draft application")
            app_file = st.file_uploader("Upload draft application", type=["pdf", "docx", "txt"], key="app_file")
            application_draft = st.text_area("Draft cover letter / application answers", value=extract_uploaded_text(app_file), height=120)
            notes = st.text_area("Extra notes for this application", height=90)

        st.subheader("Evidence context for this application")
        if st.button("Load Evidence from Neo4j"):
            service, error = get_neo4j_service()
            if error:
                st.error(error)
            else:
                try:
                    rows = service.get_evidence_items("diz", limit=30)
                    st.session_state["evidence_context"] = "\n\n".join(
                        f"- {r.get('title')}: {r.get('description')} "
                        f"[Tags: {r.get('tags')}; Skills: {r.get('skills')}; Situation: {r.get('situation')}; Result: {r.get('result')}]"
                        for r in rows
                    )
                    st.success(f"Loaded {len(rows)} evidence items.")
                finally:
                    service.close()

        evidence_context = st.text_area("Evidence context used in review", value=st.session_state.get("evidence_context", ""), height=150)

        if st.button("Review like an agent", type="primary"):
            inputs = ApplicationInputs(
                candidate_profile=candidate_profile,
                evidence_context=evidence_context,
                research_context=research_context,
                cv_text=cv_text,
                job_text=job_text,
                company_name=company_name,
                role_title=role_title,
                application_draft=application_draft,
                notes=notes,
                review_mode=review_mode,
            )

            if not inputs.candidate_profile.strip() and not inputs.cv_text.strip() and not inputs.application_draft.strip():
                st.warning("Please provide at least a Candidate Profile, CV or application draft.")
            elif not inputs.job_text.strip() and not inputs.role_title.strip():
                st.warning("Please provide at least a role title or job advert/application brief.")
            else:
                with st.spinner("Reviewing like a media-industry agent..."):
                    result = call_openai_text(review_prompt(inputs), system_prompt())
                    st.session_state["last_review"] = result
                    st.session_state["last_inputs"] = inputs
                    st.session_state["interview_company_name"] = company_name
                    st.session_state["interview_role_title"] = role_title
                    st.session_state["interview_job_text"] = job_text

        if "last_review" in st.session_state:
            st.subheader("Agent review")
            st.markdown(st.session_state["last_review"])
            st.download_button("Download review as Markdown", st.session_state["last_review"], "cv_diz_agent_review.md", "text/markdown")

            if st.button("Save Application + Review to Neo4j"):
                inputs = st.session_state.get("last_inputs")
                service, error = get_neo4j_service()
                if error:
                    st.error(error)
                else:
                    try:
                        app_id = service.save_application_review(
                            "diz", "Diz", inputs.candidate_profile, inputs.evidence_context,
                            inputs.research_context, inputs.company_name, inputs.role_title,
                            inputs.job_text, inputs.cv_text, inputs.application_draft,
                            inputs.notes, inputs.review_mode, st.session_state["last_review"]
                        )
                        st.session_state["last_application_id"] = app_id
                        st.success(f"Application and review saved: {app_id}")
                    finally:
                        service.close()

    with tab_evidence:
        st.subheader("Evidence Library")
        st.caption("Reusable real examples that support applications and interview answers.")

        c1, c2 = st.columns(2)
        with c1:
            evidence_title = st.text_input("Evidence title")
            evidence_type = st.selectbox("Evidence type", ["Production", "People / communication", "Organisation", "Resilience", "Customer-facing", "Leadership", "Technical", "Other"])
            tags = st.text_input("Tags", placeholder="runner, theatre, logistics, pressure")
            skills = st.text_input("Skills evidenced", placeholder="communication, organisation, calm under pressure")
            situation = st.text_area("Situation", height=90)
            action = st.text_area("Action", height=90)
        with c2:
            result = st.text_area("Result / impact", height=90)
            description = st.text_area("Short description", height=135)
            confidence = st.slider("Confidence this is true/useful", 1, 5, 4)
            source = st.text_input("Source / where this came from", placeholder="CV, theatre job, student film")

            if st.button("Save Evidence Item"):
                if not evidence_title.strip() or not description.strip():
                    st.warning("Add at least a title and short description.")
                else:
                    service, error = get_neo4j_service()
                    if error:
                        st.error(error)
                    else:
                        try:
                            evidence_id = service.save_evidence_item("diz", evidence_title, evidence_type, description, situation, action, result, tags, skills, confidence, source)
                            st.success(f"Evidence saved: {evidence_id}")
                        finally:
                            service.close()

        if st.button("Show Evidence Library"):
            service, error = get_neo4j_service()
            if error:
                st.error(error)
            else:
                try:
                    rows = service.get_evidence_items("diz", limit=50)
                    if not rows:
                        st.info("No evidence items yet.")
                    for r in rows:
                        with st.expander(f"{r.get('title')} — {r.get('evidence_type')}"):
                            st.write(r.get("description"))
                            st.write(f"Situation: {r.get('situation')}")
                            st.write(f"Action: {r.get('action')}")
                            st.write(f"Result: {r.get('result')}")
                            st.write(f"Tags: {r.get('tags')}")
                            st.write(f"Skills: {r.get('skills')}")
                finally:
                    service.close()

        with st.expander("Example evidence items for testing"):
            st.markdown("""
**Handled a difficult audience issue calmly**  
Type: People / communication  
Situation: During a sold-out theatre performance, a customer became upset about seating.  
Action: Stayed calm, listened, found the duty manager, and helped resolve the issue without disrupting the show.  
Result: Customer was settled and the performance continued smoothly.  
Skills: communication, calm under pressure, customer handling.

**Supported student film shoot logistics**  
Type: Production  
Situation: Student film needed cast coordinated across a long shoot day.  
Action: Helped track call times, continuity notes and performer readiness.  
Result: Shoot stayed organised and director could focus on performance and camera work.  
Skills: production support, organisation, teamwork.
""")

    with tab_interview:
        st.subheader("Interview Prep Engine")
        st.caption("Uses profile, evidence, research and latest review to prepare realistic interview answers.")

        interview_candidate_profile = st.text_area("Candidate Profile for interview", value=st.session_state.get("candidate_profile_cache", ""), height=110)
        interview_evidence_context = st.text_area("Evidence context for interview", value=st.session_state.get("evidence_context", ""), height=110)
        interview_research_context = st.text_area("Research context for interview", value=st.session_state.get("research_context", ""), height=110)
        interview_company_name = st.text_input("Interview company", value=st.session_state.get("interview_company_name", ""))
        interview_role_title = st.text_input("Interview role title", value=st.session_state.get("interview_role_title", ""))
        interview_job_text = st.text_area("Interview job advert / brief", value=st.session_state.get("interview_job_text", ""), height=110)
        review_text_for_interview = st.text_area("Most recent review text", value=st.session_state.get("last_review", ""), height=160)

        if st.button("Generate Interview Prep Pack", type="primary"):
            with st.spinner("Building interview preparation pack..."):
                st.session_state["interview_pack"] = call_openai_text(
                    interview_prompt(
                        interview_candidate_profile, interview_evidence_context,
                        interview_research_context, interview_company_name,
                        interview_role_title, interview_job_text,
                        review_text_for_interview, interview_mode
                    ),
                    system_prompt()
                )

        if "interview_pack" in st.session_state:
            st.subheader("Interview Prep Pack")
            st.markdown(st.session_state["interview_pack"])
            st.download_button("Download interview prep as Markdown", st.session_state["interview_pack"], "cv_diz_interview_prep.md", "text/markdown")

            if st.button("Save Interview Prep to Neo4j"):
                service, error = get_neo4j_service()
                if error:
                    st.error(error)
                else:
                    try:
                        prep_id = service.save_interview_prep(
                            "diz", interview_company_name, interview_role_title,
                            interview_mode, st.session_state["interview_pack"],
                            st.session_state.get("last_application_id", "")
                        )
                        st.success(f"Interview prep saved: {prep_id}")
                    finally:
                        service.close()

    with tab_history:
        st.subheader("Application History")
        if st.button("Load recent applications from Neo4j"):
            service, error = get_neo4j_service()
            if error:
                st.error(error)
            else:
                try:
                    rows = service.get_recent_applications("diz", limit=10)
                    if not rows:
                        st.info("No applications found yet.")
                    for row in rows:
                        with st.expander(f"{row.get('role_title', 'Untitled role')} — {row.get('company_name', 'Unknown company')}"):
                            st.write(f"Application ID: {row.get('application_id')}")
                            st.write(f"Created: {row.get('created_at')}")
                            st.write(f"Review mode: {row.get('review_mode')}")
                            st.markdown(row.get("review_text", "")[:2500] + ("..." if len(row.get("review_text", "")) > 2500 else ""))
                finally:
                    service.close()


if __name__ == "__main__":
    main()
