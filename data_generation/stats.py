import json
from typing import Dict, Any, List, Union
from utils.logger_config import get_logger

logger = get_logger(name="data_generation_stats", log_file="data_generation_stats.log")

class DataGenerationStats:
    """
    数据生成结果统计类
    用于统计数据生成结果的数量指标
    """
    
    def __init__(self):
        self.logger = logger
        
    def load_results(self, file_path: str) -> List[Dict[str, Any]]:
        """
        从JSONL文件加载数据生成结果

        Args:
            file_path (str): 结果文件路径

        Returns:
            List[Dict[str, Any]]: 生成结果列表
        """
        results = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        results.append(json.loads(line))
        except Exception as e:
            self.logger.error(f"Error loading results from {file_path}: {e}")
            raise
        return results
    
    def calculate_numeric_stats(self, values: List[Union[int, float]]) -> Dict[str, Any]:
        """
        计算数值列表的统计信息

        Args:
            values (List[Union[int, float]]): 数值列表

        Returns:
            Dict[str, Any]: 统计信息
        """
        if not values:
            return {
                "count": 0,
                "total": 0,
                "average": 0.0,
                "min": None,
                "max": None
            }
        
        return {
            "count": len(values),
            "total": sum(values),
            "average": sum(values) / len(values),
            "min": min(values),
            "max": max(values)
        }
    
    def calculate_distribution_stats(self, values: List[Union[int, float]]) -> Dict[str, int]:
        """
        计算数值分布统计

        Args:
            values (List[Union[int, float]]): 数值列表

        Returns:
            Dict[str, int]: 分布统计
        """
        distribution = {}
        for value in values:
            key = str(value)
            if key not in distribution:
                distribution[key] = 0
            distribution[key] += 1
        return distribution
    
    def extract_fields(self, results: List[Dict[str, Any]], field_path: str) -> List[Any]:
        """
        从结果中提取指定路径的字段值

        Args:
            results (List[Dict[str, Any]]): 结果列表
            field_path (str): 字段路径，如 "response.length"

        Returns:
            List[Any]: 字段值列表
        """
        values = []
        
        for result in results:
            # 跳过错误结果
            if "error" in result:
                continue
                
            current = result
            try:
                # 处理特殊路径
                if field_path == "response.length":
                    response = result.get("response", "")
                    if response:
                        values.append(len(response))
                else:
                    # 通用路径处理
                    path_parts = field_path.split(".")
                    for part in path_parts:
                        if isinstance(current, dict) and part in current:
                            current = current[part]
                        else:
                            current = None
                            break
                    
                    if current is not None:
                        values.append(current)
            except (KeyError, TypeError):
                continue
                
        return values
    
    def calculate_general_stats(self, results: List[Dict[str, Any]], 
                              numeric_fields: List[str] = None,
                              distribution_fields: List[str] = None) -> Dict[str, Any]:
        """
        计算通用统计信息

        Args:
            results (List[Dict[str, Any]]): 结果列表
            numeric_fields (List[str]): 需要计算数值统计的字段路径列表
            distribution_fields (List[str]): 需要计算分布统计的字段路径列表

        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            "total_count": len(results),
            "success_count": 0,
            "error_count": 0,
            "numeric_stats": {},
            "distribution_stats": {}
        }
        
        # 统计成功和错误数量
        for result in results:
            if "error" in result:
                stats["error_count"] += 1
            else:
                stats["success_count"] += 1
        
        # 计算数值统计
        if numeric_fields:
            for field in numeric_fields:
                values = self.extract_fields(results, field)
                # 转换为数值类型
                numeric_values = []
                for v in values:
                    try:
                        numeric_values.append(float(v))
                    except (ValueError, TypeError):
                        continue
                
                stats["numeric_stats"][field] = self.calculate_numeric_stats(numeric_values)
        
        # 计算分布统计
        if distribution_fields:
            for field in distribution_fields:
                values = self.extract_fields(results, field)
                stats["distribution_stats"][field] = self.calculate_distribution_stats(values)
        
        return stats
    
    def generate_report(self, file_path: str, 
                       numeric_fields: List[str] = None,
                       distribution_fields: List[str] = None) -> Dict[str, Any]:
        """
        生成完整的统计报告

        Args:
            file_path (str): 结果文件路径
            numeric_fields (List[str]): 需要计算数值统计的字段路径列表
            distribution_fields (List[str]): 需要计算分布统计的字段路径列表

        Returns:
            Dict[str, Any]: 统计报告
        """
        results = self.load_results(file_path)
        
        report = {
            "total_tasks": len(results),
            "general_stats": self.calculate_general_stats(results, numeric_fields, distribution_fields)
        }
        
        self.logger.info(f"Generated stats report for {file_path}")
        return report
    
    def print_report(self, file_path: str, 
                    numeric_fields: List[str] = None,
                    distribution_fields: List[str] = None) -> None:
        """
        打印统计报告

        Args:
            file_path (str): 结果文件路径
            numeric_fields (List[str]): 需要计算数值统计的字段路径列表
            distribution_fields (List[str]): 需要计算分布统计的字段路径列表
        """
        report = self.generate_report(file_path, numeric_fields, distribution_fields)
        
        print("=" * 50)
        print("Data Generation Stats Report")
        print("=" * 50)
        print(f"Total Tasks: {report['total_tasks']}")
        
        general_stats = report['general_stats']
        print(f"Success: {general_stats['success_count']}")
        print(f"Errors: {general_stats['error_count']}")
        
        if general_stats['numeric_stats']:
            print("\nNumeric Statistics:")
            for field, stats in general_stats['numeric_stats'].items():
                if stats['count'] > 0:
                    print(f"  {field}:")
                    print(f"    Count: {stats['count']}")
                    print(f"    Average: {stats['average']:.2f}")
                    print(f"    Total: {stats['total']}")
                    if stats['min'] is not None:
                        print(f"    Min: {stats['min']}")
                    if stats['max'] is not None:
                        print(f"    Max: {stats['max']}")
        
        if general_stats['distribution_stats']:
            print("\nDistribution Statistics:")
            for field, distribution in general_stats['distribution_stats'].items():
                print(f"  {field}:")
                for value, count in distribution.items():
                    print(f"    {value}: {count}")
        
        print("=" * 50)