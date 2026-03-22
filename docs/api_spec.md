# MicroZhi 软硬件控制协议 V1.0

## 1. 大模型输出格式规范
大语言模型回复文本严格遵守：`[拼音] # [中文] \n ```json [Action] ``` `

## 2. JSON Action 支持列表
| Action Name | 描述 | 参数 |
| :--- | :--- | :--- |
| `LED_ON` | 打开外部继电器/灯光 | 无 |
| `LED_OFF`| 关闭外部继电器/灯光 | 无 |
| `TIMER_SET`| 设置并启动闹钟 | `{"duration_sec": 60}` (待实现) |
