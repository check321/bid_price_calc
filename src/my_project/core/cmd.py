"""
命令行交互模块
提供命令行方式调用计算功能
"""
import sys
import json
from typing import List, Optional
from pathlib import Path
from .fraction_calculator import FractionCalculator


def parse_prices(args: List[str]) -> Optional[List[float]]:
    """解析命令行参数中的价格列表
    
    Args:
        args: 命令行参数列表
        
    Returns:
        Optional[List[float]]: 解析出的价格列表，解析失败返回None
    """
    try:
        return [float(arg) for arg in args]
    except ValueError:
        return None


def format_item(item: dict) -> str:
    """格式化单个价格项的输出
    
    Args:
        item: 价格项字典
        
    Returns:
        str: 格式化后的字符串
    """
    return (
        f"\n    投标价格: {item['price']:,.2f}\n"
        f"    下浮率: {item['bid_float_rate']:.4%}\n"
        f"    方案序号: {item['config_name']}\n"
        f"    浮动率A: {item['final_float_a']:.4%}\n"
        f"    评标基准价格: {item['benchmark_price']:,.2f}\n"
        f"    商务总报价评分: {item['score']:.2f}\n"
        f"    {'=' * 50}"
    )


def format_result(record: dict) -> str:
    """格式化计算结果的输出
    
    Args:
        record: 计算结果记录
        
    Returns:
        str: 格式化后的字符串
    """
    items_str = '\n'.join(format_item(item) for item in record['items'])
    return (
        f"\n计算结果:\n"
        f"{'=' * 60}\n"
        f"计算时间: {record['timestamp']}\n"
        f"平均价格: {record['avg_price']:,.2f}\n"
        f"{'=' * 60}\n"
        f"价格项列表 (按评分从高到低排序):{items_str}\n"
    )


def process_command(args: List[str]) -> None:
    """处理命令行命令
    
    Args:
        args: 命令行参数列表
    """
    if not args or args[0] != 'calc':
        print("用法: calc 价格1 价格2 价格3 ...")
        return
    
    # 解析价格列表
    prices = parse_prices(args[1:])
    if prices is None:
        print("错误: 价格必须是有效的数字")
        return
    
    if not prices:
        print("错误: 请至少输入一个价格")
        return
    
    try:
        # 执行计算
        calculator = FractionCalculator()
        result = calculator.calc(prices)
        
        # 格式化输出结果
        print(format_result(result))
        
    except Exception as e:
        print(f"计算过程中出现错误: {str(e)}")


def main():
    """命令行主入口"""
    if len(sys.argv) < 2:
        print("用法: calc 价格1 价格2 价格3 ...")
        return
    
    process_command(sys.argv[1:])


if __name__ == "__main__":
    main() 