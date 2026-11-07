# ABC Shield — Finalized Working Handover Package

## Start here
1. Open `Handover/ABC_Shield_Master_Handover_Tracker.xlsx`.
2. Use `Source_Register/ABC_Shield_Canonical_Source_Register.xlsx` as the single source register. Its source status values are preserved from the reviewed TTVCOM source register supplied by Sir.
3. Use `Regulatory_Research/ABC_Shield_Canonical_25_Record_Corpus.xlsx` as the current 25-record working corpus.
4. Use `RAG Research/ABC_Shield_Canonical_RAG_Test_Pack.xlsx` for the 15 prepared RAG tests.
5. Use `Data_Dictionary/ABC shield_Data Dictionary.xlsx` for the corpus field definitions.

## Source and validation statuses
- The canonical source register preserves Sir's statuses exactly. Core extraction sources are `Approved for Extraction - Pending SME Validation`; approved supporting sources are marked separately; deferred/monitor sources remain deferred/monitor.
- The corpus uses the shorter extraction status `Approved for Extraction` for its active records, with a separate `Validation_Status = Pending SME Validation`. This is a deliberate field separation, not an assertion of legal approval.
- All 25 active corpus records remain `Pending SME Validation`.
- `Approved for Extraction` does not mean SME validation, legal applicability review, or production approval is complete.

## Active corpus
The 25 records currently use Source IDs UK-01, UK-02, UK-03, EU-01 and UK-09. Other sources in Sir's register remain listed for governance/traceability but are not silently added to the active corpus. Deferred sources are not active RAG knowledge records.

## Scope and legal limitations
- Scope remains UK + EU-level Anti-Bribery & Corruption.
- FCA material relies on the assumption that ABC Shield is modelled as an FCA-regulated UK financial-services firm.
- EU-level Directive content must not be treated as complete national law coverage. National transposition and firm-level applicability need jurisdiction-specific review.
- Exact extracts and pinpoint references should be checked against the official source by the authorised reviewer before production use.

## RAG test status
- 15 test cases are prepared.
- They have not been executed against a live RAG application in this package. Execution status is `Not Run` / blank until the team records actual observations.
- No claim is made that backend/API integration or frontend citation display has been tested.

## Handover exit criteria
- Authorised SME reviews source universe, extracts, applicability notes and validation statuses.
- Backend schema mapping is agreed.
- 15 RAG tests are executed in the integrated environment, with defects and retests recorded.
- Frontend citation display is verified.
