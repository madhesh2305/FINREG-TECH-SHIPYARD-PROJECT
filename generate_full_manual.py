import os
import sys
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Image
)
from reportlab.pdfgen import canvas

ART_DIR = r"C:\Users\harsh\.gemini\antigravity\brain\694eb6af-9770-46bb-957e-e561eecaff80\.user_uploaded"
OUTPUT_DIR = r"C:\Users\harsh\Downloads"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "FinRegTech_ShipYard_Complete_TriRole_User_Manual.pdf")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(36, 11 * inch - 28, "FinRegTech ShipYard — Tri-Role Platform Manual & Interactive Feature Guide")
            self.drawRightString(8.5 * inch - 36, 11 * inch - 28, "Harshini · Frontend Lead")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.6)
            self.line(36, 11 * inch - 32, 8.5 * inch - 36, 11 * inch - 32)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.6)
        self.line(36, 32, 8.5 * inch - 36, 32)
        self.setFont("Helvetica", 7.5)
        self.drawString(36, 22, "CONFIDENTIAL & PROPRIETARY · FINREGTECH SHIPYARD SYSTEM DOCUMENTATION · ALL RIGHTS RESERVED")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 36, 22, page_str)
        self.restoreState()

def get_scaled_image(img_filename, max_width=500, max_height=190):
    img_path = os.path.join(ART_DIR, img_filename)
    if not os.path.exists(img_path):
        print(f"Warning: Image not found: {img_path}")
        return None
    try:
        with PILImage.open(img_path) as im:
            orig_w, orig_h = im.size
        
        scale_w = max_width / float(orig_w)
        scale_h = max_height / float(orig_h)
        scale = min(scale_w, scale_h, 1.0)
        
        target_w = orig_w * scale
        target_h = orig_h * scale
        
        return Image(img_path, width=target_w, height=target_h)
    except Exception as e:
        print(f"Error loading image {img_filename}: {e}")
        return None

def build_pdf():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Color Palette
    c_primary = colors.HexColor("#0f172a")     # Slate 900
    c_secondary = colors.HexColor("#1e293b")   # Slate 800
    c_accent = colors.HexColor("#b45309")      # Amber 700
    c_builder = colors.HexColor("#1d4ed8")     # Blue 700
    c_advisor = colors.HexColor("#047857")     # Emerald 700
    c_admin = colors.HexColor("#6d28d9")       # Purple 700
    c_text = colors.HexColor("#334155")        # Slate 700
    c_border = colors.HexColor("#cbd5e1")      # Slate 300
    c_bg_light = colors.HexColor("#f8fafc")    # Slate 50
    c_row_alt = colors.HexColor("#f1f5f9")     # Slate 100

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=19,
        leading=23,
        textColor=c_primary,
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=c_accent,
        spaceAfter=7
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.2,
        leading=10,
        textColor=c_text
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=15.5,
        textColor=c_primary,
        spaceBefore=12,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=c_secondary,
        spaceBefore=9,
        spaceAfter=3,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'Heading3_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=c_accent,
        spaceBefore=5,
        spaceAfter=2.5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.8,
        leading=11,
        textColor=c_text,
        spaceAfter=4
    )

    caption_style = ParagraphStyle(
        'Caption_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#64748b"),
        alignment=1, # Centered
        spaceBefore=2,
        spaceAfter=5
    )

    def create_btn_table(rows, col_widths=[95, 90, 85, 160, 100]):
        hdr_p = ParagraphStyle('TBHdr', fontName='Helvetica-Bold', fontSize=7.2, leading=9.2, textColor=colors.white)
        cell_p = ParagraphStyle('TBCell', fontName='Helvetica', fontSize=6.8, leading=8.8, textColor=colors.HexColor("#1e293b"))
        btn_p = ParagraphStyle('TBBtn', fontName='Helvetica-Bold', fontSize=6.8, leading=8.8, textColor=colors.HexColor("#0f172a"))
        loc_p = ParagraphStyle('TBLoc', fontName='Helvetica-Bold', fontSize=6.5, leading=8.5, textColor=c_accent)

        table_data = [[
            Paragraph("Interactive Control / Button", hdr_p),
            Paragraph("Screen Location", hdr_p),
            Paragraph("Trigger / Event", hdr_p),
            Paragraph("Action & Workflow", hdr_p),
            Paragraph("State / System Outcome", hdr_p)
        ]]

        for r in rows:
            table_data.append([
                Paragraph(f"<b>{r[0]}</b>", btn_p),
                Paragraph(r[1], loc_p),
                Paragraph(r[2], cell_p),
                Paragraph(r[3], cell_p),
                Paragraph(r[4], cell_p)
            ])

        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), c_primary),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, c_border),
            ('TOPPADDING', (0, 0), (-1, -1), 2.2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.2),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light])
        ]))
        return t

    story = []

    # =========================================================================
    # COVER / HEADER TITLE
    # =========================================================================
    story.append(Paragraph("FINREGTECH SHIPYARD — ENTERPRISE USER MANUAL", title_style))
    story.append(Paragraph("Complete Tri-Role Functional Specification & Comprehensive Screen-by-Screen Button Reference Guide", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=2, spaceAfter=5))

    # Meta summary block
    meta_info = [
        [
            Paragraph("<b>Author / Role:</b> Harshini · Frontend Lead", meta_style),
            Paragraph("<b>Target Platform:</b> FinRegTech ShipYard FCC Cockpit", meta_style),
            Paragraph("<b>Security Standard:</b> NIST 800-53 / SOC2 / ISO 27001", meta_style)
        ],
        [
            Paragraph("<b>Version:</b> 2.4.0-Production (Remediated)", meta_style),
            Paragraph("<b>Frontend Branch:</b> feature/harshini-frontend (Clean/Pushed)", meta_style),
            Paragraph("<b>Audit Status:</b> Tamper-Evident SHA-256 Chained", meta_style)
        ]
    ]
    meta_table = Table(meta_info, colWidths=[180, 180, 170])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_light),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    # Executive Overview
    story.append(Paragraph("Executive Overview & Platform Mission", h1_style))
    story.append(Paragraph(
        "FinRegTech ShipYard is an institutional-grade regulatory compliance operating system designed to orchestrate the lifecycle of FinTech products from inception through supervisory audit certification. "
        "The platform establishes a strict, cryptographically anchored <b>Tri-Role Separation of Duties (SoD)</b> model encompassing three distinct operational personas: "
        "<b>1. Builder</b> (FinTech founders and engineering compliance leads managing projects, technical architecture, and evidence), "
        "<b>2. Advisor</b> (domain specialists, regulatory attorneys, and certified auditors rendering formal compliance opinions), and "
        "<b>3. Administrator</b> (platform operators maintaining user lifecycles, cross-tenant project oversight, regulatory knowledge repositories, and immutable audit logs). "
        "This document provides the definitive operational manual, explaining every dashboard, sub-tab, workflow, and interactive control across the entire frontend ecosystem.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Defect Remediation Summary Table
    story.append(Paragraph("Frontend Quality Assurance & Defect Remediation Register (DEF-01 to DEF-13)", h2_style))
    story.append(Paragraph(
        "All thirteen identified production defects (DEF-01 through DEF-13) have been rigorously remediated and verified within the frontend codebase. "
        "The table below certifies the implementation status and affected screen components:",
        body_style
    ))

    defect_data = [
        [Paragraph("<b>Defect ID</b>", meta_style), Paragraph("<b>Severity</b>", meta_style), Paragraph("<b>Target Module / Screen</b>", meta_style), Paragraph("<b>Functional Remediation Summary</b>", meta_style), Paragraph("<b>Status</b>", meta_style)],
        [Paragraph("<b>DEF-01</b>", meta_style), Paragraph("HIGH", meta_style), Paragraph("Auth / Login Form", meta_style), Paragraph("Unified error banner, sanitization, strict form validation", meta_style), Paragraph("<font color='#047857'><b>RESOLVED</b></font>", meta_style)],
        [Paragraph("<b>DEF-02</b>", meta_style), Paragraph("MEDIUM", meta_style), Paragraph("Builder / Dashboard", meta_style), Paragraph("Persistent tab synchronization, URL query parameter state", meta_style), Paragraph("<font color='#047857'><b>RESOLVED</b></font>", meta_style)],
        [Paragraph("<b>DEF-03</b>", meta_style), Paragraph("CRITICAL", meta_style), Paragraph("Create Project Wizard", meta_style), Paragraph("Dynamic owner attribution; removed hardcoded demo strings", meta_style), Paragraph("<font color='#047857'><b>RESOLVED</b></font>", meta_style)],
        [Paragraph("<b>DEF-04</b>", meta_style), Paragraph("MEDIUM", meta_style), Paragraph("Advisors Directory", meta_style), Paragraph("Dynamic domain filtering & real-time advisor directory bindings", meta_style), Paragraph("<font color='#047857'><b>RESOLVED</b></font>", meta_style)],
        [Paragraph("<b>DEF-05</b>", meta_style), Paragraph("LOW", meta_style), Paragraph("Backend DB / Seed", meta_style), Paragraph("Architectural note: Backend DB schema migration handled by Vishal", meta_style), Paragraph("<font color='#b45309'><b>BACKEND</b></font>", meta_style)],
        [Paragraph("<b>DEF-06</b>", meta_style), Paragraph("HIGH", meta_style), Paragraph("Advisor Advice View", meta_style), Paragraph("Advice review decision modal with accept/reject state triggers", meta_style), Paragraph("<font color='#047857'><b>RESOLVED</b></font>", meta_style)],
        [Paragraph("<b>DEF-07</b>", meta_style), Paragraph("MEDIUM", meta_style), Paragraph("Advice Decisions View", meta_style), Paragraph("Governance registry logging with formal rationale audit trails", meta_style), Paragraph("<font color='#047857'><b>RESOLVED</b></font>", meta_style)],
        [Paragraph("<b>DEF-08</b>", meta_style), Paragraph("HIGH", meta_style), Paragraph("Audit Readiness", meta_style), Paragraph("Dynamic readiness score calculation & evidence checklist linkage", meta_style), Paragraph("<font color='#047857'><b>RESOLVED</b></font>", meta_style)],
        [Paragraph("<b>DEF-09</b>", meta_style), Paragraph("HIGH", meta_style), Paragraph("Audit Trail View", meta_style), Paragraph("Real-time event stream filter, SHA-256 hash integrity checks", meta_style), Paragraph("<font color='#047857'><b>RESOLVED</b></font>", meta_style)],
        [Paragraph("<b>DEF-10</b>", meta_style), Paragraph("MEDIUM", meta_style), Paragraph("Advisor Dashboard", meta_style), Paragraph("Zero-leakage project isolation; scoped mandates & empty states", meta_style), Paragraph("<font color='#047857'><b>RESOLVED</b></font>", meta_style)],
        [Paragraph("<b>DEF-11</b>", meta_style), Paragraph("HIGH", meta_style), Paragraph("Advisor Advice Form", meta_style), Paragraph("Robust validation for recommendations, citations & severity tags", meta_style), Paragraph("<font color='#047857'><b>RESOLVED</b></font>", meta_style)],
        [Paragraph("<b>DEF-12</b>", meta_style), Paragraph("CRITICAL", meta_style), Paragraph("Admin User Console", meta_style), Paragraph("Active/Inactive toggle with modal confirmation safeguard", meta_style), Paragraph("<font color='#047857'><b>RESOLVED</b></font>", meta_style)],
        [Paragraph("<b>DEF-13</b>", meta_style), Paragraph("HIGH", meta_style), Paragraph("Admin Regulatory KB", meta_style), Paragraph("Add Regulatory Source modal with validation state workflows", meta_style), Paragraph("<font color='#047857'><b>RESOLVED</b></font>", meta_style)]
    ]
    defect_table = Table(defect_data, colWidths=[55, 50, 115, 245, 65])
    defect_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_secondary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3.5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light])
    ]))
    story.append(defect_table)
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 1: AUTHENTICATION & ACCESS CONTROL GATEWAY
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("1. Authentication, Gateways & Identity Governance", h1_style))
    story.append(Paragraph(
        "FinRegTech ShipYard enforces strict multi-tenant role-based access control (RBAC). Upon accessing the platform, users are routed through the secure gateway where they identify their operational persona. "
        "The gateway separates standard commercial users (Builders and Advisors) from Administrative personnel who are protected by dedicated master-key credentials and mandatory Multi-Factor Authentication (2FA).",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Screenshots: Login & Admin Login
    img_login = get_scaled_image("media_1791713110077_089f810b.png", max_width=255, max_height=175)
    img_admin_login = get_scaled_image("media_1791714229768_980157a3.png", max_width=255, max_height=175)
    
    if img_login and img_admin_login:
        t_auth_imgs = Table([[img_login, img_admin_login]], colWidths=[265, 265])
        t_auth_imgs.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(t_auth_imgs)
        story.append(Paragraph("Figure 1.1: Standard Commercial Sign-In Gateway (Left) vs. Administrator Master Access Portal (Right)", caption_style))
        story.append(Spacer(1, 4))

    story.append(Paragraph("Authentication Screens & Registration Workflow", h2_style))
    story.append(Paragraph(
        "<b>1. Commercial Sign-In Portal:</b> Accommodates Builders and Advisors. Supports email/password input, role-mode switching, credential remember toggles, and password visibility toggles. "
        "Upon submission, client-side validation sanitizes inputs and delivers informative toast notifications (DEF-01).<br/>"
        "<b>2. System Administrator Master Portal:</b> Isolated administrative endpoint requiring high-entropy master credentials, audit-logged session establishment, and automated rate-limiting safeguards.<br/>"
        "<b>3. Account Registration & Organization Provisioning:</b> Self-service tenant creation modal for new Builders, capturing organization name, legal jurisdiction, and corporate email.<br/>"
        "<b>4. Multi-Factor Authentication (2FA):</b> Mandatory time-based one-time password (TOTP) verification step enforcing enterprise cryptographic validation before session token issuance.",
        body_style
    ))

    img_reg = get_scaled_image("media_1791309101386.png", max_width=300, max_height=150)
    if img_reg:
        story.append(Spacer(1, 2))
        story.append(img_reg)
        story.append(Paragraph("Figure 1.2: Builder Self-Service Registration & Tenant Provisioning Modal", caption_style))
        story.append(Spacer(1, 4))

    # Button Table: Auth
    story.append(Paragraph("Authentication & Gateway Interactive Control Reference", h3_style))
    auth_btn_data = [
        ("Sign In Button", "Sign-In Modal", "onClick / Form Submit", "Validates email format & password entropy; posts to /api/auth/login", "Authenticates user; redirects to role dashboard"),
        ("Role Toggle Tabs", "Sign-In Modal", "onClick (Tab select)", "Switches login context between 'Builder' and 'Advisor'", "Adjusts placeholder tips and redirects destination"),
        ("System Administrator Tab", "Sign-In Modal", "onClick", "Switches gateway to high-security Administrative master gateway", "Activates admin credential fields & security logging"),
        ("Verify Admin Credentials", "Admin Sign-In", "onClick / Form Submit", "Transmits master administrative credentials with device fingerprint", "Enforces 2FA challenge and routes to Admin Cockpit"),
        ("Create Account Link", "Sign-In Modal", "onClick", "Opens the tenant registration modal for new founders", "Renders Organization Provisioning Modal"),
        ("Register Organization", "Register Modal", "onClick / Form Submit", "Submits company name, jurisdiction, and primary admin email", "Creates tenant record; triggers email verification"),
        ("Verify 2FA OTP Code", "2FA Screen", "onClick / Enter key", "Transmits 6-digit TOTP token to authentication server", "Validates cryptographic token; establishes JWT session"),
        ("Resend Security Code", "2FA Screen", "onClick", "Requests generation and transmission of fresh SMS/Email OTP token", "Resets countdown timer; triggers rate-limited dispatch")
    ]
    story.append(create_btn_table(auth_btn_data))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 2: ROLE 1 — THE BUILDER COCKPIT
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("2. Role Specification: The Builder (FinTech Founder & Compliance Lead)", h1_style))
    story.append(Paragraph(
        "The <b>Builder Role</b> represents FinTech founders, compliance officers, and product managers tasked with architecting financial solutions that satisfy complex regulatory mandates. "
        "The Builder workspace is organized into twelve modular cockpits spanning project lifecycle tracking, advisor engagement, audit readiness quantification, and automated cryptographic logging.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Screen 2.1: Builder Main Dashboard
    story.append(Paragraph("2.1 Main Command Dashboard & KPI Metrics", h2_style))
    story.append(Paragraph(
        "The Builder Dashboard serves as the central mission control. It delivers high-altitude visibility into regulatory posture via four real-time metric cards: "
        "<b>Active Projects</b>, <b>Audit Readiness Score</b> (aggregate percentage), <b>Pending Advisor Reviews</b>, and <b>Critical Compliance Tasks</b>. "
        "Beneath the metric cards sits the Active Projects data grid, equipped with tab-based status filtering ('All Projects', 'In Progress', 'Audit Ready', 'Draft'), full-text search, "
        "and quick action launchers ('Ask AI Copilot', 'Invite Advisor', 'Run Readiness Audit', 'Download Audit Package').",
        body_style
    ))

    img_b_dash = get_scaled_image("media_1791362867917.png", max_width=510, max_height=180)
    if img_b_dash:
        story.append(img_b_dash)
        story.append(Paragraph("Figure 2.1: Builder Main Command Dashboard showing Metric Cards, Project Grid, and Quick Actions", caption_style))
        story.append(Spacer(1, 4))

    dash_btn_data = [
        ("Create Project Button", "Dashboard Header", "onClick", "Triggers the 3-step Create Compliance Project Wizard modal", "Opens project creation modal with clean form state"),
        ("Status Filter Tabs", "Project Grid Header", "onClick (Tab select)", "Filters active project rows by lifecycle stage (All, In Progress, Audit Ready)", "Dynamically filters table rows without reloading"),
        ("Search Projects Input", "Project Grid Header", "onChange (Debounced)", "Executes real-time fuzzy string matching against project title and tags", "Filters grid rows to matching project instances"),
        ("View Project Details", "Project Row Action", "onClick (Row / Button)", "Navigates into project-specific compliance workspace", "Sets active project context and renders details view"),
        ("Ask AI Copilot Button", "Quick Actions Bar", "onClick", "Launches the AI Regulatory RAG Copilot drawer", "Opens RAG inquiry prompt with loaded regulations"),
        ("Invite Advisor Button", "Quick Actions Bar", "onClick", "Directly launches the Advisor Directory and Request Gateway", "Navigates to Advisors/Experts view with active filters"),
        ("Run Readiness Audit", "Quick Actions Bar", "onClick", "Initiates automated algorithmic evaluation of project compliance rules", "Recalculates readiness percentage across categories"),
        ("Download Audit Package", "Quick Actions Bar", "onClick", "Compiles all approved evidence, advice, and decisions into a PDF bundle", "Generates and streams verified audit report to browser"),
        ("Notification Bell Icon", "Global Navbar", "onClick", "Opens flyout drawer displaying system alerts, advice notices, and updates", "Toggles notification dropdown menu"),
        ("Mark All as Read", "Notification Drawer", "onClick", "Acknowledges all pending alerts and updates unread badge counter to zero", "Updates alert state in database and resets UI badge"),
        ("User Avatar Menu", "Global Navbar", "onClick", "Expands user profile menu displaying role badge, email, and session controls", "Toggles profile dropdown"),
        ("Log Out Button", "User Avatar Menu", "onClick", "Terminates active JWT session, clears local storage, and revokes tokens", "Redirects user to Public Sign-In gateway")
    ]
    story.append(create_btn_table(dash_btn_data))
    story.append(Spacer(1, 8))

    # Screen 2.2: Create Project Wizard
    story.append(Paragraph("2.2 Create Project 3-Step Guided Provisioning Wizard", h2_style))
    story.append(Paragraph(
        "The Create Project Wizard standardizes the initialization of regulated FinTech initiatives. "
        "<b>Step 1 (Project Metadata):</b> Captures Project Name, Target Launch Date, and Architectural Overview. "
        "<b>Step 2 (Regulatory Scope):</b> Configures target jurisdictions (SEC, FCA, BaFin, MAS) and applicable compliance frameworks (AML/CFT, GDPR, MiFID II, DORA). "
        "<b>Step 3 (Attribution & Confirmation):</b> Dynamically attributes project ownership to the authenticated Builder (remediating DEF-03), verifies framework selections, and persists the project record.",
        body_style
    ))

    img_b_wizard = get_scaled_image("media_1791737402091_0e2c6bea.png", max_width=470, max_height=180)
    if img_b_wizard:
        story.append(img_b_wizard)
        story.append(Paragraph("Figure 2.2: Create Project 3-Step Guided Wizard showing Dynamic Owner Attribution (DEF-03)", caption_style))
        story.append(Spacer(1, 4))

    wizard_btn_data = [
        ("Next Step Button", "Wizard Footer", "onClick", "Validates current step form inputs; transitions wizard carousel forward", "Advances progress bar to Step 2 or Step 3"),
        ("Previous Step Button", "Wizard Footer", "onClick", "Returns wizard view to preceding step while preserving entered form data", "Rewinds carousel without data loss"),
        ("Cancel / Close Modal", "Wizard Header", "onClick", "Prompts for confirmation if dirty; closes modal and discards input", "Restores dashboard focus; resets wizard state"),
        ("Jurisdiction Checkboxes", "Wizard Step 2", "onClick (Toggle)", "Selects active regulatory zones (US SEC, UK FCA, EU BaFin, SG MAS)", "Adds/removes jurisdiction tags in project schema"),
        ("Framework Selectors", "Wizard Step 2", "onClick (Toggle)", "Binds regulatory rulebooks (AMLD6, GDPR, Basel III) to project", "Populates compliance checklist based on frameworks"),
        ("Create Project Submit", "Wizard Step 3", "onClick / Form Submit", "Executes POST /api/projects with dynamic owner attribution (DEF-03)", "Persists project; triggers audit log; opens workspace")
    ]
    story.append(create_btn_table(wizard_btn_data))
    story.append(Spacer(1, 8))

    # Screen 2.3: Advisors & Experts Directory
    story.append(PageBreak())
    story.append(Paragraph("2.3 Advisors & Domain Experts Directory", h2_style))
    story.append(Paragraph(
        "Builders require expert third-party validation to achieve regulatory readiness. The Advisors & Experts Directory provides a curated marketplace of certified specialists across five domains: "
        "<b>Regulatory Compliance Expert</b>, <b>Legal Partner</b>, <b>Tech Expert</b>, <b>Funding / Business Support</b>, and <b>Marketing Service</b>. "
        "Builders can filter by domain, inspect credentials and completed review statistics, and initiate direct advice engagements bound to active projects.",
        body_style
    ))

    img_b_advisors = get_scaled_image("media_1790742446620.png", max_width=510, max_height=175)
    if img_b_advisors:
        story.append(img_b_advisors)
        story.append(Paragraph("Figure 2.3: Advisors & Domain Experts Directory with Specialization Filters and Engagement Triggers", caption_style))
        story.append(Spacer(1, 4))

    adv_btn_data = [
        ("Domain Filter Dropdown", "Directory Toolbar", "onChange", "Filters advisor roster by specialty (e.g., AML Expert, Legal Partner)", "Updates advisor card deck in real time (DEF-04)"),
        ("Search Advisor Input", "Directory Toolbar", "onChange (Debounced)", "Matches advisor name, credentials, or bio keywords", "Limits grid to matching expert profiles"),
        ("Request Advice Button", "Advisor Card Action", "onClick", "Launches the Project Engagement & Advice Request modal", "Opens request modal pre-populated with advisor ID"),
        ("Select Project Dropdown", "Request Modal", "onChange", "Binds the advice request to a specific active project in Builder portfolio", "Links advice scope to target project requirements"),
        ("Urgency Level Selector", "Request Modal", "onChange", "Assigns SLA priority (Standard: 5 days, Expedited: 48h, Critical: 24h)", "Sets deadline timestamp and notification priority"),
        ("Scope / Note Textarea", "Request Modal", "onChange (Input)", "Captures specific regulatory questions, architectural diagrams, or links", "Buffers message payload in request payload"),
        ("Submit Advice Request", "Request Modal", "onClick / Form Submit", "Submits request to Advisor queue; emits notification event", "Creates pending review record; locks advisory quota"),
        ("View Full Profile", "Advisor Card Action", "onClick", "Expands advisor modal showing published papers, bar numbers, and reviews", "Renders verified credentials drawer")
    ]
    story.append(create_btn_table(adv_btn_data))
    story.append(Spacer(1, 8))

    # Screen 2.4: Advisor Advice Intake & Review Decisions
    story.append(Paragraph("2.4 Advisor Advice Intake & Review Decisions Console", h2_style))
    story.append(Paragraph(
        "Once an advisor evaluates a project requirement, their formal opinion appears in the Advisor Advice console. "
        "The interface highlights recommendation types: <b>Approved</b> (green), <b>Changes Requested</b> (amber), or <b>Non-Compliant</b> (red). "
        "The Builder can review the advisor's statutory justification, inspect cited regulations, and formally execute a Review Decision (remediating DEF-06).",
        body_style
    ))

    img_b_advice = get_scaled_image("media_1791737929366_a3b12230.png", max_width=510, max_height=175)
    if img_b_advice:
        story.append(img_b_advice)
        story.append(Paragraph("Figure 2.4: Advisor Advice Intake Console showing Review Decision Action Triggers (DEF-06)", caption_style))
        story.append(Spacer(1, 4))

    advice_btn_data = [
        ("Accept Advice Button", "Advice Card Action", "onClick", "Accepts recommendations; marks target requirement as advisor-verified", "Updates requirement status to 'Compliant' (DEF-06)"),
        ("Reject Advice Button", "Advice Card Action", "onClick", "Opens rejection dialog requiring Builder to state architectural rebuttal", "Marks advice as 'Rejected'; creates rebuttal log"),
        ("Request Clarification", "Advice Card Action", "onClick", "Re-opens thread with advisor for follow-up questions or amended evidence", "Transitions advice state to 'Under Discussion'"),
        ("Filter by Status Dropdown", "Advice Toolbar", "onChange", "Filters advice stream by state (Pending Review, Accepted, Superseded)", "Refreshes advice card deck"),
        ("View Full Justification", "Advice Card Action", "onClick", "Expands full text modal containing statutory citations and code references", "Opens modal drawer with markdown rendered advice")
    ]
    story.append(create_btn_table(advice_btn_data))
    story.append(Spacer(1, 8))

    # Screen 2.5: Advice & Governance Decisions Registry
    story.append(PageBreak())
    story.append(Paragraph("2.5 Advice & Governance Decisions Registry", h2_style))
    story.append(Paragraph(
        "Regulators require FinTech institutions to maintain an immutable log of architectural and compliance decisions. "
        "The Advice & Decisions Registry captures formal executive determinations resulting from advisory reviews. "
        "Builders use this screen to record formal compliance decisions, log statutory rationale, and generate audit-certified decision transcripts (DEF-07).",
        body_style
    ))

    img_b_decisions = get_scaled_image("media_1791738876275_cf9f871c.png", max_width=510, max_height=175)
    if img_b_decisions:
        story.append(img_b_decisions)
        story.append(Paragraph("Figure 2.5: Governance Decisions Registry with Formal Rationale Logging & Export (DEF-07)", caption_style))
        story.append(Spacer(1, 4))

    dec_btn_data = [
        ("Record Decision Button", "Decisions Header", "onClick", "Opens the formal governance decision entry modal", "Displays Record Decision dialog with audit prompts"),
        ("Project Selector Dropdown", "Record Modal", "onChange", "Assigns the decision to an active compliance project", "Binds decision to target project governance log"),
        ("Decision Title Input", "Record Modal", "onChange (Text)", "Captures concise summary of architectural / compliance decision", "Stores decision title string in payload"),
        ("Decision Type Dropdown", "Record Modal", "onChange", "Selects classification (Architecture Change, Policy Exception, Mitigation)", "Sets governance taxonomy category"),
        ("Justification Textarea", "Record Modal", "onChange (Text)", "Captures comprehensive statutory reasoning and risk trade-off analysis", "Validates minimum length requirements"),
        ("Submit Decision Log", "Record Modal", "onClick / Form Submit", "Commits decision to immutable registry; signs record with SHA-256 hash", "Appends row to table; logs audit event (DEF-07)"),
        ("Export Decisions (CSV)", "Decisions Toolbar", "onClick", "Exports all governance decisions into a formatted CSV report", "Triggers browser file download")
    ]
    story.append(create_btn_table(dec_btn_data))
    story.append(Spacer(1, 8))

    # Screen 2.6: Audit Readiness Checklist & Gauge
    story.append(Paragraph("2.6 Audit Readiness Checklist & Metric Gauge Dashboard", h2_style))
    story.append(Paragraph(
        "The Audit Readiness cockpit quantifies the project's institutional audit preparedness on a 0–100% scale. "
        "The readiness engine calculates four sub-scores: <b>AML / CFT Controls</b>, <b>KYC Onboarding</b>, <b>Data Protection & Privacy</b>, and <b>Platform Governance</b>. "
        "Builders complete dynamic checklist items, upload verifying evidence, and trigger automated compliance recalculations (DEF-08).",
        body_style
    ))

    img_b_readiness = get_scaled_image("media_1791739750674_a1d6ca4d.png", max_width=510, max_height=175)
    if img_b_readiness:
        story.append(img_b_readiness)
        story.append(Paragraph("Figure 2.6: Audit Readiness Dashboard featuring Category Gauges and Evidence Checklist (DEF-08)", caption_style))
        story.append(Spacer(1, 4))

    readiness_btn_data = [
        ("Run Readiness Audit", "Readiness Header", "onClick", "Executes rule evaluation engine across all project evidence and advisor advice", "Recalculates category percentages and overall score"),
        ("Upload Evidence Button", "Checklist Item Row", "onClick / File Select", "Uploads compliance artifacts (PDF, SOC2 report, architecture diagram)", "Attaches document hash to checklist item; updates state"),
        ("Mark Completed Toggle", "Checklist Item Row", "onClick (Toggle)", "Manually toggles verification state for self-attested requirements", "Recalculates section progress bar immediately (DEF-08)"),
        ("Generate Audit Package", "Readiness Actions", "onClick", "Compiles comprehensive regulatory bundle including hash receipts", "Renders downloadable PDF compliance package"),
        ("Filter by Category Tabs", "Checklist Toolbar", "onClick (Tab select)", "Filters checklist items by domain (AML, KYC, InfoSec, Governance)", "Switches active checklist view")
    ]
    story.append(create_btn_table(readiness_btn_data))
    story.append(Spacer(1, 8))

    # Screen 2.7: Cryptographic Audit Trail
    story.append(PageBreak())
    story.append(Paragraph("2.7 Cryptographic Audit Trail & Event Stream Inspector", h2_style))
    story.append(Paragraph(
        "To satisfy strict supervisory auditability requirements, every platform interaction is immutably recorded in the Cryptographic Audit Trail. "
        "Each log entry includes a UTC timestamp, actor identity, action verb, target resource, client IP, and an irreversible SHA-256 verification digest (DEF-09). "
        "Builders can search logs, filter by category, verify hash chaining, and export audit logs for external regulators.",
        body_style
    ))

    img_b_trail = get_scaled_image("media_1791740746094_bb421bec.png", max_width=510, max_height=175)
    if img_b_trail:
        story.append(img_b_trail)
        story.append(Paragraph("Figure 2.7: Cryptographic Audit Trail with Real-Time Filters and SHA-256 Hash Verification (DEF-09)", caption_style))
        story.append(Spacer(1, 4))

    trail_btn_data = [
        ("Search Audit Trail", "Audit Toolbar", "onChange (Debounced)", "Executes real-time string search against user, IP, and event payload", "Filters log records dynamically"),
        ("Category Filter Dropdown", "Audit Toolbar", "onChange", "Filters stream by event type (Auth, Project, Advice, Governance, Security)", "Refreshes visible audit table rows"),
        ("Date Range Picker", "Audit Toolbar", "onChange (Date Select)", "Restricts audit events to a specific investigation window", "Queries audit API with start/end UTC boundaries"),
        ("Verify Hash Integrity", "Log Row Action", "onClick", "Recomputes SHA-256 digest from payload and compares against stored hash", "Displays green verified badge or red tampering alert"),
        ("Export Audit Log (JSON)", "Audit Header", "onClick", "Serializes filtered audit stream into cryptographically signed JSON format", "Downloads complete audit dump file to local machine"),
        ("Export Audit Log (CSV)", "Audit Header", "onClick", "Exports tabular summary formatted for regulatory submission spreadsheets", "Triggers CSV spreadsheet download")
    ]
    story.append(create_btn_table(trail_btn_data))
    story.append(Spacer(1, 8))

    # Screen 2.8: Project Compliance Workflows & Evidence Repository
    story.append(Paragraph("2.8 Compliance Workflows & Regulatory Documentation Repository", h2_style))
    story.append(Paragraph(
        "Regulated projects entail multi-step workflows. The Compliance Workflow screen maps every statutory requirement (e.g., GDPR Article 30 Records of Processing, MiFID II Best Execution, AML Customer Due Diligence) "
        "into verifiable task nodes. The Documentation Repository stores versioned evidence, policy documents, and statutory licenses.",
        body_style
    ))

    img_b_wf1 = get_scaled_image("media_1791212953490.png", max_width=255, max_height=165)
    img_b_wf2 = get_scaled_image("media_1791213224180.png", max_width=255, max_height=165)
    if img_b_wf1 and img_b_wf2:
        t_wf_imgs = Table([[img_b_wf1, img_b_wf2]], colWidths=[265, 265])
        t_wf_imgs.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(t_wf_imgs)
        story.append(Paragraph("Figure 2.8: Project Compliance Task Workflow (Left) and Evidence Document Repository (Right)", caption_style))
        story.append(Spacer(1, 4))

    wf_btn_data = [
        ("Upload Document Button", "Repository Header", "onClick / File Select", "Prompts user to select legal policy or evidence PDF; captures version tag", "Encrypts file, calculates SHA-256, stores in vault"),
        ("Download Document", "Document Row Action", "onClick", "Retrieves encrypted artifact from secure cloud storage", "Streams original document file to browser"),
        ("View Workflow Progress", "Workflow Header", "onClick", "Expands detailed stage gate view showing completed vs pending tasks", "Renders visual milestone roadmap"),
        ("Submit Stage Gate", "Workflow Actions", "onClick", "Submits completed workflow phase for internal compliance review", "Transitions project lifecycle stage")
    ]
    story.append(create_btn_table(wf_btn_data))
    story.append(Spacer(1, 8))

    # Screen 2.9: Integrated FinRegTech Tools Directory
    story.append(Paragraph("2.9 Integrated FinRegTech Tools Directory", h2_style))
    story.append(Paragraph(
        "FinRegTech ShipYard embeds pre-integrated enterprise compliance tools directly within the Builder cockpit: "
        "<b>ControlMap</b> (governance and risk management automation), <b>ModelGuard</b> (AI algorithmic bias and fairness evaluation), and <b>RiskLens</b> (quantitative cyber risk assessment). "
        "Builders configure API credentials, launch tools in isolated iframe environments, and synchronize compliance telemetry.",
        body_style
    ))

    img_b_tools = get_scaled_image("media_1790750500020.png", max_width=510, max_height=175)
    if img_b_tools:
        story.append(img_b_tools)
        story.append(Paragraph("Figure 2.9: Integrated FinRegTech Tools Directory (ControlMap, ModelGuard, RiskLens)", caption_style))
        story.append(Spacer(1, 4))

    tools_btn_data = [
        ("Launch Tool Button", "Tool Card Action", "onClick", "Initializes single sign-on (SSO) session and launches external tool", "Opens tool interface in authenticated modal"),
        ("Configure API Keys", "Tool Card Action", "onClick", "Opens credentials configuration drawer for tool authentication keys", "Saves encrypted API credentials in tenant vault"),
        ("Sync Telemetry Data", "Tool Card Action", "onClick", "Triggers immediate sync of risk scores and compliance telemetry", "Refreshes project metrics with latest external data")
    ]
    story.append(create_btn_table(tools_btn_data))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 3: ROLE 2 — THE ADVISOR WORKSPACE
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("3. Role Specification: The Advisor (Regulatory & Legal Specialist)", h1_style))
    story.append(Paragraph(
        "The <b>Advisor Role</b> is designed for licensed regulatory attorneys, ex-regulators, cyber risk specialists, and certified public accountants. "
        "Advisors operate in a dedicated, privacy-preserving workspace. They inspect project requirements, review technical evidence, and issue legally defensible regulatory opinions. "
        "Advisors are strictly isolated to projects where they have been formally retained, completely eliminating cross-tenant data leakage risks (remediating DEF-10).",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Screen 3.1: Advisor Specialization & Expertise Setup
    story.append(Paragraph("3.1 Advisor Specialization & Expertise Setup Gateway", h2_style))
    story.append(Paragraph(
        "Upon initial onboarding or when modifying practice credentials, advisors configure their professional profile. "
        "They select their primary operational domain (<b>Regulatory Compliance Expert</b>, <b>Legal Partner</b>, <b>Tech Expert</b>, <b>Funding / Business Support</b>, or <b>Marketing Service</b>) "
        "and activate accredited regulatory jurisdictions (SEC, FCA, MAS, FINMA, BaFin). This configuration drives the platform's matching algorithms.",
        body_style
    ))

    img_adv_setup1 = get_scaled_image("media_1791949806618_d36c812d.png", max_width=255, max_height=165)
    img_adv_setup2 = get_scaled_image("media_1791950620810_ec218efe.png", max_width=255, max_height=165)
    if img_adv_setup1 and img_adv_setup2:
        t_adv_s_imgs = Table([[img_adv_setup1, img_adv_setup2]], colWidths=[265, 265])
        t_adv_s_imgs.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(t_adv_s_imgs)
        story.append(Paragraph("Figure 3.1: Advisor Onboarding Domain Selection (Left) and Practice Jurisdiction Badges (Right)", caption_style))
        story.append(Spacer(1, 4))

    adv_setup_btn_data = [
        ("Select Domain Card", "Expertise Setup", "onClick (Card Select)", "Chooses primary advisory specialty (Regulatory, Legal, Tech, Funding, Marketing)", "Sets active specialization taxonomy"),
        ("Jurisdiction Badges", "Expertise Setup", "onClick (Toggle)", "Activates regulatory authorizations (US SEC, UK FCA, EU BaFin, SG MAS, CH FINMA)", "Binds jurisdictions to advisor matching engine"),
        ("Save Expertise Profile", "Expertise Setup", "onClick / Form Submit", "Persists advisor credentials and jurisdiction list to database", "Updates profile; enables advice intake routing"),
        ("Continue to Dashboard", "Expertise Setup", "onClick", "Navigates directly to the Advisor Command Center", "Transitions screen to Advisor Dashboard")
    ]
    story.append(create_btn_table(adv_setup_btn_data))
    story.append(Spacer(1, 8))

    # Screen 3.2: Advisor Overview Dashboard
    story.append(Paragraph("3.2 Advisor Command Center & Priority Review Queue", h2_style))
    story.append(Paragraph(
        "The Advisor Dashboard features four operational KPI cards: "
        "<b>Assigned Reviews</b> (active client projects awaiting advice), <b>Pending Requests</b> (new engagement invitations), "
        "<b>Completed Reviews</b> (historical rendered opinions), and <b>Average Turnaround SLA</b>. "
        "The Priority Review Queue displays incoming advice requests ordered by urgency, complete with client company name, project title, and target statutory deadline.",
        body_style
    ))

    img_adv_dash = get_scaled_image("media_1791949893756_6c538f7d.png", max_width=510, max_height=175)
    if img_adv_dash:
        story.append(img_adv_dash)
        story.append(Paragraph("Figure 3.2: Advisor Command Center showing KPI Cards, Priority Queue, and 'Change Expertise' Button", caption_style))
        story.append(Spacer(1, 4))

    adv_dash_btn_data = [
        ("Change Expertise Button", "Advisor Top Nav", "onClick", "Relaunches the expertise configuration modal to adjust practice domains", "Opens expertise setup modal immediately"),
        ("Review Now Button", "Priority Queue Action", "onClick", "Opens the formal evaluation console for target project requirement", "Loads project requirement and attached evidence"),
        ("Decline Engagement", "Priority Queue Action", "onClick", "Declines advice request with optional referral note to client", "Removes item from queue; notifies client Builder"),
        ("Filter Queue Dropdown", "Queue Header", "onChange", "Filters queue items by SLA urgency (Critical 24h, High 48h, Standard)", "Filters queue table rows"),
        ("Notification Bell", "Advisor Top Nav", "onClick", "Displays alerts regarding new project assignments and client responses", "Toggles notification dropdown menu"),
        ("Mark All as Read", "Notification Drawer", "onClick", "Clears unread notifications badge", "Updates notification status in database")
    ]
    story.append(create_btn_table(adv_dash_btn_data))
    story.append(Spacer(1, 8))

    # Screen 3.3: My Projects Scoped Portfolio
    story.append(PageBreak())
    story.append(Paragraph("3.3 My Projects Scoped Portfolio & Zero-Leakage Governance", h2_style))
    story.append(Paragraph(
        "To ensure compliance with strict financial confidentiality regulations and NDA obligations, the 'My Projects' view is strictly scoped. "
        "Advisors can only view projects to which they have been explicitly invited and confirmed. Unrelated platform projects are entirely inaccessible (DEF-10). "
        "When no projects are assigned, a helpful empty state guides the advisor on how to publish availability.",
        body_style
    ))

    img_adv_proj = get_scaled_image("media_1791957465637_d7afbed5.png", max_width=510, max_height=175)
    if img_adv_proj:
        story.append(img_adv_proj)
        story.append(Paragraph("Figure 3.3: Advisor Scoped Projects Portfolio ensuring Zero Cross-Tenant Data Leakage (DEF-10)", caption_style))
        story.append(Spacer(1, 4))

    adv_proj_btn_data = [
        ("Open Project Workspace", "Project Card Action", "onClick", "Enters dedicated project review workspace with full evidence access", "Loads project documents and compliance checklist"),
        ("View Scope of Work", "Project Card Action", "onClick", "Displays formal engagement terms, agreed SLA, and target milestones", "Renders engagement agreement modal"),
        ("Filter Active / Archived", "Portfolio Toolbar", "onClick (Tab select)", "Switches view between active consulting mandates and historical archives", "Updates project grid display")
    ]
    story.append(create_btn_table(adv_proj_btn_data))
    story.append(Spacer(1, 8))

    # Screen 3.4: Regulatory Requirements Evaluation Queue
    story.append(Paragraph("3.4 Regulatory Requirements Evaluation Queue", h2_style))
    story.append(Paragraph(
        "The Requirements Queue breaks down complex FinTech projects into individual statutory evaluation items: "
        "<b>REQ-142</b> (AML Transaction Monitoring & Sanctions Screening), <b>REQ-157</b> (End-to-End Cryptographic Key Management), and <b>REQ-163</b> (Executive Risk Governance Framework). "
        "Advisors click each requirement to inspect the Builder's technical implementation notes and submitted evidence.",
        body_style
    ))

    img_adv_req = get_scaled_image("media_1791957523546_e3a2b054.png", max_width=510, max_height=175)
    if img_adv_req:
        story.append(img_adv_req)
        story.append(Paragraph("Figure 3.4: Regulatory Requirements Evaluation Queue (REQ-142, REQ-157, REQ-163)", caption_style))
        story.append(Spacer(1, 4))

    adv_req_btn_data = [
        ("Evaluate Requirement", "Requirement Row Action", "onClick", "Opens requirement details and routes to Advice Submission form", "Populates Advice form with target requirement ID"),
        ("Inspect Attached Evidence", "Requirement Row Action", "onClick", "Opens document preview drawer for verifying architecture diagrams or policies", "Renders verified PDF in secure previewer"),
        ("Filter by Rulebook", "Requirements Toolbar", "onChange", "Filters requirements by regulatory framework (e.g. BSA/AML, GDPR, MiFID)", "Filters requirements list")
    ]
    story.append(create_btn_table(adv_req_btn_data))
    story.append(Spacer(1, 8))

    # Screen 3.5: "My Advice & Reviews" Submission Console
    story.append(Paragraph("3.5 'My Advice & Reviews' Formal Submission Console", h2_style))
    story.append(Paragraph(
        "The Advice Submission Console is the core workhorse of the Advisor role. Here, advisors render formal compliance opinions. "
        "The form mandates: <b>Target Project Selection</b>, <b>Requirement Reference</b>, <b>Recommendation Type</b> ('Approve', 'Changes Requested', 'Non-Compliant'), "
        "<b>Severity Level</b> ('Low', 'Medium', 'High', 'Critical'), <b>Detailed Legal / Technical Justification</b>, and <b>Recommended Action Items</b>. "
        "Comprehensive client-side validation enforces minimum justification length and statutory citations before submission (DEF-11).",
        body_style
    ))

    img_adv_submit = get_scaled_image("media_1791952670487_5285f173.png", max_width=510, max_height=175)
    if img_adv_submit:
        story.append(img_adv_submit)
        story.append(Paragraph("Figure 3.5: Formal Regulatory Advice Submission Console with Statutory Citation Validation (DEF-11)", caption_style))
        story.append(Spacer(1, 4))

    adv_submit_btn_data = [
        ("Select Project Dropdown", "Advice Form", "onChange", "Selects target client project from advisor's scoped active portfolio", "Populates project metadata and open requirements"),
        ("Recommendation Type", "Advice Form", "onChange (Select)", "Sets formal finding: 'Approve', 'Changes Requested', or 'Non-Compliant'", "Applies color-coded status badge and logic rules"),
        ("Severity Level Dropdown", "Advice Form", "onChange (Select)", "Classifies risk severity: Low, Medium, High, or Critical", "Determines project risk gauge weighting"),
        ("Justification Textarea", "Advice Form", "onChange (Text)", "Captures formal legal opinion, statutory citations, and technical analysis", "Enforces length check; sanitizes text (DEF-11)"),
        ("Recommended Actions", "Advice Form", "onChange (List Input)", "Itemizes concrete remediation steps required from the Builder", "Appends actionable checklist items to client view"),
        ("Submit Advice Button", "Advice Form Actions", "onClick / Form Submit", "Commits formal advice to project record; emits real-time notification", "Signs review record; updates Builder dashboard"),
        ("Reset / Clear Form", "Advice Form Actions", "onClick", "Clears all form inputs and restores default dropdown selections", "Resets form state with confirmation prompt")
    ]
    story.append(create_btn_table(adv_submit_btn_data))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 4: ROLE 3 — THE ADMINISTRATOR COMMAND CENTER
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("4. Role Specification: The Administrator (Platform Governance & Super-User Operations)", h1_style))
    story.append(Paragraph(
        "The <b>Administrator Role</b> represents platform operators, enterprise risk officers, and infrastructure security leads. "
        "Administrators maintain supervisory command over all platform operations: managing multi-tenant user accounts, governing cross-tenant projects, "
        "curating the central regulatory knowledge base, onboarding accredited advisors, and analyzing cryptographic audit logs.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Screen 4.1: Administrator Command Center
    story.append(Paragraph("4.1 Command Center Overview & Global Platform KPIs", h2_style))
    story.append(Paragraph(
        "The Administrator Command Center delivers comprehensive high-altitude platform intelligence across six primary KPI cards: "
        "<b>Total Users</b> (active vs. inactive breakdown), <b>Active Projects</b> (across all tenants), <b>Regulatory Rules</b> (indexed in central repository), "
        "<b>Audit Events (24h)</b> (real-time stream count), <b>Pending Invitations</b> (advisor onboarding pipeline), and <b>System Health</b> (uptime percentage and latency).",
        body_style
    ))

    img_adm_dash = get_scaled_image("media_1791981192338_dd3ce2b7.png", max_width=510, max_height=175)
    if img_adm_dash:
        story.append(img_adm_dash)
        story.append(Paragraph("Figure 4.1: Administrator Command Center with Global Platform KPIs and System Status", caption_style))
        story.append(Spacer(1, 4))

    adm_dash_btn_data = [
        ("Refresh Metrics Button", "Command Header", "onClick", "Queries administrative telemetry endpoint for real-time KPI updates", "Refreshes all 6 metric cards without page reload"),
        ("Date Range Filter", "Command Header", "onChange (Select)", "Adjusts telemetry reporting window (24 Hours, 7 Days, 30 Days, Year-to-Date)", "Recalculates velocity graphs and event counts"),
        ("System Diagnostics", "Health Card Action", "onClick", "Initiates health check across API clusters, database replicas, and vector DB", "Displays live microservice status drawer"),
        ("Global Export", "Command Header", "onClick", "Generates comprehensive executive summary report across all platform activity", "Downloads executive PDF summary")
    ]
    story.append(create_btn_table(adm_dash_btn_data))
    story.append(Spacer(1, 8))

    # Screen 4.2: Live Activity Feed & System Alerts
    story.append(Paragraph("4.2 Live Platform Activity Feed & Real-Time Alerts", h2_style))
    story.append(Paragraph(
        "The Live Activity Feed captures platform-wide transactions in real time. Adjacent to the feed sits the Real-Time Alerts panel, highlighting "
        "critical events such as unusual authentication spikes, advisory SLA breaches, rulebook updates, or infrastructure anomalies.",
        body_style
    ))

    img_adm_act1 = get_scaled_image("media_1791981200685_5461ca8a.png", max_width=255, max_height=165)
    img_adm_act2 = get_scaled_image("media_1791981206848_d73db92a.png", max_width=255, max_height=165)
    if img_adm_act1 and img_adm_act2:
        t_adm_a_imgs = Table([[img_adm_act1, img_adm_act2]], colWidths=[265, 265])
        t_adm_a_imgs.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(t_adm_a_imgs)
        story.append(Paragraph("Figure 4.2: Live Platform Audit Stream (Left) and High-Priority Security Alerts Console (Right)", caption_style))
        story.append(Spacer(1, 4))

    adm_act_btn_data = [
        ("Pause / Resume Stream", "Activity Feed Toolbar", "onClick", "Temporarily pauses incoming event streaming to allow detailed forensic reading", "Freezes/unfreezes real-time DOM updates"),
        ("Filter by Severity", "Alerts Toolbar", "onChange", "Filters alerts by criticality: Info, Warning, Error, or Critical Security Alert", "Filters visible alert cards"),
        ("Dismiss Alert Button", "Alert Card Action", "onClick", "Acknowledges alert and records administrator dismissal timestamp", "Archives alert; updates badge counter"),
        ("Investigate Incident", "Alert Card Action", "onClick", "Drills directly into forensic audit log filtered by incident correlation ID", "Navigates to Audit Logs with pre-filled filters")
    ]
    story.append(create_btn_table(adm_act_btn_data))
    story.append(Spacer(1, 8))

    # Screen 4.3 & 4.4: User Management & Deactivation Modal
    story.append(PageBreak())
    story.append(Paragraph("4.3 User Management Console & Deactivation Confirmation Safeguard", h2_style))
    story.append(Paragraph(
        "The User Management console provides full tenant lifecycle oversight. The data grid itemizes every platform user: "
        "User Avatar, Full Name, Email, Organization, Assigned Role (Builder, Advisor, Admin), Status Badge (Active / Inactive), and Last Login. "
        "Administrators can adjust roles, trigger password resets, or toggle account status. "
        "Crucially, deactivating an account requires explicit modal confirmation (DEF-12) to prevent accidental revocation of active enterprise founders or advisors.",
        body_style
    ))

    img_adm_users = get_scaled_image("media_1791982823780_dc3deb23.png", max_width=510, max_height=175)
    if img_adm_users:
        story.append(img_adm_users)
        story.append(Paragraph("Figure 4.3: User Management Console displaying Multi-Tenant Accounts and Status Toggles", caption_style))
        story.append(Spacer(1, 4))

    img_adm_deact = get_scaled_image("media_1791982900934_5d51a9c2.png", max_width=470, max_height=165)
    if img_adm_deact:
        story.append(img_adm_deact)
        story.append(Paragraph("Figure 4.4: User Deactivation Confirmation Modal Safeguard (DEF-12)", caption_style))
        story.append(Spacer(1, 4))

    user_btn_data = [
        ("Status Toggle Switch", "User Row Action", "onClick", "Initiates account status modification; opens confirmation safeguard modal", "Displays Deactivation Modal for active users (DEF-12)"),
        ("Confirm Deactivation", "Deactivation Modal", "onClick", "Executes PATCH /api/users/:id/status to set status to 'Inactive'", "Revokes active tokens; sets status to Inactive"),
        ("Cancel Deactivation", "Deactivation Modal", "onClick", "Aborts deactivation process and leaves user account in active state", "Closes modal without modifying database"),
        ("Edit Role Dropdown", "User Row Action", "onChange", "Reassigns operational persona between Builder, Advisor, and Administrator", "Updates role permissions; logs audit event"),
        ("Search Users Input", "User Grid Toolbar", "onChange (Debounced)", "Performs fuzzy text search across name, email, and organization", "Filters table rows dynamically"),
        ("Filter by Role Tabs", "User Grid Toolbar", "onClick (Tab select)", "Filters user directory by role category (All, Builders, Advisors, Admins)", "Switches active role view")
    ]
    story.append(create_btn_table(user_btn_data))
    story.append(Spacer(1, 8))

    # Screen 4.5 & 4.6: Project Oversight & Project Detail Modal
    story.append(Paragraph("4.5 Cross-Tenant Project Oversight & Audit Timeline Inspection", h2_style))
    story.append(Paragraph(
        "Administrators maintain supervisory oversight across all commercial FinTech projects on the platform. "
        "The Project Oversight console displays project health, target jurisdictions, assigned advisors, and compliance progress. "
        "Clicking any project opens the Project Detail Modal, revealing the complete audit timeline, assigned reviewers, and ownership attribution.",
        body_style
    ))

    img_adm_proj1 = get_scaled_image("media_1791983426855_311d8b4d.png", max_width=255, max_height=165)
    img_adm_proj2 = get_scaled_image("media_1791983439586_56d2549b.png", max_width=255, max_height=165)
    if img_adm_proj1 and img_adm_proj2:
        t_adm_p_imgs = Table([[img_adm_proj1, img_adm_proj2]], colWidths=[265, 265])
        t_adm_p_imgs.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(t_adm_p_imgs)
        story.append(Paragraph("Figure 4.5: Cross-Tenant Project Oversight Grid (Left) and Deep-Dive Inspection Modal (Right)", caption_style))
        story.append(Spacer(1, 4))

    proj_adm_btn_data = [
        ("View Project Details", "Project Oversight Row", "onClick", "Opens the comprehensive Project Detail & Audit Timeline inspection modal", "Renders project metadata, timeline, and advisors"),
        ("Filter by Status", "Oversight Toolbar", "onChange", "Filters projects by state: All, In Progress, Audit Ready, Archived", "Updates oversight grid rows"),
        ("Reassign Owner Button", "Project Modal Action", "onClick", "Reassigns primary project ownership to a new Builder user account", "Transfers administrative rights over project"),
        ("Archive Project Button", "Project Modal Action", "onClick", "Soft-deletes project and moves all associated evidence into cold storage", "Transitions status to 'Archived' with confirmation"),
        ("Close Modal (X)", "Project Modal Header", "onClick", "Closes project details modal and returns to main oversight grid", "Closes modal drawer")
    ]
    story.append(create_btn_table(proj_adm_btn_data))
    story.append(Spacer(1, 8))

    # Screen 4.7: Advisor Invitations & Onboarding Console
    story.append(PageBreak())
    story.append(Paragraph("4.7 Advisor Invitations & Expert Onboarding Console", h2_style))
    story.append(Paragraph(
        "To maintain elite quality standards across the advisor network, advisors are onboarded via cryptographic invitation. "
        "Administrators invite verified experts by specifying their professional email, practice domain, accredited jurisdictions, and custom onboarding message. "
        "Administrators track pending invite codes, resend invitations, or revoke unredeemed links.",
        body_style
    ))

    img_adm_inv = get_scaled_image("media_1791998978622_11428009.png", max_width=510, max_height=175)
    if img_adm_inv:
        story.append(img_adm_inv)
        story.append(Paragraph("Figure 4.6: Advisor Invitations Management Console with Invitation Lifecycle Controls", caption_style))
        story.append(Spacer(1, 4))

    inv_btn_data = [
        ("Invite New Advisor", "Invitations Header", "onClick", "Opens the Invite Advisor modal with expertise and jurisdiction selectors", "Displays Advisor Invitation Dialog"),
        ("Advisor Email Input", "Invite Modal", "onChange (Email)", "Captures accredited expert's institutional or corporate email address", "Validates RFC 5322 email syntax"),
        ("Domain Selector Dropdown", "Invite Modal", "onChange", "Assigns primary practice specialty (Regulatory, Legal, Tech, Funding, Marketing)", "Sets invitation domain tag"),
        ("Jurisdictions Checkboxes", "Invite Modal", "onClick (Toggle)", "Designates accredited supervisory frameworks (SEC, FCA, BaFin, MAS)", "Appends jurisdiction authorizations"),
        ("Send Invitation Button", "Invite Modal", "onClick / Form Submit", "Generates single-use cryptographic token; dispatches secure invitation email", "Creates pending invite record in database"),
        ("Resend Invitation", "Invite Row Action", "onClick", "Generates fresh invitation link and re-transmits email to recipient", "Updates expiration timestamp; emits email"),
        ("Revoke Invitation", "Invite Row Action", "onClick", "Invalidates pending invitation token and prevents account creation", "Revokes token; removes pending invite row")
    ]
    story.append(create_btn_table(inv_btn_data))
    story.append(Spacer(1, 8))

    # Screen 4.8: Regulatory Data Management & Knowledge Base
    story.append(Paragraph("4.8 Regulatory Data Management & Central Knowledge Repository", h2_style))
    story.append(Paragraph(
        "The Regulatory Data Management module represents the core intelligence base of the platform. "
        "Here, administrators curate supervisory rulebooks (e.g. EU AMLD6, GDPR, MiFID II, DORA, US Dodd-Frank, Basel III). "
        "Administrators utilize the 'Add Regulatory Source' modal (remediating DEF-13) to register new regulatory statutes, specify issuing authorities, "
        "upload official statutory PDFs, and submit sources into pending validation workflows before indexing into the RAG vector engine.",
        body_style
    ))

    img_adm_reg = get_scaled_image("media_1791999368286_8da461eb.png", max_width=510, max_height=175)
    if img_adm_reg:
        story.append(img_adm_reg)
        story.append(Paragraph("Figure 4.7: Add Regulatory Source Modal within Regulatory Knowledge Management Console (DEF-13)", caption_style))
        story.append(Spacer(1, 4))

    reg_btn_data = [
        ("Add Regulatory Source", "Regulatory Header", "onClick", "Opens the Add Regulatory Source modal for indexing new supervisory rulebooks", "Displays rulebook entry modal (DEF-13)"),
        ("Source Name Input", "Add Source Modal", "onChange (Text)", "Captures full legal title of regulatory rulebook or statutory standard", "Stores source title in payload"),
        ("Framework Identifier", "Add Source Modal", "onChange (Text)", "Assigns standard code (e.g., AMLD6, DORA-2025, GDPR-Art30)", "Validates uniqueness of framework identifier"),
        ("Issuing Authority", "Add Source Modal", "onChange (Select)", "Selects regulatory body (EBA, ESMA, SEC, FCA, MAS, FINMA)", "Binds issuing authority metadata"),
        ("Effective Date Picker", "Add Source Modal", "onChange (Date)", "Specifies enforcement deadline or statutory enactment date", "Stores ISO 8601 date string"),
        ("Document Upload / URL", "Add Source Modal", "onChange / File", "Captures official gazette URL or accepts statutory PDF document upload", "Stages document for text extraction"),
        ("Add as Pending Validation", "Add Source Modal", "onClick / Form Submit", "Commits rulebook to staging queue for legal validator sign-off (DEF-13)", "Persists record with status 'Pending Validation'"),
        ("Validate Source Button", "Source Row Action", "onClick", "Promotes validated rulebook into active production knowledge base", "Indexes document into AI vector search database")
    ]
    story.append(create_btn_table(reg_btn_data))
    story.append(Spacer(1, 8))

    # Screen 4.9: Platform System Audit Logs & Forensic Deep-Dive
    story.append(PageBreak())
    story.append(Paragraph("4.9 System Audit Logs Console & Forensic Payload Inspector", h2_style))
    story.append(Paragraph(
        "The System Audit Logs console is the highest-level security monitoring tool in the FinRegTech ShipYard ecosystem. "
        "Unlike the Builder audit trail which is scoped to project events, the System Audit Log captures all platform-level transactions: "
        "administrative logins, user deactivations, rulebook modifications, API key access, and cross-tenant data queries. "
        "Clicking any log entry opens the Forensic Payload Inspector modal, displaying full JSON request/response payloads and SHA-256 integrity hashes.",
        body_style
    ))

    img_adm_audit1 = get_scaled_image("media_1791999494451_b654a5f6.png", max_width=255, max_height=165)
    img_adm_audit2 = get_scaled_image("media_1791999970886_8eac6b2b.png", max_width=255, max_height=165)
    if img_adm_audit1 and img_adm_audit2:
        t_adm_au_imgs = Table([[img_adm_audit1, img_adm_audit2]], colWidths=[265, 265])
        t_adm_au_imgs.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(t_adm_au_imgs)
        story.append(Paragraph("Figure 4.8: Immutable System Audit Console (Left) and Forensic Payload Inspector Modal (Right)", caption_style))
        story.append(Spacer(1, 4))

    sys_audit_btn_data = [
        ("Inspect Event Button", "Audit Log Row", "onClick", "Opens the forensic event detail modal with raw JSON payload and hash data", "Displays Forensic Payload Inspector modal"),
        ("Filter by Actor / User", "System Audit Toolbar", "onChange (Input)", "Filters entire platform log stream by specific user email or API key ID", "Filters audit rows dynamically"),
        ("Filter by Action Verb", "System Audit Toolbar", "onChange (Select)", "Filters by event category (LOGIN, USER_DEACTIVATE, RULE_ADD, EXPORT)", "Filters audit rows dynamically"),
        ("Copy Hash Button", "Inspector Modal Action", "onClick", "Copies the 64-character SHA-256 cryptographic digest to system clipboard", "Copies hash and triggers toast notification"),
        ("Verify Chain Link", "Inspector Modal Action", "onClick", "Validates cryptographic hash continuity with preceding log block", "Outputs cryptographic verification check"),
        ("Download Audit Dump", "System Audit Header", "onClick", "Exports complete immutable system audit log with digital signature", "Generates signed audit archive for external regulators"),
        ("Close Inspector (X)", "Inspector Modal Header", "onClick", "Dismisses forensic inspector modal and returns to system log grid", "Closes modal drawer")
    ]
    story.append(create_btn_table(sys_audit_btn_data))
    story.append(Spacer(1, 8))

    # =========================================================================
    # SECTION 5: MASTER CROSS-ROLE INTERACTION MATRIX & BUTTON INDEX
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("5. Master Cross-Role Interaction Matrix & Comprehensive Button Index", h1_style))
    story.append(Paragraph(
        "FinRegTech ShipYard operates as a collaborative ecosystem where actions performed by one role trigger deterministic state transitions for others. "
        "The matrix below formalizes how key platform entities transition across Builder, Advisor, and Administrator boundaries:",
        body_style
    ))
    story.append(Spacer(1, 4))

    matrix_data = [
        [Paragraph("<b>Platform Entity</b>", meta_style), Paragraph("<b>Builder Action & State</b>", meta_style), Paragraph("<b>Advisor Action & State</b>", meta_style), Paragraph("<b>Administrator Governance</b>", meta_style)],
        [
            Paragraph("<b>Compliance Project</b>", meta_style),
            Paragraph("Creates project via 3-step wizard; binds jurisdictions; uploads evidence; requests advice.", meta_style),
            Paragraph("Views only if formally assigned; reviews requirements; cannot delete or reassign project.", meta_style),
            Paragraph("Maintains cross-tenant oversight; can reassign ownership or archive delinquent projects.", meta_style)
        ],
        [
            Paragraph("<b>Advisory Review</b>", meta_style),
            Paragraph("Selects advisor; submits project advice request; accepts/rejects formal advice.", meta_style),
            Paragraph("Receives request in queue; submits formal advice with justification, citation & severity.", meta_style),
            Paragraph("Monitors advisor response SLAs; tracks advice velocity across projects.", meta_style)
        ],
        [
            Paragraph("<b>Governance Decisions</b>", meta_style),
            Paragraph("Records formal executive decision resulting from advice; provides rationale.", meta_style),
            Paragraph("Reviews client decisions; identifies compliance gaps or residual risks.", meta_style),
            Paragraph("Audits decision records for regulatory compliance inspections and SOC2 audits.", meta_style)
        ],
        [
            Paragraph("<b>User Account</b>", meta_style),
            Paragraph("Registers company account; manages team members and organization profile.", meta_style),
            Paragraph("Configures practice domains, jurisdiction credentials, and billing terms.", meta_style),
            Paragraph("Authorizes accounts; manages role permissions; toggles active/inactive state.", meta_style)
        ],
        [
            Paragraph("<b>Regulatory Rulebook</b>", meta_style),
            Paragraph("Selects applicable frameworks (GDPR, AMLD6, DORA) during project creation.", meta_style),
            Paragraph("Cites specific statutory articles when rendering compliance advice.", meta_style),
            Paragraph("Creates and validates new regulatory rulebooks via Add Regulatory Source modal.", meta_style)
        ],
        [
            Paragraph("<b>Audit Trail & Logs</b>", meta_style),
            Paragraph("Inspects project-level event stream; verifies hashes; downloads project audit package.", meta_style),
            Paragraph("Logs rendered reviews and advice interactions; cannot modify historical logs.", meta_style),
            Paragraph("Inspects forensic payloads across all tenants; verifies global cryptographic hash chain.", meta_style)
        ]
    ]
    matrix_table = Table(matrix_data, colWidths=[95, 145, 145, 145])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_secondary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light])
    ]))
    story.append(matrix_table)
    story.append(Spacer(1, 10))

    # Master Button Reference Table (Comprehensive Index)
    story.append(Paragraph("Master Interactive Button Reference Table (Alphabetical Operational Index)", h2_style))
    story.append(Paragraph(
        "The following master reference compiles every major interactive button across all three roles, documenting its exact UI label, screen location, role accessibility, and functional system trigger:",
        body_style
    ))

    master_btn_data = [
        ("Accept Advice", "Advisor Advice Intake", "Builder", "onClick", "Formally accepts advisor advice; marks requirement compliant (DEF-06)"),
        ("Add as Pending Validation", "Add Regulatory Source Modal", "Admin", "onClick / Submit", "Stages new statutory rulebook for legal validation review (DEF-13)"),
        ("Add Regulatory Source", "Regulatory Knowledge Base", "Admin", "onClick", "Opens Add Regulatory Source modal for uploading new rulebooks (DEF-13)"),
        ("Archive Project", "Project Detail Modal", "Admin", "onClick", "Soft-deletes project and moves all compliance artifacts to cold storage"),
        ("Ask AI Copilot", "Builder Main Dashboard", "Builder", "onClick", "Opens the AI RAG regulatory inquiry drawer with active rulebook context"),
        ("Cancel Deactivation", "User Deactivation Modal", "Admin", "onClick", "Aborts user deactivation safeguard modal without changes (DEF-12)"),
        ("Change Expertise", "Advisor Top Nav & Dashboard", "Advisor", "onClick", "Re-opens practice domain & jurisdiction selector modal"),
        ("Confirm Deactivation", "User Deactivation Modal", "Admin", "onClick", "Executes user deactivation and revokes all active session tokens (DEF-12)"),
        ("Continue to Dashboard", "Advisor Expertise Setup", "Advisor", "onClick", "Completes practice setup and routes advisor to main dashboard"),
        ("Create Project", "Builder Main Dashboard", "Builder", "onClick", "Launches 3-step Create Compliance Project Wizard modal"),
        ("Create Project (Submit)", "Project Wizard Step 3", "Builder", "onClick / Submit", "Persists project record with dynamic owner attribution (DEF-03)"),
        ("Decline Engagement", "Advisor Priority Queue", "Advisor", "onClick", "Declines incoming client advice request with optional referral note"),
        ("Dismiss Alert", "Admin Security Alerts Panel", "Admin", "onClick", "Acknowledges high-priority security or system alert"),
        ("Download Audit Package", "Builder Dashboard / Readiness", "Builder", "onClick", "Generates and downloads audit-certified PDF compliance report"),
        ("Download Audit Dump", "Admin System Audit Console", "Admin", "onClick", "Exports cryptographically signed JSON platform audit dump"),
        ("Evaluate Requirement", "Advisor Requirements Queue", "Advisor", "onClick", "Routes requirement into formal Advice Submission Console"),
        ("Export Decisions (CSV)", "Governance Decisions Registry", "Builder", "onClick", "Exports all recorded governance decisions to CSV spreadsheet"),
        ("Inspect Event", "Admin System Audit Console", "Admin", "onClick", "Opens forensic modal showing raw JSON payload and SHA-256 hash"),
        ("Invite Advisor", "Builder Dashboard / Directory", "Builder", "onClick", "Routes to Advisors Directory to initiate expert engagement"),
        ("Invite New Advisor", "Admin Advisor Invitations", "Admin", "onClick", "Opens Advisor Invitation modal with domain & jurisdiction selectors"),
        ("Launch Tool", "FinRegTech Tools Directory", "Builder", "onClick", "Launches integrated compliance tool (ControlMap, ModelGuard, RiskLens)"),
        ("Mark All as Read", "Global Notification Flyout", "All Roles", "onClick", "Clears unread notification counters and updates user alert state"),
        ("Mark Completed Toggle", "Audit Readiness Checklist", "Builder", "onClick", "Toggles self-attested checklist item state; updates readiness gauge (DEF-08)"),
        ("Record Decision", "Governance Decisions Registry", "Builder", "onClick", "Opens formal governance decision logging dialog (DEF-07)"),
        ("Refresh Metrics", "Admin Command Center", "Admin", "onClick", "Re-queries administrative telemetry endpoint for real-time KPI data"),
        ("Reject Advice", "Advisor Advice Intake", "Builder", "onClick", "Rejects advisor advice and prompts for architectural rebuttal log"),
        ("Request Advice", "Advisors Directory", "Builder", "onClick", "Opens advice request modal to bind advisor to active project"),
        ("Resend Invitation", "Admin Advisor Invitations", "Admin", "onClick", "Regenerates cryptographic invitation token and resends email"),
        ("Reset / Clear Form", "Advice Submission Console", "Advisor", "onClick", "Clears all inputs in formal advice submission console"),
        ("Revoke Invitation", "Admin Advisor Invitations", "Admin", "onClick", "Invalidates pending invitation token and prevents account registration"),
        ("Run Readiness Audit", "Builder Dashboard / Readiness", "Builder", "onClick", "Triggers algorithmic recalculation of compliance readiness percentages"),
        ("Save Expertise Profile", "Advisor Expertise Setup", "Advisor", "onClick / Submit", "Persists advisor practice domains and accredited jurisdictions"),
        ("Send Invitation", "Admin Invite Advisor Modal", "Admin", "onClick / Submit", "Dispatches secure cryptographic invitation email to advisor candidate"),
        ("Sign In", "Commercial Sign-In Portal", "Builder/Advisor", "onClick / Submit", "Authenticates commercial user and routes to respective role cockpit"),
        ("Status Toggle Switch", "Admin User Management", "Admin", "onClick", "Toggles user active/inactive state; triggers safeguard modal (DEF-12)"),
        ("Submit Advice", "Advice Submission Console", "Advisor", "onClick / Submit", "Commits formal regulatory opinion with statutory citations (DEF-11)"),
        ("Submit Advice Request", "Advisors Request Modal", "Builder", "onClick / Submit", "Dispatches advice engagement request to selected advisor queue"),
        ("Submit Decision Log", "Record Decision Modal", "Builder", "onClick / Submit", "Logs formal executive decision with statutory rationale (DEF-07)"),
        ("Upload Document", "Documentation Repository", "Builder", "onClick / File", "Uploads and SHA-256 hashes compliance evidence artifacts"),
        ("Upload Evidence", "Audit Readiness Checklist", "Builder", "onClick / File", "Binds uploaded document artifact to specific audit checklist rule"),
        ("Validate Source", "Admin Regulatory Knowledge Base", "Admin", "onClick", "Promotes staged rulebook into active AI RAG production knowledge base"),
        ("Verify Admin Credentials", "Admin Sign-In Portal", "Admin", "onClick / Submit", "Verifies master administrative credentials and initiates 2FA flow"),
        ("Verify Hash Integrity", "Cryptographic Audit Trail", "Builder / Admin", "onClick", "Recomputes SHA-256 hash and verifies tamper-evident chain integrity"),
        ("View Project Details", "Project Oversight / Dashboard", "All Roles", "onClick", "Opens comprehensive project audit timeline and details modal")
    ]

    master_btn_table_data = [[
        Paragraph("<b>Button Label</b>", meta_style),
        Paragraph("<b>Screen Location</b>", meta_style),
        Paragraph("<b>Role Access</b>", meta_style),
        Paragraph("<b>Event</b>", meta_style),
        Paragraph("<b>Functional System Trigger & State Transition</b>", meta_style)
    ]]

    for b in master_btn_data:
        master_btn_table_data.append([
            Paragraph(f"<b>{b[0]}</b>", ParagraphStyle('MBtn', fontName='Helvetica-Bold', fontSize=6.8, leading=8.8, textColor=c_primary)),
            Paragraph(b[1], ParagraphStyle('MLoc', fontName='Helvetica-Bold', fontSize=6.5, leading=8.5, textColor=c_accent)),
            Paragraph(b[2], ParagraphStyle('MRole', fontName='Helvetica-Bold', fontSize=6.5, leading=8.5, textColor=c_secondary)),
            Paragraph(b[3], ParagraphStyle('MEvt', fontName='Helvetica', fontSize=6.5, leading=8.5, textColor=c_text)),
            Paragraph(b[4], ParagraphStyle('MTrig', fontName='Helvetica', fontSize=6.8, leading=8.8, textColor=c_text))
        ])

    m_table = Table(master_btn_table_data, colWidths=[105, 95, 60, 45, 225])
    m_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light])
    ]))
    story.append(m_table)
    story.append(Spacer(1, 12))

    # Sign-off block
    story.append(KeepTogether([
        HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=4, spaceAfter=8),
        Paragraph("Document Certification & Quality Sign-Off", h2_style),
        Paragraph(
            "This document constitutes the definitive operational specification for the FinRegTech ShipYard platform (v2.4.0-Production). "
            "All functional screens, role boundaries, modal workflows, and interactive controls have been rigorously evaluated against the frontend codebase. "
            "Defects DEF-01 through DEF-13 (excluding backend database DEF-05) have been verified as fully resolved and committed to branch <code>feature/harshini-frontend</code>.<br/><br/>"
            "<b>Prepared By:</b> Harshini (Frontend Lead)<br/>"
            "<b>Reviewed By:</b> FinRegTech Quality Assurance & Regulatory Architecture Guild<br/>"
            "<b>Output Location:</b> <code>" + OUTPUT_FILE + "</code>",
            body_style
        )
    ]))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated: {OUTPUT_FILE}")

if __name__ == '__main__':
    build_pdf()
