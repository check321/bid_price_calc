"""
评分计算模块
处理价格数据并计算平均值和浮动率
"""
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Optional
from decimal import Decimal, ROUND_HALF_UP


class FractionCalculator:
    """评分计算类"""
    
    def __init__(self, result_path: Union[str, Path] = None, config_path: Union[str, Path] = None):
        """初始化计算器"""
        self.result_path = Path(result_path) if result_path else Path(__file__).parent / 'result.json'
        self.config_path = Path(config_path) if config_path else Path(__file__).parent.parent / 'config' / 'calc_conf.json'
        self._ensure_result_file()
        self.standard_price = self._load_standard_price()
        self.configs = self._load_configs()
    
    def _ensure_result_file(self) -> None:
        """确保结果文件存在，如果不存在则创建"""
        if not self.result_path.exists():
            self._save_result({'records': []})
    
    def _load_result(self) -> Dict:
        """加载结果文件"""
        with open(self.result_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_result(self, data: Dict) -> None:
        """保存结果到文件"""
        self.result_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.result_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def _load_standard_price(self) -> float:
        """从配置文件加载标准价格"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return float(config.get('standard_price', 5385))
        except (FileNotFoundError, json.JSONDecodeError):
            return 5385  # 默认值
    
    def _load_configs(self) -> List[Dict]:
        """加载计算配置列表"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('configs', [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _get_random_config(self) -> Optional[Dict]:
        """随机获取一个计算配置"""
        if not self.configs:
            return None
        return random.choice(self.configs)
    
    def _calculate_final_float_a(self, bid_float_rate: float, float_a: float) -> float:
        """计算最终的float_a值
        
        Args:
            bid_float_rate: 投标浮动率
            float_a: 配置中的float_a值
            
        Returns:
            float: 计算后的final_float_a值，保留4位小数
        """
        # 转换为Decimal以确保精确计算
        float_a_decimal = Decimal(str(float_a))
        bid_float_rate_decimal = Decimal(str(bid_float_rate))
        
        # 根据不同区间计算
        if bid_float_rate_decimal <= Decimal('0.08'):
            result = float_a_decimal
        elif bid_float_rate_decimal <= Decimal('0.15'):
            result = float_a_decimal - Decimal('0.025')
        else:
            result = float_a_decimal - Decimal('0.05')
        
        # 四舍五入到4位小数
        result = result.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        return float(result)
    
    def _calculate_float_rate(self, price: float) -> float:
        """计算单个价格的浮动率"""
        price_decimal = Decimal(str(price))
        standard = Decimal(str(self.standard_price))
        result = ((price_decimal - standard) / standard).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        return float(result)
    
    def _calculate_average(self, prices: List[float]) -> float:
        """计算价格平均值"""
        if not prices:
            return 0.0
        total = Decimal(str(sum(prices)))
        count = Decimal(str(len(prices)))
        avg = total / count
        return float(avg.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    def _calculate_benchmark_price(self, avg_price: float, config: Dict, final_float_a: float) -> float:
        """计算基准价格
        
        计算公式：
        benchmark_price = avg_price * (1 + float_c3) * weight_b + 
                         standard_price * (1 - final_float_a) * (1 - weight_b)
        
        Args:
            avg_price: 平均价格
            config: 计算配置
            final_float_a: 最终的float_a值
            
        Returns:
            float: 计算后的基准价格
        """
        float_c3 = Decimal(str(config['float_c3']))
        weight_b = Decimal(str(config['weight_b']))
        standard = Decimal(str(self.standard_price))
        avg = Decimal(str(avg_price))
        final_a = Decimal(str(final_float_a))
        
        # 第一部分：avg_price * (1 + float_c3) * weight_b
        part1 = avg * (1 + float_c3) * weight_b
        
        # 第二部分：standard_price * (1 - final_float_a) * (1 - weight_b)
        part2 = standard * (1 - final_a) * (1 - weight_b)
        
        # 计算总和并四舍五入到2位小数
        result = (part1 + part2).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return float(result)
    
    def _calculate_score(self, price: float, benchmark_price: float) -> float:
        """计算评分
        
        计算规则：
        - price等于benchmark_price时为100分
        - price每高于benchmark_price 1%扣2分
        - price每低于benchmark_price 1%扣1分
        - 不足1%使用直线插值法计算
        
        Args:
            price: 实际价格
            benchmark_price: 基准价格
            
        Returns:
            float: 计算后的评分，保留2位小数
        """
        # 计算价格偏差百分比
        price_decimal = Decimal(str(price))
        benchmark_decimal = Decimal(str(benchmark_price))
        
        # 计算偏差率 = (price - benchmark_price) / benchmark_price
        deviation_rate = ((price_decimal - benchmark_decimal) / benchmark_decimal).quantize(
            Decimal('0.0001'), rounding=ROUND_HALF_UP)
        
        # 初始分数
        base_score = Decimal('100')
        
        # 根据偏差计算扣分
        if deviation_rate > 0:  # 价格高于基准价
            deduction = deviation_rate * Decimal('200')  # 每1%扣2分
        else:  # 价格低于基准价
            deduction = abs(deviation_rate) * Decimal('100')  # 每1%扣1分
        
        # 计算最终分数
        final_score = (base_score - deduction).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # 确保分数不小于0
        return max(float(final_score), 0)
    
    def calc(self, prices: List[float]) -> Dict:
        """计算一组价格的评分结果"""
        # 验证输入
        if not isinstance(prices, list):
            raise ValueError("输入必须是价格列表")
        if not prices:
            raise ValueError("价格列表不能为空")
        for price in prices:
            if not isinstance(price, (int, float)) or price < 0:
                raise ValueError("价格列表中包含无效的价格值")
        
        # 计算平均价格
        avg_price = self._calculate_average(prices)
        
        # 创建价格项列表
        items = []
        for price in prices:
            # 获取随机配置
            config = self._get_random_config()
            if not config:
                raise ValueError("无法获取计算配置")
            
            # 计算浮动率
            bid_float_rate = self._calculate_float_rate(price)
            
            # 计算final_float_a
            final_float_a = self._calculate_final_float_a(
                bid_float_rate,
                config['float_a']
            )
            
            # 计算benchmark_price
            benchmark_price = self._calculate_benchmark_price(
                avg_price,
                config,
                final_float_a
            )
            
            # 计算score
            score = self._calculate_score(price, benchmark_price)
            
            # 创建价格项
            items.append({
                'price': price,
                'bid_float_rate': bid_float_rate,
                'config_name': config['name'],
                'final_float_a': final_float_a,
                'benchmark_price': benchmark_price,
                'score': score
            })
        
        # 根据score从大到小排序
        items.sort(key=lambda x: x['score'], reverse=True)
        
        # 创建新记录
        new_record = {
            'items': items,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'avg_price': avg_price
        }
        
        # 保存结果
        result = self._load_result()
        result['records'].append(new_record)
        self._save_result(result)
        
        return new_record


# main
if __name__ == "__main__":
    calculator = FractionCalculator()
    test_prices = [5200, 5100, 4980, 4900,4850,4800,4750,4700]
    result = calculator.calc(test_prices)
    
    print(f"计算时间: {result['timestamp']}")
    print(f"平均价格: {result['avg_price']}")
    print("\n价格项列表 (按评分从高到低排序):")
    for item in result['items']:
        print(f"投标价格: {item['price']}")
        print(f"下浮率: {item['bid_float_rate']}")
        print(f"方案序号: {item['config_name']}")
        print(f"浮动率A: {item['final_float_a']}")
        print(f"评标基准价格: {item['benchmark_price']}")
        print(f"商务总报价评分: {item['score']}")
        print("---")