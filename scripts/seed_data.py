import os
import sys
from datetime import date, datetime, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.core.security import get_password_hash
from app.models.identity import Role, User
from app.models.advisor import AdvisorProfile
from app.models.project import Project, ProjectProfile, ProjectMember
from app.models.regulatory import RegulatorySource, RegulatoryRequirement
from app.services.audit_service import log_audit_event

def seed_database():
    print(f"Starting seed on dialect: {engine.dialect.name}")
    
    # In SQLite fallback or testing, initialize schemas
    if engine.dialect.name == "sqlite":
        print("Initializing tables for SQLite fallback...")
        Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # 1. Seed Platform Roles
        roles_to_seed = [
            ("ADMIN", "System administrator with platform oversight"),
            ("BUILDER", "FinTech founder or builder creating and operating compliance projects"),
            ("ADVISOR", "FCC, legal, or regulatory advisor providing subject matter expertise"),
        ]
        roles_map = {}
        for role_name, desc in roles_to_seed:
            role = db.query(Role).filter(Role.role_name == role_name).first()
            if not role:
                role = Role(role_name=role_name, description=desc)
                db.add(role)
                db.flush()
                print(f"Created role: {role_name}")
            roles_map[role_name] = role

        db.commit()

        # 2. Seed Users
        password_hash = get_password_hash("Password123!")
        users_to_seed = [
            {
                "email": "jun@finregtech.io",
                "full_name": "Jun Chen",
                "role_name": "BUILDER",
                "is_active": True,
            },
            {
                "email": "eleanor.vance@vancelegal.co.uk",
                "full_name": "Eleanor Vance",
                "role_name": "ADVISOR",
                "is_active": True,
            },
            {
                "email": "marcus.reid@fccconsulting.eu",
                "full_name": "Marcus Reid",
                "role_name": "ADVISOR",
                "is_active": True,
            },
            {
                "email": "admin@finregtech.io",
                "full_name": "FinRegTech Admin",
                "role_name": "ADMIN",
                "is_active": True,
            },
            {
                "email": "builder@gmail.com",
                "full_name": "Demo Builder",
                "role_name": "BUILDER",
                "is_active": True,
            },
            {
                "email": "advisor@gmail.com",
                "full_name": "Demo Advisor",
                "role_name": "ADVISOR",
                "is_active": True,
            },
        ]

        users_map = {}
        for u_data in users_to_seed:
            user = db.query(User).filter(User.email == u_data["email"]).first()
            if not user:
                role_obj = roles_map[u_data["role_name"]]
                user = User(
                    email=u_data["email"],
                    password_hash=password_hash,
                    full_name=u_data["full_name"],
                    role_id=role_obj.role_id,
                    is_active=u_data["is_active"],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(user)
                db.flush()
                print(f"Created user: {user.email}")
            users_map[u_data["email"]] = user

        db.commit()

        # 3. Seed Advisor Profiles
        advisors_to_seed = [
            {
                "user_email": "eleanor.vance@vancelegal.co.uk",
                "organization_name": "Vance Legal LLP",
                "professional_title": "Partner & Head of Financial Regulatory Practice",
                "specialization": "UK & EU Anti-Money Laundering, Senior Managers & Certification Regime (SM&CR), FinTech Licensing",
                "bio": "Senior regulatory counsel with over 16 years advising tier-1 UK and European payments firms, challenger banks, and electronic money institutions on FCA regulatory compliance and AML governance.",
            },
            {
                "user_email": "marcus.reid@fccconsulting.eu",
                "organization_name": "FCC Consulting Europe",
                "professional_title": "Managing Director, Financial Crime Compliance",
                "specialization": "Transaction Monitoring Architectures, Sanctions Screening, MLRO Assurance & SAR Governance",
                "bio": "Former Head of Financial Crime Operations at major international financial institutions; advises scale-ups on transaction monitoring thresholds, typology models, and automated compliance risk frameworks.",
            },
            {
                "user_email": "advisor@gmail.com",
                "organization_name": "FinReg Solutions UK",
                "professional_title": "Senior FCC & Anti-Money Laundering Expert",
                "specialization": "AML/CTF, KYC/CDD, FCA Regulations",
                "bio": "Senior FCC expert advising FinTech firms on regulatory adherence and risk controls.",
            },
        ]

        for adv_data in advisors_to_seed:
            adv_user = users_map[adv_data["user_email"]]
            profile = db.query(AdvisorProfile).filter(AdvisorProfile.user_id == adv_user.user_id).first()
            if not profile:
                profile = AdvisorProfile(
                    user_id=adv_user.user_id,
                    organization_name=adv_data["organization_name"],
                    professional_title=adv_data["professional_title"],
                    specialization=adv_data["specialization"],
                    bio=adv_data["bio"],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(profile)
                db.flush()
                print(f"Created advisor profile for: {adv_data['user_email']}")

        db.commit()

        # 4. Seed Curated Regulatory Sources (18 verified UK/EU sources)
        sources_data = [
            {
                "source_title": "UK Money Laundering, Terrorist Financing and Transfer of Funds Regulations 2017 (MLR 2017)",
                "issuing_authority": "HM Treasury / UK Parliament",
                "jurisdiction": "UK",
                "source_url": "https://www.legislation.gov.uk/uksi/2017/692/contents/made",
                "version_label": "SI 2017/692 as amended",
                "publication_date": date(2017, 6, 22),
                "topic": "AML / Customer Due Diligence (CDD)",
                "relevance": "Primary UK statutory framework establishing mandatory policies, controls, risk assessments, customer identification, ongoing monitoring, and record-keeping for relevant persons.",
                "applicability_rationale": "Mandatory statutory compliance baseline for all UK credit and financial institutions, e-money firms, and payment providers.",
            },
            {
                "source_title": "Money Laundering and Terrorist Financing (Amendment) Regulations 2019",
                "issuing_authority": "HM Treasury / UK Parliament",
                "jurisdiction": "UK",
                "source_url": "https://www.legislation.gov.uk/uksi/2019/1511/contents/made",
                "version_label": "SI 2019/1511",
                "publication_date": date(2019, 12, 16),
                "topic": "AML / Virtual Asset Service Providers",
                "relevance": "Transposed 5AMLD into UK law, bringing cryptoasset exchange providers and custodian wallet providers under the scope of MLR 2017.",
                "applicability_rationale": "Applies directly to FinTech firms engaging in crypto exchange, custodian wallets, or high-value art/property intermediaries.",
            },
            {
                "source_title": "FCA Handbook: SYSC 6.1 & 6.3 Financial Crime Systems and Controls",
                "issuing_authority": "Financial Conduct Authority (FCA)",
                "jurisdiction": "UK",
                "source_url": "https://www.handbook.fca.org.uk/handbook/SYSC/6/3.html",
                "version_label": "FCA Handbook 2024 Edition",
                "publication_date": date(2024, 1, 1),
                "topic": "Systems & Controls / MLRO Oversight",
                "relevance": "Requires regulated firms to establish and maintain effective systems and controls to counter the risk that they might be used to further financial crime; defines MLRO appointment and oversight duties.",
                "applicability_rationale": "Core regulatory requirement for authorized UK FinTechs and payment institutions under FCA supervision.",
            },
            {
                "source_title": "FCA Financial Crime Guide: A Firm's Guide to Countering Financial Crime Risks (FCG)",
                "issuing_authority": "Financial Conduct Authority (FCA)",
                "jurisdiction": "UK",
                "source_url": "https://www.handbook.fca.org.uk/handbook/FCG.pdf",
                "version_label": "FCG 2023 Update",
                "publication_date": date(2023, 6, 1),
                "topic": "Financial Crime Governance & Risk Assessment",
                "relevance": "Provides practical guidance and benchmark examples of good and poor practices regarding governance, risk assessment, CDD, sanctions, and anti-bribery.",
                "applicability_rationale": "Crucial benchmark evaluated by FCA supervisory teams during authorization inspections and regulatory audits.",
            },
            {
                "source_title": "JMLSG Guidance Part I: Core AML/CTF Guidance for the UK Financial Sector",
                "issuing_authority": "Joint Money Laundering Steering Group (JMLSG)",
                "jurisdiction": "UK",
                "source_url": "https://www.jmlsg.org.uk/guidance/part-i/",
                "version_label": "2023 Ministerial Approved Text",
                "publication_date": date(2023, 7, 1),
                "topic": "Customer Due Diligence / Verification Standards",
                "relevance": "HM Treasury-approved guidance setting authoritative industry standards for customer identification, electronic verification, beneficial ownership, and suspicious reporting.",
                "applicability_rationale": "Courts and the FCA must take JMLSG compliance into account when determining whether a firm committed an MLR offense.",
            },
            {
                "source_title": "JMLSG Guidance Part II: Electronic Money and Payment Services (Sector 4)",
                "issuing_authority": "Joint Money Laundering Steering Group (JMLSG)",
                "jurisdiction": "UK",
                "source_url": "https://www.jmlsg.org.uk/guidance/part-ii/",
                "version_label": "Sector 4 Updated 2023",
                "publication_date": date(2023, 7, 1),
                "topic": "Payment Services / E-Money AML",
                "relevance": "Specific compliance expectations for merchant acquiring, payment gateways, electronic wallets, and peer-to-peer payment execution.",
                "applicability_rationale": "Directly targets FinTech payment infrastructure and wallet service architectures.",
            },
            {
                "source_title": "Proceeds of Crime Act 2002 (POCA) - Part 7: Money Laundering Offences",
                "issuing_authority": "UK Parliament",
                "jurisdiction": "UK",
                "source_url": "https://www.legislation.gov.uk/ukpga/2002/29/part/7",
                "version_label": "POCA 2002 Part 7",
                "publication_date": date(2002, 7, 24),
                "topic": "Suspicious Activity Reporting (SAR) / Tipping Off",
                "relevance": "Defines substantive money laundering offenses (ss. 327-329), failure to disclose offenses in the regulated sector (s. 330), and tipping-off offenses (s. 333A).",
                "applicability_rationale": "Criminal law foundation for mandatory suspicious activity reporting to the UK National Crime Agency (NCA).",
            },
            {
                "source_title": "Terrorism Act 2000 - Part III: Terrorist Property and Reporting",
                "issuing_authority": "UK Parliament",
                "jurisdiction": "UK",
                "source_url": "https://www.legislation.gov.uk/ukpga/2000/11/part/III",
                "version_label": "TACT 2000 Part III",
                "publication_date": date(2000, 7, 20),
                "topic": "Counter-Terrorist Financing (CTF)",
                "relevance": "Establishes criminal penalties for fund-raising, use and possession, and funding arrangements for terrorist purposes, with affirmative disclosure duties.",
                "applicability_rationale": "Core statutory requirement for CTF screening and mandatory reporting across all financial operations.",
            },
            {
                "source_title": "Sanctions and Anti-Money Laundering Act 2018 (SAMLA)",
                "issuing_authority": "UK Parliament",
                "jurisdiction": "UK",
                "source_url": "https://www.legislation.gov.uk/ukpga/2018/13/contents",
                "version_label": "SAMLA 2018",
                "publication_date": date(2018, 5, 23),
                "topic": "Financial Sanctions Framework",
                "relevance": "Enables the UK government to create post-Brexit autonomous UK financial and trade sanctions regimes.",
                "applicability_rationale": "Authorizes statutory sanctions regimes enforced by the Office of Financial Sanctions Implementation (OFSI).",
            },
            {
                "source_title": "OFSI Financial Sanctions Guidance: General Guidance for Financial Sanctions",
                "issuing_authority": "Office of Financial Sanctions Implementation (HM Treasury)",
                "jurisdiction": "UK",
                "source_url": "https://www.gov.uk/government/publications/financial-sanctions-faqs",
                "version_label": "OFSI General Guidance 2024",
                "publication_date": date(2024, 2, 1),
                "topic": "Sanctions Screening / Asset Freezing",
                "relevance": "Explains asset freezing prohibitions, licensing grounds, strict liability monetary penalties for sanctions breaches, and mandatory reporting of frozen assets.",
                "applicability_rationale": "Essential operational framework for real-time customer and payment sanctions screening engines.",
            },
            {
                "source_title": "Directive (EU) 2015/849 on the Prevention of the Use of the Financial System (4AMLD)",
                "issuing_authority": "European Parliament and Council",
                "jurisdiction": "EU",
                "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex%3A32015L0849",
                "version_label": "Directive (EU) 2015/849",
                "publication_date": date(2015, 5, 20),
                "topic": "EU AML Framework / Risk-Based Approach",
                "relevance": "Foundational European directive mandating beneficial ownership registers, comprehensive risk-based customer due diligence, and enhanced cross-border monitoring.",
                "applicability_rationale": "Key baseline for FinTechs offering cross-border services or operating legal entities in the EEA.",
            },
            {
                "source_title": "Directive (EU) 2018/843 Amending Directive 2015/849 (5AMLD)",
                "issuing_authority": "European Parliament and Council",
                "jurisdiction": "EU",
                "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32018L0843",
                "version_label": "Directive (EU) 2018/843",
                "publication_date": date(2018, 5, 30),
                "topic": "Beneficial Ownership Transparency / High-Risk Third Countries",
                "relevance": "Enhanced public access to beneficial ownership registers, reduced thresholds for prepaid cards, and standardized EDD for high-risk third countries.",
                "applicability_rationale": "Applies to EU cross-border operations and high-risk jurisdiction transaction processing.",
            },
            {
                "source_title": "Directive (EU) 2018/1673 on Combating Money Laundering by Criminal Law (6AMLD)",
                "issuing_authority": "European Parliament and Council",
                "jurisdiction": "EU",
                "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32018L1673",
                "version_label": "Directive (EU) 2018/1673",
                "publication_date": date(2018, 10, 23),
                "topic": "Criminal Liability / Corporate Responsibility",
                "relevance": "Standardized 22 predicate offenses across EU member states and introduced corporate criminal liability for failures in financial crime supervision.",
                "applicability_rationale": "Critical legal liability consideration for FinTech executives and compliance officers operating in EU member states.",
            },
            {
                "source_title": "Regulation (EU) 2023/1113 on Information Accompanying Transfers of Funds (Travel Rule)",
                "issuing_authority": "European Parliament and Council",
                "jurisdiction": "EU",
                "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32023R1113",
                "version_label": "Regulation (EU) 2023/1113 (Recast)",
                "publication_date": date(2023, 6, 9),
                "topic": "Wire Transfer Regulation / Crypto Travel Rule",
                "relevance": "Mandates that payer and payee identity information accompany fund transfers and crypto-asset transfers across intermediary PSPs and CASPs.",
                "applicability_rationale": "High-priority technical requirement for payment processors, routing gateways, and crypto asset platforms.",
            },
            {
                "source_title": "EBA Guidelines on Customer Due Diligence and AML/CFT Risk Factors (EBA/GL/2021/02)",
                "issuing_authority": "European Banking Authority (EBA)",
                "jurisdiction": "EU",
                "source_url": "https://www.eba.europa.eu/regulation-and-policy/anti-money-laundering-and-countering-the-financing-of-terrorism/guidelines-on-customer-due-diligence-and-the-risk-factors-to-be-considered",
                "version_label": "EBA/GL/2021/02",
                "publication_date": date(2021, 3, 1),
                "topic": "Risk Scoring / Business & Customer Risk Factors",
                "relevance": "Provides sector-specific risk factors for retail banking, e-money, merchant acquiring, trade finance, and crowd-funding.",
                "applicability_rationale": "Primary European supervisory benchmark for algorithmic customer risk rating models.",
            },
            {
                "source_title": "EBA Guidelines on the Role of AML/CFT Compliance Officers (EBA/GL/2022/15)",
                "issuing_authority": "European Banking Authority (EBA)",
                "jurisdiction": "EU",
                "source_url": "https://www.eba.europa.eu/regulation-and-policy/anti-money-laundering-and-countering-the-financing-of-terrorism/guidelines-on-the-role-of-aml-cft-compliance-officers",
                "version_label": "EBA/GL/2022/15",
                "publication_date": date(2022, 6, 14),
                "topic": "Compliance Governance & Second Line Oversight",
                "relevance": "Clarifies the roles, competencies, independence, and reporting lines of AML/CFT compliance officers and management body members.",
                "applicability_rationale": "Required governance standard for European FinTech authorization and operational licensing.",
            },
            {
                "source_title": "FATF 40 Recommendations: International Standards on Combating ML and TF",
                "issuing_authority": "Financial Action Task Force (FATF)",
                "jurisdiction": "International",
                "source_url": "https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Fatf-recommendations.html",
                "version_label": "FATF Recommendations (Updated Nov 2023)",
                "publication_date": date(2023, 11, 1),
                "topic": "Global Standards / PEPs / Targeted Financial Sanctions",
                "relevance": "The recognized international standard for countering money laundering, terrorist financing, and proliferation of weapons of mass destruction.",
                "applicability_rationale": "Foundational global baseline adopted across 200+ jurisdictions worldwide.",
            },
            {
                "source_title": "FATF Guidance on the Risk-Based Approach for the Banking and Payment Sector",
                "issuing_authority": "Financial Action Task Force (FATF)",
                "jurisdiction": "International",
                "source_url": "https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Rba-banking-sector.html",
                "version_label": "FATF RBA Guidelines",
                "publication_date": date(2021, 10, 21),
                "topic": "Risk-Based Allocation of Compliance Resources",
                "relevance": "Detailed guidance on conducting enterprise-wide risk assessments and allocating compliance resources proportionally to risk exposure.",
                "applicability_rationale": "Informs proportionate, risk-based compliance software engineering and automated alerting architectures.",
            },
        ]

        sources_map = {}
        for s_data in sources_data:
            source = db.query(RegulatorySource).filter(RegulatorySource.source_title == s_data["source_title"]).first()
            if not source:
                source = RegulatorySource(
                    source_title=s_data["source_title"],
                    issuing_authority=s_data["issuing_authority"],
                    jurisdiction=s_data["jurisdiction"],
                    source_url=s_data["source_url"],
                    version_label=s_data["version_label"],
                    publication_date=s_data["publication_date"],
                    retrieved_at=datetime.now(timezone.utc),
                    validation_status="VALIDATED",
                    topic=s_data["topic"],
                    relevance=s_data["relevance"],
                    applicability_rationale=s_data["applicability_rationale"],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(source)
                db.flush()
                print(f"Created regulatory source: {source.source_title[:60]}...")
            sources_map[s_data["source_title"]] = source

        db.commit()

        # 5. Seed Demo Project: ABC Shield
        jun_user = users_map["jun@finregtech.io"]
        project = db.query(Project).filter(Project.project_code == "PRJ-ABC-001").first()
        if not project:
            project = Project(
                project_name="ABC Shield Compliance Infrastructure",
                project_code="PRJ-ABC-001",
                status="ACTIVE",
                created_by=jun_user.user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(project)
            db.flush()

            # Profile
            profile = ProjectProfile(
                project_id=project.project_id,
                description="ABC Shield Compliance Infrastructure for UK Payment Institutions and E-Money Issuers.",
                jurisdiction="UK",
                regulatory_scope="UK Money Laundering Regulations 2017 (MLR 2017), FCA Senior Management Arrangements, Systems and Controls (SYSC), Proceeds of Crime Act 2002 (POCA)",
                objectives="Deliver an integrated AML transaction monitoring, KYC identity verification, and regulatory reporting cockpit.",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(profile)

            # Owner Membership
            member = ProjectMember(
                project_id=project.project_id,
                user_id=jun_user.user_id,
                service_role="OWNER",
                service_scope="PROJECT_CONTROL",
                member_status="ACTIVE",
                joined_at=datetime.now(timezone.utc),
            )
            db.add(member)
            db.flush()

            # Log audit event
            log_audit_event(
                db=db,
                project_id=project.project_id,
                actor_user_id=jun_user.user_id,
                event_type="PROJECT_CREATED",
                entity_type="PROJECT",
                entity_id=project.project_id,
                event_description=f"Project '{project.project_name}' created with code '{project.project_code}'",
                new_values={
                    "project_name": project.project_name,
                    "project_code": project.project_code,
                    "status": project.status,
                    "created_by": jun_user.user_id,
                },
            )
            print("Created demo project: ABC Shield")

        db.commit()

        # 6. Seed Mapped Project Requirements (8 requirements linked to sources)
        requirements_data = [
            {
                "requirement_code": "REQ-ABC-001",
                "source_title_key": "UK Money Laundering, Terrorist Financing and Transfer of Funds Regulations 2017 (MLR 2017)",
                "title": "Customer Due Diligence (CDD) Verification Before Account Activation",
                "text": "The platform must verify the customer's identity before establishing a business relationship or executing an occasional transaction in accordance with MLR 2017 Regulation 27 and 28.",
                "applicability_status": "APPLICABLE",
                "requirement_status": "COMPLETED",
            },
            {
                "requirement_code": "REQ-ABC-002",
                "source_title_key": "UK Money Laundering, Terrorist Financing and Transfer of Funds Regulations 2017 (MLR 2017)",
                "title": "Enhanced Due Diligence (EDD) for Politically Exposed Persons (PEPs) & High-Risk Clients",
                "text": "Mandatory EDD workflows including senior management approval, source of wealth investigation, and enhanced transaction frequency monitoring per Regulation 33.",
                "applicability_status": "APPLICABLE",
                "requirement_status": "IN_REVIEW",
            },
            {
                "requirement_code": "REQ-ABC-003",
                "source_title_key": "FCA Handbook: SYSC 6.1 & 6.3 Financial Crime Systems and Controls",
                "title": "Real-Time Transaction Monitoring and Velocity Rule Anomaly Detection",
                "text": "Automated behavioral monitoring must inspect transaction values, frequencies, geographic velocity, and rapid movement of funds in compliance with SYSC 6.3.7R.",
                "applicability_status": "APPLICABLE",
                "requirement_status": "OPEN",
            },
            {
                "requirement_code": "REQ-ABC-004",
                "source_title_key": "Proceeds of Crime Act 2002 (POCA) - Part 7: Money Laundering Offences",
                "title": "Suspicious Activity Report (SAR) Escalation and Secure NCA Submission",
                "text": "Internal reporting mechanism allowing any team member to file an internal SAR to the nominated MLRO without tipping off the customer (POCA ss. 330 & 333A).",
                "applicability_status": "APPLICABLE",
                "requirement_status": "IN_REVIEW",
            },
            {
                "requirement_code": "REQ-ABC-005",
                "source_title_key": "OFSI Financial Sanctions Guidance: General Guidance for Financial Sanctions",
                "title": "Automated Daily & Pre-Execution Financial Sanctions Screening",
                "text": "System must screen customer entities, ultimate beneficial owners, and payment counterparties against OFSI Consolidated List before funds release.",
                "applicability_status": "APPLICABLE",
                "requirement_status": "COMPLETED",
            },
            {
                "requirement_code": "REQ-ABC-006",
                "source_title_key": "Regulation (EU) 2023/1113 on Information Accompanying Transfers of Funds (Travel Rule)",
                "title": "Payment Originator and Beneficiary Information Transmission (Travel Rule)",
                "text": "Verify and transmit verified originator and beneficiary details for outbound payment messages exceeding statutory thresholds.",
                "applicability_status": "APPLICABLE",
                "requirement_status": "OPEN",
            },
            {
                "requirement_code": "REQ-ABC-007",
                "source_title_key": "JMLSG Guidance Part I: Core AML/CTF Guidance for the UK Financial Sector",
                "title": "Beneficial Ownership Register (>25% Equity/Voting Rights Verification)",
                "text": "Identification and verification of all natural persons who ultimately own or control more than 25% of corporate account applicants.",
                "applicability_status": "APPLICABLE",
                "requirement_status": "COMPLETED",
            },
            {
                "requirement_code": "REQ-ABC-008",
                "source_title_key": "EBA Guidelines on Customer Due Diligence and AML/CFT Risk Factors (EBA/GL/2021/02)",
                "title": "Enterprise-Wide Compliance Risk Assessment and Dynamic Scoring",
                "text": "Continuous institutional risk assessment evaluating customer risk, country risk, product risk, and channel risk vectors.",
                "applicability_status": "APPLICABLE",
                "requirement_status": "OPEN",
            },
        ]

        for req_data in requirements_data:
            existing_req = db.query(RegulatoryRequirement).filter(
                RegulatoryRequirement.project_id == project.project_id,
                RegulatoryRequirement.requirement_code == req_data["requirement_code"]
            ).first()
            if not existing_req:
                src = sources_map[req_data["source_title_key"]]
                req = RegulatoryRequirement(
                    project_id=project.project_id,
                    source_id=src.source_id,
                    requirement_code=req_data["requirement_code"],
                    requirement_title=req_data["title"],
                    requirement_text=req_data["text"],
                    applicability_status=req_data["applicability_status"],
                    requirement_status=req_data["requirement_status"],
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                db.add(req)
                db.flush()
                print(f"Created requirement: {req.requirement_code}")

        db.commit()
        print("Database seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
