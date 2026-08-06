from __future__ import annotations

import argparse
import re
from pathlib import Path

from transform_baoming_to_source_aligned import validate


SOURCE_SUBTITLE = "## 前三章·纯关键词直背版V4"
TARGET_SUBTITLE = "## 前三章·关键词强化直背版V5"


# 这些词组均承担概念边界、分类、机制、条件、关系、结果或评价的采分功能。
# 按答案原句选取，不改写内容；渲染时跳过既有加粗与【标签】，避免整句加粗。
KEYWORD_PHRASES = tuple(
    phrase.strip()
    for phrase in """
对信息进行加工处理
感觉、知觉、记忆、思维和想象
客观事物是否满足需要
态度体验
自觉确定目的
克服内外部困难
实现预定目的
同一心理过程的不同方面
最基本的心理活动
反过来影响认知
客观事物的态度
活动对象的选择和趋向
指向性和基本动力
需要、动机、兴趣、理想和价值观
稳定而经常表现
独特结合
能力、气质和性格
发生和变化
稳定而独特
共同构成人的心理现象
实验研究进入心理学
核心标志
世界上第一个心理学实验室
科学心理学诞生
独立科学
系统阐述心理活动及其功能
推动美国心理学发展
中国第一个心理学实验室
实验化和科学化
摆脱单纯的哲学思辨
感觉、意象和激情
重要研究对象
摆脱纯哲学思辨
独立的经验科学
由什么构成
有什么作用
元素和结构
过程、功能与适应
内省报告与客观刺激测量
实验法和观察法
实验研究道路
研究范围较窄
主观性较强
重复性和适用性有限
面向实际生活
教育心理学、工业心理学
理论体系较松散
排斥其他学派
研究对象、方法和应用范围
观察和测量的外显行为
无法客观验证的意识经验
主要受环境影响
刺激与反应之间的联系
控制环境和学习条件
预测、塑造及改变行为
客观、可验证、可重复
向自然科学靠拢
学习规律、条件反射、强化、惩罚和行为矫正
排斥内省和意识研究
过度强调环境决定作用
忽视遗传、认知和内部心理过程
缩小了心理学的研究范围
客观方法研究行为
过度简化为刺激与反应的联系
具有结构的整体
不能还原为部分
大于部分之和
先于部分存在
决定部分的性质
复杂心理活动分解为孤立元素
知觉、学习和思维
整体组织规律
过度分解心理现象
知觉、顿悟学习和认知心理学
组织关系
不同整体结构
不同意义
无意识、早期经验和内部冲突
少部分能够被意识到
大量思想、欲望和冲突
持续影响人的思维、情绪和行为
本能需要、无意识愿望和内部冲突
口腔期、肛门期、性器期、潜伏期和生殖期
快乐原则
现实原则
道德规范
三者发生冲突
焦虑
被压抑的无意识冲突
进入意识
理解冲突并缓解情绪问题
个体内部和人格整体
难以操作和验证
临床个案
客观性与普遍性
可验证证据
意识、社会环境
研究正常、健康的人
选择自由、发展潜能和主动成长
人的需要、主观经验、价值和尊严
个体自身体验
忽视人的主体性
偏重病态人格
需要、自我和心理咨询
概念界定不够清晰
实证检验相对不足
心理活动的内部机制
通过可观察行为推断
主动接收、编码、存储、提取和使用信息
内部心理过程
重要研究范式
客观实验数据
检验内部加工模型
认知结构和加工阶段
外显反应
客观方法
内部信息加工过程
自然情境
有系统、有计划的观察记录
心理活动产生和发展规律
相关系数
关联的强度和方向
有计划、有目的地控制条件
产生某种心理活动
分析研究
自然性较高
真实、丰富的行为资料
较难重复和精确控制
不能据此确定因果关系
自然发生、难以人为操纵
量化变量关系、进行预测
相关不等于因果
因果方向不明
第三变量
控制严密、可重复
内部效度较高
因果推断
情境较人为
外部效度可能较低
情境真实性较高
控制和测量精度相对较低
变量可以操纵
伦理和现实条件
观察发现现象
相关研究检验变量关系
实验法考察因果
多种证据相互验证
与实验目的无关
对实验结果产生影响
需要加以控制
操纵自变量、测量因变量
保持恒定
各组平衡
统计控制
随机分入实验组和控制组
个体差异在概率上得到平衡
降低选择偏差
增强组间可比性
排除自变量以外的其他解释
避免混淆变量
因果解释力
排除、恒定、匹配、随机化、抵消平衡或统计控制
有效操纵自变量
可靠测量因变量
控制无关变量
较强的因果解释力
标准化测验工具
个体间或个体内反应差异
信度和效度两个基本要求
测量结果真实反映
编制、施测、评分和解释程序
建立适用的常模
必要而非充分条件
效度高，信度必须高
信度高，效度不一定高
信度低，效度不可能高
程序规范
操作简便
定量化程度高
个体间比较
间接测量
不能揭示因果关系
工具质量、施测情境和被试反应
专业能力
难以呈现完整心理过程
真正测到目标心理品质
测量目的
模糊刺激材料
被试自由反应
专家加以解释
个体动机、欲望等人格特征
解释墨迹图形
模糊图片编写故事
非结构任务
反应较少受限制
测量目的具有掩蔽性
减少伪装
人格的整体解释
跨文化研究
评分缺乏客观标准
难以量化
常模资料不足
受主试影响
信度和效度不易建立
经过训练的专业人员
反应自由、目的隐蔽和整体解释
评分主观、量化困难及信效度不足
基础研究与实际应用
正常成年人心理现象的一般规律
基础性学科
心理活动的生理机制
脑、神经系统和内分泌活动与行为的关系
生命全程
心理发生和发展
教与学的心理活动规律
教育过程与心理发展的内在关系
群体环境
个体心理和行为发生、发展及变化
人与机器的关系
人员选拔、激励和工作效率
评估、诊断和治疗心理异常
最基本的结构和功能单位
接受刺激、整合信息和传递信息
接收信息
整合信息
传递给另一个神经元或效应器
刺激信息传入中枢神经系统
神经冲动传至肌肉或腺体等效应器
联结传入神经元与传出神经元
接收—整合—传出
神经活动通路
从静息状态转为活跃状态
钾离子外流
钠离子内流
功能联系的部位
钾离子的通透性较大
膜内相对负、膜外相对正
刺激达到阈限
钠离子快速内流
去极化
达到阈限即完整发生
未达到阈限则不发生
沿轴突以电信号形式传递
双向传导
由胞体方向传向轴突末梢
神经递质释放
跨越突触间隙
突触后膜受体结合
兴奋或抑制
电传导
化学传递
神经递质为媒介
电信号传导
化学信号传递
位于脑和脊髓之外
连接中枢神经系统与感觉器官、肌肉和腺体
输入信息进行分析和综合
调节行为与生理活动的指令
内脏和腺体的信息交换
不由主观意志决定的不随意运动
脑神经和脊神经
感觉器官、骨骼肌与中枢
受到意志控制
动员能量
降低兴奋
促进能量储存和机体恢复
共同维持机体内环境稳定
信息传导通路
简单反射的控制中心
感觉整合、运动调节、觉醒、情绪和高级认知
信息传入与传出
分析、整合并形成指令
输入—加工—输出
分工协作
感知环境、加工信息并作出适应性反应
躯体感觉的主要投射区
整合视交叉后的信息并产生视觉
接收和加工听觉信息
支配和调节身体姿势、位置及躯体各部位的运动
身体部位越重要、感觉越精细
皮层上的代表区越大
动作越精细的部位
外界和身体信息投射到皮层
皮层指令传向躯体
精细的感觉—运动调节
优势半球额叶
言语表达
运动性失语症
优势半球颞叶后部
口头言语理解
听觉性失语症
顶叶、颞叶和枕叶交界附近
文字和视觉符号的理解
视觉失语症或失读症
综合处理
感觉联合区、运动联合区和前额联合区
理解相对保留
感觉性失语
失读症或视觉失语
书面表达
整合感觉信息
复杂运动的组织
计划、决策、问题解决和行为控制
多个言语区与联合区分工协作
相对优势
不是绝对的
胼胝体被切断的患者
分别向左右半球呈现信息
两半球功能分工
语言、阅读、书写、逻辑分析和顺序加工
控制身体右侧
空间关系、图形、音乐、整体知觉和情绪信息加工
控制身体左侧
右视野
进入左半球
能够说出刺激名称
左视野
进入右半球
无法口头命名
左手选择相应物体
胼胝体交换信息
分工协作完成
相互联系的整体
除嗅觉外大多数感觉信息
进入大脑皮层前
传递感觉信息
调节内分泌系统活动和内稳态
感觉信息筛选
投射到相应皮层区域
参与知觉形成
其他感觉缺失或异常
摄食、饮水、体温、睡眠—觉醒、性行为和情绪反应
机体内部需要转化为动机和行为
恢复平衡
感觉信息中转
协调生理需要、情绪反应和内稳态
适应性反应
感觉信息送往皮层
顺行性遗忘
难以形成新的外显长时记忆
不一定妨碍内隐记忆
威胁与恐惧线索
识别和加工
情绪调节、注意监控和冲突检测
情境和事件内容的记忆
事件的情绪意义及情绪记忆
事件内容与情绪体验结合
多个结构共同参与
功能网络
不同区域分别负责不同的心理机能
以总体发生作用
同等程度的影响
多个机能系统协同完成
高度专门化且相对独立的模块
不同模块的结合
神经元构成的复杂神经网络
连接权重和连接方式
布洛卡区、威尔尼克区
潘菲尔德的电刺激研究
相对分工
完全归因于单一脑区
脑区之间的协同作用
弗罗伦斯的毁损研究
皮层整体作用
相对功能分工
分工与协同
相对明确的功能分工
协同完成复杂心理活动
局部专门化
整体协同
第一机能系统维持觉醒
第二机能系统接收、加工和存储信息
第三机能系统计划、调节和控制行为
相对专门化
多个节点的分布式连接
通过练习或经验
行为或行为潜能
比较持久改变
个体与环境之间相互作用
外显行为改变
行为能力变化
疲劳、药物、疾病或短暂情绪
即时变化不属于学习
先天成熟或本能反应
个体与环境相互作用的经验
根据经验修正行为
形成新技能
提高对变化环境的适应能力
神经系统的基本活动方式
中枢神经系统参与
内外环境刺激
规律性反应
实现反射活动的神经结构
生理基础
感受器、传入神经、神经中枢、传出神经和效应器
种系发展过程中形成并遗传
不学而能
维持有机体生命和延续种族繁衍
无条件反射基础
适应环境变化
后天学习建立
神经联系是暂时的
感受器接收
传入神经到达神经中枢
传出神经支配效应器
任一环节受损
先天遗传、联系固定、种族共有
后天习得、联系暂时
灵活性和适应性
根据环境信号调整行为
神经通路
先天基础
扩展个体的适应能力
原来不能引起某种无条件反射
中性刺激物
无条件刺激物
反复配对
中性刺激物也能引起相应反应
无条件刺激能够自然引起无条件反应
中性刺激不能引起目标反应
反复、适时配对
暂时性神经联系
无条件刺激（US）
无条件反应（UR）
条件刺激（CS）
条件反应（CR）
行为之后出现结果
一个刺激通过与另一个刺激配对
获得信号作用
两个刺激之间形成联结
条件反射形成初期
原条件刺激
相似的一系列刺激
刺激越相似，泛化越明显
条件反射精确化
只对特定刺激作出反应
其他类似刺激不作出反应
不再进行强化
出现率逐渐降低并最终消失
重新给予强化
条件反射可以恢复
条件反射延迟
抑制过程
已经形成的条件反射基础
原来的条件刺激作为强化信号
另一个中性刺激同时出现
新的、更复杂条件反射
同时性、延迟性和痕迹性条件作用
先呈现条件刺激
结束前呈现无条件刺激
最容易形成
反应扩展到相似刺激
反应变得精确
停止配对后反应减弱
时间控制和联结层级
迅速反应
避免对无关线索作出过度反应
条件反射的适应性
具体事物及其属性
只对客观事物作直接反应
人和动物共有
言语、文字等
概括反映客观事物的本质与规律
人类独有
新异刺激出现
正在进行的条件反射
非条件性抑制
相对过强、过多或延续时间过久
保护性抑制
邻近区域兴奋过程
兴奋过程
邻近区域抑制过程
具体刺激为信号
词和语言为信号
抽象概括功能
以第一信号系统为基础
对第一信号系统起调节作用
相互制约、保持动态平衡
先天的非条件性抑制
后天形成的条件性抑制
外抑制和超限抑制
停止强化形成的消退抑制
选择性强化形成的分化抑制
扩散到邻近区域
集中到特定区域
由广泛变得精确
引起或加强相反的神经过程
正诱导与负诱导
动态联系
获得信号意义
动态调节
一定刺激情境
反应的结果能够满足其需要
操作因得到强化
反应与结果联系
得到强化后再次表现
提高该行为反应出现的频率
降低该行为反应出现的频率
提高行为频率
降低行为频率
负强化仍属于强化
不是惩罚
能否实际提高特定个体的目标行为
个体需要
结果紧随行为出现
抗消退能力更强
定比率、定时距、变比率和变时距
可观察、可记录的目标行为
基线频率
选择有效后果并紧随行为呈现
停止原有强化
谨慎使用惩罚
强化与其不相容的正确行为
根据行为变化及时调整
针对具体行为
清楚、一致和及时
准确识别行为结果
选择有效后果
逐步调整强化程序
稳定目标行为
后天经验建立暂时性联系
习得、消退、泛化和分化
反射性、非随意反应
自主性、随意行为
相对被动地接受刺激配对
主动作用于环境
承受行为结果
无条件刺激通常出现在条件反应之前
强化或惩罚发生在行为之后
刺激与刺激的联系
条件刺激后将出现无条件刺激
行为与结果的联系
行为将产生特定结果
同时包含两种条件作用
重新组织学习情境
领悟其内在关系
顿悟而非试误
分散的条件重新组织
有意义的整体
目标与手段之间的关系
解决办法会突然出现
迅速出现
迁移到结构相似的新问题
不仅依赖反复尝试
条件之间关系的理解
问题结构的重新组织
主动理解
机械试误
不是刺激与反应的直接联结
整体性行为
中介变量
基于过去经验
场景的类似地图的表征
学习已经发生
暂时不表现为外部行为
需要系统、认知—信念—价值系统和行为空间
机体变量
对刺激进行加工
有目的的整体行为
没有立即获得强化
已经形成认知地图
强化主要影响学习成果是否表现
不必然决定学习是否发生
主动形成认知表征
依据目标选择行为
由外显行为深入到内部认知过程
不直接参与学习活动
观察榜样的行为及其结果
仿照榜样行为
习得该行为
选择并关注榜样行为
显著性、可辨别性、功能价值和吸引力
认知能力、经验、动机和观察习惯
转入记忆
组织和复述
长期保存
符号表征转化为实际行为
尝试、反馈、监控和修正
逐渐接近榜样行为
是否值得表现
已经学会某行为
缺乏积极后果
暂不表现
相似性、威信、吸引力和行为价值
受到奖励
增强观察者模仿倾向
受到惩罚
降低模仿倾向
注意到榜样
保持表征
复现动作
表现动机
可信、可亲近且行为清晰的榜样
分解为可观察步骤
复述要点并及时练习
反馈和适当强化
示范行为过程和结果
人格生物学理论
奖励、惩罚等强化信号
系统的敏感性差异
积极情绪和趋近行为
提高警觉
行为抑制或回避
内外倾差异
静息状态下的皮层唤醒水平较低
寻求较强刺激
带来回报的情境
基础唤醒水平较高
较弱刺激也可能引起较强感受
受惩罚信号影响
关注奖励、接近目标
重复可能获得奖励的行为
关注威胁、暂停当前行为、评估风险
回避可能受罚的情境
BIS与BAS活动水平的差异
奖励和积极结果驱动
惩罚、失败和不确定性警示
神经行为系统的敏感性
个体差异
BAS相对更敏感
奖励线索更易吸引注意
引发趋近动机
行为—奖励联系更易建立
积极情绪又会促进该行为重复
惩罚信号对其行为的抑制作用较弱
奖励学习较好
惩罚学习较差
""".splitlines()
    if phrase.strip()
)


# 定义链、四项成分和比较题两端不能因密度上限而只标出一半。
MANDATORY_PHRASES = (
    "刺激与反应之间的联系",
    "控制环境和学习条件",
    "改变行为",
    "无意识冲突及其根源",
    "无意识、早期经验、人格动力及心理治疗",
    "反应自由、目的隐蔽和整体解释",
    "建立适用的常模",
    "信度和效度",
    "动员能量",
    "促进能量储存和机体恢复",
    "电信号传导",
    "身体部位越重要、感觉越精细",
    "皮层上的代表区越大",
    "上下倒置",
    "头面部区域正置",
    "不是由单一脑区独立完成",
    "相对明确的功能优势",
    "单一半球",
    "丘脑侧重感觉信息中转",
    "丘脑侧重把感觉信息送往皮层",
    "通过练习或经验",
    "行为或行为潜能",
    "比较持久改变",
    "行为能力变化",
    "后天习得、联系暂时",
    "中性刺激物",
    "无条件刺激物",
    "无条件刺激（US）",
    "无条件反应（UR）",
    "条件刺激（CS）",
    "条件反应（CR）",
    "行为之后出现结果",
    "获得信号作用",
    "反应与结果联系",
    "降低行为频率",
    "负强化仍属于强化",
    "不是惩罚",
    "后天经验建立暂时性联系",
    "习得、消退、泛化和分化",
    "反射性、非随意反应",
    "自主性、随意行为",
    "强化或惩罚发生在行为之后",
    "刺激与刺激的联系",
    "行为与结果的联系",
    "不直接参与学习活动",
    "仿照榜样行为",
    "习得该行为",
    "注意到榜样",
    "保持表征",
    "复现动作",
    "表现动机",
    "积极情绪和趋近行为",
    "提高警觉",
    "行为抑制或回避",
    "关注奖励、接近目标",
    "回避可能受罚的情境",
    "BAS相对更敏感",
    "惩罚信号对其行为的抑制作用较弱",
    "奖励学习较好",
    "惩罚学习较差",
)


PROTECTED_RE = re.compile(r"(\*\*.*?\*\*|【[^】]*】)")
VISIBLE_MARK_RE = re.compile(r"\*\*(.+?)\*\*")


def _mark_answer_line(line: str, phrases: tuple[str, ...]) -> str:
    parts = PROTECTED_RE.split(line)
    core_line = re.sub(r"\s*\*\*【[^】]+】\*\*|\s*【[^】]+】", "", line)
    core_line = re.sub(r"^\d+\. \*\*[^*]+\*\*：", "", core_line)
    visible_length = len(core_line.replace("**", ""))
    existing_bold_chars = sum(len(mark) for mark in VISIBLE_MARK_RE.findall(core_line))
    if visible_length == 0:
        return line

    target_bold_chars = round(visible_length * 0.28)
    if visible_length <= 35:
        max_new_marks = 1
    elif visible_length <= 60:
        max_new_marks = 2
    elif visible_length <= 90:
        max_new_marks = 3
    elif visible_length <= 130:
        max_new_marks = 4
    else:
        max_new_marks = 5

    candidates: list[tuple[int, int, int, int, str]] = []
    searchable_phrases = tuple(dict.fromkeys(phrases + MANDATORY_PHRASES))
    display_prefix = ""
    for part_index, part in enumerate(parts):
        if PROTECTED_RE.fullmatch(part):
            if not part.startswith("【") and not part.startswith("**【"):
                display_prefix += part.replace("**", "")
            continue
        for phrase in searchable_phrases:
            start = 0
            while True:
                index = part.find(phrase, start)
                if index < 0:
                    break
                clause = len(re.findall(r"[；。]", display_prefix + part[:index]))
                candidates.append((part_index, index, index + len(phrase), clause, phrase))
                start = index + len(phrase)
        display_prefix += part

    occupied: dict[int, list[bool]] = {
        index: [False] * len(part)
        for index, part in enumerate(parts)
        if not PROTECTED_RE.fullmatch(part)
    }
    selected: list[tuple[int, int, int, int, str]] = []

    def try_select(
        candidate: tuple[int, int, int, int, str], *, mandatory: bool = False
    ) -> bool:
        part_index, start, end, _, _ = candidate
        if (not mandatory and len(selected) >= max_new_marks) or any(
            occupied[part_index][start:end]
        ):
            return False
        selected.append(candidate)
        for position in range(start, end):
            occupied[part_index][position] = True
        return True

    # 定义链、固定成分和比较两端先强制保留，防止只标出关系的一侧。
    mandatory_set = set(MANDATORY_PHRASES)
    current_chars = existing_bold_chars
    for candidate in sorted(candidates, key=lambda item: (item[0], item[1], -(item[2] - item[1]))):
        if candidate[4] in mandatory_set and try_select(candidate, mandatory=True):
            current_chars += candidate[2] - candidate[1]

    # 再让长答案的不同判断分句都至少留下一个记忆抓手，最后补到约28%的正文密度。
    by_clause: dict[int, list[tuple[int, int, int, int, str]]] = {}
    for candidate in candidates:
        by_clause.setdefault(candidate[3], []).append(candidate)
    for clause in sorted(by_clause):
        if current_chars >= target_bold_chars or len(selected) >= max_new_marks:
            break
        ranked = sorted(
            by_clause[clause],
            key=lambda item: (-(item[2] - item[1]), item[0], item[1]),
        )
        for candidate in ranked:
            if try_select(candidate):
                current_chars += candidate[2] - candidate[1]
                break

    for candidate in sorted(
        candidates,
        key=lambda item: (-(item[2] - item[1]), item[0], item[1]),
    ):
        if current_chars >= target_bold_chars or len(selected) >= max_new_marks:
            break
        if try_select(candidate):
            current_chars += candidate[2] - candidate[1]

    selected_by_part: dict[int, list[tuple[int, int]]] = {}
    for part_index, start, end, _, _ in selected:
        selected_by_part.setdefault(part_index, []).append((start, end))

    output: list[str] = []
    for part_index, part in enumerate(parts):
        intervals = sorted(selected_by_part.get(part_index, ()))
        if not intervals:
            output.append(part)
            continue
        cursor = 0
        for start, end in intervals:
            output.append(part[cursor:start])
            output.append(f"**{part[start:end]}**")
            cursor = end
        output.append(part[cursor:])
    return "".join(output)


def transform(source: str) -> str:
    if source.count(SOURCE_SUBTITLE) != 1:
        raise ValueError("V4版本标题定位异常")
    if len(KEYWORD_PHRASES) != len(set(KEYWORD_PHRASES)):
        raise ValueError("关键词候选表存在重复")

    output_lines: list[str] = []
    answer_mode = False
    for line in source.replace(SOURCE_SUBTITLE, TARGET_SUBTITLE, 1).splitlines():
        stripped = line.strip()
        if stripped == "### 综合答案":
            answer_mode = True
            output_lines.append(line)
            continue
        if stripped.startswith("## ") or stripped.startswith("# "):
            answer_mode = False
        output_lines.append(_mark_answer_line(line, KEYWORD_PHRASES) if answer_mode else line)

    output = "\n".join(output_lines) + ("\n" if source.endswith("\n") else "")
    output = output.replace("****", "")
    if "++" in output:
        raise ValueError("V5仍存在关键句下划线标记")

    # 除版本名与加粗标记外，答案文字必须与V4逐字一致。
    normalized_source = source.replace(SOURCE_SUBTITLE, TARGET_SUBTITLE, 1).replace("**", "")
    normalized_output = output.replace("**", "")
    if normalized_source != normalized_output:
        raise ValueError("关键词强化过程中改动了V4实质文字")

    validate(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    source = arguments.input.read_text(encoding="utf-8")
    transformed = transform(source)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(transformed, encoding="utf-8")


if __name__ == "__main__":
    main()
