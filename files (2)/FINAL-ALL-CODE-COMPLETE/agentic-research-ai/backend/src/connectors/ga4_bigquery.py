"""
Complete GA4 BigQuery Connector - Production Ready
==================================================
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account

from backend.src.core.config import get_settings


settings = get_settings()


class GA4BigQueryConnector:
    """Production GA4 BigQuery connector with full functionality."""
    
    def __init__(self):
        self.project_id = settings.ga4_project_id
        self.dataset = settings.ga4_dataset
        
        # Initialize BigQuery client
        if settings.google_credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                settings.google_credentials_path
            )
            self.client = bigquery.Client(
                credentials=credentials,
                project=self.project_id
            )
        else:
            self.client = bigquery.Client(project=self.project_id)
    
    async def query_funnel(
        self,
        steps: List[str],
        date_range: Tuple[str, str],
        segment_by: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build and execute funnel query.
        
        Args:
            steps: Event names in order
            date_range: (start_date, end_date) as "YYYY-MM-DD"
            segment_by: Fields to segment by (e.g., ["device.category"])
            filters: Additional WHERE conditions
            
        Returns:
            Complete funnel analysis with drop-off points
        """
        # Build SQL query
        sql = self._build_funnel_sql(steps, date_range, segment_by, filters)
        
        # Execute query
        job = self.client.query(sql)
        results = job.result()
        
        # Process results
        funnel_data = []
        for row in results:
            funnel_data.append({
                "step": row.step,
                "event_name": row.event_name,
                "users": row.user_count,
                "conversion_rate": float(row.conversion_rate),
                "drop_off_rate": float(row.drop_off_rate) if row.drop_off_rate else 0,
            })
        
        # Calculate insights
        biggest_drop = self._find_biggest_drop(funnel_data)
        
        return {
            "success": True,
            "funnel_steps": funnel_data,
            "total_users": funnel_data[0]["users"] if funnel_data else 0,
            "overall_conversion": funnel_data[-1]["conversion_rate"] if funnel_data else 0,
            "biggest_drop": biggest_drop,
            "date_range": date_range,
        }
    
    def _build_funnel_sql(
        self,
        steps: List[str],
        date_range: Tuple[str, str],
        segment_by: Optional[List[str]],
        filters: Optional[Dict[str, Any]],
    ) -> str:
        """Build SQL for funnel analysis."""
        
        table_name = f"`{self.project_id}.{self.dataset}.events_*`"
        
        # Build date filter
        start_date = date_range[0].replace("-", "")
        end_date = date_range[1].replace("-", "")
        
        # Build CTEs for each step
        ctes = []
        for i, event in enumerate(steps):
            cte = f"""
            step_{i} AS (
                SELECT DISTINCT user_pseudo_id
                FROM {table_name}
                WHERE _TABLE_SUFFIX BETWEEN '{start_date}' AND '{end_date}'
                AND event_name = '{event}'
                {self._build_filters_clause(filters)}
            )
            """
            ctes.append(cte)
        
        # Build main query with LEFT JOINs
        main_query = f"""
        WITH {','.join(ctes)}
        SELECT 
            step_num,
            step_name,
            COUNT(DISTINCT user_pseudo_id) as user_count,
            COUNT(DISTINCT user_pseudo_id) / 
                FIRST_VALUE(COUNT(DISTINCT user_pseudo_id)) 
                OVER (ORDER BY step_num) as conversion_rate,
            LAG(COUNT(DISTINCT user_pseudo_id)) 
                OVER (ORDER BY step_num) as prev_count
        FROM (
        """
        
        # Union all steps
        unions = []
        for i, event in enumerate(steps):
            unions.append(f"""
                SELECT {i+1} as step_num, '{event}' as step_name, user_pseudo_id
                FROM step_{i}
            """)
        
        main_query += " UNION ALL ".join(unions)
        main_query += """
        )
        GROUP BY step_num, step_name
        ORDER BY step_num
        """
        
        return main_query
    
    def _build_filters_clause(self, filters: Optional[Dict[str, Any]]) -> str:
        """Build WHERE clause from filters."""
        if not filters:
            return ""
        
        conditions = []
        for key, value in filters.items():
            if isinstance(value, str):
                conditions.append(f"AND {key} = '{value}'")
            else:
                conditions.append(f"AND {key} = {value}")
        
        return " ".join(conditions)
    
    def _find_biggest_drop(self, funnel_data: List[Dict]) -> Dict[str, Any]:
        """Find step with biggest drop-off."""
        if len(funnel_data) < 2:
            return {}
        
        max_drop = {"drop_rate": 0}
        
        for i in range(len(funnel_data) - 1):
            current = funnel_data[i]
            next_step = funnel_data[i + 1]
            
            drop_rate = current["conversion_rate"] - next_step["conversion_rate"]
            
            if drop_rate > max_drop["drop_rate"]:
                max_drop = {
                    "from_step": i + 1,
                    "to_step": i + 2,
                    "from_event": current["event_name"],
                    "to_event": next_step["event_name"],
                    "drop_rate": drop_rate,
                    "users_lost": current["users"] - next_step["users"],
                }
        
        return max_drop
    
    async def query_cohort(
        self,
        cohort_definition: str,
        metric: str,
        periods: int,
        date_range: Tuple[str, str],
    ) -> Dict[str, Any]:
        """
        Cohort retention analysis.
        
        Args:
            cohort_definition: How to define cohorts (e.g., "first_visit_date")
            metric: What to measure ("retention", "revenue", "engagement")
            periods: Number of periods to track (e.g., 12 weeks)
            date_range: Analysis date range
            
        Returns:
            Cohort matrix and retention curves
        """
        sql = self._build_cohort_sql(cohort_definition, metric, periods, date_range)
        
        job = self.client.query(sql)
        results = job.result()
        
        # Build cohort matrix
        cohort_matrix = {}
        for row in results:
            cohort = row.cohort
            period = row.period
            value = float(row.value)
            
            if cohort not in cohort_matrix:
                cohort_matrix[cohort] = {}
            
            cohort_matrix[cohort][period] = value
        
        return {
            "success": True,
            "cohort_matrix": cohort_matrix,
            "metric": metric,
            "periods": periods,
        }
    
    def _build_cohort_sql(
        self,
        cohort_definition: str,
        metric: str,
        periods: int,
        date_range: Tuple[str, str],
    ) -> str:
        """Build SQL for cohort analysis."""
        
        table_name = f"`{self.project_id}.{self.dataset}.events_*`"
        
        start_date = date_range[0].replace("-", "")
        end_date = date_range[1].replace("-", "")
        
        # Metric calculation
        if metric == "retention":
            metric_calc = "COUNT(DISTINCT user_pseudo_id)"
        elif metric == "revenue":
            metric_calc = "SUM(event_value_in_usd)"
        else:
            metric_calc = "COUNT(*)"
        
        sql = f"""
        WITH cohorts AS (
            SELECT 
                user_pseudo_id,
                DATE_TRUNC(MIN(PARSE_DATE('%Y%m%d', event_date)), WEEK) as cohort_week
            FROM {table_name}
            WHERE _TABLE_SUFFIX BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY user_pseudo_id
        ),
        user_activity AS (
            SELECT 
                e.user_pseudo_id,
                c.cohort_week,
                DATE_TRUNC(PARSE_DATE('%Y%m%d', e.event_date), WEEK) as activity_week,
                DATE_DIFF(
                    DATE_TRUNC(PARSE_DATE('%Y%m%d', e.event_date), WEEK),
                    c.cohort_week,
                    WEEK
                ) as period
            FROM {table_name} e
            JOIN cohorts c ON e.user_pseudo_id = c.user_pseudo_id
            WHERE _TABLE_SUFFIX BETWEEN '{start_date}' AND '{end_date}'
            AND DATE_DIFF(
                DATE_TRUNC(PARSE_DATE('%Y%m%d', e.event_date), WEEK),
                c.cohort_week,
                WEEK
            ) <= {periods}
        )
        SELECT 
            cohort_week as cohort,
            period,
            {metric_calc} as value
        FROM user_activity
        GROUP BY cohort_week, period
        ORDER BY cohort_week, period
        """
        
        return sql
    
    async def query_user_journey(
        self,
        start_event: str,
        max_depth: int,
        min_users: int,
        date_range: Tuple[str, str],
    ) -> Dict[str, Any]:
        """
        Path analysis - what do users do after event X?
        
        Returns Sankey diagram data showing user flows.
        """
        sql = self._build_journey_sql(start_event, max_depth, min_users, date_range)
        
        job = self.client.query(sql)
        results = job.result()
        
        # Build path data
        paths = []
        for row in results:
            paths.append({
                "from": row.source_event,
                "to": row.target_event,
                "value": int(row.user_count),
                "step": int(row.step),
            })
        
        return {
            "success": True,
            "paths": paths,
            "start_event": start_event,
        }
    
    def _build_journey_sql(
        self,
        start_event: str,
        max_depth: int,
        min_users: int,
        date_range: Tuple[str, str],
    ) -> str:
        """Build SQL for user journey analysis."""
        
        table_name = f"`{self.project_id}.{self.dataset}.events_*`"
        
        start_date = date_range[0].replace("-", "")
        end_date = date_range[1].replace("-", "")
        
        sql = f"""
        WITH sessions AS (
            SELECT 
                user_pseudo_id,
                event_name,
                event_timestamp,
                ROW_NUMBER() OVER (
                    PARTITION BY user_pseudo_id 
                    ORDER BY event_timestamp
                ) as event_sequence
            FROM {table_name}
            WHERE _TABLE_SUFFIX BETWEEN '{start_date}' AND '{end_date}'
        ),
        paths AS (
            SELECT 
                s1.event_name as source_event,
                s2.event_name as target_event,
                s1.event_sequence as step,
                s1.user_pseudo_id
            FROM sessions s1
            JOIN sessions s2 
                ON s1.user_pseudo_id = s2.user_pseudo_id
                AND s2.event_sequence = s1.event_sequence + 1
            WHERE s1.event_name = '{start_event}'
            AND s1.event_sequence <= {max_depth}
        )
        SELECT 
            source_event,
            target_event,
            step,
            COUNT(DISTINCT user_pseudo_id) as user_count
        FROM paths
        GROUP BY source_event, target_event, step
        HAVING COUNT(DISTINCT user_pseudo_id) >= {min_users}
        ORDER BY step, user_count DESC
        """
        
        return sql
    
    async def estimate_query_cost(self, sql: str) -> Dict[str, Any]:
        """
        Estimate query cost before running.
        
        Important for cost control with BigQuery.
        """
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        
        job = self.client.query(sql, job_config=job_config)
        
        bytes_processed = job.total_bytes_processed
        cost_per_tb = 5.0  # $5 per TB
        estimated_cost = (bytes_processed / (1024**4)) * cost_per_tb
        
        return {
            "bytes_processed": bytes_processed,
            "estimated_cost_usd": round(estimated_cost, 4),
            "warning": "Confirm before running" if estimated_cost > 1.0 else None,
        }


# Singleton
_ga4_connector: Optional[GA4BigQueryConnector] = None


def get_ga4_connector() -> GA4BigQueryConnector:
    """Get GA4 connector singleton."""
    global _ga4_connector
    
    if _ga4_connector is None:
        if not settings.ga4_project_id:
            raise ValueError("GA4_PROJECT_ID not configured")
        _ga4_connector = GA4BigQueryConnector()
    
    return _ga4_connector
