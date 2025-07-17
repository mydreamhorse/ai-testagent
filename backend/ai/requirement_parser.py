import re
import jieba
import spacy
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sqlalchemy.orm import Session
from ..models import ParsedFeature, Requirement
from ..config import settings
import logging

logger = logging.getLogger(__name__)

@dataclass
class FeatureInfo:
    name: str
    type: str
    description: str
    parameters: Dict[str, Any]
    constraints: Dict[str, Any]
    dependencies: List[str]
    priority: str


class RequirementParser:
    def __init__(self):
        # Initialize Chinese word segmentation
        jieba.initialize()
        
        # Load spaCy model for English (if available)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("English spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        
        # Define seat function keywords
        self.seat_functions = {
            "电动调节": ["电动", "调节", "前后", "上下", "靠背", "角度", "高度"],
            "记忆功能": ["记忆", "存储", "位置", "用户", "设置", "自动"],
            "加热功能": ["加热", "温度", "控制", "调温", "保温"],
            "通风功能": ["通风", "风扇", "换气", "散热", "吹风"],
            "按摩功能": ["按摩", "震动", "模式", "强度", "节奏"],
            "安全功能": ["安全", "保护", "防夹", "过载", "故障", "检测"]
        }
        
        # Define test types
        self.test_types = {
            "功能测试": ["功能", "正常", "基本", "操作"],
            "边界测试": ["边界", "极限", "最大", "最小", "范围"],
            "异常测试": ["异常", "错误", "故障", "失败", "中断"],
            "性能测试": ["性能", "速度", "响应", "时间", "效率"],
            "安全测试": ["安全", "防护", "保护", "风险"]
        }
        
        # Define priority keywords
        self.priority_keywords = {
            "high": ["重要", "关键", "核心", "必须", "紧急"],
            "medium": ["一般", "普通", "常规", "标准"],
            "low": ["次要", "可选", "建议", "补充"]
        }
    
    def parse_requirement(self, requirement: Requirement, db: Session) -> List[FeatureInfo]:
        """Parse a requirement and extract features"""
        try:
            content = requirement.content
            features = []
            
            # Split content into sentences
            sentences = self._split_sentences(content)
            
            # Extract features from each sentence
            for sentence in sentences:
                feature_info = self._extract_feature_from_sentence(sentence)
                if feature_info:
                    features.append(feature_info)
            
            # Save parsed features to database
            self._save_features_to_db(features, requirement.id, db)
            
            return features
            
        except Exception as e:
            logger.error(f"Error parsing requirement {requirement.id}: {str(e)}")
            return []
    
    def _split_sentences(self, content: str) -> List[str]:
        """Split content into sentences"""
        # Simple sentence splitting for Chinese and English
        sentences = re.split(r'[。！？\.\!\?]', content)
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_feature_from_sentence(self, sentence: str) -> Optional[FeatureInfo]:
        """Extract feature information from a sentence"""
        # Tokenize the sentence
        tokens = list(jieba.cut(sentence))
        
        # Find function type
        function_type = self._identify_function_type(tokens)
        if not function_type:
            return None
        
        # Extract feature name
        feature_name = self._extract_feature_name(sentence, function_type)
        
        # Extract parameters
        parameters = self._extract_parameters(sentence, tokens)
        
        # Extract constraints
        constraints = self._extract_constraints(sentence, tokens)
        
        # Extract dependencies
        dependencies = self._extract_dependencies(sentence, tokens)
        
        # Determine priority
        priority = self._determine_priority(sentence, tokens)
        
        return FeatureInfo(
            name=feature_name,
            type=function_type,
            description=sentence,
            parameters=parameters,
            constraints=constraints,
            dependencies=dependencies,
            priority=priority
        )
    
    def _identify_function_type(self, tokens: List[str]) -> Optional[str]:
        """Identify the function type based on tokens"""
        for function_type, keywords in self.seat_functions.items():
            if any(keyword in tokens for keyword in keywords):
                return function_type
        return None
    
    def _extract_feature_name(self, sentence: str, function_type: str) -> str:
        """Extract feature name from sentence"""
        # Simple name extraction - can be improved
        if function_type in sentence:
            return function_type
        
        # Try to find action words
        action_words = re.findall(r'(\w+)(调节|控制|设置|操作)', sentence)
        if action_words:
            return f"{action_words[0][0]}{action_words[0][1]}"
        
        return f"{function_type}功能"
    
    def _extract_parameters(self, sentence: str, tokens: List[str]) -> Dict[str, Any]:
        """Extract parameters from sentence"""
        parameters = {}
        
        # Extract numerical parameters
        numbers = re.findall(r'(\d+(?:\.\d+)?)\s*([°%秒分钟小时毫米厘米]?)', sentence)
        for value, unit in numbers:
            if unit:
                parameters[f"value_{unit}"] = float(value)
        
        # Extract range parameters
        ranges = re.findall(r'(\d+(?:\.\d+)?)\s*[-~到至]\s*(\d+(?:\.\d+)?)', sentence)
        for min_val, max_val in ranges:
            parameters["min_value"] = float(min_val)
            parameters["max_value"] = float(max_val)
        
        return parameters
    
    def _extract_constraints(self, sentence: str, tokens: List[str]) -> Dict[str, Any]:
        """Extract constraints from sentence"""
        constraints = {}
        
        # Extract time constraints
        time_constraints = re.findall(r'(\d+)\s*(秒|分钟|小时)', sentence)
        for value, unit in time_constraints:
            constraints[f"time_{unit}"] = int(value)
        
        # Extract safety constraints
        if any(word in sentence for word in ["不能", "禁止", "不允许", "不得"]):
            constraints["safety_restriction"] = True
        
        # Extract operational constraints
        if any(word in sentence for word in ["同时", "并发", "冲突"]):
            constraints["concurrent_operation"] = True
        
        return constraints
    
    def _extract_dependencies(self, sentence: str, tokens: List[str]) -> List[str]:
        """Extract dependencies from sentence"""
        dependencies = []
        
        # Look for dependency keywords
        dependency_keywords = ["依赖", "需要", "要求", "基于", "前提"]
        for keyword in dependency_keywords:
            if keyword in sentence:
                # Try to find what it depends on
                parts = sentence.split(keyword)
                if len(parts) > 1:
                    dep_part = parts[1].strip()
                    # Extract the dependency (simplified)
                    dep_match = re.search(r'(\w+功能|\w+系统|\w+模块)', dep_part)
                    if dep_match:
                        dependencies.append(dep_match.group(1))
        
        return dependencies
    
    def _determine_priority(self, sentence: str, tokens: List[str]) -> str:
        """Determine priority based on sentence content"""
        for priority, keywords in self.priority_keywords.items():
            if any(keyword in sentence for keyword in keywords):
                return priority
        
        # Default priority
        return "medium"
    
    def _save_features_to_db(self, features: List[FeatureInfo], requirement_id: int, db: Session):
        """Save parsed features to database"""
        try:
            # Delete existing features for this requirement
            db.query(ParsedFeature).filter(ParsedFeature.requirement_id == requirement_id).delete()
            
            # Add new features
            for feature in features:
                db_feature = ParsedFeature(
                    requirement_id=requirement_id,
                    feature_name=feature.name,
                    feature_type=feature.type,
                    description=feature.description,
                    parameters=feature.parameters,
                    constraints=feature.constraints,
                    dependencies=feature.dependencies,
                    priority=feature.priority
                )
                db.add(db_feature)
            
            db.commit()
            logger.info(f"Saved {len(features)} features for requirement {requirement_id}")
            
        except Exception as e:
            logger.error(f"Error saving features to database: {str(e)}")
            db.rollback()
    
    def get_test_type_suggestions(self, feature: FeatureInfo) -> List[str]:
        """Get test type suggestions based on feature"""
        suggestions = []
        
        # Always suggest function test
        suggestions.append("功能测试")
        
        # Suggest based on feature type
        if feature.type in ["安全功能"]:
            suggestions.append("安全测试")
        
        if feature.parameters:
            suggestions.append("边界测试")
        
        if "异常" in feature.description or "错误" in feature.description:
            suggestions.append("异常测试")
        
        if "性能" in feature.description or "速度" in feature.description:
            suggestions.append("性能测试")
        
        return suggestions