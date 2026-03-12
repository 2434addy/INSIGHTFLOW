# Skill: Data Quality Validation

## Overview

Provides a comprehensive data quality validation framework for marketing metrics at every stage of the pipeline — from raw ingestion through normalization to AI output verification. Ensures data integrity across the entire system.

## Skill Tier: Atomic

Foundational validation logic used across multiple agents.

## Validation Stages

### Stage 1: Raw Data Validation (Post-Ingestion)

```python
class RawDataValidator:
    def validate(self, records: list[dict], platform: str) -> ValidationResult:
        """Validate raw API response records before normalization."""
        errors = []
        warnings = []

        for i, record in enumerate(records):
            # Required fields present
            required = PLATFORM_REQUIRED_FIELDS[platform]
            missing = [f for f in required if f not in record or record[f] is None]
            if missing:
                errors.append(ValidationIssue(
                    level="error", record_index=i,
                    message=f"Missing required fields: {missing}",
                ))

            # Non-negative metrics
            for field in NUMERIC_FIELDS.get(platform, []):
                if field in record and record[field] is not None:
                    if float(record[field]) < 0:
                        errors.append(ValidationIssue(
                            level="error", record_index=i,
                            message=f"Negative value for {field}: {record[field]}",
                        ))

            # Date validity
            date_field = PLATFORM_DATE_FIELD[platform]
            if date_field in record:
                try:
                    parse_date(record[date_field])
                except ValueError:
                    errors.append(ValidationIssue(
                        level="error", record_index=i,
                        message=f"Invalid date: {record[date_field]}",
                    ))

        return ValidationResult(
            total_records=len(records),
            valid_records=len(records) - len(errors),
            errors=errors,
            warnings=warnings,
        )
```

### Stage 2: Normalized Data Validation (Post-Normalization)

```python
class NormalizedDataValidator:
    def validate(self, record: MetricRecord) -> list[ValidationIssue]:
        """Validate a normalized metric record."""
        issues = []

        # Non-negative core metrics
        for field in ["spend", "impressions", "clicks", "conversions", "conversion_value"]:
            value = getattr(record, field, None)
            if value is not None and value < 0:
                issues.append(ValidationIssue("error", f"Negative {field}: {value}"))

        # Cross-field consistency
        if record.clicks and record.impressions:
            if record.clicks > record.impressions:
                issues.append(ValidationIssue("warning", "Clicks exceed impressions"))

        if record.conversions and record.clicks:
            if record.conversions > record.clicks:
                issues.append(ValidationIssue("warning", "Conversions exceed clicks"))

        # Derived metric ranges
        if record.ctr is not None and (record.ctr < 0 or record.ctr > 100):
            issues.append(ValidationIssue("error", f"CTR out of range: {record.ctr}%"))

        if record.roas is not None and record.roas > 1000:
            issues.append(ValidationIssue("warning", f"Unusually high ROAS: {record.roas}x"))

        if record.cpa is not None and record.cpa > 10000:
            issues.append(ValidationIssue("warning", f"Unusually high CPA: ${record.cpa}"))

        return issues
```

### Stage 3: Analysis Validation (Post-Analysis)

```python
class AnalysisValidator:
    def validate(self, analysis: AnalysisOutput) -> list[ValidationIssue]:
        """Validate analysis output for consistency."""
        issues = []

        # Comparison math check
        comp = analysis.summary.comparison
        curr = analysis.summary.current_period
        prev = analysis.summary.previous_period

        expected_spend_pct = ((curr.spend - prev.spend) / prev.spend * 100) if prev.spend else None
        if expected_spend_pct is not None and comp.spend_change_pct is not None:
            if abs(expected_spend_pct - comp.spend_change_pct) > 0.1:
                issues.append(ValidationIssue(
                    "error",
                    f"Spend change % mismatch: computed {expected_spend_pct:.1f}%, "
                    f"reported {comp.spend_change_pct:.1f}%"
                ))

        # Trend consistency
        for trend in analysis.trends:
            if trend.direction == "increasing" and trend.slope < 0:
                issues.append(ValidationIssue(
                    "error",
                    f"Trend direction/slope mismatch for {trend.metric}"
                ))

        return issues
```

### Stage 4: AI Output Validation (Post-Generation)

```python
class AIOutputValidator:
    def validate(
        self, ai_text: str, source_data: dict
    ) -> list[ValidationIssue]:
        """
        Validate AI-generated text against source data.
        Ensures no hallucinated numbers or false claims.
        """
        issues = []

        # Extract all numbers from text
        numbers = extract_numbers_with_context(ai_text)

        for num in numbers:
            source_value = lookup_in_source(num.context, source_data)
            if source_value is not None:
                tolerance = get_tolerance(num.type)  # $ → 0.01, % → 0.1, count → 0
                if abs(num.value - source_value) > tolerance:
                    issues.append(ValidationIssue(
                        "error",
                        f"Number mismatch: AI said {num.value}, source has {source_value}",
                        context=num.surrounding_text,
                    ))

        # Check directional claims
        directional_claims = extract_directional_claims(ai_text)
        for claim in directional_claims:
            if not verify_direction(claim, source_data):
                issues.append(ValidationIssue(
                    "error",
                    f"False directional claim: '{claim.text}'",
                ))

        return issues
```

## Validation Issue Schema

```python
@dataclass
class ValidationIssue:
    level: str          # "error" | "warning" | "info"
    message: str
    record_index: int = None
    field: str = None
    context: str = None
    auto_fixable: bool = False

@dataclass
class ValidationResult:
    total_records: int
    valid_records: int
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def error_rate(self) -> float:
        return len(self.errors) / self.total_records if self.total_records > 0 else 0
```

## Used By

| Agent | Purpose |
|-------|---------|
| Data Ingestion Agent | Raw data validation |
| Data Normalization Agent | Normalized record validation |
| Data Analysis Agent | Analysis output verification |
| Validation Agent | AI output fact-checking |
