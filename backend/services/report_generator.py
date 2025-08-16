"""
Report Generation Service

This module implements the core report generation functionality for the intelligent
test reporting system. It provides the ReportGenerator class and related interfaces
for generating various types of test reports.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from dataclasses import dataclass, asdict

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from backend.models import (
    Report, TestCase, Requirement, Defect, CoverageAnalysis, 
    TestCaseEvaluation, User, ReportTemplate
)

logger = logging.getLogger(__name__)


def serialize_for_json(obj):
    """Convert objects to JSON-serializable format"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return serialize_for_json(obj.__dict__)
    else:
        return obj


class ReportFormat(Enum):
    """Supported report export formats"""
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"


class ReportType(Enum):
    """Types of reports that can be generated"""
    EXECUTION = "execution"
    DEFECT_ANALYSIS = "defect_analysis"
    COVERAGE = "coverage"
    TREND = "trend"
    CUSTOM = "custom"


@dataclass
class DateRange:
    """Date range for report data filtering"""
    start_date: datetime
    end_date: datetime


@dataclass
class ExecutionSummary:
    """Summary of test execution results"""
    total_test_cases: int
    passed_test_cases: int
    failed_test_cases: int
    pass_rate: float
    execution_time: Optional[float] = None
    avg_score: Optional[float] = None


@dataclass
class DefectSummary:
    """Summary of defect analysis"""
    total_defects: int
    critical_defects: int
    high_defects: int
    medium_defects: int
    low_defects: int
    open_defects: int
    resolved_defects: int
    defect_rate: float


@dataclass
class CoverageSummary:
    """Summary of coverage analysis"""
    total_requirements: int
    covered_requirements: int
    coverage_percentage: float
    uncovered_areas: List[str]
    coverage_by_module: Dict[str, float]


class DefectPatternAnalyzer:
    """Analyzes defect patterns and trends"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def identify_defect_patterns(self, defects: List[Defect]) -> Dict[str, Any]:
        """Identify patterns in defect data"""
        patterns = {
            'recurring_defects': self._find_recurring_defects(defects),
            'severity_trends': self._analyze_severity_trends(defects),
            'type_correlations': self._analyze_type_correlations(defects),
            'resolution_time_patterns': self._analyze_resolution_times(defects)
        }
        return patterns
    
    def _find_recurring_defects(self, defects: List[Defect]) -> List[Dict[str, Any]]:
        """Find defects that occur repeatedly"""
        defect_descriptions = {}
        for defect in defects:
            # Simple pattern matching based on description similarity
            desc_key = defect.description.lower()[:50]  # First 50 chars as key
            if desc_key not in defect_descriptions:
                defect_descriptions[desc_key] = []
            defect_descriptions[desc_key].append(defect)
        
        # Find patterns with more than one occurrence
        recurring = []
        for desc_key, defect_list in defect_descriptions.items():
            if len(defect_list) > 1:
                recurring.append({
                    'pattern': desc_key,
                    'count': len(defect_list),
                    'defect_ids': [d.id for d in defect_list],
                    'severity_distribution': self._get_severity_distribution(defect_list)
                })
        
        return sorted(recurring, key=lambda x: x['count'], reverse=True)
    
    def _analyze_severity_trends(self, defects: List[Defect]) -> Dict[str, Any]:
        """Analyze trends in defect severity over time"""
        if not defects:
            return {'trend': 'no_data', 'severity_over_time': []}
        
        # Sort defects by detection time
        sorted_defects = sorted(defects, key=lambda d: d.detected_at)
        
        # Group by time periods (e.g., weekly)
        severity_over_time = []
        current_week_start = None
        current_week_data = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for defect in sorted_defects:
            week_start = defect.detected_at.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = week_start - timedelta(days=week_start.weekday())
            
            if current_week_start != week_start:
                if current_week_start is not None:
                    severity_over_time.append({
                        'week_start': current_week_start,
                        'severities': current_week_data.copy()
                    })
                current_week_start = week_start
                current_week_data = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            
            if defect.severity in current_week_data:
                current_week_data[defect.severity] += 1
        
        # Add the last week
        if current_week_start is not None:
            severity_over_time.append({
                'week_start': current_week_start,
                'severities': current_week_data
            })
        
        # Determine trend
        if len(severity_over_time) >= 2:
            recent_critical = severity_over_time[-1]['severities']['critical']
            previous_critical = severity_over_time[-2]['severities']['critical']
            
            if recent_critical > previous_critical:
                trend = 'worsening'
            elif recent_critical < previous_critical:
                trend = 'improving'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'trend': trend,
            'severity_over_time': severity_over_time
        }
    
    def _analyze_type_correlations(self, defects: List[Defect]) -> Dict[str, Any]:
        """Analyze correlations between defect types and other factors"""
        type_severity_correlation = {}
        type_resolution_correlation = {}
        
        for defect in defects:
            defect_type = defect.defect_type
            
            # Type-Severity correlation
            if defect_type not in type_severity_correlation:
                type_severity_correlation[defect_type] = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            type_severity_correlation[defect_type][defect.severity] += 1
            
            # Type-Resolution time correlation
            if defect.resolved_at and defect.detected_at:
                resolution_time = (defect.resolved_at - defect.detected_at).days
                if defect_type not in type_resolution_correlation:
                    type_resolution_correlation[defect_type] = []
                type_resolution_correlation[defect_type].append(resolution_time)
        
        # Calculate average resolution times
        avg_resolution_times = {}
        for defect_type, times in type_resolution_correlation.items():
            if times:
                avg_resolution_times[defect_type] = sum(times) / len(times)
        
        return {
            'type_severity_correlation': type_severity_correlation,
            'avg_resolution_times': avg_resolution_times
        }
    
    def _analyze_resolution_times(self, defects: List[Defect]) -> Dict[str, Any]:
        """Analyze patterns in defect resolution times"""
        resolution_times = []
        unresolved_count = 0
        
        for defect in defects:
            if defect.resolved_at and defect.detected_at:
                resolution_time = (defect.resolved_at - defect.detected_at).days
                resolution_times.append({
                    'defect_id': defect.id,
                    'severity': defect.severity,
                    'type': defect.defect_type,
                    'resolution_days': resolution_time
                })
            else:
                unresolved_count += 1
        
        if not resolution_times:
            return {
                'avg_resolution_time': 0,
                'resolution_by_severity': {},
                'unresolved_count': unresolved_count
            }
        
        # Calculate averages by severity
        resolution_by_severity = {}
        for item in resolution_times:
            severity = item['severity']
            if severity not in resolution_by_severity:
                resolution_by_severity[severity] = []
            resolution_by_severity[severity].append(item['resolution_days'])
        
        # Calculate averages
        for severity in resolution_by_severity:
            times = resolution_by_severity[severity]
            resolution_by_severity[severity] = {
                'avg_days': sum(times) / len(times),
                'count': len(times),
                'min_days': min(times),
                'max_days': max(times)
            }
        
        avg_resolution_time = sum(item['resolution_days'] for item in resolution_times) / len(resolution_times)
        
        return {
            'avg_resolution_time': avg_resolution_time,
            'resolution_by_severity': resolution_by_severity,
            'unresolved_count': unresolved_count,
            'total_resolved': len(resolution_times)
        }
    
    def _get_severity_distribution(self, defects: List[Defect]) -> Dict[str, int]:
        """Get severity distribution for a list of defects"""
        distribution = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for defect in defects:
            if defect.severity in distribution:
                distribution[defect.severity] += 1
        return distribution
    
    def predict_defect_trends(self, defects: List[Defect], days_ahead: int = 30) -> Dict[str, Any]:
        """Predict defect trends for the next period"""
        if len(defects) < 5:  # Need minimum data for prediction
            return {
                'prediction': 'insufficient_data',
                'confidence': 0,
                'predicted_defects': 0
            }
        
        # Simple linear trend analysis
        sorted_defects = sorted(defects, key=lambda d: d.detected_at)
        
        # Calculate defects per day over the last period
        if len(sorted_defects) >= 2:
            time_span = (sorted_defects[-1].detected_at - sorted_defects[0].detected_at).days
            if time_span > 0:
                defects_per_day = len(sorted_defects) / time_span
                predicted_defects = int(defects_per_day * days_ahead)
                
                # Simple confidence calculation based on data consistency
                confidence = min(0.8, len(sorted_defects) / 20)  # Max 80% confidence
                
                return {
                    'prediction': 'trend_based',
                    'confidence': confidence,
                    'predicted_defects': predicted_defects,
                    'defects_per_day': defects_per_day,
                    'prediction_period_days': days_ahead
                }
        
        return {
            'prediction': 'insufficient_data',
            'confidence': 0,
            'predicted_defects': 0
        }


class CoverageAnalyzer:
    """Analyzes test coverage and requirement mapping"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_requirement_coverage(self, requirements: List[Requirement], 
                                   test_cases: List[TestCase]) -> Dict[str, Any]:
        """Analyze coverage of requirements by test cases"""
        coverage_map = {}
        uncovered_requirements = []
        coverage_gaps = []
        
        for requirement in requirements:
            # Find test cases that cover this requirement
            covering_test_cases = [tc for tc in test_cases if tc.requirement_id == requirement.id]
            
            coverage_info = {
                'requirement_id': requirement.id,
                'requirement_title': requirement.title,
                'total_test_cases': len(covering_test_cases),
                'test_case_ids': [tc.id for tc in covering_test_cases],
                'coverage_percentage': 0,
                'coverage_quality': 'none'
            }
            
            if covering_test_cases:
                # Calculate coverage quality based on test case diversity
                test_types = set(tc.test_type for tc in covering_test_cases if tc.test_type)
                priorities = set(tc.priority for tc in covering_test_cases if tc.priority)
                
                # Simple coverage percentage calculation
                # This could be enhanced with more sophisticated algorithms
                base_coverage = min(100, len(covering_test_cases) * 20)  # 20% per test case, max 100%
                type_bonus = len(test_types) * 5  # Bonus for test type diversity
                priority_bonus = len(priorities) * 3  # Bonus for priority diversity
                
                coverage_percentage = min(100, base_coverage + type_bonus + priority_bonus)
                coverage_info['coverage_percentage'] = coverage_percentage
                
                # Determine coverage quality
                if coverage_percentage >= 80:
                    coverage_info['coverage_quality'] = 'excellent'
                elif coverage_percentage >= 60:
                    coverage_info['coverage_quality'] = 'good'
                elif coverage_percentage >= 40:
                    coverage_info['coverage_quality'] = 'fair'
                else:
                    coverage_info['coverage_quality'] = 'poor'
                
                coverage_info['test_type_diversity'] = list(test_types)
                coverage_info['priority_diversity'] = list(priorities)
            else:
                uncovered_requirements.append({
                    'requirement_id': requirement.id,
                    'requirement_title': requirement.title,
                    'description': requirement.description
                })
            
            coverage_map[requirement.id] = coverage_info
        
        # Identify coverage gaps
        for req_id, coverage_info in coverage_map.items():
            if coverage_info['coverage_percentage'] < 60:  # Threshold for coverage gap
                coverage_gaps.append({
                    'requirement_id': req_id,
                    'requirement_title': coverage_info['requirement_title'],
                    'current_coverage': coverage_info['coverage_percentage'],
                    'gap_severity': 'high' if coverage_info['coverage_percentage'] < 30 else 'medium',
                    'recommended_actions': self._generate_coverage_recommendations(coverage_info)
                })
        
        return {
            'coverage_map': coverage_map,
            'uncovered_requirements': uncovered_requirements,
            'coverage_gaps': coverage_gaps,
            'overall_stats': self._calculate_overall_coverage_stats(coverage_map)
        }
    
    def _generate_coverage_recommendations(self, coverage_info: Dict[str, Any]) -> List[str]:
        """Generate recommendations to improve coverage"""
        recommendations = []
        
        if coverage_info['total_test_cases'] == 0:
            recommendations.append("Create basic functional test cases")
            recommendations.append("Add boundary value test cases")
            recommendations.append("Include negative test scenarios")
        elif coverage_info['total_test_cases'] < 3:
            recommendations.append("Add more test cases to improve coverage")
            
        if len(coverage_info.get('test_type_diversity', [])) < 2:
            recommendations.append("Add different types of tests (functional, boundary, exception)")
            
        if len(coverage_info.get('priority_diversity', [])) < 2:
            recommendations.append("Include test cases with different priority levels")
            
        if coverage_info['coverage_percentage'] < 40:
            recommendations.append("Consider requirement complexity and add comprehensive test scenarios")
            
        return recommendations
    
    def _calculate_overall_coverage_stats(self, coverage_map: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall coverage statistics"""
        if not coverage_map:
            return {
                'total_requirements': 0,
                'covered_requirements': 0,
                'average_coverage': 0,
                'coverage_distribution': {}
            }
        
        total_requirements = len(coverage_map)
        covered_requirements = sum(1 for info in coverage_map.values() if info['coverage_percentage'] > 0)
        average_coverage = sum(info['coverage_percentage'] for info in coverage_map.values()) / total_requirements
        
        # Coverage distribution
        distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0, 'none': 0}
        for info in coverage_map.values():
            quality = info['coverage_quality']
            distribution[quality] += 1
        
        return {
            'total_requirements': total_requirements,
            'covered_requirements': covered_requirements,
            'uncovered_requirements': total_requirements - covered_requirements,
            'average_coverage': average_coverage,
            'coverage_distribution': distribution
        }
    
    def create_coverage_heatmap_data(self, coverage_map: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """Create data structure for coverage heatmap visualization"""
        heatmap_data = []
        
        for req_id, coverage_info in coverage_map.items():
            heatmap_data.append({
                'requirement_id': req_id,
                'requirement_title': coverage_info['requirement_title'],
                'coverage_percentage': coverage_info['coverage_percentage'],
                'test_count': coverage_info['total_test_cases'],
                'quality': coverage_info['coverage_quality'],
                'color_intensity': self._calculate_color_intensity(coverage_info['coverage_percentage'])
            })
        
        # Sort by coverage percentage for better visualization
        heatmap_data.sort(key=lambda x: x['coverage_percentage'], reverse=True)
        
        return {
            'heatmap_data': heatmap_data,
            'color_scale': {
                'excellent': '#2E8B57',  # Sea Green
                'good': '#32CD32',       # Lime Green
                'fair': '#FFD700',       # Gold
                'poor': '#FF6347',       # Tomato
                'none': '#DC143C'        # Crimson
            },
            'visualization_config': {
                'title': 'Test Coverage Heatmap',
                'x_axis': 'Requirements',
                'y_axis': 'Coverage Percentage',
                'tooltip_fields': ['requirement_title', 'coverage_percentage', 'test_count']
            }
        }
    
    def _calculate_color_intensity(self, coverage_percentage: float) -> float:
        """Calculate color intensity for heatmap (0.0 to 1.0)"""
        return min(1.0, coverage_percentage / 100.0)
    
    def identify_coverage_trends(self, historical_coverage: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify trends in coverage over time"""
        if len(historical_coverage) < 2:
            return {
                'trend': 'insufficient_data',
                'trend_direction': 'unknown',
                'improvement_rate': 0
            }
        
        # Sort by date
        sorted_coverage = sorted(historical_coverage, key=lambda x: x.get('analysis_date', datetime.min))
        
        # Calculate trend
        recent_coverage = sorted_coverage[-1]['coverage_percentage']
        previous_coverage = sorted_coverage[-2]['coverage_percentage']
        
        if recent_coverage > previous_coverage:
            trend_direction = 'improving'
        elif recent_coverage < previous_coverage:
            trend_direction = 'declining'
        else:
            trend_direction = 'stable'
        
        # Calculate improvement rate (percentage points per time period)
        if len(sorted_coverage) >= 3:
            time_periods = len(sorted_coverage) - 1
            total_change = recent_coverage - sorted_coverage[0]['coverage_percentage']
            improvement_rate = total_change / time_periods
        else:
            improvement_rate = recent_coverage - previous_coverage
        
        return {
            'trend': 'trend_available',
            'trend_direction': trend_direction,
            'improvement_rate': improvement_rate,
            'current_coverage': recent_coverage,
            'previous_coverage': previous_coverage,
            'data_points': len(sorted_coverage)
        }


class ReportDataCollector:
    """Collects and processes data for report generation"""
    
    def __init__(self, db: Session):
        self.db = db
        self.defect_analyzer = DefectPatternAnalyzer(db)
        self.coverage_analyzer = CoverageAnalyzer(db)
    
    def collect_execution_data(self, 
                             test_case_ids: Optional[List[int]] = None,
                             date_range: Optional[DateRange] = None,
                             user_id: Optional[int] = None) -> Dict[str, Any]:
        """Collect test execution data for reporting"""
        try:
            query = self.db.query(TestCase)
            
            # Apply filters
            if test_case_ids:
                query = query.filter(TestCase.id.in_(test_case_ids))
            
            if user_id:
                query = query.filter(TestCase.user_id == user_id)
            
            if date_range:
                query = query.filter(
                    and_(
                        TestCase.created_at >= date_range.start_date,
                        TestCase.created_at <= date_range.end_date
                    )
                )
            
            test_cases = query.all()
            
            # Collect evaluation data
            evaluation_data = []
            total_score = 0
            evaluated_count = 0
            
            for test_case in test_cases:
                latest_evaluation = (
                    self.db.query(TestCaseEvaluation)
                    .filter(TestCaseEvaluation.test_case_id == test_case.id)
                    .order_by(TestCaseEvaluation.evaluated_at.desc())
                    .first()
                )
                
                if latest_evaluation:
                    evaluation_data.append({
                        'test_case_id': test_case.id,
                        'test_case_title': test_case.title,
                        'total_score': latest_evaluation.total_score,
                        'completeness_score': latest_evaluation.completeness_score,
                        'accuracy_score': latest_evaluation.accuracy_score,
                        'executability_score': latest_evaluation.executability_score,
                        'coverage_score': latest_evaluation.coverage_score,
                        'clarity_score': latest_evaluation.clarity_score,
                        'evaluated_at': latest_evaluation.evaluated_at,
                        'status': 'passed' if latest_evaluation.total_score >= 70 else 'failed'
                    })
                    total_score += latest_evaluation.total_score
                    evaluated_count += 1
                else:
                    evaluation_data.append({
                        'test_case_id': test_case.id,
                        'test_case_title': test_case.title,
                        'total_score': 0,
                        'status': 'not_evaluated'
                    })
            
            # Calculate summary statistics
            passed_count = sum(1 for eval_data in evaluation_data if eval_data['status'] == 'passed')
            failed_count = sum(1 for eval_data in evaluation_data if eval_data['status'] == 'failed')
            pass_rate = (passed_count / len(test_cases)) * 100 if test_cases else 0
            avg_score = total_score / evaluated_count if evaluated_count > 0 else 0
            
            summary = ExecutionSummary(
                total_test_cases=len(test_cases),
                passed_test_cases=passed_count,
                failed_test_cases=failed_count,
                pass_rate=pass_rate,
                avg_score=avg_score
            )
            
            data = {
                'summary': asdict(summary),
                'test_cases': evaluation_data,
                'collection_time': datetime.utcnow(),
                'filters_applied': {
                    'test_case_ids': test_case_ids,
                    'date_range': {
                        'start_date': date_range.start_date,
                        'end_date': date_range.end_date
                    } if date_range else None,
                    'user_id': user_id
                }
            }
            return serialize_for_json(data)
            
        except Exception as e:
            logger.error(f"Error collecting execution data: {str(e)}")
            raise
    
    def collect_defect_data(self, 
                          date_range: Optional[DateRange] = None,
                          severity_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """Collect defect data for analysis reporting"""
        try:
            query = self.db.query(Defect)
            
            # Apply filters
            if date_range:
                query = query.filter(
                    and_(
                        Defect.detected_at >= date_range.start_date,
                        Defect.detected_at <= date_range.end_date
                    )
                )
            
            if severity_filter:
                query = query.filter(Defect.severity.in_(severity_filter))
            
            defects = query.all()
            
            # Analyze defect patterns
            defect_by_type = {}
            defect_by_severity = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            defect_by_status = {}
            
            for defect in defects:
                # Count by type
                defect_by_type[defect.defect_type] = defect_by_type.get(defect.defect_type, 0) + 1
                
                # Count by severity
                if defect.severity in defect_by_severity:
                    defect_by_severity[defect.severity] += 1
                
                # Count by status
                defect_by_status[defect.status] = defect_by_status.get(defect.status, 0) + 1
            
            # Calculate summary
            total_defects = len(defects)
            open_defects = defect_by_status.get('open', 0) + defect_by_status.get('in_progress', 0)
            resolved_defects = defect_by_status.get('resolved', 0) + defect_by_status.get('closed', 0)
            
            # Calculate defect rate (defects per test case)
            total_test_cases = self.db.query(TestCase).count()
            defect_rate = (total_defects / total_test_cases) * 100 if total_test_cases > 0 else 0
            
            summary = DefectSummary(
                total_defects=total_defects,
                critical_defects=defect_by_severity['critical'],
                high_defects=defect_by_severity['high'],
                medium_defects=defect_by_severity['medium'],
                low_defects=defect_by_severity['low'],
                open_defects=open_defects,
                resolved_defects=resolved_defects,
                defect_rate=defect_rate
            )
            
            # Perform advanced pattern analysis
            pattern_analysis = self.defect_analyzer.identify_defect_patterns(defects)
            trend_prediction = self.defect_analyzer.predict_defect_trends(defects)
            
            data = {
                'summary': asdict(summary),
                'defects': [
                    {
                        'id': defect.id,
                        'test_case_id': defect.test_case_id,
                        'defect_type': defect.defect_type,
                        'severity': defect.severity,
                        'description': defect.description,
                        'status': defect.status,
                        'detected_at': defect.detected_at,
                        'resolved_at': defect.resolved_at
                    } for defect in defects
                ],
                'patterns': {
                    'by_type': defect_by_type,
                    'by_severity': defect_by_severity,
                    'by_status': defect_by_status
                },
                'advanced_analysis': {
                    'pattern_analysis': pattern_analysis,
                    'trend_prediction': trend_prediction
                },
                'collection_time': datetime.utcnow()
            }
            return serialize_for_json(data)
            
        except Exception as e:
            logger.error(f"Error collecting defect data: {str(e)}")
            raise
    
    def collect_coverage_data(self, 
                            requirement_ids: Optional[List[int]] = None) -> Dict[str, Any]:
        """Collect coverage analysis data for reporting"""
        try:
            # Get requirements and test cases
            req_query = self.db.query(Requirement)
            if requirement_ids:
                req_query = req_query.filter(Requirement.id.in_(requirement_ids))
            requirements = req_query.all()
            
            # Get all test cases for coverage analysis
            test_cases = self.db.query(TestCase).all()
            
            # Get existing coverage analyses
            coverage_query = self.db.query(CoverageAnalysis)
            if requirement_ids:
                coverage_query = coverage_query.filter(CoverageAnalysis.requirement_id.in_(requirement_ids))
            coverage_analyses = coverage_query.all()
            
            # Perform advanced coverage analysis
            requirement_coverage = self.coverage_analyzer.analyze_requirement_coverage(requirements, test_cases)
            
            # Create heatmap data for visualization
            heatmap_data = self.coverage_analyzer.create_coverage_heatmap_data(requirement_coverage['coverage_map'])
            
            # Analyze coverage trends if historical data exists
            historical_coverage = [
                {
                    'coverage_percentage': ca.coverage_percentage,
                    'analysis_date': ca.analysis_date
                } for ca in coverage_analyses
            ]
            coverage_trends = self.coverage_analyzer.identify_coverage_trends(historical_coverage)
            
            # Calculate basic statistics for backward compatibility
            total_requirements = len(requirements)
            covered_requirements = requirement_coverage['overall_stats']['covered_requirements']
            overall_coverage = requirement_coverage['overall_stats']['average_coverage']
            
            # Group by module from existing coverage analyses
            coverage_by_module = {}
            uncovered_areas = []
            
            for analysis in coverage_analyses:
                module = analysis.function_module
                if module not in coverage_by_module:
                    coverage_by_module[module] = []
                
                coverage_by_module[module].append(analysis.coverage_percentage)
                
                # Collect uncovered areas
                if analysis.uncovered_areas:
                    uncovered_areas.extend(analysis.uncovered_areas)
            
            # Calculate average coverage by module
            module_averages = {
                module: sum(percentages) / len(percentages)
                for module, percentages in coverage_by_module.items()
            }
            
            summary = CoverageSummary(
                total_requirements=total_requirements,
                covered_requirements=covered_requirements,
                coverage_percentage=overall_coverage,
                uncovered_areas=list(set(uncovered_areas)),
                coverage_by_module=module_averages
            )
            
            data = {
                'summary': asdict(summary),
                'coverage_details': [
                    {
                        'requirement_id': ca.requirement_id,
                        'function_module': ca.function_module,
                        'coverage_percentage': ca.coverage_percentage,
                        'covered_test_cases': ca.covered_test_cases,
                        'total_test_cases': ca.total_test_cases,
                        'uncovered_areas': ca.uncovered_areas,
                        'analysis_date': ca.analysis_date
                    } for ca in coverage_analyses
                ],
                'advanced_analysis': {
                    'requirement_coverage': requirement_coverage,
                    'heatmap_data': heatmap_data,
                    'coverage_trends': coverage_trends
                },
                'collection_time': datetime.utcnow()
            }
            return serialize_for_json(data)
            
        except Exception as e:
            logger.error(f"Error collecting coverage data: {str(e)}")
            raise


class ReportGenerator:
    """Main report generation class"""
    
    def __init__(self, db: Session):
        self.db = db
        self.data_collector = ReportDataCollector(db)
    
    def generate_execution_report(self, 
                                test_case_ids: Optional[List[int]] = None,
                                date_range: Optional[DateRange] = None,
                                user_id: Optional[int] = None,
                                template_id: Optional[int] = None) -> Report:
        """Generate test execution report"""
        try:
            logger.info(f"Generating execution report for user {user_id}")
            
            # Collect execution data
            execution_data = self.data_collector.collect_execution_data(
                test_case_ids=test_case_ids,
                date_range=date_range,
                user_id=user_id
            )
            
            # Create report record
            report = Report(
                title=f"Test Execution Report - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                report_type=ReportType.EXECUTION.value,
                template_id=template_id,
                generated_by=user_id,
                generation_time=datetime.utcnow(),
                data_range_start=date_range.start_date if date_range else None,
                data_range_end=date_range.end_date if date_range else None,
                report_data=execution_data,
                status="completed"
            )
            
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            
            logger.info(f"Successfully generated execution report with ID {report.id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating execution report: {str(e)}")
            self.db.rollback()
            raise
    
    def generate_defect_analysis_report(self,
                                      date_range: Optional[DateRange] = None,
                                      severity_filter: Optional[List[str]] = None,
                                      user_id: Optional[int] = None,
                                      template_id: Optional[int] = None) -> Report:
        """Generate defect analysis report"""
        try:
            logger.info(f"Generating defect analysis report for user {user_id}")
            
            # Collect defect data
            defect_data = self.data_collector.collect_defect_data(
                date_range=date_range,
                severity_filter=severity_filter
            )
            
            # Create report record
            report = Report(
                title=f"Defect Analysis Report - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                report_type=ReportType.DEFECT_ANALYSIS.value,
                template_id=template_id,
                generated_by=user_id,
                generation_time=datetime.utcnow(),
                data_range_start=date_range.start_date if date_range else None,
                data_range_end=date_range.end_date if date_range else None,
                report_data=defect_data,
                status="completed"
            )
            
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            
            logger.info(f"Successfully generated defect analysis report with ID {report.id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating defect analysis report: {str(e)}")
            self.db.rollback()
            raise
    
    def generate_coverage_report(self,
                               requirement_ids: Optional[List[int]] = None,
                               user_id: Optional[int] = None,
                               template_id: Optional[int] = None) -> Report:
        """Generate coverage analysis report"""
        try:
            logger.info(f"Generating coverage report for user {user_id}")
            
            # Collect coverage data
            coverage_data = self.data_collector.collect_coverage_data(
                requirement_ids=requirement_ids
            )
            
            # Create report record
            report = Report(
                title=f"Coverage Analysis Report - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                report_type=ReportType.COVERAGE.value,
                template_id=template_id,
                generated_by=user_id,
                generation_time=datetime.utcnow(),
                report_data=coverage_data,
                status="completed"
            )
            
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            
            logger.info(f"Successfully generated coverage report with ID {report.id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating coverage report: {str(e)}")
            self.db.rollback()
            raise
    
    def export_report(self, report: Report, format: ReportFormat) -> bytes:
        """Export report to specified format"""
        try:
            logger.info(f"Exporting report {report.id} to {format.value} format")
            
            if format == ReportFormat.JSON:
                return self._export_to_json(report)
            elif format == ReportFormat.HTML:
                return self._export_to_html(report)
            elif format == ReportFormat.PDF:
                return self._export_to_pdf(report)
            elif format == ReportFormat.EXCEL:
                return self._export_to_excel(report)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting report: {str(e)}")
            raise
    
    def _export_to_json(self, report: Report) -> bytes:
        """Export report to JSON format"""
        export_data = {
            'report_id': report.id,
            'title': report.title,
            'report_type': report.report_type,
            'generation_time': report.generation_time.isoformat(),
            'data_range_start': report.data_range_start.isoformat() if report.data_range_start else None,
            'data_range_end': report.data_range_end.isoformat() if report.data_range_end else None,
            'report_data': report.report_data
        }
        
        return json.dumps(export_data, indent=2, default=str).encode('utf-8')
    
    def _export_to_html(self, report: Report) -> bytes:
        """Export report to HTML format"""
        # Basic HTML template - can be enhanced with proper templating
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; }}
                .summary {{ margin: 20px 0; }}
                .data-section {{ margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report.title}</h1>
                <p>Generated: {report.generation_time}</p>
                <p>Type: {report.report_type}</p>
            </div>
            <div class="summary">
                <h2>Report Data</h2>
                <pre>{json.dumps(report.report_data, indent=2, default=str)}</pre>
            </div>
        </body>
        </html>
        """
        
        return html_content.encode('utf-8')
    
    def _export_to_pdf(self, report: Report) -> bytes:
        """Export report to PDF format"""
        # Placeholder implementation - would need PDF library like reportlab
        # For now, return HTML content as bytes
        return self._export_to_html(report)
    
    def _export_to_excel(self, report: Report) -> bytes:
        """Export report to Excel format"""
        # Placeholder implementation - would need Excel library like openpyxl
        # For now, return JSON content as bytes
        return self._export_to_json(report)