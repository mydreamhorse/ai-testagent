"""
Unit tests for Analytics Engine

Tests the statistical analysis, data aggregation, and analytics functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from backend.services.analytics_engine import (
    AnalyticsEngine, StatisticalAnalyzer, DataAggregator,
    StatisticalSummary, TrendAnalysis, CorrelationResult,
    MetricType, AnalysisType
)
from backend.models import (
    TestCase, Requirement, Defect, CoverageAnalysis, TestCaseEvaluation
)


class TestStatisticalAnalyzer:
    """Test statistical analysis functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock(spec=Session)
        self.analyzer = StatisticalAnalyzer(self.mock_db)
    
    def test_calculate_basic_statistics_empty_data(self):
        """Test statistical calculation with empty data"""
        result = self.analyzer.calculate_basic_statistics([])
        
        assert result.count == 0
        assert result.mean == 0
        assert result.median == 0
        assert result.std_dev == 0
    
    def test_calculate_basic_statistics_single_value(self):
        """Test statistical calculation with single value"""
        values = [75.5]
        result = self.analyzer.calculate_basic_statistics(values)
        
        assert result.count == 1
        assert result.mean == 75.5
        assert result.median == 75.5
        assert result.std_dev == 0
        assert result.min_value == 75.5
        assert result.max_value == 75.5
    
    def test_calculate_basic_statistics_multiple_values(self):
        """Test statistical calculation with multiple values"""
        values = [10, 20, 30, 40, 50]
        result = self.analyzer.calculate_basic_statistics(values)
        
        assert result.count == 5
        assert result.mean == 30.0
        assert result.median == 30.0
        assert result.min_value == 10
        assert result.max_value == 50
        assert result.percentile_25 == 20.0
        assert result.percentile_75 == 40.0
        assert result.std_dev > 0
    
    def test_calculate_percentile(self):
        """Test percentile calculation"""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        p25 = self.analyzer._calculate_percentile(values, 25)
        p50 = self.analyzer._calculate_percentile(values, 50)
        p75 = self.analyzer._calculate_percentile(values, 75)
        
        assert p25 == 3.25
        assert p50 == 5.5
        assert p75 == 7.75
    
    def test_identify_outliers(self):
        """Test outlier identification"""
        values = [1, 2, 3, 4, 5, 100]  # 100 is an outlier
        q1 = 2.25
        q3 = 4.75
        
        outliers = self.analyzer._identify_outliers(values, q1, q3)
        
        assert len(outliers) == 1
        assert outliers[0]['value'] == 100
        assert outliers[0]['type'] == 'high'
    
    def test_create_distribution_bins(self):
        """Test distribution bin creation"""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        distribution = self.analyzer._create_distribution_bins(values, num_bins=5)
        
        assert len(distribution['bins']) == 5
        assert len(distribution['counts']) == 5
        assert sum(distribution['counts']) == len(values)
    
    def test_create_distribution_bins_single_value(self):
        """Test distribution bins with single unique value"""
        values = [5, 5, 5, 5, 5]
        
        distribution = self.analyzer._create_distribution_bins(values)
        
        assert len(distribution['bins']) == 1
        assert distribution['counts'][0] == 5
    
    @patch('backend.services.analytics_engine.StatisticalAnalyzer._collect_metric_values')
    def test_analyze_metric_distribution(self, mock_collect):
        """Test metric distribution analysis"""
        mock_collect.return_value = [10, 20, 30, 40, 50]
        
        result = self.analyzer.analyze_metric_distribution(MetricType.QUALITY_SCORE)
        
        assert result['metric_type'] == 'quality_score'
        assert 'statistics' in result
        assert 'distribution' in result
        assert 'outliers' in result
        assert 'analysis_time' in result
    
    @patch('backend.services.analytics_engine.StatisticalAnalyzer._collect_metric_values')
    def test_analyze_metric_distribution_empty_data(self, mock_collect):
        """Test metric distribution analysis with empty data"""
        mock_collect.return_value = []
        
        result = self.analyzer.analyze_metric_distribution(MetricType.QUALITY_SCORE)
        
        assert result['metric_type'] == 'quality_score'
        assert result['statistics']['count'] == 0
        assert result['distribution'] == {}
        assert result['outliers'] == []
    
    def test_calculate_pearson_correlation(self):
        """Test Pearson correlation calculation"""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]  # Perfect positive correlation
        
        correlation = self.analyzer._calculate_pearson_correlation(x, y)
        
        assert abs(correlation - 1.0) < 0.001  # Should be very close to 1
    
    def test_calculate_pearson_correlation_no_correlation(self):
        """Test Pearson correlation with no correlation"""
        x = [1, 2, 3, 4, 5]
        y = [5, 3, 1, 4, 2]  # No clear correlation
        
        correlation = self.analyzer._calculate_pearson_correlation(x, y)
        
        assert abs(correlation) <= 0.5  # Should be weak correlation
    
    def test_determine_significance(self):
        """Test correlation significance determination"""
        assert self.analyzer._determine_significance(0.8) == 'strong'
        assert self.analyzer._determine_significance(0.6) == 'moderate'
        assert self.analyzer._determine_significance(0.4) == 'weak'
        assert self.analyzer._determine_significance(0.2) == 'none'
    
    @patch('backend.services.analytics_engine.StatisticalAnalyzer._collect_metric_values')
    def test_perform_correlation_analysis(self, mock_collect):
        """Test correlation analysis between metrics"""
        # Mock will be called twice, once for each metric
        mock_collect.side_effect = [
            [10, 20, 30, 40, 50],  # First metric
            [15, 25, 35, 45, 55]   # Second metric (positive correlation)
        ]
        
        result = self.analyzer.perform_correlation_analysis(
            MetricType.QUALITY_SCORE, MetricType.COVERAGE_RATE
        )
        
        assert isinstance(result, CorrelationResult)
        assert result.sample_size == 5
        assert result.correlation_coefficient > 0.9  # Strong positive correlation
        assert result.significance in ['strong', 'moderate', 'weak', 'none']
        
        # Verify the mock was called twice
        assert mock_collect.call_count == 2


class TestDataAggregator:
    """Test data aggregation functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock(spec=Session)
        self.aggregator = DataAggregator(self.mock_db)
    
    @patch('backend.services.analytics_engine.DataAggregator._collect_aggregated_data')
    def test_aggregate_by_time_period_daily(self, mock_collect):
        """Test daily aggregation"""
        mock_collect.return_value = [
            {'period': '2024-01-01', 'average': 75.5, 'count': 10},
            {'period': '2024-01-02', 'average': 80.2, 'count': 8}
        ]
        
        result = self.aggregator.aggregate_by_time_period(
            MetricType.QUALITY_SCORE, 'daily'
        )
        
        assert result['metric_type'] == 'quality_score'
        assert result['period'] == 'daily'
        assert len(result['data']) == 2
        assert result['data'][0]['period'] == '2024-01-01'
    
    @patch('backend.services.analytics_engine.DataAggregator._collect_aggregated_data')
    def test_aggregate_by_time_period_weekly(self, mock_collect):
        """Test weekly aggregation"""
        mock_collect.return_value = [
            {'period': '2024-W01', 'average': 77.8, 'count': 25}
        ]
        
        result = self.aggregator.aggregate_by_time_period(
            MetricType.COVERAGE_RATE, 'weekly'
        )
        
        assert result['period'] == 'weekly'
        assert len(result['data']) == 1
    
    def test_aggregate_by_time_period_invalid_period(self):
        """Test aggregation with invalid period"""
        with pytest.raises(ValueError, match="Unsupported period"):
            self.aggregator.aggregate_by_time_period(
                MetricType.QUALITY_SCORE, 'invalid_period'
            )
    
    def test_group_by_category_defect_severity(self):
        """Test grouping defects by severity"""
        # Mock database query results
        mock_results = [
            Mock(severity='critical', count=5),
            Mock(severity='high', count=10),
            Mock(severity='medium', count=15),
            Mock(severity='low', count=8)
        ]
        
        mock_query = Mock()
        mock_query.group_by.return_value.all.return_value = mock_results
        self.mock_db.query.return_value = mock_query
        
        result = self.aggregator.group_by_category(
            MetricType.DEFECT_RATE, 'severity'
        )
        
        assert result['metric_type'] == 'defect_rate'
        assert result['category_field'] == 'severity'
        assert result['grouped_data']['critical'] == 5
        assert result['grouped_data']['high'] == 10


class TestAnalyticsEngine:
    """Test main analytics engine functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock(spec=Session)
        self.engine = AnalyticsEngine(self.mock_db)
    
    def create_mock_requirement(self, req_id: int, title: str) -> Mock:
        """Create mock requirement"""
        req = Mock(spec=Requirement)
        req.id = req_id
        req.title = title
        return req
    
    def create_mock_test_case(self, tc_id: int, req_id: int, test_type: str = 'functional') -> Mock:
        """Create mock test case"""
        tc = Mock(spec=TestCase)
        tc.id = tc_id
        tc.requirement_id = req_id
        tc.test_type = test_type
        return tc
    
    def create_mock_defect(self, defect_id: int, severity: str, defect_type: str, 
                          description: str, detected_at: datetime = None, 
                          resolved_at: datetime = None) -> Mock:
        """Create mock defect"""
        defect = Mock(spec=Defect)
        defect.id = defect_id
        defect.severity = severity
        defect.defect_type = defect_type
        defect.description = description
        defect.status = 'open' if not resolved_at else 'resolved'
        defect.detected_at = detected_at or datetime.utcnow()
        defect.resolved_at = resolved_at
        return defect
    
    def test_analyze_test_coverage_full_coverage(self):
        """Test coverage analysis with full coverage"""
        requirements = [
            self.create_mock_requirement(1, "Requirement 1"),
            self.create_mock_requirement(2, "Requirement 2")
        ]
        
        test_cases = [
            self.create_mock_test_case(1, 1, 'functional'),
            self.create_mock_test_case(2, 1, 'boundary'),
            self.create_mock_test_case(3, 2, 'functional'),
            self.create_mock_test_case(4, 2, 'exception')
        ]
        
        result = self.engine.analyze_test_coverage(requirements, test_cases)
        
        assert result['total_requirements'] == 2
        assert result['covered_requirements'] == 2
        assert len(result['coverage_map']) == 2
        assert 'coverage_statistics' in result
        assert 'coverage_gaps' in result
    
    def test_analyze_test_coverage_partial_coverage(self):
        """Test coverage analysis with partial coverage"""
        requirements = [
            self.create_mock_requirement(1, "Requirement 1"),
            self.create_mock_requirement(2, "Requirement 2"),
            self.create_mock_requirement(3, "Requirement 3")
        ]
        
        test_cases = [
            self.create_mock_test_case(1, 1, 'functional'),
            # No test cases for requirement 2 and 3
        ]
        
        result = self.engine.analyze_test_coverage(requirements, test_cases)
        
        assert result['total_requirements'] == 3
        assert result['covered_requirements'] == 1
        assert len(result['coverage_gaps']) >= 2  # Requirements 2 and 3 should have gaps
    
    def test_analyze_test_coverage_no_test_cases(self):
        """Test coverage analysis with no test cases"""
        requirements = [
            self.create_mock_requirement(1, "Requirement 1")
        ]
        test_cases = []
        
        result = self.engine.analyze_test_coverage(requirements, test_cases)
        
        assert result['total_requirements'] == 1
        assert result['covered_requirements'] == 0
        assert result['average_coverage'] == 0
        assert len(result['coverage_gaps']) == 1
    
    def test_analyze_defect_patterns_empty_defects(self):
        """Test defect pattern analysis with no defects"""
        result = self.engine.analyze_defect_patterns([])
        
        assert result['total_defects'] == 0
        assert result['patterns'] == {}
        assert result['statistics'] == {}
    
    def test_analyze_defect_patterns_with_defects(self):
        """Test defect pattern analysis with defects"""
        now = datetime.utcnow()
        resolved_time = now + timedelta(days=5)
        
        defects = [
            self.create_mock_defect(1, 'critical', 'functional', 'Login failure issue', now, resolved_time),
            self.create_mock_defect(2, 'high', 'performance', 'Slow response time', now),
            self.create_mock_defect(3, 'medium', 'functional', 'Login validation error', now, resolved_time),
            self.create_mock_defect(4, 'low', 'usability', 'Minor UI issue', now)
        ]
        
        result = self.engine.analyze_defect_patterns(defects)
        
        assert result['total_defects'] == 4
        assert 'by_severity' in result['patterns']
        assert 'by_type' in result['patterns']
        assert 'by_status' in result['patterns']
        assert 'recurring_patterns' in result['patterns']
        assert result['patterns']['by_severity']['critical'] == 1
        assert result['patterns']['by_type']['functional'] == 2
    
    def test_identify_recurring_defect_patterns(self):
        """Test identification of recurring defect patterns"""
        defects = [
            self.create_mock_defect(1, 'high', 'functional', 'Login authentication failure'),
            self.create_mock_defect(2, 'medium', 'functional', 'Login validation error'),
            self.create_mock_defect(3, 'low', 'performance', 'Database connection timeout'),
            self.create_mock_defect(4, 'high', 'functional', 'Authentication service unavailable')
        ]
        
        patterns = self.engine._identify_recurring_defect_patterns(defects)
        
        # Should find patterns based on common keywords
        assert len(patterns) > 0
        # Look for patterns with keywords like "login", "authentication", etc.
        pattern_keywords = [p['pattern_keyword'] for p in patterns]
        assert any(keyword in ['login', 'authentication', 'failure'] for keyword in pattern_keywords)
    
    def test_predict_risk_areas(self):
        """Test risk area prediction"""
        historical_data = {
            'defects': [
                {'test_case_id': 1, 'severity': 'high'},
                {'test_case_id': 1, 'severity': 'medium'},
                {'test_case_id': 2, 'severity': 'critical'},
                {'test_case_id': 3, 'severity': 'low'}
            ],
            'coverage_data': {
                '1': {'coverage_percentage': 25},  # Low coverage
                '2': {'coverage_percentage': 85},  # Good coverage
                '3': {'coverage_percentage': 45}   # Medium coverage
            }
        }
        
        result = self.engine.predict_risk_areas(historical_data)
        
        assert 'high_risk_test_cases' in result
        assert 'coverage_risk_areas' in result
        assert 'prediction_confidence' in result
        
        # Test case 1 should be high risk (2 defects)
        high_risk_cases = result['high_risk_test_cases']
        assert len(high_risk_cases) >= 1
        assert high_risk_cases[0]['test_case_id'] == 1
        assert high_risk_cases[0]['defect_count'] == 2
        
        # Requirements 1 and 3 should be coverage risks
        coverage_risks = result['coverage_risk_areas']
        risk_req_ids = [risk['requirement_id'] for risk in coverage_risks]
        assert '1' in risk_req_ids
        assert '3' in risk_req_ids
    
    def test_calculate_prediction_confidence(self):
        """Test prediction confidence calculation"""
        # Test with minimal data
        minimal_data = {'defects': [1, 2], 'coverage_data': {}, 'test_cases': []}
        confidence = self.engine._calculate_prediction_confidence(minimal_data)
        assert 0 <= confidence <= 0.9
        
        # Test with substantial data
        substantial_data = {
            'defects': list(range(50)),
            'coverage_data': {str(i): {} for i in range(30)},
            'test_cases': list(range(40))
        }
        confidence = self.engine._calculate_prediction_confidence(substantial_data)
        assert confidence > 0.5
    
    def test_generate_optimization_suggestions(self):
        """Test optimization suggestion generation"""
        test_suite_data = {
            'test_cases': [
                {'test_case_id': 1, 'total_score': 45},  # Low quality
                {'test_case_id': 2, 'total_score': 85},  # Good quality
                {'test_case_id': 3, 'total_score': 55}   # Low quality
            ],
            'coverage_gaps': [
                {'requirement_id': 1, 'coverage_percentage': 30},
                {'requirement_id': 2, 'coverage_percentage': 45}
            ],
            'defect_patterns': {
                'recurring_patterns': [
                    {'pattern_keyword': 'authentication', 'occurrence_count': 3}
                ]
            }
        }
        
        suggestions = self.engine.generate_optimization_suggestions(test_suite_data)
        
        assert len(suggestions) >= 3  # Should have suggestions for quality, coverage, and defects
        
        # Check suggestion types
        suggestion_types = [s['type'] for s in suggestions]
        assert 'quality_improvement' in suggestion_types
        assert 'coverage_improvement' in suggestion_types
        assert 'defect_prevention' in suggestion_types
        
        # Check priority ordering (high priority first)
        priorities = [s['priority'] for s in suggestions]
        high_count = priorities.count('high')
        assert high_count >= 1  # Should have at least one high priority suggestion
    
    def test_generate_optimization_suggestions_empty_data(self):
        """Test optimization suggestions with empty data"""
        suggestions = self.engine.generate_optimization_suggestions({})
        
        assert isinstance(suggestions, list)
        # Should return empty list or minimal suggestions for empty data


if __name__ == '__main__':
    pytest.main([__file__])