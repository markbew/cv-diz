"""
Neo4j service for CV-Diz v0.6.
Adds EvidenceItem and InterviewPrep.
"""

from datetime import datetime, timezone
from uuid import uuid4
from neo4j import GraphDatabase


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Neo4jService:
    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        self.driver.close()

    def verify_connectivity(self):
        self.driver.verify_connectivity()

    def initialise_constraints(self):
        queries = [
            "CREATE CONSTRAINT candidate_id_unique IF NOT EXISTS FOR (n:Candidate) REQUIRE n.candidate_id IS UNIQUE",
            "CREATE CONSTRAINT company_name_unique IF NOT EXISTS FOR (n:Company) REQUIRE n.name IS UNIQUE",
            "CREATE CONSTRAINT application_id_unique IF NOT EXISTS FOR (n:Application) REQUIRE n.application_id IS UNIQUE",
            "CREATE CONSTRAINT review_id_unique IF NOT EXISTS FOR (n:AIReview) REQUIRE n.review_id IS UNIQUE",
            "CREATE CONSTRAINT cv_version_id_unique IF NOT EXISTS FOR (n:CVVersion) REQUIRE n.cv_version_id IS UNIQUE",
            "CREATE CONSTRAINT cover_letter_version_id_unique IF NOT EXISTS FOR (n:CoverLetterVersion) REQUIRE n.cover_letter_version_id IS UNIQUE",
            "CREATE CONSTRAINT company_research_id_unique IF NOT EXISTS FOR (n:CompanyResearch) REQUIRE n.research_id IS UNIQUE",
            "CREATE CONSTRAINT evidence_id_unique IF NOT EXISTS FOR (n:EvidenceItem) REQUIRE n.evidence_id IS UNIQUE",
            "CREATE CONSTRAINT interview_prep_id_unique IF NOT EXISTS FOR (n:InterviewPrep) REQUIRE n.prep_id IS UNIQUE",
        ]
        with self.driver.session() as session:
            for query in queries:
                session.run(query)

    def upsert_candidate_profile(self, candidate_id, display_name, profile_text):
        now = utc_now_iso()
        with self.driver.session() as session:
            session.run("""
                MERGE (c:Candidate {candidate_id: $candidate_id})
                SET c.display_name = $display_name, c.updated_at = $now
                MERGE (p:CandidateProfile {candidate_id: $candidate_id})
                SET p.profile_text = $profile_text, p.updated_at = $now
                MERGE (c)-[:HAS_PROFILE]->(p)
            """, candidate_id=candidate_id, display_name=display_name, profile_text=profile_text, now=now)

    def save_company_research(self, company_name, role_title, job_text, research_text, source_notes):
        now = utc_now_iso()
        research_id = f"research-{uuid4()}"
        clean_company = company_name.strip() if company_name and company_name.strip() else "Unknown company"
        clean_role = role_title.strip() if role_title and role_title.strip() else "Unknown role"
        with self.driver.session() as session:
            session.run("""
                MERGE (co:Company {name: $company_name})
                SET co.updated_at = $now
                MERGE (r:Role {title: $role_title})
                SET r.updated_at = $now
                CREATE (cr:CompanyResearch {
                    research_id: $research_id,
                    research_text: $research_text,
                    source_notes: $source_notes,
                    job_text: $job_text,
                    created_at: $now
                })
                MERGE (co)-[:HAS_RESEARCH]->(cr)
                MERGE (cr)-[:RELATES_TO_ROLE]->(r)
            """, company_name=clean_company, role_title=clean_role, research_id=research_id,
                 research_text=research_text, source_notes=source_notes, job_text=job_text, now=now)
        return research_id

    def save_evidence_item(self, candidate_id, title, evidence_type, description, situation, action, result, tags, skills, confidence, source):
        now = utc_now_iso()
        evidence_id = f"evidence-{uuid4()}"
        with self.driver.session() as session:
            session.run("""
                MERGE (c:Candidate {candidate_id: $candidate_id})
                CREATE (e:EvidenceItem {
                    evidence_id: $evidence_id,
                    title: $title,
                    evidence_type: $evidence_type,
                    description: $description,
                    situation: $situation,
                    action: $action,
                    result: $result,
                    tags: $tags,
                    skills: $skills,
                    confidence: $confidence,
                    source: $source,
                    created_at: $now,
                    updated_at: $now
                })
                MERGE (c)-[:HAS_EVIDENCE]->(e)
            """, candidate_id=candidate_id, evidence_id=evidence_id, title=title, evidence_type=evidence_type,
                 description=description, situation=situation, action=action, result=result,
                 tags=tags, skills=skills, confidence=confidence, source=source, now=now)
        return evidence_id

    def get_evidence_items(self, candidate_id, limit=50):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (:Candidate {candidate_id: $candidate_id})-[:HAS_EVIDENCE]->(e:EvidenceItem)
                RETURN e.evidence_id AS evidence_id, e.title AS title, e.evidence_type AS evidence_type,
                       e.description AS description, e.situation AS situation, e.action AS action,
                       e.result AS result, e.tags AS tags, e.skills AS skills, e.confidence AS confidence,
                       e.source AS source, e.created_at AS created_at
                ORDER BY e.created_at DESC
                LIMIT $limit
            """, candidate_id=candidate_id, limit=limit)
            return [dict(record) for record in result]

    def save_application_review(self, candidate_id, candidate_name, candidate_profile, evidence_context, research_context,
                                company_name, role_title, job_text, cv_text, application_draft, notes, review_mode, review_text):
        now = utc_now_iso()
        application_id = f"app-{uuid4()}"
        review_id = f"review-{uuid4()}"
        cv_version_id = f"cv-{uuid4()}"
        cover_letter_version_id = f"cover-{uuid4()}"
        clean_company = company_name.strip() if company_name and company_name.strip() else "Unknown company"
        clean_role = role_title.strip() if role_title and role_title.strip() else "Unknown role"
        with self.driver.session() as session:
            session.run("""
                MERGE (c:Candidate {candidate_id: $candidate_id})
                SET c.display_name = $candidate_name, c.updated_at = $now
                MERGE (p:CandidateProfile {candidate_id: $candidate_id})
                SET p.profile_text = $candidate_profile, p.updated_at = $now
                MERGE (c)-[:HAS_PROFILE]->(p)
                MERGE (co:Company {name: $company_name})
                SET co.updated_at = $now
                MERGE (r:Role {title: $role_title})
                SET r.updated_at = $now
                CREATE (a:Application {
                    application_id: $application_id,
                    job_text: $job_text,
                    notes: $notes,
                    evidence_context: $evidence_context,
                    research_context: $research_context,
                    review_mode: $review_mode,
                    status: 'draft_reviewed',
                    created_at: $now,
                    updated_at: $now
                })
                CREATE (cv:CVVersion {cv_version_id: $cv_version_id, cv_text: $cv_text, created_at: $now})
                CREATE (cl:CoverLetterVersion {cover_letter_version_id: $cover_letter_version_id, application_text: $application_draft, created_at: $now})
                CREATE (ar:AIReview {review_id: $review_id, review_text: $review_text, created_at: $now})
                MERGE (c)-[:SUBMITTED]->(a)
                MERGE (a)-[:AT]->(co)
                MERGE (a)-[:FOR_ROLE]->(r)
                MERGE (a)-[:USES_CV]->(cv)
                MERGE (a)-[:USES_COVER_LETTER]->(cl)
                MERGE (a)-[:HAS_REVIEW]->(ar)
            """, candidate_id=candidate_id, candidate_name=candidate_name, candidate_profile=candidate_profile,
                 evidence_context=evidence_context, research_context=research_context, company_name=clean_company,
                 role_title=clean_role, application_id=application_id, job_text=job_text, cv_version_id=cv_version_id,
                 cv_text=cv_text, cover_letter_version_id=cover_letter_version_id, application_draft=application_draft,
                 notes=notes, review_mode=review_mode, review_id=review_id, review_text=review_text, now=now)
        return application_id

    def save_interview_prep(self, candidate_id, company_name, role_title, mode, prep_text, application_id=""):
        now = utc_now_iso()
        prep_id = f"prep-{uuid4()}"
        clean_company = company_name.strip() if company_name and company_name.strip() else "Unknown company"
        clean_role = role_title.strip() if role_title and role_title.strip() else "Unknown role"
        with self.driver.session() as session:
            session.run("""
                MERGE (c:Candidate {candidate_id: $candidate_id})
                MERGE (co:Company {name: $company_name})
                MERGE (r:Role {title: $role_title})
                CREATE (p:InterviewPrep {
                    prep_id: $prep_id,
                    mode: $mode,
                    prep_text: $prep_text,
                    application_id: $application_id,
                    created_at: $now
                })
                MERGE (c)-[:HAS_INTERVIEW_PREP]->(p)
                MERGE (p)-[:FOR_COMPANY]->(co)
                MERGE (p)-[:FOR_ROLE]->(r)
            """, candidate_id=candidate_id, company_name=clean_company, role_title=clean_role,
                 prep_id=prep_id, mode=mode, prep_text=prep_text, application_id=application_id, now=now)
        return prep_id

    def get_recent_applications(self, candidate_id, limit=10):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (:Candidate {candidate_id: $candidate_id})-[:SUBMITTED]->(a:Application)
                OPTIONAL MATCH (a)-[:AT]->(co:Company)
                OPTIONAL MATCH (a)-[:FOR_ROLE]->(r:Role)
                OPTIONAL MATCH (a)-[:HAS_REVIEW]->(ar:AIReview)
                RETURN a.application_id AS application_id, a.created_at AS created_at,
                       a.review_mode AS review_mode, co.name AS company_name,
                       r.title AS role_title, ar.review_text AS review_text
                ORDER BY a.created_at DESC
                LIMIT $limit
            """, candidate_id=candidate_id, limit=limit)
            return [dict(record) for record in result]
