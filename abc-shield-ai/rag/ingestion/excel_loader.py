"""Excel loader for raw regulatory workbooks.

Strictly reads data without modifying, overwriting, or altering the original files.
Uses openpyxl with read_only=True and data_only=True.

Supports both the new Week 4 RAG-ready workbooks and maintains 100% backward
compatibility with the legacy Week 3 workbooks.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import openpyxl

from rag.ingestion.schemas import (
    DataDictionaryEntry,
    SourceRegisterRecord,
    SourceControlRecord,
    ConflictOverlapRecord,
    RAGRuleRecord,
    OfficialVerificationRecord,
)


class ExcelWorkbookLoader:
    """Safely loads regulatory data from Excel workbooks in read-only mode."""

    CANONICAL_25_CORPUS_FILENAME = "ABC_Shield_Canonical_25_Record_Corpus.xlsx"
    CANONICAL_SOURCE_REGISTER_FILENAME = "ABC_Shield_Canonical_Source_Register.xlsx"

    PREFERRED_RAG_KNOWLEDGE_FILENAME = "ABC_Shield_RAG_Ready_Regulatory_Knowledge.xlsx"
    LEGACY_REGULATORY_RECORDS_FILENAME = "ABC_Shield_Regulatory_Records_15_with_Conflict_Overlap.xlsx"

    PREFERRED_SOURCE_REGISTER_FILENAME = "ABC_Shield_Source_Register_Reviewed (1).xlsx"
    LEGACY_SOURCE_REGISTER_FILENAME = "ABC_Shield_Source_Register (1).xlsx"

    DATA_DICTIONARY_FILENAME = "ABC shield_Data Dictionary.xlsx"

    # Compatibility aliases for legacy code/tests
    REGULATORY_RECORDS_FILENAME = PREFERRED_RAG_KNOWLEDGE_FILENAME
    SOURCE_REGISTER_FILENAME = PREFERRED_SOURCE_REGISTER_FILENAME

    def __init__(
        self,
        raw_data_dir: Path,
        regulatory_records_path: Optional[Path] = None,
        source_register_path: Optional[Path] = None,
        data_dictionary_path: Optional[Path] = None,
        conflict_overlap_path: Optional[Path] = None,
        corpus_mode: Optional[str] = None,
        target_corpus: Optional[str] = None,
    ):
        import os
        self.raw_data_dir = Path(raw_data_dir)
        try:
            from config.settings import settings
            settings_mode = getattr(settings, "rag_corpus_mode", None)
        except Exception:
            settings_mode = None
        mode = (corpus_mode or target_corpus or settings_mode or os.getenv("RAG_CORPUS_LOADER_MODE", "preferred")).strip().lower()
        self.corpus_mode = mode

        # 1. Resolve regulatory records / knowledge workbook path
        if regulatory_records_path:
            self.regulatory_records_path = Path(regulatory_records_path)
        elif mode == "canonical":
            canonical = self._find_file(self.CANONICAL_25_CORPUS_FILENAME)
            preferred = self._find_file(self.PREFERRED_RAG_KNOWLEDGE_FILENAME)
            legacy = self._find_file(self.LEGACY_REGULATORY_RECORDS_FILENAME)
            self.regulatory_records_path = canonical or preferred or legacy or (self.raw_data_dir / self.CANONICAL_25_CORPUS_FILENAME)
        else:
            preferred = self._find_file(self.PREFERRED_RAG_KNOWLEDGE_FILENAME)
            legacy = self._find_file(self.LEGACY_REGULATORY_RECORDS_FILENAME)
            canonical = self._find_file(self.CANONICAL_25_CORPUS_FILENAME)
            self.regulatory_records_path = preferred or legacy or canonical or (self.raw_data_dir / self.PREFERRED_RAG_KNOWLEDGE_FILENAME)

        self.rag_knowledge_path = self.regulatory_records_path

        # 2. Resolve source register workbook path
        if source_register_path:
            self.source_register_path = Path(source_register_path)
        elif mode == "canonical":
            canonical = self._find_file(self.CANONICAL_SOURCE_REGISTER_FILENAME)
            preferred = self._find_file(self.PREFERRED_SOURCE_REGISTER_FILENAME)
            legacy = self._find_file(self.LEGACY_SOURCE_REGISTER_FILENAME)
            self.source_register_path = canonical or preferred or legacy or (self.raw_data_dir / self.CANONICAL_SOURCE_REGISTER_FILENAME)
        else:
            preferred = self._find_file(self.PREFERRED_SOURCE_REGISTER_FILENAME)
            legacy = self._find_file(self.LEGACY_SOURCE_REGISTER_FILENAME)
            canonical = self._find_file(self.CANONICAL_SOURCE_REGISTER_FILENAME)
            self.source_register_path = preferred or legacy or canonical or (self.raw_data_dir / self.PREFERRED_SOURCE_REGISTER_FILENAME)

        # 3. Resolve data dictionary workbook path
        if data_dictionary_path:
            self.data_dictionary_path = Path(data_dictionary_path)
        else:
            dd = self._find_file(self.DATA_DICTIONARY_FILENAME)
            self.data_dictionary_path = dd if dd else (self.raw_data_dir / self.DATA_DICTIONARY_FILENAME)

        # 4. Deterministically identify verified conflict/overlap source workbook
        if conflict_overlap_path:
            self.conflict_overlap_path = Path(conflict_overlap_path)
        else:
            verified_knowledge = self._find_file(self.PREFERRED_RAG_KNOWLEDGE_FILENAME)
            verified_legacy = self._find_file(self.LEGACY_REGULATORY_RECORDS_FILENAME)
            if not verified_knowledge and not verified_legacy:
                default_raw = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
                if (default_raw / self.PREFERRED_RAG_KNOWLEDGE_FILENAME).exists():
                    verified_knowledge = default_raw / self.PREFERRED_RAG_KNOWLEDGE_FILENAME
                elif (default_raw / self.LEGACY_REGULATORY_RECORDS_FILENAME).exists():
                    verified_legacy = default_raw / self.LEGACY_REGULATORY_RECORDS_FILENAME

            self.conflict_overlap_path = verified_knowledge or verified_legacy

    def _find_file(self, filename: str) -> Optional[Path]:
        """Find a file directly in raw_data_dir or its immediate subdirectories."""
        if not self.raw_data_dir.exists():
            return None
        direct = self.raw_data_dir / filename
        if direct.exists():
            return direct
        # Also inspect immediate child subdirectories (e.g. Regulatory_Research/, Source_Register/, Data_Dictionary/)
        if self.raw_data_dir.is_dir():
            try:
                for sub in self.raw_data_dir.iterdir():
                    if sub.is_dir():
                        cand = sub / filename
                        if cand.exists():
                            return cand
            except (OSError, PermissionError):
                pass
        return None

    def _clean_cell_value(self, val: Any) -> Any:
        """Strip trailing spaces and normalize empty dashes/unestablished markers."""
        if val is None:
            return None
        if isinstance(val, str):
            val_clean = val.strip()
            # If the cell is an em-dash, en-dash, hyphen, or empty string, treat it as None
            if val_clean in ("", "—", "–", "-"):
                return None
            return val_clean
        return str(val)

    def _read_sheet_rows(self, filepath: Path, sheet_name: str) -> List[Dict[str, Any]]:
        """Read rows from a worksheet into a list of dictionaries with cleaned values."""
        if not filepath.exists():
            raise FileNotFoundError(f"Required Excel file not found: {filepath}")

        # Always open in read-only mode to prevent accidental writes
        wb = openpyxl.load_workbook(filepath, data_only=True, read_only=True)
        try:
            if sheet_name not in wb.sheetnames:
                raise ValueError(f"Sheet '{sheet_name}' not found in {filepath.name}. Available: {wb.sheetnames}")
            
            sheet = wb[sheet_name]
            rows = list(sheet.iter_rows(values_only=True))
            if not rows:
                return []

            raw_headers = [str(c).strip() if c is not None else f"col_{i}" for i, c in enumerate(rows[0])]
            
            records = []
            for r in rows[1:]:
                # Ignore empty rows
                if not any(c is not None and str(c).strip() != "" for c in r):
                    continue
                row_dict = {}
                for idx, header in enumerate(raw_headers):
                    val = r[idx] if idx < len(r) else None
                    row_dict[header] = self._clean_cell_value(val)
                records.append(row_dict)
            return records
        finally:
            wb.close()

    def get_sheet_names(self, filepath: Path) -> List[str]:
        """Inspect sheet names in a workbook."""
        wb = openpyxl.load_workbook(filepath, data_only=True, read_only=True)
        names = list(wb.sheetnames)
        wb.close()
        return names

    def load_data_dictionary(self) -> List[DataDictionaryEntry]:
        """Load fields from ABC shield_Data Dictionary.xlsx."""
        available_sheets = self.get_sheet_names(self.data_dictionary_path)
        if "Data_Dictionary" in available_sheets:
            sheet_name = "Data_Dictionary"
        elif "Sheet1" in available_sheets:
            sheet_name = "Sheet1"
        else:
            raise ValueError(
                f"Data Dictionary workbook '{self.data_dictionary_path.name}' does not contain "
                f"expected sheet ('Data_Dictionary' or 'Sheet1'). Available: {available_sheets}"
            )
        rows = self._read_sheet_rows(self.data_dictionary_path, sheet_name)
        entries = []
        for r in rows:
            entry = DataDictionaryEntry(
                field_name=r.get("Field Name", ""),
                description=r.get("Description", ""),
                example=r.get("Example"),
                required=str(r.get("Required?", "")).strip().lower() in ("yes", "true", "1")
            )
            entries.append(entry)
        return entries

    def load_source_register(self) -> List[SourceRegisterRecord]:
        """Load sources from reviewed Source Register, canonical Source Register, or legacy Source Register."""
        rows = self._read_sheet_rows(self.source_register_path, "Source Register")
        sources = []
        for r in rows:
            # Map canonical or reviewed relevance and QA note fields without fabricating
            abc_shield_relevance = r.get("ABC Shield Relevance / In-Scope Rationale") or r.get("Programme Decision / Scope Note")
            source_qa_note = r.get("Source Verification / QA Note") or r.get("Reconciliation_Note")

            raw_count = r.get("Corpus_Record_Count")
            corpus_record_count = None
            if raw_count is not None:
                try:
                    corpus_record_count = int(raw_count)
                except (ValueError, TypeError):
                    pass

            source = SourceRegisterRecord(
                source_id=r.get("Source ID") or "",
                source_name=r.get("Source Name") or "",
                issuing_authority=r.get("Issuing Authority") or "",
                jurisdiction=r.get("Jurisdiction") or "",
                source_type=r.get("Source Type") or "",
                authority_level=r.get("Authority Level") or "",
                publication_effective_date=r.get("Publication/Effective Date"),
                version_last_updated=r.get("Version/Last Updated"),
                official_link_reference=r.get("Official Link/Reference"),
                topic=r.get("Topic"),
                status=r.get("Status") or "Candidate - Awaiting Approval",
                approval_validator=r.get("Approval/Validator"),
                notes_limitations=r.get("Notes/Limitations"),
                # Week 4 reviewed fields (gracefully None for legacy workbooks)
                adoption_date=r.get("Adoption Date"),
                publication_date=r.get("Publication Date"),
                effective_date=r.get("Effective Date"),
                abc_shield_relevance=abc_shield_relevance,
                extraction_priority=r.get("Extraction Priority"),
                legal_regulatory_effect=r.get("Legal / Regulatory Effect (screening only)"),
                sme_decision_date_comments=r.get("SME Decision Date / Comments"),
                last_checked=r.get("Last Checked"),
                source_qa_note=source_qa_note,
                # Canonical handover fields
                regulatory_layer=r.get("Regulatory Layer"),
                corpus_status_current=r.get("Corpus_Status_Current"),
                corpus_record_count=corpus_record_count,
                reconciliation_note=r.get("Reconciliation_Note"),
            )
            sources.append(source)
        return sources

    def load_regulatory_records_raw(self) -> List[Dict[str, Any]]:
        """Load raw rows from Regulatory_Records (canonical 25), RAG_Records (Week 4), or Regulatory Records (legacy) sheet."""
        available_sheets = self.get_sheet_names(self.regulatory_records_path)
        if "Regulatory_Records" in available_sheets:
            sheet_name = "Regulatory_Records"
        elif "RAG_Records" in available_sheets:
            sheet_name = "RAG_Records"
        elif "Regulatory Records" in available_sheets:
            sheet_name = "Regulatory Records"
        else:
            raise ValueError(
                f"Neither 'Regulatory_Records', 'RAG_Records', nor 'Regulatory Records' "
                f"found in {self.regulatory_records_path.name}. Available: {available_sheets}"
            )
        return self._read_sheet_rows(self.regulatory_records_path, sheet_name)

    def load_validation_notes(self) -> List[Dict[str, Any]]:
        """Load validation notes from Validation Notes or Review Notes sheet if present."""
        available_sheets = self.get_sheet_names(self.regulatory_records_path)
        if "Validation Notes" in available_sheets:
            return self._read_sheet_rows(self.regulatory_records_path, "Validation Notes")
        
        # Check source register for Review Notes
        sr_sheets = self.get_sheet_names(self.source_register_path)
        if "Review Notes" in sr_sheets:
            return self._read_sheet_rows(self.source_register_path, "Review Notes")

        # Fallback to preferred source register or conflict workbook if available
        pref_sr = self._find_file(self.PREFERRED_SOURCE_REGISTER_FILENAME)
        if pref_sr and pref_sr.exists():
            if "Review Notes" in self.get_sheet_names(pref_sr):
                return self._read_sheet_rows(pref_sr, "Review Notes")

        if self.conflict_overlap_path and self.conflict_overlap_path.exists():
            co_sheets = self.get_sheet_names(self.conflict_overlap_path)
            if "Validation Notes" in co_sheets:
                return self._read_sheet_rows(self.conflict_overlap_path, "Validation Notes")
        return []

    def load_conflict_overlap(self, conflict_path: Optional[Path] = None) -> List[ConflictOverlapRecord]:
        """Load pre-mapped conflict and overlap records from verified Conflict_Handling or Conflict Overlap sheet.

        Strictly loads from the explicitly configured conflict path or deterministic verified source.
        Fails clearly if the verified conflict source workbook or required sheet cannot be found.
        """
        target_path = Path(conflict_path) if conflict_path else self.conflict_overlap_path
        if not target_path or not target_path.exists():
            # If still None, check if regulatory_records_path contains conflict sheets
            if self.regulatory_records_path and self.regulatory_records_path.exists():
                sheets = self.get_sheet_names(self.regulatory_records_path)
                if "Conflict_Handling" in sheets or "Conflict Overlap" in sheets:
                    target_path = self.regulatory_records_path

        if not target_path or not target_path.exists():
            raise FileNotFoundError(
                f"Verified conflict/overlap source workbook not found. "
                f"Expected verified source containing 'Conflict_Handling' or 'Conflict Overlap' sheet."
            )

        available_sheets = self.get_sheet_names(target_path)
        if "Conflict_Handling" in available_sheets:
            sheet_name = "Conflict_Handling"
        elif "Conflict Overlap" in available_sheets:
            sheet_name = "Conflict Overlap"
        else:
            raise ValueError(
                f"Verified conflict source workbook '{target_path.name}' does not contain "
                f"required conflict sheet ('Conflict_Handling' or 'Conflict Overlap'). Available sheets: {available_sheets}"
            )

        rows = self._read_sheet_rows(target_path, sheet_name)
        conflicts = []
        for r in rows:
            record = ConflictOverlapRecord(
                conflict_id=r.get("Conflict_ID") or "",
                topic=r.get("Topic") or "",
                source_id_1=r.get("Source_ID_1") or "",
                source_1=r.get("Source_1") or "",
                source_id_2=r.get("Source_ID_2") or "",
                source_2=r.get("Source_2") or "",
                relationship=r.get("Relationship") or "",
                requirement_comparison=r.get("Requirement_Comparison"),
                scope_difference=r.get("Scope_Difference"),
                authority_difference=r.get("Authority_Difference"),
                version_effective_date_difference=r.get("Version_Effective_Date_Difference"),
                conflict_status=r.get("Conflict_Status") or "No direct conflict identified",
                rag_use=r.get("RAG_Use")
            )
            conflicts.append(record)
        return conflicts

    def load_rag_rules(self) -> List[RAGRuleRecord]:
        """Load RAG rules from RAG_Rules sheet if present, with fallback to verified knowledge workbook."""
        target_path = self.regulatory_records_path
        available_sheets = self.get_sheet_names(target_path)
        if "RAG_Rules" not in available_sheets:
            pref = self._find_file(self.PREFERRED_RAG_KNOWLEDGE_FILENAME)
            if pref and "RAG_Rules" in self.get_sheet_names(pref):
                target_path = pref
            else:
                return []

        rows = self._read_sheet_rows(target_path, "RAG_Rules")
        rules = []
        for r in rows:
            rule = RAGRuleRecord(
                rule_id=r.get("Rule_ID") or "",
                rule_type=r.get("Rule_Type") or "",
                rag_rule=r.get("RAG_Rule") or "",
                implementation_note=r.get("Implementation_Note"),
            )
            rules.append(rule)

        # If rules exist but rag_rule text is empty (e.g. from canonical summary sheet), fallback to preferred workbook
        if rules and not any(r.rag_rule for r in rules):
            pref = self._find_file(self.PREFERRED_RAG_KNOWLEDGE_FILENAME)
            if pref and pref != target_path and "RAG_Rules" in self.get_sheet_names(pref):
                pref_rows = self._read_sheet_rows(pref, "RAG_Rules")
                return [
                    RAGRuleRecord(
                        rule_id=r.get("Rule_ID") or "",
                        rule_type=r.get("Rule_Type") or "",
                        rag_rule=r.get("RAG_Rule") or "",
                        implementation_note=r.get("Implementation_Note"),
                    )
                    for r in pref_rows
                ]
        return rules

    def load_official_verification(self) -> List[OfficialVerificationRecord]:
        """Load official verification notes from Official_Verification sheet if present, with fallback."""
        target_path = self.regulatory_records_path
        available_sheets = self.get_sheet_names(target_path)
        if "Official_Verification" not in available_sheets:
            pref = self._find_file(self.PREFERRED_RAG_KNOWLEDGE_FILENAME)
            if pref and "Official_Verification" in self.get_sheet_names(pref):
                target_path = pref
            else:
                return []

        rows = self._read_sheet_rows(target_path, "Official_Verification")
        verifications = []
        for r in rows:
            ver = OfficialVerificationRecord(
                source_id=r.get("Source_ID") or "",
                source_name=r.get("Source_Name") or "",
                official_origin=r.get("Official_Origin"),
                verification=r.get("Verification") or "Unverified",
                official_url=r.get("Official_URL"),
                verification_note=r.get("Verification_Note"),
            )
            verifications.append(ver)
        return verifications

    def load_source_control(self) -> List[SourceControlRecord]:
        """Load source control and approval gating records from Source_Control sheet if present."""
        target_path = self.regulatory_records_path
        available_sheets = self.get_sheet_names(target_path)
        if "Source_Control" not in available_sheets:
            pref = self._find_file(self.PREFERRED_RAG_KNOWLEDGE_FILENAME)
            if pref and "Source_Control" in self.get_sheet_names(pref):
                target_path = pref
            else:
                return []

        rows = self._read_sheet_rows(target_path, "Source_Control")
        records = []
        for r in rows:
            rec = SourceControlRecord(
                source_id=r.get("Source ID") or r.get("Source_ID") or "",
                source_name=r.get("Source Name") or r.get("Source_Name") or "",
                jurisdiction=r.get("Jurisdiction") or "",
                source_type=r.get("Source Type") or r.get("Source_Type") or "",
                authority_level=r.get("Authority Level") or r.get("Authority_Level") or "",
                topic=r.get("Topic"),
                status=r.get("Status") or r.get("Validation_Status") or r.get("Source_Status_As_Provided") or "Candidate - Awaiting Approval",
                extraction_priority=r.get("Extraction Priority") or r.get("Extraction_Priority"),
                official_link_reference=r.get("Official Link/Reference") or r.get("Official_URL"),
                abc_shield_relevance=r.get("ABC Shield Relevance / In-Scope Rationale") or r.get("Programme_Decision_Scope_Note"),
                legal_regulatory_effect=r.get("Legal / Regulatory Effect (screening only)"),
                notes_limitations=r.get("Notes/Limitations") or r.get("Notes_Limitations"),
                rag_use=r.get("RAG_Use"),
                approval_gate=r.get("Approval_Gate") or r.get("Validation_Status") or r.get("Status") or "Candidate - Awaiting Approval",
            )
            records.append(rec)
        return records
