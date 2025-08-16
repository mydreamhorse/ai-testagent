"""
Analytics Engine Service

This module implements the core analytics and intelligent suggestion functionality
for the intelligent test reporting system. It provides statistical analysis,
data aggregation, and intelligent recommendations.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
import statistics
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from backend.models import (
    TestCase, Requirement, Defect, CoverageAnalysis, TestCaseEvaluation,
    User, SystemMetric, Report, AlertRule, Alert
)

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of analysis that can be performed"""
    STATISTICAL = "statistical"
    TREND = "trend"
    CORRELATION = "correlation"
    PREDICTION = "prediction"


class MetricType(Enum):
    """Types of metrics for analysis"""
    COVERAGE_RATE = "coverage_rate"
    DEFECT_RATE = "defect_rate"
    PASS_RATE = "pass_rate"
    EXECUTION_TIME = "execution_time"
    QUALITY_SCORE = "quality_score"


@dataclass
class StatisticalSummary:
    """Statistical summary of a dataset"""
    count: int
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    percentile_25: float
    percentile_75: float


@dataclass
class TrendAnalysis:
    """Trend analysis results"""
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    trend_strength: float  # 0.0 to 1.0
    slope: float
    r_squared: float
    data_points: int
    confidence: float


@dataclass
class CorrelationResult:
    """Correlation analysis result"""
    correlation_coefficient: float
    p_value: float
    significance: str  # 'strong', 'moderate', 'weak', 'none'
    sample_size: int


class StatisticalAnalyzer:
    """Performs statistical analysis on test data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_basic_statistics(self, values: List[float]) -> StatisticalSummary:
        """Calculate basic statistical measures for a dataset"""
        if not values:
            return StatisticalSummary(0, 0, 0, 0, 0, 0, 0, 0)
        
        try:
            count = len(values)
            mean = statistics.mean(values)
            median = statistics.median(values)
            std_dev = statistics.stdev(values) if count > 1 else 0
            min_value = min(values)
            max_value = max(values)
            
            # Calculate percentiles
            sorted_values = sorted(values)
            percentile_25 = self._calculate_percentile(sorted_values, 25)
            percentile_75 = self._calculate_percentile(sorted_values, 75)
            
            return StatisticalSummary(
                count=count,
                mean=mean,
                median=median,
                std_dev=std_dev,
                min_value=min_value,
                max_value=max_value,
                percentile_25=percentile_25,
                percentile_75=percentile_75
            )
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            return StatisticalSummary(0, 0, 0, 0, 0, 0, 0, 0)
    
    def _calculate_percentile(self, sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile value from sorted data"""
        if not sorted_values:
            return 0
        
        index = (percentile / 100) * (len(sorted_values) - 1)
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            if upper_index >= len(sorted_values):
                return sorted_values[lower_index]
            
            weight = index - lower_index
            return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight
    
    def analyze_metric_distribution(self, metric_type: MetricType, 
                                  date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Analyze distribution of a specific metric"""
        try:
            values = self._collect_metric_values(metric_type, date_range)
            
            if not values:
                return {
                    'metric_type': metric_type.value,
                    'statistics': asdict(StatisticalSummary(0, 0, 0, 0, 0, 0, 0, 0)),
                    'distribution': {},
                    'outliers': [],
                    'analysis_time': datetime.utcnow()
                }
            
            # Calculate basic statistics
            stats = self.calculate_basic_statistics(values)
            
            # Identify outliers using IQR method
            outliers = self._identify_outliers(values, stats.percentile_25, stats.percentile_75)
            
            # Create distribution bins
            distribution = self._create_distribution_bins(values)
            
            return {
                'metric_type': metric_type.value,
                'statistics': asdict(stats),
                'distribution': distribution,
                'outliers': outliers,
                'analysis_time': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing metric distribution: {str(e)}")
            raise
    
    def _collect_metric_values(self, metric_type: MetricType, 
                             date_range: Optional[Tuple[datetime, datetime]]) -> List[float]:
        """Collect metric values from database"""
        values = []
        
        try:
            if metric_type == MetricType.COVERAGE_RATE:
                query = self.db.query(CoverageAnalysis.coverage_percentage)
                if date_range:
                    query = query.filter(
                        and_(
                            CoverageAnalysis.analysis_date >= date_range[0],
                            CoverageAnalysis.analysis_date <= date_range[1]
                        )
                    )
                values = [row[0] for row in query.all() if row[0] is not None]
                
            elif metric_type == MetricType.DEFECT_RATE:
                # Calculate defect rate per test case
                query = self.db.query(
                    TestCase.id,
                    func.count(Defect.id).label('defect_count')
                ).outerjoin(Defect).group_by(TestCase.id)
                
                if date_range:
                    query = query.filter(
                        and_(
                            TestCase.created_at >= date_range[0],
                            TestCase.created_at <= date_range[1]
                        )
                    )
                
                results = query.all()
                values = [float(row.defect_count) for row in results]
                
            elif metric_type == MetricType.PASS_RATE:
                # Calculate pass rate based on evaluation scores
                query = self.db.query(TestCaseEvaluation.total_score)
                if date_range:
                    query = query.filter(
                        and_(
                            TestCaseEvaluation.evaluated_at >= date_range[0],
                            TestCaseEvaluation.evaluated_at <= date_range[1]
                        )
                    )
                
                scores = [row[0] for row in query.all() if row[0] is not None]
                # Convert scores to pass/fail (70% threshold) then to rates
                pass_rates = [100.0 if score >= 70 else 0.0 for score in scores]
                values = pass_rates
                
            elif metric_type == MetricType.QUALITY_SCORE:
                query = self.db.query(TestCaseEvaluation.total_score)
                if date_range:
                    query = query.filter(
                        and_(
                            TestCaseEvaluation.evaluated_at >= date_range[0],
                            TestCaseEvaluation.evaluated_at <= date_range[1]
                        )
                    )
                values = [row[0] for row in query.all() if row[0] is not None]
                
        except Exception as e:
            logger.error(f"Error collecting metric values for {metric_type}: {str(e)}")
            
        return values
    
    def _identify_outliers(self, values: List[float], q1: float, q3: float) -> List[Dict[str, Any]]:
        """Identify outliers using IQR method"""
        if not values or q1 == q3:
            return []
        
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outliers.append({
                    'index': i,
                    'value': value,
                    'type': 'low' if value < lower_bound else 'high',
                    'deviation': abs(value - (q1 + q3) / 2)
                })
        
        return sorted(outliers, key=lambda x: x['deviation'], reverse=True)
    
    def _create_distribution_bins(self, values: List[float], num_bins: int = 10) -> Dict[str, Any]:
        """Create distribution bins for histogram"""
        if not values:
            return {'bins': [], 'counts': [], 'bin_edges': []}
        
        min_val = min(values)
        max_val = max(values)
        
        if min_val == max_val:
            return {
                'bins': [f"{min_val:.2f}"],
                'counts': [len(values)],
                'bin_edges': [min_val, max_val]
            }
        
        bin_width = (max_val - min_val) / num_bins
        bin_edges = [min_val + i * bin_width for i in range(num_bins + 1)]
        bin_counts = [0] * num_bins
        
        for value in values:
            bin_index = min(int((value - min_val) / bin_width), num_bins - 1)
            bin_counts[bin_index] += 1
        
        bin_labels = [
            f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}"
            for i in range(num_bins)
        ]
        
        return {
            'bins': bin_labels,
            'counts': bin_counts,
            'bin_edges': bin_edges
        }
    
    def perform_correlation_analysis(self, metric1: MetricType, metric2: MetricType,
                                   date_range: Optional[Tuple[datetime, datetime]] = None) -> CorrelationResult:
        """Perform correlation analysis between two metrics"""
        try:
            values1 = self._collect_metric_values(metric1, date_range)
            values2 = self._collect_metric_values(metric2, date_range)
            
            # Ensure same length by taking minimum
            min_length = min(len(values1), len(values2))
            if min_length < 2:
                return CorrelationResult(0.0, 1.0, 'none', min_length)
            
            values1 = values1[:min_length]
            values2 = values2[:min_length]
            
            # Calculate Pearson correlation coefficient
            correlation = self._calculate_pearson_correlation(values1, values2)
            
            # Simple p-value estimation (for demonstration)
            p_value = self._estimate_p_value(correlation, min_length)
            
            # Determine significance
            significance = self._determine_significance(abs(correlation))
            
            return CorrelationResult(
                correlation_coefficient=correlation,
                p_value=p_value,
                significance=significance,
                sample_size=min_length
            )
            
        except Exception as e:
            logger.error(f"Error performing correlation analysis: {str(e)}")
            return CorrelationResult(0.0, 1.0, 'none', 0)
    
    def _calculate_pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        sum_y2 = sum(yi * yi for yi in y)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y)) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _estimate_p_value(self, correlation: float, sample_size: int) -> float:
        """Estimate p-value for correlation (simplified)"""
        if sample_size < 3:
            return 1.0
        
        # Handle perfect correlation case
        if abs(correlation) >= 0.999:
            return 0.001  # Very low p-value for perfect correlation
        
        # Simplified p-value estimation
        t_stat = abs(correlation) * ((sample_size - 2) / (1 - correlation * correlation)) ** 0.5
        
        # Very rough p-value estimation
        if t_stat > 2.576:  # 99% confidence
            return 0.01
        elif t_stat > 1.96:  # 95% confidence
            return 0.05
        elif t_stat > 1.645:  # 90% confidence
            return 0.10
        else:
            return 0.20
    
    def _determine_significance(self, abs_correlation: float) -> str:
        """Determine correlation significance level"""
        if abs_correlation >= 0.7:
            return 'strong'
        elif abs_correlation >= 0.5:
            return 'moderate'
        elif abs_correlation >= 0.3:
            return 'weak'
        else:
            return 'none'


class DataAggregator:
    """Aggregates and groups data for analysis"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def aggregate_by_time_period(self, metric_type: MetricType, 
                               period: str = 'daily',
                               date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Aggregate metrics by time period"""
        try:
            # Determine time grouping function
            if period == 'daily':
                time_format = '%Y-%m-%d'
                group_func = func.date
            elif period == 'weekly':
                time_format = '%Y-W%U'
                group_func = func.strftime('%Y-W%U')
            elif period == 'monthly':
                time_format = '%Y-%m'
                group_func = func.strftime('%Y-%m')
            else:
                raise ValueError(f"Unsupported period: {period}")
            
            aggregated_data = self._collect_aggregated_data(metric_type, group_func, date_range)
            
            return {
                'metric_type': metric_type.value,
                'period': period,
                'data': aggregated_data,
                'aggregation_time': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error aggregating data by time period: {str(e)}")
            raise
    
    def _collect_aggregated_data(self, metric_type: MetricType, group_func, 
                               date_range: Optional[Tuple[datetime, datetime]]) -> List[Dict[str, Any]]:
        """Collect aggregated data based on metric type"""
        aggregated_data = []
        
        try:
            if metric_type == MetricType.COVERAGE_RATE:
                query = self.db.query(
                    group_func(CoverageAnalysis.analysis_date).label('period'),
                    func.avg(CoverageAnalysis.coverage_percentage).label('avg_value'),
                    func.count(CoverageAnalysis.id).label('count')
                ).group_by('period')
                
                if date_range:
                    query = query.filter(
                        and_(
                            CoverageAnalysis.analysis_date >= date_range[0],
                            CoverageAnalysis.analysis_date <= date_range[1]
                        )
                    )
                
                results = query.all()
                aggregated_data = [
                    {
                        'period': str(row.period),
                        'average': float(row.avg_value) if row.avg_value else 0,
                        'count': row.count
                    }
                    for row in results
                ]
                
            elif metric_type == MetricType.QUALITY_SCORE:
                query = self.db.query(
                    group_func(TestCaseEvaluation.evaluated_at).label('period'),
                    func.avg(TestCaseEvaluation.total_score).label('avg_score'),
                    func.count(TestCaseEvaluation.id).label('count')
                ).group_by('period')
                
                if date_range:
                    query = query.filter(
                        and_(
                            TestCaseEvaluation.evaluated_at >= date_range[0],
                            TestCaseEvaluation.evaluated_at <= date_range[1]
                        )
                    )
                
                results = query.all()
                aggregated_data = [
                    {
                        'period': str(row.period),
                        'average': float(row.avg_score) if row.avg_score else 0,
                        'count': row.count
                    }
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"Error collecting aggregated data: {str(e)}")
            
        return aggregated_data
    
    def group_by_category(self, metric_type: MetricType, 
                         category_field: str) -> Dict[str, Any]:
        """Group metrics by category"""
        try:
            grouped_data = {}
            
            if metric_type == MetricType.DEFECT_RATE and category_field == 'severity':
                query = self.db.query(
                    Defect.severity,
                    func.count(Defect.id).label('count')
                ).group_by(Defect.severity)
                
                results = query.all()
                grouped_data = {
                    row.severity: row.count
                    for row in results
                }
                
            elif metric_type == MetricType.DEFECT_RATE and category_field == 'type':
                query = self.db.query(
                    Defect.defect_type,
                    func.count(Defect.id).label('count')
                ).group_by(Defect.defect_type)
                
                results = query.all()
                grouped_data = {
                    row.defect_type: row.count
                    for row in results
                }
                
            elif metric_type == MetricType.QUALITY_SCORE and category_field == 'test_type':
                query = self.db.query(
                    TestCase.test_type,
                    func.avg(TestCaseEvaluation.total_score).label('avg_score')
                ).join(TestCaseEvaluation).group_by(TestCase.test_type)
                
                results = query.all()
                grouped_data = {
                    row.test_type: float(row.avg_score) if row.avg_score else 0
                    for row in results
                }
            
            return {
                'metric_type': metric_type.value,
                'category_field': category_field,
                'grouped_data': grouped_data,
                'aggregation_time': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error grouping by category: {str(e)}")
            raise


class AnalyticsEngine:
    """Main analytics engine that coordinates all analysis components"""
    
    def __init__(self, db: Session):
        self.db = db
        self.statistical_analyzer = StatisticalAnalyzer(db)
        self.data_aggregator = DataAggregator(db)
    
    def analyze_test_coverage(self, requirements: List[Requirement], 
                            test_cases: List[TestCase]) -> Dict[str, Any]:
        """Analyze test coverage with statistical insights"""
        try:
            # Basic coverage calculation
            coverage_map = {}
            coverage_percentages = []
            
            for requirement in requirements:
                covering_test_cases = [tc for tc in test_cases if tc.requirement_id == requirement.id]
                
                # Calculate coverage percentage
                if covering_test_cases:
                    test_types = set(tc.test_type for tc in covering_test_cases if tc.test_type)
                    base_coverage = min(100, len(covering_test_cases) * 20)
                    type_bonus = len(test_types) * 5
                    coverage_percentage = min(100, base_coverage + type_bonus)
                else:
                    coverage_percentage = 0
                
                coverage_map[requirement.id] = {
                    'requirement_id': requirement.id,
                    'requirement_title': requirement.title,
                    'coverage_percentage': coverage_percentage,
                    'test_count': len(covering_test_cases)
                }
                coverage_percentages.append(coverage_percentage)
            
            # Statistical analysis of coverage
            coverage_stats = self.statistical_analyzer.calculate_basic_statistics(coverage_percentages)
            
            # Identify coverage gaps
            coverage_gaps = [
                info for info in coverage_map.values()
                if info['coverage_percentage'] < 60
            ]
            
            return {
                'coverage_map': coverage_map,
                'coverage_statistics': asdict(coverage_stats),
                'coverage_gaps': coverage_gaps,
                'total_requirements': len(requirements),
                'covered_requirements': sum(1 for p in coverage_percentages if p > 0),
                'average_coverage': coverage_stats.mean,
                'analysis_time': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing test coverage: {str(e)}")
            raise
    
    def analyze_defect_patterns(self, defects: List[Defect]) -> Dict[str, Any]:
        """Analyze defect patterns with statistical insights"""
        try:
            if not defects:
                return {
                    'total_defects': 0,
                    'patterns': {},
                    'statistics': {},
                    'analysis_time': datetime.utcnow()
                }
            
            # Group defects by various attributes
            by_severity = Counter(d.severity for d in defects)
            by_type = Counter(d.defect_type for d in defects)
            by_status = Counter(d.status for d in defects)
            
            # Calculate resolution times
            resolution_times = []
            for defect in defects:
                if defect.resolved_at and defect.detected_at:
                    resolution_time = (defect.resolved_at - defect.detected_at).days
                    resolution_times.append(resolution_time)
            
            # Statistical analysis of resolution times
            resolution_stats = None
            if resolution_times:
                resolution_stats = self.statistical_analyzer.calculate_basic_statistics(resolution_times)
            
            # Identify recurring patterns
            recurring_patterns = self._identify_recurring_defect_patterns(defects)
            
            return {
                'total_defects': len(defects),
                'patterns': {
                    'by_severity': dict(by_severity),
                    'by_type': dict(by_type),
                    'by_status': dict(by_status),
                    'recurring_patterns': recurring_patterns
                },
                'resolution_statistics': asdict(resolution_stats) if resolution_stats else None,
                'analysis_time': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing defect patterns: {str(e)}")
            raise
    
    def _identify_recurring_defect_patterns(self, defects: List[Defect]) -> List[Dict[str, Any]]:
        """Identify recurring defect patterns"""
        # Simple pattern matching based on description keywords
        keyword_patterns = defaultdict(list)
        
        for defect in defects:
            # Extract keywords from description (simplified)
            words = defect.description.lower().split()
            significant_words = [w for w in words if len(w) > 4]  # Words longer than 4 chars
            
            for word in significant_words[:3]:  # Take first 3 significant words
                keyword_patterns[word].append(defect)
        
        # Find patterns with multiple occurrences
        recurring = []
        for keyword, defect_list in keyword_patterns.items():
            if len(defect_list) > 1:
                recurring.append({
                    'pattern_keyword': keyword,
                    'occurrence_count': len(defect_list),
                    'defect_ids': [d.id for d in defect_list],
                    'severity_distribution': Counter(d.severity for d in defect_list)
                })
        
        return sorted(recurring, key=lambda x: x['occurrence_count'], reverse=True)[:10]
    
    def predict_risk_areas(self, historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict risk areas based on historical data"""
        try:
            risk_predictions = []
            
            # Analyze defect trends by test case
            defect_by_test_case = defaultdict(int)
            if 'defects' in historical_data:
                for defect in historical_data['defects']:
                    if 'test_case_id' in defect:
                        defect_by_test_case[defect['test_case_id']] += 1
            
            # Identify high-risk test cases
            high_risk_threshold = 2  # Test cases with 2+ defects
            high_risk_test_cases = [
                {'test_case_id': tc_id, 'defect_count': count}
                for tc_id, count in defect_by_test_case.items()
                if count >= high_risk_threshold
            ]
            
            # Analyze coverage gaps as risk areas
            coverage_risks = []
            if 'coverage_data' in historical_data:
                for req_id, coverage_info in historical_data['coverage_data'].items():
                    if coverage_info.get('coverage_percentage', 0) < 50:
                        coverage_risks.append({
                            'requirement_id': req_id,
                            'coverage_percentage': coverage_info.get('coverage_percentage', 0),
                            'risk_level': 'high' if coverage_info.get('coverage_percentage', 0) < 30 else 'medium'
                        })
            
            return {
                'high_risk_test_cases': sorted(high_risk_test_cases, 
                                             key=lambda x: x['defect_count'], reverse=True),
                'coverage_risk_areas': coverage_risks,
                'prediction_confidence': self._calculate_prediction_confidence(historical_data),
                'prediction_time': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error predicting risk areas: {str(e)}")
            raise
    
    def _calculate_prediction_confidence(self, historical_data: Dict[str, Any]) -> float:
        """Calculate confidence level for predictions"""
        # Simple confidence calculation based on data availability
        data_points = 0
        
        if 'defects' in historical_data:
            data_points += len(historical_data['defects'])
        
        if 'coverage_data' in historical_data:
            data_points += len(historical_data['coverage_data'])
        
        if 'test_cases' in historical_data:
            data_points += len(historical_data['test_cases'])
        
        # Normalize to 0-1 scale
        max_confidence = 0.9  # Never claim 100% confidence
        confidence = min(max_confidence, data_points / 100)  # 100 data points = 90% confidence
        
        return confidence
    
    async def query_analytics(self, metric_types: Optional[List[str]] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            group_by: Optional[str] = None,
                            aggregation: Optional[str] = "avg") -> Dict[str, Any]:
        """Query analytics data with specified parameters"""
        try:
            # Set default date range if not provided
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            results = {}
            
            # Query system metrics if requested
            if not metric_types or 'system' in metric_types:
                system_metrics = self.db.query(SystemMetric).filter(
                    and_(
                        SystemMetric.recorded_at >= start_date,
                        SystemMetric.recorded_at <= end_date,
                        SystemMetric.metric_type == 'system'
                    )
                ).all()
                
                results['system_metrics'] = self._aggregate_metrics(system_metrics, group_by, aggregation)
            
            # Query business metrics if requested
            if not metric_types or 'business' in metric_types:
                business_metrics = self.db.query(SystemMetric).filter(
                    and_(
                        SystemMetric.recorded_at >= start_date,
                        SystemMetric.recorded_at <= end_date,
                        SystemMetric.metric_type == 'business'
                    )
                ).all()
                
                results['business_metrics'] = self._aggregate_metrics(business_metrics, group_by, aggregation)
            
            # Add summary statistics
            results['summary'] = {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'group_by': group_by,
                'aggregation': aggregation,
                'query_time': datetime.utcnow().isoformat()
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying analytics: {str(e)}")
            return {'error': str(e)}
    
    def _aggregate_metrics(self, metrics: List[SystemMetric], group_by: Optional[str], 
                          aggregation: str) -> Dict[str, Any]:
        """Aggregate metrics by specified grouping and aggregation method"""
        if not metrics:
            return {}
        
        # Group metrics by name
        grouped = defaultdict(list)
        for metric in metrics:
            grouped[metric.metric_name].append(metric)
        
        aggregated = {}
        for metric_name, metric_list in grouped.items():
            values = [m.metric_value for m in metric_list]
            
            if aggregation == 'avg':
                aggregated[metric_name] = statistics.mean(values) if values else 0
            elif aggregation == 'sum':
                aggregated[metric_name] = sum(values)
            elif aggregation == 'min':
                aggregated[metric_name] = min(values) if values else 0
            elif aggregation == 'max':
                aggregated[metric_name] = max(values) if values else 0
            elif aggregation == 'count':
                aggregated[metric_name] = len(values)
            else:
                aggregated[metric_name] = statistics.mean(values) if values else 0
        
        return aggregated
    
    async def analyze_coverage_trends(self, coverage_data: List[CoverageAnalysis]) -> Dict[str, Any]:
        """Analyze coverage trends over time"""
        try:
            if not coverage_data:
                return {
                    'trend_analysis': 'insufficient_data',
                    'current_average': 0,
                    'trend_direction': 'unknown',
                    'recommendations': []
                }
            
            # Extract coverage percentages and dates
            coverage_values = [c.coverage_percentage for c in coverage_data if c.coverage_percentage is not None]
            dates = [c.analysis_date for c in coverage_data if c.analysis_date is not None]
            
            if not coverage_values:
                return {
                    'trend_analysis': 'no_valid_data',
                    'current_average': 0,
                    'trend_direction': 'unknown',
                    'recommendations': []
                }
            
            # Calculate basic statistics
            current_average = statistics.mean(coverage_values)
            
            # Simple trend analysis (compare first half vs second half)
            mid_point = len(coverage_values) // 2
            if mid_point > 0:
                first_half_avg = statistics.mean(coverage_values[:mid_point])
                second_half_avg = statistics.mean(coverage_values[mid_point:])
                
                if second_half_avg > first_half_avg + 5:
                    trend_direction = 'improving'
                elif second_half_avg < first_half_avg - 5:
                    trend_direction = 'declining'
                else:
                    trend_direction = 'stable'
            else:
                trend_direction = 'insufficient_data'
            
            # Generate recommendations
            recommendations = []
            if current_average < 70:
                recommendations.append('Coverage is below recommended threshold of 70%')
                recommendations.append('Focus on adding test cases for uncovered requirements')
            
            if trend_direction == 'declining':
                recommendations.append('Coverage trend is declining - review recent changes')
                recommendations.append('Consider implementing coverage monitoring alerts')
            
            # Group by module if available
            module_coverage = defaultdict(list)
            for coverage in coverage_data:
                if coverage.function_module:
                    module_coverage[coverage.function_module].append(coverage.coverage_percentage)
            
            module_analysis = {}
            for module, percentages in module_coverage.items():
                if percentages:
                    module_analysis[module] = {
                        'average_coverage': statistics.mean(percentages),
                        'min_coverage': min(percentages),
                        'max_coverage': max(percentages),
                        'data_points': len(percentages)
                    }
            
            return {
                'trend_analysis': 'completed',
                'current_average': current_average,
                'trend_direction': trend_direction,
                'total_data_points': len(coverage_values),
                'date_range': {
                    'start': min(dates).isoformat() if dates else None,
                    'end': max(dates).isoformat() if dates else None
                },
                'module_analysis': module_analysis,
                'recommendations': recommendations,
                'analysis_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing coverage trends: {str(e)}")
            return {'error': str(e)}
    
    async def analyze_defect_patterns(self, defects: List[Defect]) -> Dict[str, Any]:
        """Analyze defect patterns and trends"""
        try:
            if not defects:
                return {
                    'total_defects': 0,
                    'patterns': {},
                    'trends': {},
                    'recommendations': []
                }
            
            # Basic defect statistics
            total_defects = len(defects)
            
            # Group by severity
            severity_distribution = Counter(d.severity for d in defects if d.severity)
            
            # Group by type
            type_distribution = Counter(d.defect_type for d in defects if d.defect_type)
            
            # Group by status
            status_distribution = Counter(d.status for d in defects if d.status)
            
            # Calculate resolution times
            resolution_times = []
            for defect in defects:
                if defect.resolved_at and defect.detected_at:
                    resolution_time = (defect.resolved_at - defect.detected_at).days
                    resolution_times.append(resolution_time)
            
            resolution_stats = None
            if resolution_times:
                resolution_stats = {
                    'average_days': statistics.mean(resolution_times),
                    'median_days': statistics.median(resolution_times),
                    'min_days': min(resolution_times),
                    'max_days': max(resolution_times),
                    'total_resolved': len(resolution_times)
                }
            
            # Identify recurring patterns
            recurring_patterns = self._identify_recurring_defect_patterns(defects)
            
            # Time-based trend analysis
            defects_by_date = defaultdict(int)
            for defect in defects:
                if defect.detected_at:
                    date_key = defect.detected_at.date().isoformat()
                    defects_by_date[date_key] += 1
            
            # Generate recommendations
            recommendations = []
            
            # High severity defects
            critical_high_count = severity_distribution.get('critical', 0) + severity_distribution.get('high', 0)
            if critical_high_count > total_defects * 0.3:
                recommendations.append('High number of critical/high severity defects detected')
                recommendations.append('Review testing processes and quality gates')
            
            # Slow resolution times
            if resolution_stats and resolution_stats['average_days'] > 7:
                recommendations.append(f"Average resolution time is {resolution_stats['average_days']:.1f} days")
                recommendations.append('Consider improving defect triage and resolution processes')
            
            # Recurring patterns
            if recurring_patterns:
                top_pattern = recurring_patterns[0]
                recommendations.append(f"Recurring pattern detected: '{top_pattern['pattern_keyword']}' appears {top_pattern['occurrence_count']} times")
                recommendations.append('Focus on root cause analysis for recurring issues')
            
            return {
                'total_defects': total_defects,
                'patterns': {
                    'by_severity': dict(severity_distribution),
                    'by_type': dict(type_distribution),
                    'by_status': dict(status_distribution),
                    'recurring_patterns': recurring_patterns[:5]  # Top 5 patterns
                },
                'resolution_statistics': resolution_stats,
                'trends': {
                    'defects_by_date': dict(defects_by_date),
                    'trend_direction': self._calculate_defect_trend(defects_by_date)
                },
                'recommendations': recommendations,
                'analysis_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing defect patterns: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_defect_trend(self, defects_by_date: Dict[str, int]) -> str:
        """Calculate defect trend direction"""
        if len(defects_by_date) < 2:
            return 'insufficient_data'
        
        dates = sorted(defects_by_date.keys())
        values = [defects_by_date[date] for date in dates]
        
        # Simple trend: compare first half vs second half
        mid_point = len(values) // 2
        if mid_point > 0:
            first_half_avg = statistics.mean(values[:mid_point])
            second_half_avg = statistics.mean(values[mid_point:])
            
            if second_half_avg > first_half_avg * 1.2:
                return 'increasing'
            elif second_half_avg < first_half_avg * 0.8:
                return 'decreasing'
            else:
                return 'stable'
        
        return 'stable'

    def generate_optimization_suggestions(self, test_suite_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization suggestions based on analysis"""
        try:
            suggestions = []
            
            # Analyze test case quality scores
            if 'test_cases' in test_suite_data:
                low_quality_cases = [
                    tc for tc in test_suite_data['test_cases']
                    if tc.get('total_score', 0) < 60
                ]
                
                if low_quality_cases:
                    suggestions.append({
                        'type': 'quality_improvement',
                        'priority': 'high',
                        'title': 'Improve Low-Quality Test Cases',
                        'description': f'Found {len(low_quality_cases)} test cases with quality scores below 60%',
                        'affected_items': [tc.get('test_case_id') for tc in low_quality_cases],
                        'recommended_actions': [
                            'Review test case clarity and completeness',
                            'Enhance test steps and expected results',
                            'Improve test data and preconditions'
                        ]
                    })
            
            # Analyze coverage gaps
            if 'coverage_gaps' in test_suite_data:
                coverage_gaps = test_suite_data['coverage_gaps']
                if coverage_gaps:
                    suggestions.append({
                        'type': 'coverage_improvement',
                        'priority': 'medium',
                        'title': 'Address Coverage Gaps',
                        'description': f'Found {len(coverage_gaps)} requirements with insufficient test coverage',
                        'affected_items': [gap.get('requirement_id') for gap in coverage_gaps],
                        'recommended_actions': [
                            'Create additional test cases for uncovered requirements',
                            'Add boundary and negative test scenarios',
                            'Include performance and security test cases'
                        ]
                    })
            
            # Analyze defect patterns
            if 'defect_patterns' in test_suite_data:
                recurring_patterns = test_suite_data['defect_patterns'].get('recurring_patterns', [])
                if recurring_patterns:
                    suggestions.append({
                        'type': 'defect_prevention',
                        'priority': 'high',
                        'title': 'Address Recurring Defect Patterns',
                        'description': f'Identified {len(recurring_patterns)} recurring defect patterns',
                        'affected_items': [pattern.get('pattern_keyword') for pattern in recurring_patterns],
                        'recommended_actions': [
                            'Review and strengthen test cases in problem areas',
                            'Implement additional validation checks',
                            'Consider root cause analysis for recurring issues'
                        ]
                    })
            
            # Sort suggestions by priority
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            suggestions.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {str(e)}")
            raise