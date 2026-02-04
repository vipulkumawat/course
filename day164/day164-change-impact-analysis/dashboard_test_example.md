# Dashboard Test Examples

## Example 1: High Risk - Schema Change (Recommended for Testing)

**Change Type:** Schema Change
**Target Service:** elasticsearch-cluster
**Change Description:** Add new required field 'user_segment' to log schema, breaking backward compatibility

**Expected Results:**
- Risk Score: High (70-100)
- Blast Radius: Multiple services (5+)
- Critical Path: YES
- Multiple recommendations

---

## Example 2: Medium Risk - API Modification

**Change Type:** API Modification
**Target Service:** log-enrichment
**Change Description:** Add new enrichment endpoint /api/v2/enrich with additional metadata fields

**Expected Results:**
- Risk Score: Medium (40-69)
- Blast Radius: 5-10 services
- Critical Path: YES
- Recommendations for feature flag deployment

---

## Example 3: Low Risk - Configuration Change

**Change Type:** Configuration Change
**Target Service:** reporting-service
**Change Description:** Update report refresh interval from 5 minutes to 10 minutes

**Expected Results:**
- Risk Score: Low (0-39)
- Blast Radius: 1 service
- Critical Path: NO
- Standard deployment recommendations

---

## Example 4: Critical Infrastructure Change

**Change Type:** Infrastructure Update
**Target Service:** rabbitmq-cluster
**Change Description:** Upgrade RabbitMQ from version 3.8 to 4.0 (major version upgrade)

**Expected Results:**
- Risk Score: High (70-100)
- Blast Radius: 8-10 services
- Critical Path: YES
- Maintenance window recommendations

---

## Quick Test Steps:

1. Open dashboard: http://localhost:3000
2. Select "Schema Change" from Change Type dropdown
3. Select "elasticsearch-cluster" from Target Service dropdown
4. Enter: "Add new required field 'user_segment' to log schema"
5. Click "Analyze Impact"
6. Verify all metrics display non-zero values:
   - Risk Score should show a number (not 0 or -)
   - Blast Radius should show "X services" (not 0)
   - Critical Path should show YES or NO (not -)
   - Affected Services list should show service tags
   - Recommendations should be displayed
