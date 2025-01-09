"""
Gradio Web 界面模块
提供基于 Web 的交互式计算界面
"""
import json
import gradio as gr
import pandas as pd
from typing import List, Dict, Tuple, Any
from pathlib import Path
from .fraction_calculator import FractionCalculator


class PriceCalculatorUI:
    def __init__(self):
        self.calculator = FractionCalculator()
        self.next_input_id = 1
    
    def format_item(self, item: dict) -> str:
        """格式化单个价格项的输出"""
        return (
            f"【价格项 {item['price']:,.2f}】\n"
            f"  ├─ 下浮率: {item['bid_float_rate']:.4%}\n"
            f"  ├─ 方案序号: {item['config_name']}\n"
            f"  ├─ 浮动率A: {item['final_float_a']:.4%}\n"
            f"  ├─ 评标基准价格: {item['benchmark_price']:,.2f}\n"
            f"  └─ 商务总报价评分: {item['score']:.2f}\n"
        )
    
    def format_result(self, record: dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """格式化计算结果为DataFrame
        
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: (概要信息表, 详细数据表)
        """
        # 创建概要信息表
        summary_data = {
            '计算时间': [record['timestamp']],
            '平均价格': [f"{record['avg_price']:,.2f}"],
            '价格数量': [len(record['items'])]
        }
        summary_df = pd.DataFrame(summary_data)
        
        # 创建详细数据表
        detail_data = []
        for item in record['items']:
            detail_data.append({
                '序号': len(detail_data) + 1,
                '投标价格': f"{item['price']:,.2f}",
                '下浮率': f"{item['bid_float_rate']:.2%}",
                '方案序号': item['config_name'],
                '浮动率A': f"{item['final_float_a']:.4%}",
                '评标基准价格': f"{item['benchmark_price']:,.2f}",
                '商务总报价评分': f"{item['score']:.2f}"
            })
        detail_df = pd.DataFrame(detail_data)
        
        return summary_df, detail_df
    
    def add_price_input(self, prices: List[float], num_inputs: int) -> Tuple[List[float], int]:
        """添加新的价格输入框"""
        prices.append(None)
        return prices, num_inputs + 1
    
    def remove_price_input(self, prices: List[float], idx: int, num_inputs: int) -> Tuple[List[float], int]:
        """删除指定的价格输入框"""
        if 0 <= idx < len(prices):
            prices.pop(idx)
        return prices, max(1, num_inputs - 1)
    
    def calculate(self, prices: List[float]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """执行计算并返回格式化结果"""
        valid_prices = [p for p in prices if p is not None]
        
        if not valid_prices:
            return pd.DataFrame(), pd.DataFrame()
        
        try:
            result = self.calculator.calc(valid_prices)
            return self.format_result(result)
        except Exception as e:
            return pd.DataFrame({'错误': [str(e)]}, index=[0]), pd.DataFrame()
    
    def update_ui_state(self, prices, num_inputs):
        """更新UI状态"""
        row_updates = []    # 行的可见性更新
        number_updates = [] # 数字输入框的更新
        button_updates = [] # 按钮的更新
        
        for i in range(50):
            # 行只需要更新可见性
            row_updates.append(gr.update(visible=(i < num_inputs)))
            
            # 数字输入框需要更新值、标签和可见性
            if i < num_inputs:
                number_updates.append(gr.update(
                    value=prices[i] if i < len(prices) else None,
                    label=f"投标价格 {i+1}",
                    visible=True
                ))
            else:
                number_updates.append(gr.update(visible=False))
            
            # 按钮只需要更新可见性和文本
            if i < num_inputs:
                button_updates.append(gr.update(
                    visible=True,
                    value="删除此价格"
                ))
            else:
                button_updates.append(gr.update(visible=False))
        
        # 返回所有更新和计数显示
        return row_updates + number_updates + button_updates + [gr.update(value=f"已添加: {num_inputs}/50")]
    
    def reset_all(self) -> None:
        """重置所有数据和输入框"""
        # 清空 result.json
        self.calculator._save_result({'records': []})
        
        # 创建保留列定义的空DataFrame
        empty_summary = pd.DataFrame(columns=['计算时间', '平均价格', '价格数量'])
        empty_detail = pd.DataFrame(columns=[
            '序号', '投标价格', '下浮率', '方案序号', 
            '浮动率A', '评标基准价格', '商务总报价评分'
        ])
        
        # 重新加载页面（返回初始状态）
        return [
            [None],  # prices_state: 只保留一个空输入框
            1,      # num_inputs_state: 重置为1
            gr.update(visible=True),  # 第一个输入行可见
            *[gr.update(visible=False) for _ in range(49)],  # 其他输入行隐藏
            gr.update(value=None, label="投标价格 1", visible=True),  # 第一个输入框
            *[gr.update(visible=False) for _ in range(49)],  # 其他输入框隐藏
            gr.update(value="删除此价格", visible=True),  # 第一个删除按钮
            *[gr.update(visible=False) for _ in range(49)],  # 其他删除按钮隐藏
            gr.update(value="已添加: 1/50"),  # 更新计数
            empty_summary,  # 清空概要表但保留列定义
            empty_detail   # 清空详细表但保留列定义
        ]
    
    def create_ui(self) -> gr.Interface:
        """创建 Gradio 界面"""
        with gr.Blocks(title="投标报价计算器", theme=gr.themes.Soft()) as interface:
            gr.Markdown(
                """
                # 投标报价计算器
                ### 使用说明
                1. 输入投标价格（可添加多个，最多50个）
                2. 点击"计算"按钮获取结果
                3. 使用"添加"和"删除"按钮管理价格输入
                4. 点击"重置"清空所有数据
                """
            )
            
            # 状态变量
            prices_state = gr.State([None])
            num_inputs_state = gr.State(1)
            
            with gr.Row():
                with gr.Column(scale=3):
                    input_rows = []
                    numbers = []
                    remove_btns = []
                    
                    # 预创建50个输入框组
                    for i in range(50):
                        with gr.Row(visible=False) as row:
                            number = gr.Number(
                                label=f"投标价格",
                                precision=2,
                                container=True,
                                scale=4
                            )
                            remove_btn = gr.Button(
                                "删除此价格",
                                size="sm",
                                scale=1
                            )
                            input_rows.append(row)
                            numbers.append(number)
                            remove_btns.append(remove_btn)
                    
                    # 添加价格按钮
                    with gr.Row():
                        add_btn = gr.Button(
                            "➕ 添加价格输入",
                            size="sm"
                        )
                        price_count = gr.Text(
                            value="已添加: 1/50",
                            label="",
                            scale=1,
                            interactive=False
                        )
                
                with gr.Column(scale=2):
                    with gr.Group():
                        gr.Markdown("### 计算结果")
                        summary_output = gr.DataFrame(
                            label="概要信息",
                            headers=['计算时间', '平均价格', '价格数量'],
                            wrap=True,
                            interactive=False,
                            value=pd.DataFrame({
                                '计算时间': [],
                                '平均价格': [],
                                '价格数量': []
                            })
                        )
                        detail_output = gr.DataFrame(
                            label="详细数据（按评分从高到低排序）",
                            headers=['序号', '投标价格', '下浮率', '方案序号', 
                                    '浮动率A', '评标基准价格', '商务总报价评分'],
                            wrap=True,
                            interactive=False,
                            value=pd.DataFrame({
                                '序号': [],
                                '投标价格': [],
                                '下浮率': [],
                                '方案序号': [],
                                '浮动率A': [],
                                '评标基准价格': [],
                                '商务总报价评分': []
                            })
                        )
            
            with gr.Row():
                calc_btn = gr.Button("计算", variant="primary", scale=2)
                reset_btn = gr.Button("重置", variant="secondary", scale=1)
            
            def handle_add(prices, num_inputs):
                """处理添加按钮点击"""
                if num_inputs < 50:
                    prices.append(None)
                    num_inputs += 1
                return [prices, num_inputs] + self.update_ui_state(prices, num_inputs)
            
            def handle_remove(idx, prices, num_inputs):
                """处理删除按钮点击"""
                if num_inputs > 1 and 0 <= idx < len(prices):
                    prices.pop(idx)
                    num_inputs -= 1
                return [prices, num_inputs] + self.update_ui_state(prices, num_inputs)
            
            def handle_reset():
                """处理重置按钮点击"""
                self.calculator._save_result({'records': []})
                prices = [None]
                num_inputs = 1
                empty_df = pd.DataFrame()
                return [prices, num_inputs] + self.update_ui_state(prices, num_inputs) + [price_count, empty_df, empty_df]
            
            # 绑定事件
            add_btn.click(
                fn=handle_add,
                inputs=[prices_state, num_inputs_state],
                outputs=[prices_state, num_inputs_state] + input_rows + numbers + remove_btns + [price_count]
            )
            
            # 为每个删除按钮绑定事件
            for i, btn in enumerate(remove_btns):
                btn.click(
                    fn=handle_remove,
                    inputs=[gr.State(i), prices_state, num_inputs_state],
                    outputs=[prices_state, num_inputs_state] + input_rows + numbers + remove_btns + [price_count]
                )
            
            # 为每个输入框绑定值更新事件
            for i, number in enumerate(numbers):
                number.change(
                    fn=lambda x, p, idx=i: (p[:idx] + [x] + p[idx+1:] if idx < len(p) else p),
                    inputs=[number, prices_state],
                    outputs=[prices_state]
                )
            
            # 更新计算按钮事件
            calc_btn.click(
                fn=self.calculate,
                inputs=[prices_state],
                outputs=[summary_output, detail_output]
            )
            
            # 更新重置按钮事件
            reset_btn.click(
                fn=self.reset_all,
                inputs=None,
                outputs=[
                    prices_state,
                    num_inputs_state,
                    *input_rows,
                    *numbers,
                    *remove_btns,
                    price_count,
                    summary_output,
                    detail_output
                ]
            )
            
            # 初始渲染
            interface.load(
                fn=lambda: [prices_state.value, num_inputs_state.value] + 
                          self.update_ui_state(prices_state.value, num_inputs_state.value),
                inputs=None,
                outputs=[prices_state, num_inputs_state] + input_rows + numbers + remove_btns + [price_count]
            )
        
        return interface


def main():
    """启动 Gradio 服务器"""
    ui = PriceCalculatorUI()
    interface = ui.create_ui()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


if __name__ == "__main__":
    main() 