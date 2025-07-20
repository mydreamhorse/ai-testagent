import pytest
import sys
import os
import warnings
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 从根本上过滤警告
warnings.filterwarnings("ignore", category=pytest.PytestCollectionWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 特别过滤spacy和weasel的弃用警告
warnings.filterwarnings("ignore", message="Importing 'parser.split_arg_string' is deprecated")
warnings.filterwarnings("ignore", message="'BaseCommand' is deprecated")

def pytest_ignore_collect(collection_path):
    """从根本上忽略backend目录，避免pytest尝试收集其中的类"""
    path_str = str(collection_path)
    if "backend" in path_str:
        return True
    return False

def pytest_collection_modifyitems(config, items):
    """确保只收集tests目录中的测试"""
    items[:] = [item for item in items if item.nodeid.startswith("tests/")]

def pytest_configure(config):
    """配置pytest，确保正确的收集行为"""
    # 设置环境变量来阻止pytest收集backend目录
    os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    
    # 确保只从tests目录收集
    if not hasattr(config.option, 'testpaths'):
        config.option.testpaths = ["tests"]

# 从根本上阻止pytest收集backend模块中的类
def pytest_collect_file(parent, path):
    """阻止收集backend目录中的文件"""
    if "backend" in str(path):
        return None
    return None

# 使用pytest的钩子来阻止收集特定类
def pytest_collectstart(collector):
    """在收集开始时过滤掉backend模块中的类"""
    if hasattr(collector, 'obj') and collector.obj:
        module_name = getattr(collector.obj, '__module__', '')
        if 'backend' in module_name:
            # 如果是backend模块中的类，跳过收集
            collector.obj = None

# 在pytest会话开始时设置警告过滤
def pytest_sessionstart(session):
    """在测试会话开始时设置警告过滤"""
    import warnings
    warnings.filterwarnings("ignore", category=pytest.PytestCollectionWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", message="Importing 'parser.split_arg_string' is deprecated")
    warnings.filterwarnings("ignore", message="'BaseCommand' is deprecated") 