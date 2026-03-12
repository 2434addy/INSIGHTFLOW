"""
Data Quality Validation skill — validates data at every pipeline stage.

Checks raw data integrity, normalized record consistency, analysis output
correctness, and AI-generated content accuracy.
"""

from __future__ import annotations

import re

from app.pipeline.schemas import (
    MetricRecord,
    ValidationIssue,
    ValidationResult,
)


class RawDataValidator:
    """Validates raw metric records before further processing."""

    REQUIRED_FIELDS = ["campaign_id", "platform", "date", "organization_id"]
    NON_NEGATIVE_FIELDS = ["impressions", "clicks", "spend", "conversions", "conversion_value"]

    def validate(self, records: list[MetricRecord]) -> ValidationResult:
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []

        for i, record in enumerate(records):
            # Check required fields
            for field in self.REQUIRED_FIELDS:
                val = getattr(record, field, None)
                if val is None:
                    errors.append(ValidationIssue(
                        level="error",
                        record_index=i,
                        field=field,
                        message=f"Missing required field: {field}",
                    ))

            # Non-negative metrics
            for field in self.NON_NEGATIVE_FIELDS:
                val = getattr(record, field, None)
                if val is not None and val < 0:
                    errors.append(ValidationIssue(
                        level="error",
                        record_index=i,
                        field=field,
                        message=f"Negative value for {field}: {val}",
                    ))

            # Cross-field consistency
            if record.clicks > record.impressions and record.impressions > 0:
                warnings.append(ValidationIssue(
                    level="warning",
                    record_index=i,
                    message="Clicks exceed impressions",
                ))

            if record.conversions > record.clicks and record.clicks > 0:
                warnings.append(ValidationIssue(
                    level="warning",
                    record_index=i,
                    message="Conversions exceed clicks",
                ))

        return ValidationResult(
            total_records=len(records),
            valid_records=len(records) - len(errors),
            errors=errors,
            warnings=warnings,
        )


class NormalizedDataValidator:
    """Validates records after derived metrics have been computed."""

    def validate(self, records: list[MetricRecord]) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for i, record in enumerate(records):
            if record.ctr is not None and (record.ctr < 0 or record.ctr > 100):
                issues.append(ValidationIssue(
                    level="error",
                    record_index=i,
                    field="ctr",
                    message=f"CTR out of range: {record.ctr:.2f}%",
                ))

            if record.roas is not None and record.roas > 1000:
                issues.append(ValidationIssue(
                    level="warning",
                    record_index=i,
                    field="roas",
                    message=f"Unusually high ROAS: {record.roas:.2f}x",
                ))

            if record.cpa is not None and record.cpa > 10000:
                issues.append(ValidationIssue(
                    level="warning",
                    record_index=i,
                    field="cpa",
                    message=f"Unusually high CPA: ${record.cpa:.2f}",
                ))

        return issues


class AnalysisValidator:
    """Validates analysis outputs for internal consistency."""

    def validate_comparison(
        self,
        current_spend: float,
        previous_spend: float,
        reported_change_pct: float | None,
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if previous_spend and reported_change_pct is not None:
            expected = ((current_spend - previous_spend) / previous_spend) * 100
            if abs(expected - reported_change_pct) > 0.1:
                issues.append(ValidationIssue(
                    level="error",
                    message=(
                        f"Spend change % mismatch: computed {expected:.1f}%, "
                        f"reported {reported_change_pct:.1f}%"
                    ),
                ))
        return issues

    def validate_trend_consistency(
        self,
        direction: str,
        slope: float,
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        if direction == "increasing" and slope < 0:
            issues.append(ValidationIssue(
                level="error",
                message="Trend direction/slope mismatch: increasing but negative slope",
            ))
        if direction == "decreasing" and slope > 0:
            issues.append(ValidationIssue(
                level="error",
                message="Trend direction/slope mismatch: decreasing but positive slope",
            ))
        return issues


class AIOutputValidator:
    """Validates AI-generated text against source data to catch hallucinations."""

    def validate(
        self,
        ai_text: str,
        source_data: dict,
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        # Extract numbers from AI text
        numbers = self._extract_numbers(ai_text)

        for num_str, value in numbers:
            # Try to find a matching value in source data
            if not self._value_exists_in_source(value, source_data):
                issues.append(ValidationIssue(
                    level="warning",
                    message=f"Number {num_str} in AI text not found in source data",
                ))

        return issues

    @staticmethod
    def _extract_numbers(text: str) -> list[tuple[str, float]]:
        """Extract numeric values from text with context."""
        results: list[tuple[str, float]] = []
        # Match currency, percentage, and plain numbers
        patterns = [
            r'\$[\d,]+\.?\d*',      # $1,234.56
            r'[\d,]+\.?\d*%',       # 12.5%
            r'[\d,]+\.?\d*x',       # 4.5x
            r'\b\d+\.?\d*\b',       # plain numbers
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                num_str = match.group()
                cleaned = num_str.replace('$', '').replace('%', '').replace('x', '').replace(',', '')
                try:
                    results.append((num_str, float(cleaned)))
                except ValueError:
                    continue
        return results

    @staticmethod
    def _value_exists_in_source(
        value: float,
        source: dict,
        tolerance: float = 0.5,
    ) -> bool:
        """Recursively search source data for a matching value."""
        for v in _flatten_values(source):
            if isinstance(v, (int, float)) and abs(v - value) <= tolerance:
                return True
        return False


def _flatten_values(data: dict | list | float | int | str | None) -> list:
    """Recursively extract all numeric values from nested data."""
    results: list = []
    if isinstance(data, dict):
        for v in data.values():
            results.extend(_flatten_values(v))
    elif isinstance(data, list):
        for item in data:
            results.extend(_flatten_values(item))
    elif isinstance(data, (int, float)):
        results.append(data)
    return results
