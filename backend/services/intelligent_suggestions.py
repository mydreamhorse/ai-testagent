"""
Intelligent Suggestions Service

This module implements intelligent suggestion and recommendation functionality
for test optimization, risk assessment, and quality improvement.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from backend.models import (
    TestCase, Requirement, Defect, CoverageAnalysis, TestCaseEvaluation,
    User, SystemMetric, Report, AlertRule, Alert
)

logger = logging.getLogger(__name__)


class SuggestionType(Enum):
    """Types of suggestions that can be generated"""
    TEST_OPTIMIZATION = "test_optimization"
    QUALITY_IMPROVEMENT = "quality_improvement"
    COVERAGE_ENHANCEMENT = "coverage_enhancement"
    DEFECT_PREVENTION = "defect_prevention"
    RISK_MITIGATION = "risk_mitigation"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"


class Priority(Enum):
    """Priority levels for suggestions"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Suggestion:
    """A single suggestion with details and actions"""
    id: str
    type: SuggestionType
    priority: Priority
    title: str
    description: str
    rationale: str
    confidence: float  # 0.0 to 1.0
    impact_score: float  # 0.0 to 1.0
    effort_estimate: str  # "low", "medium", "high"
    affected_items: List[int]  # IDs of affected test cases, requirements, etc.
    recommended_actions: List[str]
    expected_benefits: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class RiskAssessment:
    """Risk assessment result"""
    risk_level: str  # "low", "medium", "high", "critical"
    risk_score: float  # 0.0 to 1.0
    risk_factors: List[str]
    mitigation_suggestions: List[str]
    confidence: float


class RuleBasedSuggestionEngine:
    """Rule-based suggestion engine for generating recommendations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.rules = self._initialize_rules()
    
    def _initialize_rules(self) -> Dict[str, Any]:
        """Initialize suggestion rules"""
        return {
            'quality_thresholds': {
                'low_quality_threshold': 60,
                'excellent_quality_threshold': 85,
                'min_test_cases_per_requirement': 2,
                'max_defects_per_test_case': 2
            },
            'coverage_thresholds': {
                'minimum_coverage': 70,
                'target_coverage': 90,
                'critical_coverage': 50
            },
            'defect_thresholds': {
                'high_defect_rate': 0.3,  # 30% of test cases have defects
                'critical_defect_threshold': 2,  # 2+ critical defects
                'recurring_pattern_threshold': 3,  # 3+ similar defects
                'max_defects_per_test_case': 2  # 2+ defects per test case
            },
            'performance_thresholds': {
                'slow_execution_threshold': 300,  # 5 minutes
                'high_complexity_threshold': 10  # 10+ test steps
            }
        }
    
    def generate_quality_improvement_suggestions(self, test_cases: List[TestCase],
                                               evaluations: List[TestCaseEvaluation]) -> List[Suggestion]:
        """Generate suggestions for improving test case quality"""
        suggestions = []
        
        # Create evaluation lookup
        eval_lookup = {eval.test_case_id: eval for eval in evaluations}
        
        # Identify low-quality test cases
        low_quality_cases = []
        for tc in test_cases:
            evaluation = eval_lookup.get(tc.id)
            if evaluation and evaluation.total_score < self.rules['quality_thresholds']['low_quality_threshold']:
                low_quality_cases.append({
                    'test_case': tc,
                    'evaluation': evaluation,
                    'score': evaluation.total_score
                })
        
        if low_quality_cases:
            # Sort by score (lowest first)
            low_quality_cases.sort(key=lambda x: x['score'])
            
            # Generate suggestion for worst cases
            worst_cases = low_quality_cases[:5]  # Top 5 worst cases
            
            suggestion = Suggestion(
                id=f"quality_improvement_{datetime.utcnow().timestamp()}",
                type=SuggestionType.QUALITY_IMPROVEMENT,
                priority=Priority.HIGH if len(low_quality_cases) > 10 else Priority.MEDIUM,
                title="Improve Low-Quality Test Cases",
                description=f"Found {len(low_quality_cases)} test cases with quality scores below {self.rules['quality_thresholds']['low_quality_threshold']}%",
                rationale=f"Low-quality test cases reduce testing effectiveness and may miss critical defects. The worst {len(worst_cases)} cases have scores between {worst_cases[-1]['score']:.1f}% and {worst_cases[0]['score']:.1f}%.",
                confidence=0.9,
                impact_score=0.8,
                effort_estimate="medium",
                affected_items=[case['test_case'].id for case in worst_cases],
                recommended_actions=[
                    "Review and enhance test case clarity and completeness",
                    "Improve test steps with more specific actions",
                    "Add detailed expected results and validation criteria",
                    "Include proper preconditions and test data",
                    "Consider breaking complex test cases into smaller ones"
                ],
                expected_benefits=[
                    "Improved test execution reliability",
                    "Better defect detection capability",
                    "Reduced test maintenance effort",
                    "Enhanced team productivity"
                ],
                created_at=datetime.utcnow()
            )
            suggestions.append(suggestion)
        
        # Identify test cases with specific quality issues
        clarity_issues = [
            tc for tc in test_cases
            if tc.id in eval_lookup and eval_lookup[tc.id].clarity_score < 60
        ]
        
        if clarity_issues:
            suggestion = Suggestion(
                id=f"clarity_improvement_{datetime.utcnow().timestamp()}",
                type=SuggestionType.QUALITY_IMPROVEMENT,
                priority=Priority.MEDIUM,
                title="Improve Test Case Clarity",
                description=f"Found {len(clarity_issues)} test cases with poor clarity scores",
                rationale="Unclear test cases lead to inconsistent execution and maintenance difficulties.",
                confidence=0.85,
                impact_score=0.6,
                effort_estimate="low",
                affected_items=[tc.id for tc in clarity_issues],
                recommended_actions=[
                    "Rewrite test steps using clear, actionable language",
                    "Remove ambiguous terms and add specific details",
                    "Use consistent terminology throughout test cases",
                    "Add screenshots or diagrams where helpful"
                ],
                expected_benefits=[
                    "Consistent test execution across team members",
                    "Reduced time spent understanding test cases",
                    "Lower maintenance overhead"
                ],
                created_at=datetime.utcnow()
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def generate_coverage_enhancement_suggestions(self, requirements: List[Requirement],
                                                test_cases: List[TestCase],
                                                coverage_analyses: List[CoverageAnalysis]) -> List[Suggestion]:
        """Generate suggestions for improving test coverage"""
        suggestions = []
        
        # Analyze coverage gaps
        coverage_map = {}
        for req in requirements:
            req_test_cases = [tc for tc in test_cases if tc.requirement_id == req.id]
            coverage_analysis = next((ca for ca in coverage_analyses if ca.requirement_id == req.id), None)
            
            coverage_percentage = coverage_analysis.coverage_percentage if coverage_analysis else 0
            coverage_map[req.id] = {
                'requirement': req,
                'test_cases': req_test_cases,
                'coverage_percentage': coverage_percentage,
                'test_count': len(req_test_cases)
            }
        
        # Identify critical coverage gaps
        critical_gaps = [
            info for info in coverage_map.values()
            if info['coverage_percentage'] < self.rules['coverage_thresholds']['critical_coverage']
        ]
        
        if critical_gaps:
            suggestion = Suggestion(
                id=f"critical_coverage_{datetime.utcnow().timestamp()}",
                type=SuggestionType.COVERAGE_ENHANCEMENT,
                priority=Priority.HIGH,
                title="Address Critical Coverage Gaps",
                description=f"Found {len(critical_gaps)} requirements with coverage below {self.rules['coverage_thresholds']['critical_coverage']}%",
                rationale="Critical coverage gaps represent high-risk areas where defects are likely to go undetected.",
                confidence=0.95,
                impact_score=0.9,
                effort_estimate="high",
                affected_items=[info['requirement'].id for info in critical_gaps],
                recommended_actions=[
                    "Create comprehensive test cases for uncovered requirements",
                    "Add boundary value and edge case testing",
                    "Include negative test scenarios",
                    "Implement integration test cases",
                    "Consider automated test case generation"
                ],
                expected_benefits=[
                    "Reduced risk of undetected defects",
                    "Improved system reliability",
                    "Better compliance with testing standards",
                    "Increased confidence in releases"
                ],
                created_at=datetime.utcnow()
            )
            suggestions.append(suggestion)
        
        # Identify requirements with insufficient test diversity
        low_diversity = [
            info for info in coverage_map.values()
            if info['test_count'] > 0 and len(set(tc.test_type for tc in info['test_cases'] if tc.test_type)) < 2
        ]
        
        if low_diversity:
            suggestion = Suggestion(
                id=f"test_diversity_{datetime.utcnow().timestamp()}",
                type=SuggestionType.COVERAGE_ENHANCEMENT,
                priority=Priority.MEDIUM,
                title="Improve Test Type Diversity",
                description=f"Found {len(low_diversity)} requirements with limited test type diversity",
                rationale="Limited test type diversity may miss different categories of defects.",
                confidence=0.8,
                impact_score=0.7,
                effort_estimate="medium",
                affected_items=[info['requirement'].id for info in low_diversity],
                recommended_actions=[
                    "Add different types of test cases (functional, boundary, exception)",
                    "Include performance and security test cases where applicable",
                    "Create usability and compatibility test scenarios",
                    "Implement stress and load testing"
                ],
                expected_benefits=[
                    "More comprehensive defect detection",
                    "Better coverage of different failure modes",
                    "Improved system quality assurance"
                ],
                created_at=datetime.utcnow()
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def generate_defect_prevention_suggestions(self, defects: List[Defect],
                                             test_cases: List[TestCase]) -> List[Suggestion]:
        """Generate suggestions for preventing defects"""
        suggestions = []
        
        # Analyze defect patterns
        defect_by_test_case = defaultdict(list)
        for defect in defects:
            if defect.test_case_id:
                defect_by_test_case[defect.test_case_id].append(defect)
        
        # Identify high-defect test cases
        high_defect_cases = [
            (tc_id, defect_list) for tc_id, defect_list in defect_by_test_case.items()
            if len(defect_list) >= self.rules['defect_thresholds']['max_defects_per_test_case']
        ]
        
        if high_defect_cases:
            suggestion = Suggestion(
                id=f"high_defect_areas_{datetime.utcnow().timestamp()}",
                type=SuggestionType.DEFECT_PREVENTION,
                priority=Priority.HIGH,
                title="Address High-Defect Areas",
                description=f"Found {len(high_defect_cases)} test cases with multiple defects",
                rationale="Test cases with multiple defects indicate problematic areas that need attention.",
                confidence=0.9,
                impact_score=0.85,
                effort_estimate="high",
                affected_items=[tc_id for tc_id, _ in high_defect_cases],
                recommended_actions=[
                    "Conduct root cause analysis for high-defect areas",
                    "Strengthen test cases in problematic areas",
                    "Add additional validation checks",
                    "Consider code review and refactoring",
                    "Implement preventive measures and monitoring"
                ],
                expected_benefits=[
                    "Reduced defect recurrence",
                    "Improved system stability",
                    "Lower maintenance costs",
                    "Better user experience"
                ],
                created_at=datetime.utcnow()
            )
            suggestions.append(suggestion)
        
        # Analyze recurring defect patterns
        defect_descriptions = defaultdict(list)
        for defect in defects:
            # Simple keyword extraction
            words = defect.description.lower().split()
            significant_words = [w for w in words if len(w) > 4]
            for word in significant_words[:3]:  # First 3 significant words
                defect_descriptions[word].append(defect)
        
        recurring_patterns = [
            (keyword, defect_list) for keyword, defect_list in defect_descriptions.items()
            if len(defect_list) >= self.rules['defect_thresholds']['recurring_pattern_threshold']
        ]
        
        if recurring_patterns:
            suggestion = Suggestion(
                id=f"recurring_patterns_{datetime.utcnow().timestamp()}",
                type=SuggestionType.DEFECT_PREVENTION,
                priority=Priority.HIGH,
                title="Address Recurring Defect Patterns",
                description=f"Identified {len(recurring_patterns)} recurring defect patterns",
                rationale="Recurring defect patterns suggest systematic issues that need to be addressed.",
                confidence=0.85,
                impact_score=0.8,
                effort_estimate="medium",
                affected_items=[defect.id for _, defect_list in recurring_patterns for defect in defect_list],
                recommended_actions=[
                    "Investigate root causes of recurring patterns",
                    "Implement systematic fixes for common issues",
                    "Create preventive test cases for known patterns",
                    "Establish monitoring for pattern detection",
                    "Update development guidelines and standards"
                ],
                expected_benefits=[
                    "Prevention of similar defects in the future",
                    "Improved development process quality",
                    "Reduced testing and fixing costs",
                    "Better predictability of system behavior"
                ],
                created_at=datetime.utcnow()
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def generate_test_optimization_suggestions(self, test_cases: List[TestCase],
                                             evaluations: List[TestCaseEvaluation]) -> List[Suggestion]:
        """Generate suggestions for optimizing test suite"""
        suggestions = []
        
        # Create evaluation lookup
        eval_lookup = {eval.test_case_id: eval for eval in evaluations}
        
        # Identify redundant test cases (similar high-scoring test cases)
        high_quality_cases = [
            tc for tc in test_cases
            if tc.id in eval_lookup and eval_lookup[tc.id].total_score >= self.rules['quality_thresholds']['excellent_quality_threshold']
        ]
        
        # Group by requirement to find potential redundancy
        cases_by_requirement = defaultdict(list)
        for tc in high_quality_cases:
            if tc.requirement_id:
                cases_by_requirement[tc.requirement_id].append(tc)
        
        redundant_candidates = [
            (req_id, tc_list) for req_id, tc_list in cases_by_requirement.items()
            if len(tc_list) > 5  # More than 5 high-quality test cases for one requirement
        ]
        
        if redundant_candidates:
            suggestion = Suggestion(
                id=f"test_optimization_{datetime.utcnow().timestamp()}",
                type=SuggestionType.TEST_OPTIMIZATION,
                priority=Priority.MEDIUM,
                title="Optimize Test Suite for Efficiency",
                description=f"Found {len(redundant_candidates)} requirements with potentially redundant test cases",
                rationale="Too many similar test cases can slow down testing without adding significant value.",
                confidence=0.7,
                impact_score=0.6,
                effort_estimate="medium",
                affected_items=[req_id for req_id, _ in redundant_candidates],
                recommended_actions=[
                    "Review test cases for redundancy and overlap",
                    "Consolidate similar test scenarios",
                    "Focus on high-value, unique test cases",
                    "Consider parameterized testing for variations",
                    "Maintain coverage while reducing execution time"
                ],
                expected_benefits=[
                    "Faster test execution",
                    "Reduced maintenance overhead",
                    "More focused testing effort",
                    "Better resource utilization"
                ],
                created_at=datetime.utcnow()
            )
            suggestions.append(suggestion)
        
        # Identify test cases that might benefit from automation
        manual_candidates = [
            tc for tc in test_cases
            if tc.id in eval_lookup and 
            eval_lookup[tc.id].executability_score >= 80 and
            eval_lookup[tc.id].total_score >= 75
        ]
        
        if len(manual_candidates) > 10:  # Suggest automation if many good candidates
            suggestion = Suggestion(
                id=f"automation_opportunity_{datetime.utcnow().timestamp()}",
                type=SuggestionType.TEST_OPTIMIZATION,
                priority=Priority.MEDIUM,
                title="Consider Test Automation Opportunities",
                description=f"Found {len(manual_candidates)} test cases suitable for automation",
                rationale="High-quality, executable test cases are good candidates for automation.",
                confidence=0.8,
                impact_score=0.7,
                effort_estimate="high",
                affected_items=[tc.id for tc in manual_candidates[:20]],  # Top 20 candidates
                recommended_actions=[
                    "Evaluate test cases for automation feasibility",
                    "Prioritize repetitive and regression test cases",
                    "Implement automated test frameworks",
                    "Start with highest-value test cases",
                    "Maintain manual tests for exploratory testing"
                ],
                expected_benefits=[
                    "Faster regression testing",
                    "Consistent test execution",
                    "Reduced manual testing effort",
                    "Better test coverage in CI/CD"
                ],
                created_at=datetime.utcnow()
            )
            suggestions.append(suggestion)
        
        return suggestions


class RiskAssessmentEngine:
    """Engine for assessing risks and generating mitigation suggestions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def assess_test_coverage_risk(self, requirements: List[Requirement],
                                test_cases: List[TestCase],
                                coverage_analyses: List[CoverageAnalysis]) -> RiskAssessment:
        """Assess risk based on test coverage"""
        try:
            total_requirements = len(requirements)
            if total_requirements == 0:
                return RiskAssessment("low", 0.0, [], [], 0.0)
            
            # Calculate overall coverage
            coverage_scores = []
            uncovered_count = 0
            
            for req in requirements:
                coverage_analysis = next((ca for ca in coverage_analyses if ca.requirement_id == req.id), None)
                if coverage_analysis:
                    coverage_scores.append(coverage_analysis.coverage_percentage)
                else:
                    coverage_scores.append(0.0)
                    uncovered_count += 1
            
            avg_coverage = sum(coverage_scores) / len(coverage_scores)
            low_coverage_count = sum(1 for score in coverage_scores if score < 50)
            
            # Calculate risk score
            risk_score = 0.0
            risk_factors = []
            
            if avg_coverage < 50:
                risk_score += 0.4
                risk_factors.append(f"Low average coverage ({avg_coverage:.1f}%)")
            
            if uncovered_count > total_requirements * 0.2:  # More than 20% uncovered
                risk_score += 0.3
                risk_factors.append(f"High number of uncovered requirements ({uncovered_count})")
            
            if low_coverage_count > total_requirements * 0.3:  # More than 30% with low coverage
                risk_score += 0.3
                risk_factors.append(f"Many requirements with low coverage ({low_coverage_count})")
            
            # Determine risk level
            if risk_score >= 0.8:
                risk_level = "critical"
            elif risk_score >= 0.6:
                risk_level = "high"
            elif risk_score >= 0.3:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            # Generate mitigation suggestions
            mitigation_suggestions = []
            if avg_coverage < 70:
                mitigation_suggestions.append("Increase overall test coverage to at least 70%")
            if uncovered_count > 0:
                mitigation_suggestions.append("Create test cases for uncovered requirements")
            if low_coverage_count > 0:
                mitigation_suggestions.append("Enhance test cases for low-coverage requirements")
            
            confidence = min(0.9, len(coverage_analyses) / max(1, total_requirements))
            
            return RiskAssessment(
                risk_level=risk_level,
                risk_score=risk_score,
                risk_factors=risk_factors,
                mitigation_suggestions=mitigation_suggestions,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error assessing coverage risk: {str(e)}")
            return RiskAssessment("unknown", 0.0, ["Error in risk assessment"], [], 0.0)
    
    def assess_defect_trend_risk(self, defects: List[Defect]) -> RiskAssessment:
        """Assess risk based on defect trends"""
        try:
            if not defects:
                return RiskAssessment("low", 0.0, [], [], 1.0)
            
            # Analyze defect trends over time
            now = datetime.utcnow()
            recent_defects = [d for d in defects if (now - d.detected_at).days <= 30]
            older_defects = [d for d in defects if (now - d.detected_at).days > 30]
            
            # Calculate defect rates
            recent_rate = len(recent_defects) / 30 if recent_defects else 0  # defects per day
            older_rate = len(older_defects) / max(1, (now - min(d.detected_at for d in older_defects)).days) if older_defects else 0
            
            # Analyze severity distribution
            critical_defects = [d for d in recent_defects if d.severity == 'critical']
            high_defects = [d for d in recent_defects if d.severity == 'high']
            
            # Calculate risk score
            risk_score = 0.0
            risk_factors = []
            
            if recent_rate > older_rate * 1.5:  # 50% increase in defect rate
                risk_score += 0.4
                risk_factors.append("Increasing defect detection rate")
            
            if len(critical_defects) >= 2:
                risk_score += 0.3
                risk_factors.append(f"High number of critical defects ({len(critical_defects)})")
            
            if len(high_defects) > 5:
                risk_score += 0.2
                risk_factors.append(f"High number of high-severity defects ({len(high_defects)})")
            
            # Check for unresolved defects
            unresolved_defects = [d for d in defects if d.status in ['open', 'in_progress']]
            if len(unresolved_defects) > len(defects) * 0.3:  # More than 30% unresolved
                risk_score += 0.2
                risk_factors.append(f"High number of unresolved defects ({len(unresolved_defects)})")
            
            # Determine risk level
            if risk_score >= 0.8:
                risk_level = "critical"
            elif risk_score >= 0.6:
                risk_level = "high"
            elif risk_score >= 0.3:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            # Generate mitigation suggestions
            mitigation_suggestions = []
            if critical_defects:
                mitigation_suggestions.append("Prioritize resolution of critical defects")
            if recent_rate > older_rate:
                mitigation_suggestions.append("Investigate causes of increasing defect rate")
            if unresolved_defects:
                mitigation_suggestions.append("Focus on resolving unresolved defects")
            
            confidence = min(0.9, len(defects) / 20)  # Higher confidence with more data
            
            return RiskAssessment(
                risk_level=risk_level,
                risk_score=risk_score,
                risk_factors=risk_factors,
                mitigation_suggestions=mitigation_suggestions,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error assessing defect trend risk: {str(e)}")
            return RiskAssessment("unknown", 0.0, ["Error in risk assessment"], [], 0.0)


class IntelligentSuggestionEngine:
    """Main intelligent suggestion engine that coordinates all suggestion components"""
    
    def __init__(self, db: Session):
        self.db = db
        self.rule_engine = RuleBasedSuggestionEngine(db)
        self.risk_engine = RiskAssessmentEngine(db)
    
    def generate_comprehensive_suggestions(self, 
                                         requirements: List[Requirement],
                                         test_cases: List[TestCase],
                                         evaluations: List[TestCaseEvaluation],
                                         defects: List[Defect],
                                         coverage_analyses: List[CoverageAnalysis]) -> Dict[str, Any]:
        """Generate comprehensive suggestions across all categories"""
        try:
            all_suggestions = []
            
            # Generate different types of suggestions
            quality_suggestions = self.rule_engine.generate_quality_improvement_suggestions(
                test_cases, evaluations
            )
            all_suggestions.extend(quality_suggestions)
            
            coverage_suggestions = self.rule_engine.generate_coverage_enhancement_suggestions(
                requirements, test_cases, coverage_analyses
            )
            all_suggestions.extend(coverage_suggestions)
            
            defect_suggestions = self.rule_engine.generate_defect_prevention_suggestions(
                defects, test_cases
            )
            all_suggestions.extend(defect_suggestions)
            
            optimization_suggestions = self.rule_engine.generate_test_optimization_suggestions(
                test_cases, evaluations
            )
            all_suggestions.extend(optimization_suggestions)
            
            # Perform risk assessments
            coverage_risk = self.risk_engine.assess_test_coverage_risk(
                requirements, test_cases, coverage_analyses
            )
            
            defect_risk = self.risk_engine.assess_defect_trend_risk(defects)
            
            # Sort suggestions by priority and impact
            all_suggestions.sort(key=lambda s: (
                {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}[s.priority.value],
                s.impact_score
            ), reverse=True)
            
            # Generate summary statistics
            suggestion_stats = {
                'total_suggestions': len(all_suggestions),
                'by_priority': Counter(s.priority.value for s in all_suggestions),
                'by_type': Counter(s.type.value for s in all_suggestions),
                'high_impact_count': sum(1 for s in all_suggestions if s.impact_score >= 0.8),
                'actionable_count': sum(1 for s in all_suggestions if s.confidence >= 0.7)
            }
            
            return {
                'suggestions': [asdict(s) for s in all_suggestions],
                'risk_assessments': {
                    'coverage_risk': asdict(coverage_risk),
                    'defect_risk': asdict(defect_risk)
                },
                'statistics': suggestion_stats,
                'generated_at': datetime.utcnow(),
                'total_items_analyzed': {
                    'requirements': len(requirements),
                    'test_cases': len(test_cases),
                    'evaluations': len(evaluations),
                    'defects': len(defects),
                    'coverage_analyses': len(coverage_analyses)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating comprehensive suggestions: {str(e)}")
            raise
    
    def get_prioritized_action_plan(self, suggestions: List[Suggestion],
                                  max_items: int = 10) -> List[Dict[str, Any]]:
        """Get a prioritized action plan from suggestions"""
        try:
            # Filter and sort suggestions
            actionable_suggestions = [s for s in suggestions if s.confidence >= 0.7]
            actionable_suggestions.sort(key=lambda s: (
                {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}[s.priority.value],
                s.impact_score,
                s.confidence
            ), reverse=True)
            
            # Create action plan
            action_plan = []
            for i, suggestion in enumerate(actionable_suggestions[:max_items]):
                action_item = {
                    'rank': i + 1,
                    'suggestion_id': suggestion.id,
                    'title': suggestion.title,
                    'priority': suggestion.priority.value,
                    'impact_score': suggestion.impact_score,
                    'effort_estimate': suggestion.effort_estimate,
                    'confidence': suggestion.confidence,
                    'immediate_actions': suggestion.recommended_actions[:3],  # Top 3 actions
                    'affected_items_count': len(suggestion.affected_items),
                    'expected_roi': self._calculate_expected_roi(suggestion)
                }
                action_plan.append(action_item)
            
            return action_plan
            
        except Exception as e:
            logger.error(f"Error creating action plan: {str(e)}")
            return []
    
    def _calculate_expected_roi(self, suggestion: Suggestion) -> str:
        """Calculate expected ROI for a suggestion"""
        # Simple ROI calculation based on impact and effort
        effort_scores = {'low': 1, 'medium': 2, 'high': 3}
        effort_score = effort_scores.get(suggestion.effort_estimate, 2)
        
        roi_score = (suggestion.impact_score * suggestion.confidence) / effort_score
        
        if roi_score >= 0.8:
            return "high"
        elif roi_score >= 0.5:
            return "medium"
        else:
            return "low"