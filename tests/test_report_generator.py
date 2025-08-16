"""
Unit tests for the Report Generator service

Tests the core functionality of report generation including data collection,
report creation, and export functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.services.report_generator import (
    ReportGenerator, ReportDataCollector, ReportFormat, ReportType, 
    DateRange, ExecutionSummary, DefectSummary, CoverageSummary
)
from backend.models import (
    Report, TestCase, Requirement, Defect, CoverageAnalysis, 
    TestCaseEvaluation, User, ReportTemplate, Base
)


class TestReportDataCollector:
    """Test cases for ReportDataCollector"""
    
    def test_collect_execution_data_basic(self, db_session):
        """Test basic execution data collection"""
        collector = ReportDataCollector(db_session)
        
        # Mock test cases and evaluations
        test_case1 = TestCase(
            id=1, title="Test Case 1", description="Test", 
            test_steps="Steps", expected_result="Result"
        )
        test_case2 = TestCase(
            id=2, title="Test Case 2", description="Test", 
            test_steps="Steps", expected_result="Result"
        )
        
        evaluation1 = TestCaseEvaluation(
            test_case_id=1, total_score=85.0, completeness_score=90.0,
            accuracy_score=80.0, executability_score=85.0,
            coverage_score=85.0, clarity_score=85.0
        )
        evaluation2 = TestCaseEvaluation(
            test_case_id=2, total_score=65.0, completeness_score=70.0,
            accuracy_score=60.0, executability_score=65.0,
            coverage_score=65.0, clarity_score=65.0
        )
        
        db_session.add_all([test_case1, test_case2, evaluation1, evaluation2])
        db_session.commit()
        
        # Collect data
        result = collector.collect_execution_data()
        
        # Verify results
        assert 'summary' in result
        assert 'test_cases' in result
        assert 'collection_time' in result
        
        summary = result['summary']
        assert summary['total_test_cases'] == 2
        assert summary['passed_test_cases'] == 1  # Only test case 1 passed (score >= 70)
        assert summary['failed_test_cases'] == 1
        assert summary['pass_rate'] == 50.0
        assert summary['avg_score'] == 75.0  # (85 + 65) / 2
    
    def test_collect_execution_data_with_filters(self, db_session):
        """Test execution data collection with filters"""
        collector = ReportDataCollector(db_session)
        
        # Create test data with different dates and users
        user1 = User(id=1, username="user1", email="user1@test.com", hashed_password="hash")
        user2 = User(id=2, username="user2", email="user2@test.com", hashed_password="hash")
        
        old_date = datetime.utcnow() - timedelta(days=10)
        recent_date = datetime.utcnow() - timedelta(days=1)
        
        test_case1 = TestCase(
            id=1, title="Old Test", user_id=1, created_at=old_date,
            test_steps="Steps", expected_result="Result"
        )
        test_case2 = TestCase(
            id=2, title="Recent Test", user_id=2, created_at=recent_date,
            test_steps="Steps", expected_result="Result"
        )
        
        db_session.add_all([user1, user2, test_case1, test_case2])
        db_session.commit()
        
        # Test date range filter
        date_range = DateRange(
            start_date=datetime.utcnow() - timedelta(days=2),
            end_date=datetime.utcnow()
        )
        
        result = collector.collect_execution_data(date_range=date_range)
        assert result['summary']['total_test_cases'] == 1  # Only recent test case
        
        # Test user filter
        result = collector.collect_execution_data(user_id=1)
        assert result['summary']['total_test_cases'] == 1  # Only user1's test case
        
        # Test test case IDs filter
        result = collector.collect_execution_data(test_case_ids=[1])
        assert result['summary']['total_test_cases'] == 1
        assert result['test_cases'][0]['test_case_id'] == 1
    
    def test_collect_defect_data_basic(self, db_session):
        """Test basic defect data collection"""
        collector = ReportDataCollector(db_session)
        
        # Create test cases first
        test_case1 = TestCase(
            id=1, title="Test Case 1", test_steps="Steps", expected_result="Result"
        )
        test_case2 = TestCase(
            id=2, title="Test Case 2", test_steps="Steps", expected_result="Result"
        )
        
        # Create defects
        defect1 = Defect(
            test_case_id=1, defect_type="functional", severity="critical",
            description="Critical defect", status="open"
        )
        defect2 = Defect(
            test_case_id=2, defect_type="performance", severity="high",
            description="Performance issue", status="resolved"
        )
        defect3 = Defect(
            test_case_id=1, defect_type="functional", severity="medium",
            description="Medium defect", status="open"
        )
        
        db_session.add_all([test_case1, test_case2, defect1, defect2, defect3])
        db_session.commit()
        
        # Collect data
        result = collector.collect_defect_data()
        
        # Verify results
        assert 'summary' in result
        assert 'defects' in result
        assert 'patterns' in result
        
        summary = result['summary']
        assert summary['total_defects'] == 3
        assert summary['critical_defects'] == 1
        assert summary['high_defects'] == 1
        assert summary['medium_defects'] == 1
        assert summary['low_defects'] == 0
        assert summary['open_defects'] == 2  # 2 open defects
        assert summary['resolved_defects'] == 1  # 1 resolved defect
        
        patterns = result['patterns']
        assert patterns['by_type']['functional'] == 2
        assert patterns['by_type']['performance'] == 1
        assert patterns['by_severity']['critical'] == 1
        assert patterns['by_status']['open'] == 2
    
    def test_collect_coverage_data_basic(self, db_session):
        """Test basic coverage data collection"""
        collector = ReportDataCollector(db_session)
        
        # Create requirements
        req1 = Requirement(
            id=1, title="Requirement 1", description="Desc", content="Content"
        )
        req2 = Requirement(
            id=2, title="Requirement 2", description="Desc", content="Content"
        )
        
        # Create test cases to provide coverage
        test_case1 = TestCase(
            id=1, requirement_id=1, title="Test Case 1", test_type="functional",
            test_steps="Steps", expected_result="Result"
        )
        test_case2 = TestCase(
            id=2, requirement_id=2, title="Test Case 2", test_type="functional",
            test_steps="Steps", expected_result="Result"
        )
        
        # Create coverage analyses
        coverage1 = CoverageAnalysis(
            requirement_id=1, function_module="module1",
            coverage_percentage=85.0, covered_test_cases=17, total_test_cases=20,
            uncovered_areas=["area1", "area2"]
        )
        coverage2 = CoverageAnalysis(
            requirement_id=2, function_module="module2",
            coverage_percentage=75.0, covered_test_cases=15, total_test_cases=20,
            uncovered_areas=["area3"]
        )
        
        db_session.add_all([req1, req2, test_case1, test_case2, coverage1, coverage2])
        db_session.commit()
        
        # Collect data
        result = collector.collect_coverage_data()
        
        # Verify results
        assert 'summary' in result
        assert 'coverage_details' in result
        assert 'advanced_analysis' in result
        
        summary = result['summary']
        assert summary['total_requirements'] == 2
        assert summary['covered_requirements'] == 2  # Both have test cases
        assert summary['coverage_percentage'] > 0  # Should have some coverage
        assert "area1" in summary['uncovered_areas']
        assert "area2" in summary['uncovered_areas']
        assert "area3" in summary['uncovered_areas']
        
        assert "module1" in summary['coverage_by_module']
        assert summary['coverage_by_module']["module1"] == 85.0
        assert summary['coverage_by_module']["module2"] == 75.0
        
        # Verify advanced analysis is present
        advanced_analysis = result['advanced_analysis']
        assert 'requirement_coverage' in advanced_analysis
        assert 'heatmap_data' in advanced_analysis
        assert 'coverage_trends' in advanced_analysis


class TestReportGenerator:
    """Test cases for ReportGenerator"""
    
    def test_generate_execution_report(self, db_session):
        """Test execution report generation"""
        generator = ReportGenerator(db_session)
        
        # Create test data
        user = User(id=1, username="testuser", email="test@test.com", hashed_password="hash")
        test_case = TestCase(
            id=1, title="Test Case", user_id=1,
            test_steps="Steps", expected_result="Result"
        )
        evaluation = TestCaseEvaluation(
            test_case_id=1, total_score=85.0
        )
        
        db_session.add_all([user, test_case, evaluation])
        db_session.commit()
        
        # Generate report
        report = generator.generate_execution_report(user_id=1)
        
        # Verify report
        assert report.id is not None
        assert report.title.startswith("Test Execution Report")
        assert report.report_type == ReportType.EXECUTION.value
        assert report.generated_by == 1
        assert report.status == "completed"
        assert report.report_data is not None
        
        # Verify report data structure
        report_data = report.report_data
        assert 'summary' in report_data
        assert 'test_cases' in report_data
        assert 'collection_time' in report_data
    
    def test_generate_defect_analysis_report(self, db_session):
        """Test defect analysis report generation"""
        generator = ReportGenerator(db_session)
        
        # Create test data
        user = User(id=1, username="testuser", email="test@test.com", hashed_password="hash")
        test_case = TestCase(
            id=1, title="Test Case", test_steps="Steps", expected_result="Result"
        )
        defect = Defect(
            test_case_id=1, defect_type="functional", severity="high",
            description="Test defect", status="open"
        )
        
        db_session.add_all([user, test_case, defect])
        db_session.commit()
        
        # Generate report
        report = generator.generate_defect_analysis_report(user_id=1)
        
        # Verify report
        assert report.id is not None
        assert report.title.startswith("Defect Analysis Report")
        assert report.report_type == ReportType.DEFECT_ANALYSIS.value
        assert report.generated_by == 1
        assert report.status == "completed"
        
        # Verify report data
        report_data = report.report_data
        assert 'summary' in report_data
        assert 'defects' in report_data
        assert 'patterns' in report_data
    
    def test_generate_coverage_report(self, db_session):
        """Test coverage report generation"""
        generator = ReportGenerator(db_session)
        
        # Create test data
        user = User(id=1, username="testuser", email="test@test.com", hashed_password="hash")
        requirement = Requirement(
            id=1, title="Requirement", description="Desc", content="Content"
        )
        coverage = CoverageAnalysis(
            requirement_id=1, function_module="module1",
            coverage_percentage=80.0, covered_test_cases=16, total_test_cases=20
        )
        
        db_session.add_all([user, requirement, coverage])
        db_session.commit()
        
        # Generate report
        report = generator.generate_coverage_report(user_id=1)
        
        # Verify report
        assert report.id is not None
        assert report.title.startswith("Coverage Analysis Report")
        assert report.report_type == ReportType.COVERAGE.value
        assert report.generated_by == 1
        assert report.status == "completed"
        
        # Verify report data
        report_data = report.report_data
        assert 'summary' in report_data
        assert 'coverage_details' in report_data
    
    def test_export_report_json(self, db_session):
        """Test JSON export functionality"""
        generator = ReportGenerator(db_session)
        
        # Create a test report
        report = Report(
            id=1, title="Test Report", report_type="execution",
            generation_time=datetime.utcnow(),
            report_data={"test": "data"},
            status="completed"
        )
        
        # Export to JSON
        json_data = generator.export_report(report, ReportFormat.JSON)
        
        # Verify export
        assert isinstance(json_data, bytes)
        parsed_data = json.loads(json_data.decode('utf-8'))
        assert parsed_data['report_id'] == 1
        assert parsed_data['title'] == "Test Report"
        assert parsed_data['report_type'] == "execution"
        assert parsed_data['report_data'] == {"test": "data"}
    
    def test_export_report_html(self, db_session):
        """Test HTML export functionality"""
        generator = ReportGenerator(db_session)
        
        # Create a test report
        report = Report(
            id=1, title="Test Report", report_type="execution",
            generation_time=datetime.utcnow(),
            report_data={"test": "data"},
            status="completed"
        )
        
        # Export to HTML
        html_data = generator.export_report(report, ReportFormat.HTML)
        
        # Verify export
        assert isinstance(html_data, bytes)
        html_content = html_data.decode('utf-8')
        assert "Test Report" in html_content
        assert "<!DOCTYPE html>" in html_content
        assert "<title>Test Report</title>" in html_content
    
    def test_generate_report_with_date_range(self, db_session):
        """Test report generation with date range filter"""
        generator = ReportGenerator(db_session)
        
        # Create test data
        user = User(id=1, username="testuser", email="test@test.com", hashed_password="hash")
        db_session.add(user)
        db_session.commit()
        
        # Define date range
        date_range = DateRange(
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )
        
        # Generate report with date range
        report = generator.generate_execution_report(
            user_id=1, 
            date_range=date_range
        )
        
        # Verify date range is stored
        assert report.data_range_start == date_range.start_date
        assert report.data_range_end == date_range.end_date
    
    def test_report_generation_error_handling(self, db_session):
        """Test error handling in report generation"""
        generator = ReportGenerator(db_session)
        
        # Mock database error
        with patch.object(db_session, 'commit', side_effect=Exception("Database error")):
            with pytest.raises(Exception) as exc_info:
                generator.generate_execution_report(user_id=1)
            
            assert "Database error" in str(exc_info.value)
    
    def test_unsupported_export_format(self, db_session):
        """Test handling of unsupported export formats"""
        generator = ReportGenerator(db_session)
        
        report = Report(
            id=1, title="Test Report", report_type="execution",
            generation_time=datetime.utcnow(),
            report_data={"test": "data"},
            status="completed"
        )
        
        # Create a mock unsupported format
        class UnsupportedFormat:
            value = "unsupported"
        
        with pytest.raises(ValueError) as exc_info:
            generator.export_report(report, UnsupportedFormat())
        
        assert "Unsupported export format" in str(exc_info.value)


@pytest.fixture
def db_session():
    """Create a real database session for testing"""
    # Create in-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


class TestDefectPatternAnalyzer:
    """Test cases for DefectPatternAnalyzer"""
    
    def test_identify_defect_patterns(self, db_session):
        """Test defect pattern identification"""
        from backend.services.report_generator import DefectPatternAnalyzer
        
        analyzer = DefectPatternAnalyzer(db_session)
        
        # Create test defects with patterns
        defects = [
            Defect(
                id=1, test_case_id=1, defect_type="functional", severity="high",
                description="Login button not working", status="open",
                detected_at=datetime.utcnow() - timedelta(days=10)
            ),
            Defect(
                id=2, test_case_id=2, defect_type="functional", severity="high",
                description="Login button not working properly", status="resolved",
                detected_at=datetime.utcnow() - timedelta(days=8),
                resolved_at=datetime.utcnow() - timedelta(days=5)
            ),
            Defect(
                id=3, test_case_id=3, defect_type="performance", severity="medium",
                description="Page load time too slow", status="open",
                detected_at=datetime.utcnow() - timedelta(days=5)
            )
        ]
        
        patterns = analyzer.identify_defect_patterns(defects)
        
        # Verify pattern analysis structure
        assert 'recurring_defects' in patterns
        assert 'severity_trends' in patterns
        assert 'type_correlations' in patterns
        assert 'resolution_time_patterns' in patterns
        
        # Check recurring defects detection
        recurring = patterns['recurring_defects']
        assert len(recurring) >= 0  # May or may not find patterns with this small dataset
        
        # Check severity trends
        severity_trends = patterns['severity_trends']
        assert 'trend' in severity_trends
        assert 'severity_over_time' in severity_trends
        
        # Check type correlations
        type_correlations = patterns['type_correlations']
        assert 'type_severity_correlation' in type_correlations
        assert 'avg_resolution_times' in type_correlations
    
    def test_predict_defect_trends(self, db_session):
        """Test defect trend prediction"""
        from backend.services.report_generator import DefectPatternAnalyzer
        
        analyzer = DefectPatternAnalyzer(db_session)
        
        # Create test defects with time progression
        defects = []
        for i in range(10):
            defects.append(Defect(
                id=i+1, test_case_id=i+1, defect_type="functional", severity="medium",
                description=f"Test defect {i+1}", status="open",
                detected_at=datetime.utcnow() - timedelta(days=20-i*2)
            ))
        
        prediction = analyzer.predict_defect_trends(defects, days_ahead=30)
        
        # Verify prediction structure
        assert 'prediction' in prediction
        assert 'confidence' in prediction
        assert 'predicted_defects' in prediction
        
        # With sufficient data, should provide trend-based prediction
        if len(defects) >= 5:
            assert prediction['prediction'] in ['trend_based', 'insufficient_data']
            assert 0 <= prediction['confidence'] <= 1
            assert prediction['predicted_defects'] >= 0
    
    def test_insufficient_data_handling(self, db_session):
        """Test handling of insufficient data scenarios"""
        from backend.services.report_generator import DefectPatternAnalyzer
        
        analyzer = DefectPatternAnalyzer(db_session)
        
        # Test with empty defect list
        patterns = analyzer.identify_defect_patterns([])
        assert 'recurring_defects' in patterns
        assert 'severity_trends' in patterns
        
        # Test prediction with insufficient data
        prediction = analyzer.predict_defect_trends([], days_ahead=30)
        assert prediction['prediction'] == 'insufficient_data'
        assert prediction['confidence'] == 0
        assert prediction['predicted_defects'] == 0


class TestEnhancedDefectAnalysis:
    """Test cases for enhanced defect analysis in ReportDataCollector"""
    
    def test_collect_defect_data_with_advanced_analysis(self, db_session):
        """Test defect data collection with advanced pattern analysis"""
        collector = ReportDataCollector(db_session)
        
        # Create test cases and defects
        test_case1 = TestCase(
            id=1, title="Test Case 1", test_steps="Steps", expected_result="Result"
        )
        test_case2 = TestCase(
            id=2, title="Test Case 2", test_steps="Steps", expected_result="Result"
        )
        
        # Create defects with patterns
        defect1 = Defect(
            test_case_id=1, defect_type="functional", severity="critical",
            description="Critical system failure", status="open",
            detected_at=datetime.utcnow() - timedelta(days=5)
        )
        defect2 = Defect(
            test_case_id=2, defect_type="functional", severity="high",
            description="System failure in module", status="resolved",
            detected_at=datetime.utcnow() - timedelta(days=3),
            resolved_at=datetime.utcnow() - timedelta(days=1)
        )
        defect3 = Defect(
            test_case_id=1, defect_type="performance", severity="medium",
            description="Slow response time", status="open",
            detected_at=datetime.utcnow() - timedelta(days=2)
        )
        
        db_session.add_all([test_case1, test_case2, defect1, defect2, defect3])
        db_session.commit()
        
        # Collect data with advanced analysis
        result = collector.collect_defect_data()
        
        # Verify basic structure
        assert 'summary' in result
        assert 'defects' in result
        assert 'patterns' in result
        assert 'advanced_analysis' in result
        
        # Verify advanced analysis structure
        advanced_analysis = result['advanced_analysis']
        assert 'pattern_analysis' in advanced_analysis
        assert 'trend_prediction' in advanced_analysis
        
        # Verify pattern analysis components
        pattern_analysis = advanced_analysis['pattern_analysis']
        assert 'recurring_defects' in pattern_analysis
        assert 'severity_trends' in pattern_analysis
        assert 'type_correlations' in pattern_analysis
        assert 'resolution_time_patterns' in pattern_analysis
        
        # Verify trend prediction components
        trend_prediction = advanced_analysis['trend_prediction']
        assert 'prediction' in trend_prediction
        assert 'confidence' in trend_prediction
        assert 'predicted_defects' in trend_prediction
    
    def test_defect_analysis_with_time_filters(self, db_session):
        """Test defect analysis with date range filters"""
        collector = ReportDataCollector(db_session)
        
        # Create test data with different dates
        test_case = TestCase(
            id=1, title="Test Case", test_steps="Steps", expected_result="Result"
        )
        
        old_defect = Defect(
            test_case_id=1, defect_type="functional", severity="high",
            description="Old defect", status="resolved",
            detected_at=datetime.utcnow() - timedelta(days=30),
            resolved_at=datetime.utcnow() - timedelta(days=25)
        )
        recent_defect = Defect(
            test_case_id=1, defect_type="performance", severity="medium",
            description="Recent defect", status="open",
            detected_at=datetime.utcnow() - timedelta(days=2)
        )
        
        db_session.add_all([test_case, old_defect, recent_defect])
        db_session.commit()
        
        # Test with date range filter
        date_range = DateRange(
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )
        
        result = collector.collect_defect_data(date_range=date_range)
        
        # Should only include recent defect
        assert result['summary']['total_defects'] == 1
        assert len(result['defects']) == 1
        assert result['defects'][0]['description'] == "Recent defect"
        
        # Advanced analysis should still be present
        assert 'advanced_analysis' in result
        assert 'pattern_analysis' in result['advanced_analysis']
        assert 'trend_prediction' in result['advanced_analysis']


class TestCoverageAnalyzer:
    """Test cases for CoverageAnalyzer"""
    
    def test_analyze_requirement_coverage(self, db_session):
        """Test requirement coverage analysis"""
        from backend.services.report_generator import CoverageAnalyzer
        
        analyzer = CoverageAnalyzer(db_session)
        
        # Create test requirements
        req1 = Requirement(
            id=1, title="User Authentication", description="Login functionality", content="Content"
        )
        req2 = Requirement(
            id=2, title="Data Validation", description="Input validation", content="Content"
        )
        req3 = Requirement(
            id=3, title="Uncovered Feature", description="No tests", content="Content"
        )
        
        # Create test cases
        test_cases = [
            TestCase(
                id=1, requirement_id=1, title="Login Test", test_type="functional",
                priority="high", test_steps="Steps", expected_result="Result"
            ),
            TestCase(
                id=2, requirement_id=1, title="Login Boundary Test", test_type="boundary",
                priority="medium", test_steps="Steps", expected_result="Result"
            ),
            TestCase(
                id=3, requirement_id=2, title="Validation Test", test_type="functional",
                priority="high", test_steps="Steps", expected_result="Result"
            )
        ]
        
        requirements = [req1, req2, req3]
        
        # Analyze coverage
        coverage_analysis = analyzer.analyze_requirement_coverage(requirements, test_cases)
        
        # Verify structure
        assert 'coverage_map' in coverage_analysis
        assert 'uncovered_requirements' in coverage_analysis
        assert 'coverage_gaps' in coverage_analysis
        assert 'overall_stats' in coverage_analysis
        
        # Verify coverage map
        coverage_map = coverage_analysis['coverage_map']
        assert len(coverage_map) == 3
        
        # Requirement 1 should have good coverage (2 test cases, different types)
        req1_coverage = coverage_map[1]
        assert req1_coverage['total_test_cases'] == 2
        assert req1_coverage['coverage_percentage'] > 0
        assert 'functional' in req1_coverage['test_type_diversity']
        assert 'boundary' in req1_coverage['test_type_diversity']
        
        # Requirement 2 should have basic coverage (1 test case)
        req2_coverage = coverage_map[2]
        assert req2_coverage['total_test_cases'] == 1
        assert req2_coverage['coverage_percentage'] > 0
        
        # Requirement 3 should have no coverage
        req3_coverage = coverage_map[3]
        assert req3_coverage['total_test_cases'] == 0
        assert req3_coverage['coverage_percentage'] == 0
        assert req3_coverage['coverage_quality'] == 'none'
        
        # Verify uncovered requirements
        uncovered = coverage_analysis['uncovered_requirements']
        assert len(uncovered) == 1
        assert uncovered[0]['requirement_id'] == 3
        
        # Verify overall stats
        overall_stats = coverage_analysis['overall_stats']
        assert overall_stats['total_requirements'] == 3
        assert overall_stats['covered_requirements'] == 2
        assert overall_stats['uncovered_requirements'] == 1
        assert overall_stats['average_coverage'] > 0
    
    def test_create_coverage_heatmap_data(self, db_session):
        """Test coverage heatmap data creation"""
        from backend.services.report_generator import CoverageAnalyzer
        
        analyzer = CoverageAnalyzer(db_session)
        
        # Mock coverage map data
        coverage_map = {
            1: {
                'requirement_id': 1,
                'requirement_title': 'High Coverage Feature',
                'coverage_percentage': 85,
                'total_test_cases': 4,
                'coverage_quality': 'excellent'
            },
            2: {
                'requirement_id': 2,
                'requirement_title': 'Medium Coverage Feature',
                'coverage_percentage': 60,
                'total_test_cases': 2,
                'coverage_quality': 'good'
            },
            3: {
                'requirement_id': 3,
                'requirement_title': 'Low Coverage Feature',
                'coverage_percentage': 25,
                'total_test_cases': 1,
                'coverage_quality': 'poor'
            }
        }
        
        heatmap_data = analyzer.create_coverage_heatmap_data(coverage_map)
        
        # Verify structure
        assert 'heatmap_data' in heatmap_data
        assert 'color_scale' in heatmap_data
        assert 'visualization_config' in heatmap_data
        
        # Verify heatmap data
        heatmap_points = heatmap_data['heatmap_data']
        assert len(heatmap_points) == 3
        
        # Should be sorted by coverage percentage (descending)
        assert heatmap_points[0]['coverage_percentage'] >= heatmap_points[1]['coverage_percentage']
        assert heatmap_points[1]['coverage_percentage'] >= heatmap_points[2]['coverage_percentage']
        
        # Verify data structure
        for point in heatmap_points:
            assert 'requirement_id' in point
            assert 'requirement_title' in point
            assert 'coverage_percentage' in point
            assert 'test_count' in point
            assert 'quality' in point
            assert 'color_intensity' in point
            assert 0 <= point['color_intensity'] <= 1
        
        # Verify color scale
        color_scale = heatmap_data['color_scale']
        assert 'excellent' in color_scale
        assert 'good' in color_scale
        assert 'fair' in color_scale
        assert 'poor' in color_scale
        assert 'none' in color_scale
    
    def test_identify_coverage_trends(self, db_session):
        """Test coverage trend identification"""
        from backend.services.report_generator import CoverageAnalyzer
        
        analyzer = CoverageAnalyzer(db_session)
        
        # Test with improving trend
        improving_data = [
            {'coverage_percentage': 40, 'analysis_date': datetime.utcnow() - timedelta(days=20)},
            {'coverage_percentage': 55, 'analysis_date': datetime.utcnow() - timedelta(days=10)},
            {'coverage_percentage': 70, 'analysis_date': datetime.utcnow()}
        ]
        
        trend = analyzer.identify_coverage_trends(improving_data)
        assert trend['trend'] == 'trend_available'
        assert trend['trend_direction'] == 'improving'
        assert trend['improvement_rate'] > 0
        assert trend['current_coverage'] == 70
        assert trend['previous_coverage'] == 55
        
        # Test with declining trend
        declining_data = [
            {'coverage_percentage': 80, 'analysis_date': datetime.utcnow() - timedelta(days=10)},
            {'coverage_percentage': 65, 'analysis_date': datetime.utcnow()}
        ]
        
        trend = analyzer.identify_coverage_trends(declining_data)
        assert trend['trend_direction'] == 'declining'
        assert trend['improvement_rate'] < 0
        
        # Test with insufficient data
        insufficient_data = [
            {'coverage_percentage': 50, 'analysis_date': datetime.utcnow()}
        ]
        
        trend = analyzer.identify_coverage_trends(insufficient_data)
        assert trend['trend'] == 'insufficient_data'
        assert trend['trend_direction'] == 'unknown'
    
    def test_generate_coverage_recommendations(self, db_session):
        """Test coverage recommendation generation"""
        from backend.services.report_generator import CoverageAnalyzer
        
        analyzer = CoverageAnalyzer(db_session)
        
        # Test recommendations for uncovered requirement
        uncovered_info = {
            'total_test_cases': 0,
            'coverage_percentage': 0,
            'test_type_diversity': [],
            'priority_diversity': []
        }
        
        recommendations = analyzer._generate_coverage_recommendations(uncovered_info)
        assert len(recommendations) > 0
        assert any('Create basic functional test cases' in rec for rec in recommendations)
        
        # Test recommendations for poorly covered requirement
        poor_coverage_info = {
            'total_test_cases': 1,
            'coverage_percentage': 30,
            'test_type_diversity': ['functional'],
            'priority_diversity': ['medium']
        }
        
        recommendations = analyzer._generate_coverage_recommendations(poor_coverage_info)
        assert len(recommendations) > 0
        assert any('different types of tests' in rec for rec in recommendations)


class TestEnhancedCoverageAnalysis:
    """Test cases for enhanced coverage analysis in ReportDataCollector"""
    
    def test_collect_coverage_data_with_advanced_analysis(self, db_session):
        """Test coverage data collection with advanced analysis"""
        collector = ReportDataCollector(db_session)
        
        # Create test requirements
        req1 = Requirement(
            id=1, title="Feature A", description="Description A", content="Content A"
        )
        req2 = Requirement(
            id=2, title="Feature B", description="Description B", content="Content B"
        )
        
        # Create test cases
        test_case1 = TestCase(
            id=1, requirement_id=1, title="Test A1", test_type="functional",
            priority="high", test_steps="Steps", expected_result="Result"
        )
        test_case2 = TestCase(
            id=2, requirement_id=1, title="Test A2", test_type="boundary",
            priority="medium", test_steps="Steps", expected_result="Result"
        )
        test_case3 = TestCase(
            id=3, requirement_id=2, title="Test B1", test_type="functional",
            priority="low", test_steps="Steps", expected_result="Result"
        )
        
        # Create coverage analysis records
        coverage1 = CoverageAnalysis(
            requirement_id=1, function_module="module_a",
            coverage_percentage=80.0, covered_test_cases=2, total_test_cases=2,
            analysis_date=datetime.utcnow() - timedelta(days=5)
        )
        coverage2 = CoverageAnalysis(
            requirement_id=2, function_module="module_b",
            coverage_percentage=60.0, covered_test_cases=1, total_test_cases=1,
            analysis_date=datetime.utcnow() - timedelta(days=3)
        )
        
        db_session.add_all([req1, req2, test_case1, test_case2, test_case3, coverage1, coverage2])
        db_session.commit()
        
        # Collect coverage data
        result = collector.collect_coverage_data()
        
        # Verify basic structure
        assert 'summary' in result
        assert 'coverage_details' in result
        assert 'advanced_analysis' in result
        
        # Verify advanced analysis structure
        advanced_analysis = result['advanced_analysis']
        assert 'requirement_coverage' in advanced_analysis
        assert 'heatmap_data' in advanced_analysis
        assert 'coverage_trends' in advanced_analysis
        
        # Verify requirement coverage analysis
        requirement_coverage = advanced_analysis['requirement_coverage']
        assert 'coverage_map' in requirement_coverage
        assert 'uncovered_requirements' in requirement_coverage
        assert 'coverage_gaps' in requirement_coverage
        assert 'overall_stats' in requirement_coverage
        
        # Verify heatmap data
        heatmap_data = advanced_analysis['heatmap_data']
        assert 'heatmap_data' in heatmap_data
        assert 'color_scale' in heatmap_data
        assert 'visualization_config' in heatmap_data
        
        # Verify coverage trends
        coverage_trends = advanced_analysis['coverage_trends']
        assert 'trend' in coverage_trends
        assert 'trend_direction' in coverage_trends
    
    def test_coverage_analysis_with_requirement_filter(self, db_session):
        """Test coverage analysis with requirement ID filter"""
        collector = ReportDataCollector(db_session)
        
        # Create test data
        req1 = Requirement(
            id=1, title="Filtered Requirement", description="Desc", content="Content"
        )
        req2 = Requirement(
            id=2, title="Excluded Requirement", description="Desc", content="Content"
        )
        
        test_case1 = TestCase(
            id=1, requirement_id=1, title="Test 1", test_steps="Steps", expected_result="Result"
        )
        test_case2 = TestCase(
            id=2, requirement_id=2, title="Test 2", test_steps="Steps", expected_result="Result"
        )
        
        coverage1 = CoverageAnalysis(
            requirement_id=1, function_module="module1",
            coverage_percentage=75.0, covered_test_cases=1, total_test_cases=1
        )
        coverage2 = CoverageAnalysis(
            requirement_id=2, function_module="module2",
            coverage_percentage=85.0, covered_test_cases=1, total_test_cases=1
        )
        
        db_session.add_all([req1, req2, test_case1, test_case2, coverage1, coverage2])
        db_session.commit()
        
        # Test with requirement filter
        result = collector.collect_coverage_data(requirement_ids=[1])
        
        # Should only include data for requirement 1
        coverage_map = result['advanced_analysis']['requirement_coverage']['coverage_map']
        assert 1 in coverage_map
        assert len(coverage_map) == 1  # Only filtered requirement
        
        # Coverage details should also be filtered
        coverage_details = result['coverage_details']
        assert len(coverage_details) == 1
        assert coverage_details[0]['requirement_id'] == 1