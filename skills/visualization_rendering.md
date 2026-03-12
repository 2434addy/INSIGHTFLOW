# Skill: Visualization Rendering

## Overview

Provides chart type selection logic, Recharts configuration generation, and server-side chart image rendering for PDF reports. Translates raw data into visual formats with consistent design tokens.

## Skill Tier: Atomic

Visualization logic used by the Visualization Agent and Report Writer Agent.

## Capabilities

### 1. Chart Type Selection

```python
class ChartTypeSelector:
    RULES = [
        # (data_pattern, chart_type, priority)
        ("single_metric_over_time", "line", 1),
        ("multiple_metrics_over_time", "composed_line_area", 1),
        ("comparison_2_to_5_categories", "bar_horizontal", 2),
        ("part_of_whole", "donut", 2),
        ("ranking_ordered", "bar_horizontal", 1),
        ("single_kpi_snapshot", "kpi_card", 1),
        ("distribution", "histogram", 3),
        ("timeseries_with_anomalies", "line_with_markers", 1),
    ]

    def select(self, data_descriptor: DataDescriptor) -> str:
        """
        Select optimal chart type based on data characteristics.

        Considers:
        - Number of data points (time series length)
        - Number of series/categories
        - Data type (temporal, categorical, continuous)
        - Output format (web interactive vs. PDF static)
        """
        if data_descriptor.is_temporal and data_descriptor.series_count == 1:
            return "line"
        elif data_descriptor.is_temporal and data_descriptor.series_count <= 3:
            return "composed"  # Line + Area combo
        elif data_descriptor.is_categorical and data_descriptor.category_count <= 5:
            return "bar_horizontal"
        elif data_descriptor.is_part_of_whole:
            return "donut"
        elif data_descriptor.is_ranking:
            return "bar_horizontal"
        else:
            return "table"  # Fallback for complex data
```

### 2. Recharts Config Generation

```python
class RechartsConfigBuilder:
    def build_line_chart(
        self,
        data: list[dict],
        x_key: str,
        y_keys: list[dict],  # [{"key": "spend", "label": "Spend", "color": "#2563EB"}]
        anomaly_markers: list[dict] = None,
    ) -> dict:
        """Generate Recharts-compatible configuration."""
        return {
            "type": "ResponsiveContainer",
            "props": {"width": "100%", "height": 400},
            "children": {
                "type": "ComposedChart",
                "props": {"data": data, "margin": {"top": 20, "right": 30, "left": 20, "bottom": 20}},
                "children": [
                    {"type": "CartesianGrid", "props": {"strokeDasharray": "3 3", "stroke": "#E5E7EB"}},
                    {"type": "XAxis", "props": {"dataKey": x_key, "tick": {"fontSize": 12}}},
                    *[self._build_y_axis(y, i) for i, y in enumerate(y_keys)],
                    *[self._build_series(y) for y in y_keys],
                    {"type": "Tooltip", "props": {"formatter": "currency_or_number"}},
                    {"type": "Legend", "props": {"verticalAlign": "bottom"}},
                    *(self._build_anomaly_markers(anomaly_markers) if anomaly_markers else []),
                ],
            },
        }

    def build_donut_chart(
        self,
        data: list[dict],  # [{"name": "Meta Ads", "value": 7800, "color": "#1877F2"}]
        center_label: dict = None,
    ) -> dict:
        return {
            "type": "ResponsiveContainer",
            "props": {"width": "100%", "height": 400},
            "children": {
                "type": "PieChart",
                "children": [
                    {
                        "type": "Pie",
                        "props": {
                            "data": data,
                            "dataKey": "value",
                            "nameKey": "name",
                            "innerRadius": "60%",
                            "outerRadius": "80%",
                            "paddingAngle": 2,
                        },
                    },
                    {"type": "Tooltip"},
                    {"type": "Legend", "props": {"verticalAlign": "bottom"}},
                ],
            },
        }

    def build_kpi_card(
        self,
        label: str,
        value: str,
        trend: float,
        direction: str,
        sparkline_data: list[float] = None,
    ) -> dict:
        return {
            "type": "kpi_card",
            "props": {
                "label": label,
                "value": value,
                "trend": trend,
                "trend_direction": direction,
                "trend_color": "#16A34A" if direction == "up" else "#DC2626",
                "sparkline": sparkline_data,
            },
        }
```

### 3. Server-Side Rendering

```python
class ChartRenderer:
    async def render_to_image(
        self,
        chart_config: dict,
        width: int = 800,
        height: int = 400,
        scale: int = 2,
        format: str = "png",
    ) -> bytes:
        """
        Render chart to PNG image using headless browser.

        Pipeline:
        1. Generate minimal HTML page with React + Recharts
        2. Inject chart_config as props
        3. Open in Puppeteer/Playwright
        4. Wait for render complete
        5. Screenshot at specified dimensions
        6. Return image bytes
        """
        html = self._generate_chart_html(chart_config)
        async with self._get_browser() as browser:
            page = await browser.new_page()
            await page.set_viewport_size(
                {"width": width * scale, "height": height * scale}
            )
            await page.set_content(html)
            await page.wait_for_selector(".recharts-wrapper")
            screenshot = await page.screenshot(type=format)
        return screenshot
```

### 4. Design Token Application

```python
CHART_DESIGN_TOKENS = {
    "colors": {
        "series": ["#2563EB", "#16A34A", "#D97706", "#DC2626", "#8B5CF6", "#06B6D4"],
        "platforms": {
            "meta_ads": "#1877F2",
            "google_ads": "#4285F4",
            "ga4": "#E37400",
            "shopify": "#96BF48",
        },
        "sentiment": {
            "positive": "#16A34A",
            "negative": "#DC2626",
            "neutral": "#6B7280",
        },
        "grid": "#E5E7EB",
        "background": "#FFFFFF",
    },
    "typography": {
        "axis": {"fontSize": 12, "fontFamily": "Inter", "fill": "#6B7280"},
        "label": {"fontSize": 14, "fontFamily": "Inter", "fontWeight": 600, "fill": "#111827"},
        "tooltip": {"fontSize": 13, "fontFamily": "Inter"},
    },
    "layout": {
        "margin": {"top": 20, "right": 30, "bottom": 20, "left": 30},
        "legend_position": "bottom",
    },
}
```

## Used By

| Agent | Purpose |
|-------|---------|
| Visualization Agent | Chart generation and rendering |
| Report Writer Agent | Chart embedding in reports |
