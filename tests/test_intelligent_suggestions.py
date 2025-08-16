"""
Unit tests for Intelligent Suggestions Service

Tests the intelligent suggestion generation, risk assessment, and recommendation functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from backend.services.intelligent_suggestions import (
    IntelligentSuggestionEngine, RuleBasedSuggestionEngine, RiskAssessmentEngine,
    Suggestion, RiskAssessment, SuggestionType, Priority
)
from backend.models import (
    TestCase, Requirement, Defect, CoverageAnalysis, TestCaseEvaluation
)


class TestRuleBasedSuggestionEngine:
    """Test rule-based suggestion generation"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock(spec=Session)
        self.engine = RuleBasedSuggestionEngine(self.mock_db)
    
    def create_mock_test_case(self, tc_id: int, req_id: int = 1, test_type: str = 'functional') -> Mock:
        """Create mock test case"""
        tc = Mock(spec=TestCase)
        tc.id = tc_id
        tc.requirement_id = req_id
        tc.test_type = test_type
        tc.title = f"Test Case {tc_id}"
        return tc
    
    def create_mock_evaluation(self, tc_id: int, total_score: float = 75.0,
                             clarity_score: float = 75.0) -> Mock:
        """Create mock test case evaluation"""
        eval = Mock(spec=TestCaseEvaluation)
        eval.test_case_id = tc_id
        eval.total_score = total_score
        eval.clarity_score = clarity_score
        eval.completeness_score = 75.0
        eval.accuracy_score = 75.0
        eval.executability_score = 75.0
        eval.coverage_score = 75.0
        return eval
    
    def create_mock_requirement(self, req_id: int, title: str = "Test Requirement") -> Mock:
        """Create mock requirement"""
        req = Mock(spec=Requirement)
        req.id = req_id
        req.title = title
        return req
    
    def create_mock_coverage_analysis(self, req_id: int, coverage_percentage: float = 75.0) -> Mock:
        """Create mock coverage analysis"""
        ca = Mock(spec=CoverageAnalysis)
        ca.requirement_id = req_id
        ca.coverage_percentage = coverage_percentage
        return ca
    
    def create_mock_defect(self, defect_id: int, tc_id: int, severity: str = 'medium',
                          description: str = 'Test defect', status: str = 'open') -> Mock:
        """Create mock defect"""
        defect = Mock(spec=Defect)
        defect.id = defect_id
        defect.test_case_id = tc_id
        defect.severity = severity
        defect.defect_type = 'functional'
        defect.description = description
        defect.status = status
        defect.detected_at = datetime.utcnow()
        defect.resolved_at = None if status == 'open' else datetime.utcnow()
        return defect
    
    def test_initialize_rules(self):
        """Test rule initialization"""
        rules = self.engine._initialize_rules()
        
        assert 'quality_thresholds' in rules
        assert 'coverage_thresholds' in rules
        assert 'defect_thresholds' in rules
        assert 'performance_thresholds' in rules
        
        assert rules['quality_thresholds']['low_quality_threshold'] == 60
        assert rules['coverage_thresholds']['minimum_coverage'] == 70
    
    def test_generate_quality_improvement_suggestions_no_issues(self):
        """Test quality suggestions with no quality issues"""
        test_cases = [
            self.create_mock_test_case(1),
            self.create_mock_test_case(2)
        ]
        evaluations = [
            self.create_mock_evaluation(1, 85.0),  # High quality
            self.create_mock_evaluation(2, 80.0)   # High quality
        ]
        
        suggestions = self.engine.generate_quality_improvement_suggestions(test_cases, evaluations)
        
        assert len(suggestions) == 0
    
    def test_generate_quality_improvement_suggestions_low_quality(self):
        """Test quality suggestions with low quality test cases"""
        test_cases = [
            self.create_mock_test_case(1),
            self.create_mock_test_case(2),
            self.create_mock_test_case(3)
        ]
        evaluations = [
            self.create_mock_evaluation(1, 45.0),  # Low quality
            self.create_mock_evaluation(2, 50.0),  # Low quality
            self.create_mock_evaluation(3, 85.0)   # High quality
        ]
        
        suggestions = self.engine.generate_quality_improvement_suggestions(test_cases, evaluations)
        
        assert len(suggestions) >= 1
        quality_suggestion = next((s for s in suggestions if s.type == SuggestionType.QUALITY_IMPROVEMENT), None)
        assert quality_suggestion is not None
        assert quality_suggestion.priority in [Priority.HIGH, Priority.MEDIUM]
        assert len(quality_suggestion.affected_items) == 2  # Two low quality cases
        assert "improve" in quality_suggestion.title.lower()
    
    def test_generate_quality_improvement_suggestions_clarity_issues(self):
        """Test quality suggestions with clarity issues"""
        test_cases = [
            self.create_mock_test_case(1),
            self.create_mock_test_case(2)
        ]
        evaluations = [
            self.create_mock_evaluation(1, 75.0, clarity_score=45.0),  # Poor clarity
            self.create_mock_evaluation(2, 80.0, clarity_score=50.0)   # Poor clarity
        ]
        
        suggestions = self.engine.generate_quality_improvement_suggestions(test_cases, evaluations)
        
        clarity_suggestion = next((s for s in suggestions if "clarity" in s.title.lower()), None)
        assert clarity_suggestion is not None
        assert clarity_suggestion.type == SuggestionType.QUALITY_IMPROVEMENT
        assert len(clarity_suggestion.affected_items) == 2
    
    def test_generate_coverage_enhancement_suggestions_critical_gaps(self):
        """Test coverage suggestions with critical gaps"""
        requirements = [
            self.create_mock_requirement(1, "Critical Requirement"),
            self.create_mock_requirement(2, "Important Requirement")
        ]
        test_cases = [
            self.create_mock_test_case(1, req_id=1)  # Only one requirement has test cases
        ]
        coverage_analyses = [
            self.create_mock_coverage_analysis(1, 30.0),  # Critical gap
            self.create_mock_coverage_analysis(2, 0.0)    # No coverage
        ]
        
        suggestions = self.engine.generate_coverage_enhancement_suggestions(
            requirements, test_cases, coverage_analyses
        )
        
        critical_suggestion = next((s for s in suggestions if "critical" in s.title.lower()), None)
        assert critical_suggestion is not None
        assert critical_suggestion.type == SuggestionType.COVERAGE_ENHANCEMENT
        assert critical_suggestion.priority == Priority.HIGH
        assert len(critical_suggestion.affected_items) == 2
    
    def test_generate_coverage_enhancement_suggestions_low_diversity(self):
        """Test coverage suggestions with low test diversity"""
        requirements = [
            self.create_mock_requirement(1, "Test Requirement")
        ]
        test_cases = [
            self.create_mock_test_case(1, req_id=1, test_type='functional'),
            self.create_mock_test_case(2, req_id=1, test_type='functional')  # Same type
        ]
        coverage_analyses = [
            self.create_mock_coverage_analysis(1, 75.0)  # Good coverage but low diversity
        ]
        
        suggestions = self.engine.generate_coverage_enhancement_suggestions(
            requirements, test_cases, coverage_analyses
        )
        
        diversity_suggestion = next((s for s in suggestions if "diversity" in s.title.lower()), None)
        assert diversity_suggestion is not None
        assert diversity_suggestion.type == SuggestionType.COVERAGE_ENHANCEMENT
        assert diversity_suggestion.priority == Priority.MEDIUM
    
    def test_generate_defect_prevention_suggestions_high_defect_areas(self):
        """Test defect prevention suggestions for high-defect areas"""
        test_cases = [
            self.create_mock_test_case(1),
            self.create_mock_test_case(2)
        ]
        defects = [
            self.create_mock_defect(1, tc_id=1, severity='critical'),
            self.create_mock_defect(2, tc_id=1, severity='high'),
            self.create_mock_defect(3, tc_id=1, severity='medium'),  # Test case 1 has 3 defects
            self.create_mock_defect(4, tc_id=2, severity='low')      # Test case 2 has 1 defect
        ]
        
        suggestions = self.engine.generate_defect_prevention_suggestions(defects, test_cases)
        
        high_defect_suggestion = next((s for s in suggestions if "high-defect" in s.title.lower()), None)
        assert high_defect_suggestion is not None
        assert high_defect_suggestion.type == SuggestionType.DEFECT_PREVENTION
        assert high_defect_suggestion.priority == Priority.HIGH
        assert 1 in high_defect_suggestion.affected_items  # Test case 1 should be affected
    
    def test_generate_defect_prevention_suggestions_recurring_patterns(self):
        """Test defect prevention suggestions for recurring patterns"""
        test_cases = [
            self.create_mock_test_case(1),
            self.create_mock_test_case(2),
            self.create_mock_test_case(3)
        ]
        defects = [
            self.create_mock_defect(1, tc_id=1, description='Login authentication failure'),
            self.create_mock_defect(2, tc_id=2, description='Login validation error'),
            self.create_mock_defect(3, tc_id=3, description='Authentication service timeout'),
            self.create_mock_defect(4, tc_id=1, description='Login system malfunction')
        ]
        
        suggestions = self.engine.generate_defect_prevention_suggestions(defects, test_cases)
        
        pattern_suggestion = next((s for s in suggestions if "recurring" in s.title.lower()), None)
        assert pattern_suggestion is not None
        assert pattern_suggestion.type == SuggestionType.DEFECT_PREVENTION
        assert pattern_suggestion.priority == Priority.HIGH
    
    def test_generate_test_optimization_suggestions_redundancy(self):
        """Test optimization suggestions for redundant test cases"""
        test_cases = [
            self.create_mock_test_case(i, req_id=1) for i in range(1, 8)  # 7 test cases for one requirement
        ]
        evaluations = [
            self.create_mock_evaluation(i, 90.0) for i in range(1, 8)  # All high quality
        ]
        
        suggestions = self.engine.generate_test_optimization_suggestions(test_cases, evaluations)
        
        optimization_suggestion = next((s for s in suggestions if s.type == SuggestionType.TEST_OPTIMIZATION), None)
        assert optimization_suggestion is not None
        assert "optimize" in optimization_suggestion.title.lower()
        assert optimization_suggestion.priority == Priority.MEDIUM
    
    def test_generate_test_optimization_suggestions_automation(self):
        """Test optimization suggestions for automation opportunities"""
        test_cases = [
            self.create_mock_test_case(i) for i in range(1, 15)  # 14 test cases
        ]
        evaluations = [
            self.create_mock_evaluation(i, total_score=80.0) for i in range(1, 15)  # All suitable for automation
        ]
        # Set high executability scores
        for eval in evaluations:
            eval.executability_score = 85.0
        
        suggestions = self.engine.generate_test_optimization_suggestions(test_cases, evaluations)
        
        automation_suggestion = next((s for s in suggestions if "automation" in s.title.lower()), None)
        assert automation_suggestion is not None
        assert automation_suggestion.type == SuggestionType.TEST_OPTIMIZATION
        assert automation_suggestion.priority == Priority.MEDIUM


class TestRiskAssessmentEngine:
    """Test risk assessment functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock(spec=Session)
        self.engine = RiskAssessmentEngine(self.mock_db)
    
    def create_mock_requirement(self, req_id: int) -> Mock:
        """Create mock requirement"""
        req = Mock(spec=Requirement)
        req.id = req_id
        req.title = f"Requirement {req_id}"
        return req
    
    def create_mock_test_case(self, tc_id: int, req_id: int) -> Mock:
        """Create mock test case"""
        tc = Mock(spec=TestCase)
        tc.id = tc_id
        tc.requirement_id = req_id
        return tc
    
    def create_mock_coverage_analysis(self, req_id: int, coverage_percentage: float) -> Mock:
        """Create mock coverage analysis"""
        ca = Mock(spec=CoverageAnalysis)
        ca.requirement_id = req_id
        ca.coverage_percentage = coverage_percentage
        return ca
    
    def create_mock_defect(self, defect_id: int, severity: str = 'medium',
                          detected_at: datetime = None, status: str = 'open') -> Mock:
        """Create mock defect"""
        defect = Mock(spec=Defect)
        defect.id = defect_id
        defect.severity = severity
        defect.status = status
        defect.detected_at = detected_at or datetime.utcnow()
        return defect
    
    def test_assess_test_coverage_risk_no_requirements(self):
        """Test coverage risk assessment with no requirements"""
        result = self.engine.assess_test_coverage_risk([], [], [])
        
        assert result.risk_level == "low"
        assert result.risk_score == 0.0
        assert len(result.risk_factors) == 0
    
    def test_assess_test_coverage_risk_low_coverage(self):
        """Test coverage risk assessment with low coverage"""
        requirements = [
            self.create_mock_requirement(1),
            self.create_mock_requirement(2),
            self.create_mock_requirement(3)
        ]
        test_cases = [
            self.create_mock_test_case(1, req_id=1)  # Only one requirement covered
        ]
        coverage_analyses = [
            self.create_mock_coverage_analysis(1, 30.0),  # Low coverage
            self.create_mock_coverage_analysis(2, 0.0),   # No coverage
            self.create_mock_coverage_analysis(3, 20.0)   # Low coverage
        ]
        
        result = self.engine.assess_test_coverage_risk(requirements, test_cases, coverage_analyses)
        
        assert result.risk_level in ["high", "critical"]
        assert result.risk_score > 0.5
        assert len(result.risk_factors) > 0
        assert any("coverage" in factor.lower() for factor in result.risk_factors)
        assert len(result.mitigation_suggestions) > 0
    
    def test_assess_test_coverage_risk_good_coverage(self):
        """Test coverage risk assessment with good coverage"""
        requirements = [
            self.create_mock_requirement(1),
            self.create_mock_requirement(2)
        ]
        test_cases = [
            self.create_mock_test_case(1, req_id=1),
            self.create_mock_test_case(2, req_id=2)
        ]
        coverage_analyses = [
            self.create_mock_coverage_analysis(1, 85.0),  # Good coverage
            self.create_mock_coverage_analysis(2, 90.0)   # Excellent coverage
        ]
        
        result = self.engine.assess_test_coverage_risk(requirements, test_cases, coverage_analyses)
        
        assert result.risk_level in ["low", "medium"]
        assert result.risk_score < 0.5
    
    def test_assess_defect_trend_risk_no_defects(self):
        """Test defect trend risk assessment with no defects"""
        result = self.engine.assess_defect_trend_risk([])
        
        assert result.risk_level == "low"
        assert result.risk_score == 0.0
        assert result.confidence == 1.0
    
    def test_assess_defect_trend_risk_increasing_defects(self):
        """Test defect trend risk assessment with increasing defects"""
        now = datetime.utcnow()
        recent_date = now - timedelta(days=15)
        old_date = now - timedelta(days=60)
        
        defects = [
            # Recent defects (higher rate)
            self.create_mock_defect(1, 'critical', recent_date),
            self.create_mock_defect(2, 'high', recent_date),
            self.create_mock_defect(3, 'critical', recent_date),
            self.create_mock_defect(4, 'medium', recent_date),
            # Older defects (lower rate)
            self.create_mock_defect(5, 'low', old_date),
            self.create_mock_defect(6, 'medium', old_date)
        ]
        
        result = self.engine.assess_defect_trend_risk(defects)
        
        assert result.risk_level in ["medium", "high", "critical"]
        assert result.risk_score > 0.3
        assert len(result.risk_factors) > 0
        assert any("critical" in factor.lower() for factor in result.risk_factors)
    
    def test_assess_defect_trend_risk_many_unresolved(self):
        """Test defect trend risk assessment with many unresolved defects"""
        now = datetime.utcnow()
        defects = [
            self.create_mock_defect(1, 'high', now, 'open'),
            self.create_mock_defect(2, 'medium', now, 'open'),
            self.create_mock_defect(3, 'high', now, 'in_progress'),
            self.create_mock_defect(4, 'low', now, 'resolved')
        ]
        
        result = self.engine.assess_defect_trend_risk(defects)
        
        assert result.risk_score > 0.0
        assert any("unresolved" in factor.lower() for factor in result.risk_factors)
        assert any("unresolved" in suggestion.lower() for suggestion in result.mitigation_suggestions)


class TestIntelligentSuggestionEngine:
    """Test main intelligent suggestion engine"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock(spec=Session)
        self.engine = IntelligentSuggestionEngine(self.mock_db)
    
    def create_sample_data(self):
        """Create sample data for testing"""
        requirements = [Mock(spec=Requirement, id=1, title="Test Requirement")]
        test_cases = [Mock(spec=TestCase, id=1, requirement_id=1, test_type='functional')]
        evaluations = [Mock(spec=TestCaseEvaluation, test_case_id=1, total_score=75.0, clarity_score=75.0)]
        defects = [Mock(spec=Defect, id=1, test_case_id=1, severity='medium', status='open')]
        coverage_analyses = [Mock(spec=CoverageAnalysis, requirement_id=1, coverage_percentage=75.0)]
        
        # Set required attributes
        defects[0].defect_type = 'functional'
        defects[0].description = 'Test defect'
        defects[0].detected_at = datetime.utcnow()
        
        evaluations[0].completeness_score = 75.0
        evaluations[0].accuracy_score = 75.0
        evaluations[0].executability_score = 75.0
        evaluations[0].coverage_score = 75.0
        
        return requirements, test_cases, evaluations, defects, coverage_analyses
    
    def test_generate_comprehensive_suggestions(self):
        """Test comprehensive suggestion generation"""
        requirements, test_cases, evaluations, defects, coverage_analyses = self.create_sample_data()
        
        result = self.engine.generate_comprehensive_suggestions(
            requirements, test_cases, evaluations, defects, coverage_analyses
        )
        
        assert 'suggestions' in result
        assert 'risk_assessments' in result
        assert 'statistics' in result
        assert 'generated_at' in result
        assert 'total_items_analyzed' in result
        
        # Check statistics
        stats = result['statistics']
        assert 'total_suggestions' in stats
        assert 'by_priority' in stats
        assert 'by_type' in stats
        
        # Check risk assessments
        risk_assessments = result['risk_assessments']
        assert 'coverage_risk' in risk_assessments
        assert 'defect_risk' in risk_assessments
        
        # Check analyzed items count
        analyzed = result['total_items_analyzed']
        assert analyzed['requirements'] == 1
        assert analyzed['test_cases'] == 1
        assert analyzed['evaluations'] == 1
        assert analyzed['defects'] == 1
        assert analyzed['coverage_analyses'] == 1
    
    def test_get_prioritized_action_plan(self):
        """Test prioritized action plan generation"""
        # Create mock suggestions
        suggestions = [
            Suggestion(
                id="test_1",
                type=SuggestionType.QUALITY_IMPROVEMENT,
                priority=Priority.HIGH,
                title="High Priority Suggestion",
                description="Test description",
                rationale="Test rationale",
                confidence=0.9,
                impact_score=0.8,
                effort_estimate="medium",
                affected_items=[1, 2],
                recommended_actions=["Action 1", "Action 2", "Action 3", "Action 4"],
                expected_benefits=["Benefit 1"],
                created_at=datetime.utcnow()
            ),
            Suggestion(
                id="test_2",
                type=SuggestionType.COVERAGE_ENHANCEMENT,
                priority=Priority.MEDIUM,
                title="Medium Priority Suggestion",
                description="Test description",
                rationale="Test rationale",
                confidence=0.8,
                impact_score=0.7,
                effort_estimate="low",
                affected_items=[3],
                recommended_actions=["Action A", "Action B"],
                expected_benefits=["Benefit A"],
                created_at=datetime.utcnow()
            ),
            Suggestion(
                id="test_3",
                type=SuggestionType.TEST_OPTIMIZATION,
                priority=Priority.LOW,
                title="Low Priority Suggestion",
                description="Test description",
                rationale="Test rationale",
                confidence=0.6,  # Low confidence, should be filtered out
                impact_score=0.5,
                effort_estimate="high",
                affected_items=[4],
                recommended_actions=["Action X"],
                expected_benefits=["Benefit X"],
                created_at=datetime.utcnow()
            )
        ]
        
        action_plan = self.engine.get_prioritized_action_plan(suggestions, max_items=5)
        
        # Should only include high-confidence suggestions (>= 0.7)
        assert len(action_plan) == 2
        
        # Check ordering (high priority first)
        assert action_plan[0]['rank'] == 1
        assert action_plan[0]['priority'] == 'high'
        assert action_plan[1]['rank'] == 2
        assert action_plan[1]['priority'] == 'medium'
        
        # Check action plan structure
        for item in action_plan:
            assert 'rank' in item
            assert 'suggestion_id' in item
            assert 'title' in item
            assert 'priority' in item
            assert 'impact_score' in item
            assert 'effort_estimate' in item
            assert 'confidence' in item
            assert 'immediate_actions' in item
            assert 'affected_items_count' in item
            assert 'expected_roi' in item
            
            # Should have max 3 immediate actions
            assert len(item['immediate_actions']) <= 3
    
    def test_calculate_expected_roi(self):
        """Test ROI calculation for suggestions"""
        # High impact, low effort = high ROI
        high_roi_suggestion = Suggestion(
            id="high_roi",
            type=SuggestionType.QUALITY_IMPROVEMENT,
            priority=Priority.HIGH,
            title="High ROI Suggestion",
            description="Test",
            rationale="Test",
            confidence=0.9,
            impact_score=0.9,
            effort_estimate="low",
            affected_items=[1],
            recommended_actions=["Action"],
            expected_benefits=["Benefit"],
            created_at=datetime.utcnow()
        )
        
        roi = self.engine._calculate_expected_roi(high_roi_suggestion)
        assert roi == "high"
        
        # Low impact, high effort = low ROI
        low_roi_suggestion = Suggestion(
            id="low_roi",
            type=SuggestionType.TEST_OPTIMIZATION,
            priority=Priority.LOW,
            title="Low ROI Suggestion",
            description="Test",
            rationale="Test",
            confidence=0.7,
            impact_score=0.3,
            effort_estimate="high",
            affected_items=[1],
            recommended_actions=["Action"],
            expected_benefits=["Benefit"],
            created_at=datetime.utcnow()
        )
        
        roi = self.engine._calculate_expected_roi(low_roi_suggestion)
        assert roi == "low"


if __name__ == '__main__':
    pytest.main([__file__])