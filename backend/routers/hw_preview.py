import logging
import json
import asyncio
from typing import List, Dict, Any, Callable
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from langchain_core.messages import SystemMessage, HumanMessage
from fastapi.concurrency import run_in_threadpool
from ..dependencies import *
from ..utils import *

# --- 日志和应用基础设置 ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/hw_preview",
    tags=["hw_preview"]
)

# --- 1. 设计 Prompt ---

SYSTEM_PROMPT = """
你是一个专业的AI助教，，拥有相关领域的研究生专业知识水平，专门负责分析纯文本格式的作业解答内容，擅长处理和结构化学生的作业提交。
你的任务是分析单个学生的提交文件，并完成以下两项工作：
1.  **身份识别**: 从提供的【文件名】中，准确提取学生的【学号】和【姓名】。
    - `stu_id`: 学生的学号，通常是字母和数字的组合或者纯数字；若不存在，则填写空字符串。
    - `stu_name`: 学生的姓名，通常是2~4个汉字，或者是包含首字母大写的拼音名或英文名；若不存在，则填写空字符串。
2.  **答案分割**: 从提供的纯文本学生作答中，根据提供的【题目数据】的描述，为每一道题找到并提取对应的学生答案。
    **请注意**：纯文本学生作答可能只包含了题号（\"number\"）而没有包括题干，你需要根据【题目数据】中的题号（"number"）进行分割。纯文本学生作答也可能**未**包含题号，你需要通过作答间距等信息（但需要考虑可能同一题的解答分在了多页中的情况，以及页面顺序混乱时，你需要尝试不同页面顺序组合以尽可能进准完整的识别每个题目）以及作答内容的逻辑是否匹配【题目数据】的题干来进行推理后给出准确的分割。
    **务必注意**：学生可能会跳过不会作答的题目，因此需要与【题目数据】中的\"q_id\"及\"number\"保持数量及内容完全一致，这种情况\"content\"为空字符串。
    - `stu_ans`: 学生的全部可识别的题目作答，整合为一个列表，每个元素是一个字典，包含key:一个包含该生所有题目答案的列表，列表每个元素是一个json字典，包含key:\"q_id\"（题目唯一标识，来自【题目数据】）、\"number\"（题目作答中显示的题号，来自【题目数据】）、\"type\"（题目类型分类，来自【题目数据】）、\"content\"（识别得到的解答过程）、\"flag\"（识别异常情况，见下面详述）。
**重要指令：请保证提取作答内容\"content\"字段的完整性，你被禁止自行删减内容，也不允许进行翻译，请“完整”保留题干信息，你的工作只是将他们划分为多个题目。**

3.  **识别可信情况**: “答案分割”过程中对每个题目如有任何处理置信度不高或者完全无法处理的情况，需要给出**列表**包含所有可能存在的问题。
    - `flag`: 如题目作答页面混乱、题目作答不全等等。如果没有任何问题，则为空列表；如果有一个或多个问题，每个以字符串形式存入列表中。

4.  **格式化输出**：将上述所有处理好的1~3的信息整合成一个字典，key为\"stu_id\"、\"stu_name"\、\"stu_ans\", value分别为字符串、字符串、列表，其中列表每个元素是一个json字典，包含 "q_id", "number", "type", "content", "flag" 这几个字段。
例如，对于一个学生5道题目的作答，你的输出应该是这样的结构：
{
    "stu_id":"PB20111639",
    "stu_name":"张三",
    "stu_ans":
    [
        {"q_id": "q1", "number": "1.1", "type": "概念题", "content":"ans1", "flag":[]},
        {"q_id": "q2", "number": "1.2", "type": "计算题", "content":"ans2", "flag":["页面混乱,作答提取可能错误",]},
        {"q_id": "q3", "number": "2", "type": "编程题", "content":"ans3", "flag":["缺页",]},
        {"q_id": "q4", "number": "3.1", "type": "证明题", "content":"ans4", "flag":["缺页","识别乱码"]},
        {"q_id": "q5", "number": "3.2", "type": "推理题", "content":"ans5", "flag::[]},
    ],
}

**[重要指令]：你的回答必须是一个单一、完整且格式正确的JSON对象，应该直接以 { 开始，并以 `}` 结束。不要包含任何解释性文字、评论、或者Markdown的代码块标记（如```json）。 禁止在JSON对象前后添加任何前沿、导语、解释、注释、代码或任何非JSON内容，也不要包含换行符、tab符等。**
**[务必注意]**：在生成JSON时，请确保字符串值中的所有反斜杠 \"\\" 都被正确转义为 \"\\\"。这对于包含LaTeX公式的字段尤其重要。
"""

"""
**[注意事项]**:
- 你必须严格根据提供的 【题目数据】（一个JSON对象）来构建答案列表。输出字典中 'stu_ans' 中每一题的 `q_id`, `number`, 和 `type` 字段必须与【题目数据】中的信息完全匹配。
- 请仔细阅读【学生作答内容】，智能地识别学生对每个题目的解答。
- 如果在【学生作答内容】中找不到某个题目的明确答案，你仍然需要在答案列表中包含该题目的条目，但其 `content` 字段应设为空字符串。
- 你的最终输出必须是一个遵循上述指定JSON字典格式的单一对象。
**[重要指令]：你的回答必须是一个单一、完整且格式正确的JSON对象，应该直接以 { 开始，并以 `}` 结束。不要包含任何解释性文字、评论、或者Markdown的代码块标记（如```json）。 禁止在JSON对象前后添加任何前沿、导语、解释、注释、代码或任何非JSON内容，也不要包含换行符、tab符等。**
**[务必注意]**：不要包含任何换行符，只能是标准json格式字符串。
"""

SYSTEM_PROMPT = """
You are a professional AI teaching assistant with graduate-level expertise in relevant fields. You specialize in analyzing assignment submissions in plain text format and are skilled in processing and structuring student homework.

Your task is to analyze a single student's submission file and complete the following two tasks:

1. **Identity Recognition**: Accurately extract the student's [Student ID] and [Name] from the provided [Filename].
    - `stu_id`: The student's ID, usually a combination of letters and numbers or pure numbers; if not present, fill with an empty string.
    - `stu_name`: The student's name, usually 2-4 Chinese characters, or a Pinyin/English name with capitalized initials; if not present, fill with an empty string.

2. **Answer Segmentation**: From the provided plain text student submission, identify and extract the corresponding student answer for each question based on the description in the provided [Question Data].
    **Note**: The plain text submission may only contain question numbers ("number") without the question text; you must segment based on the "number" in [Question Data]. The submission might also **not** contain question numbers. In this case, you need to infer the correct segmentation using information such as spacing between answers (considering cases where an answer spans multiple pages, or if page order is chaotic, try different page combinations to identify each question as accurately and completely as possible) and whether the logic of the answer matches the question text in [Question Data].
    **Crucial**: Students may skip questions they cannot answer. Therefore, you must ensure strict consistency in quantity and content with the "q_id" and "number" in [Question Data]. In such cases, "content" should be an empty string.
    - `stu_ans`: A list of all identifiable student answers. Each element is a dictionary containing keys corresponding to the student's answers. Each element is a JSON dictionary containing the keys: "q_id" (unique question identifier, from [Question Data]), "number" (question number displayed in submission, from [Question Data]), "type" (question type classification, from [Question Data]), "content" (the recognized answer process), and "flag" (recognized anomalies, detailed below).

    **Important Instruction: Ensure the integrity of the extracted "content" field. You are prohibited from deleting content or translating it. Please preserve the text "completely". Your job is solely to divide them into separate questions.**

3. **Identify Reliability**: During "Answer Segmentation", if there are any low-confidence situations or unprocessable parts for a question, provide a **list** of all potential issues.
    - `flag`: E.g., chaotic page order, incomplete answer, etc. If there are no issues, use an empty list; if there are one or more issues, store each as a string in the list.

4. **Formatted Output**: Integrate all processed information from steps 1-3 into a single dictionary. The keys are "stu_id", "stu_name", and "stu_ans", and the values are string, string, and list respectively. Each element in the list is a JSON dictionary containing the fields "q_id", "number", "type", "content", and "flag".

For example, for a student submission with 5 questions, your output should have the following structure:
{
    "stu_id": "PB20111639",
    "stu_name": "Zhang San",
    "stu_ans":
    [
        {"q_id": "q1", "number": "1.1", "type": "概念题", "content": "ans1", "flag": []},
        {"q_id": "q2", "number": "1.2", "type": "计算题", "content": "ans2", "flag": ["Page confusion, answer extraction may be incorrect"]},
        {"q_id": "q3", "number": "2", "type": "编程题", "content": "ans3", "flag": ["Missing page"]},
        {"q_id": "q4", "number": "3.1", "type": "证明题", "content": "ans4", "flag": ["Missing page", "Garbled text recognized"]},
        {"q_id": "q5", "number": "3.2", "type": "推理题", "content": "ans5", "flag": []}
    ]
}

**[Important Instruction]: Your response must be a single, complete, and correctly formatted JSON object. It should start directly with { and end with `}`. Do not include any explanatory text, comments, or Markdown code block markers (like ```json). Do not add any preamble, intro, explanation, notes, code, or non-JSON content before or after the JSON object, and do not include newlines or tab characters.**

**[Crucial Note]**: When generating JSON, ensure all backslashes "\\" in string values are correctly escaped as "\\". This is especially important for fields containing LaTeX formulas.
"""

"""
**[Notes]**:
- You must strictly build the answer list based on the provided [Question Data] (a JSON object). The `q_id`, `number`, and `type` fields in each item of 'stu_ans' must perfectly match the information in [Question Data]. **(Note: The `type` value must remain in Chinese as provided in the source data)**.
- Please read the [Student Submission Content] carefully to intelligently identify the student's answer for each question.
- If a clear answer for a question cannot be found in the [Student Submission Content], you still need to include the entry for that question in the answer list, but set its `content` field to an empty string.
- Your final output must be a single object following the specified JSON dictionary format.
**[Important Instruction]: Your response must be a single, complete, and correctly formatted JSON object. It should start directly with { and end with `}`. Do not include any explanatory text, comments, or Markdown code block markers (like ```json). Do not add any preamble, intro, explanation, notes, code, or non-JSON content before or after the JSON object, and do not include newlines or tab characters.**
**[Crucial Note]**: Do not include any newline characters; it must be a standard JSON format string.
"""

example = '''
{
    "students":
    [
        {
            "stu_id":"stu1",
            "stu_name":"张三",
            "stu_ans":
            [
                {"q_id": "q1", "number": "1.1", "type": "概念题", "content":"ans1", "flag":[]},
                {"q_id": "q2", "number": "1.2", "type": "计算题", "content":"ans2",},
                {"q_id": "q3", "number": "2", "type": "编程题", "content":"ans3",},
                {"q_id": "q4", "number": "3.1", "type": "证明题", "content":"ans4",},
                {"q_id": "q5", "number": "3.2", "type": "推理题", "content":"ans5",},
            ],
        },
        {
            "stu_id":"stu2",
            "stu_name":"李四",
            "stu_ans":
            [
                {"q_id": "q1", "number": "1.1", "type": "概念题", "content":"ans1",},
                {"q_id": "q2", "number": "1.2", "type": "计算题", "content":"ans2",},
                {"q_id": "q3", "number": "2", "type": "编程题", "content":"ans3",},
                {"q_id": "q4", "number": "3.1", "type": "证明题", "content":"ans4",},
                {"q_id": "q5", "number": "3.2", "type": "推理题", "content":"ans5",},
            ],
        },
    ]
}
'''

async def analyze_submissions(
    files_data: List[Dict[str, str]],
    problems_data: Dict[str, Dict[str,str]],
    student_store: Dict[str, Dict[str, Any]], # 接收学生存储字典的引用
    # llm: Any, # 传入一个LangChain LLM实例
    llm_factory: Callable[[], Any], # 修改点：接收工厂函数，而不是实例
) -> List[Dict[str, Any]]:
    """
    使用 LangChain 分析学生提交的文件，提取学生信息并分割答案。

    Args:
        files_data: 解压后读取的文件数据列表。
                    格式: [{"filename": "20240101_张三.txt", "content": "这是第一题的答案..."}, ...]
        problems_data: 包含所有题目信息的JSON对象（或Python字典）。
                        格式: {"q1": {"q_id": "q1", "number": "1.1", ...}, ...]}
        llm: 已经初始化的 LangChain 聊天模型实例 (e.g., ChatZhipuAI).

    Returns:
        一个包含所有学生分析结果的字典，格式符合用户要求。
    """
    # 优化：使用工厂模式在线程池中创建独立实例，避免死锁并提高并发效率。
    if not files_data:
        raise HTTPException(status_code=400, detail="输入的学生作答不能为空#1。")

    # 将 Pydantic 模型与 LLM 绑定，使其能够输出我们想要的结构
    # structured_llm = llm.with_structured_output(StudentSubmission)

    prob_main_data = []
    for prob in problems_data.values():
        prob_main = {}
        prob_main["q_id"] = prob["q_id"]
        prob_main["number"] = prob["number"]
        prob_main["type"] = prob["type"]
        prob_main["stem"] = prob["stem"]

        prob_main_data.append(prob_main)

    # 为了方便LLM处理，将题目数据字典转换为JSON字符串
    problems_json_str = json.dumps(prob_main_data, ensure_ascii=False, indent=1)

    all_students_results = []

    print(f"开始处理 {len(files_data)}份学生提交...")
    
    # Define a helper function for processing a single file

    # 修改点：创建信号量限制同时进行的AI请求数量，防止 API 429
    semaphore = asyncio.Semaphore(20) 
    
    async def process_single_file(file_info):
        # 异步等待信号量
        async with semaphore:
            filename = file_info.get("filename", "")
            content = file_info.get("content", "")

            if not filename or not content:
                logger.warning(f"文件 {filename} 内容为空，跳过。")
                return None

            print(f"正在分析文件: {filename}")

            # 修改点：将 HumanMessage 改为英文
            human_message_content = f"""
            Please process this student submission based on the following information:

            **[Filename]**:
            {filename}

            **[Question Data (JSON)]**:
            {problems_json_str}

            **[Student Submission Content]**:
            ---
            {content}
            ---"""
            
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=human_message_content)
            ]

            # 修改点：定义一个同步函数，用于在线程池中运行
            def _sync_analyze():
                try:
                    # 关键修改：在线程内部创建全新的 LLM 实例（独立连接池，无竞争）
                    local_llm = llm_factory()
                    # 同步调用，只会阻塞当前线程
                    raw_output = local_llm.invoke(messages)
                    # 解析 JSON
                    return parse_llm_json_output(raw_output.content, StudentSubmission).model_dump()
                except Exception as e:
                    logger.error(f"AI分析文件 {filename} 失败: {str(e)}")
                    return None

            # 将同步函数放入线程池执行
            # 这样既利用了多线程并发，又规避了 asyncio+grpc 的死锁风险
            result = await run_in_threadpool(_sync_analyze)
            
            if result:
                logger.info(f"完成分析: {filename}, 提取到: {result.get('stu_name')}")
            return result

    # 创建任务列表
    tasks = [process_single_file(file_info) for file_info in files_data]
    
    # 并发执行 (I/O wait 时会切换任务)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 处理结果
    for result in results:
        try:
            if isinstance(result, Exception):
                logger.error(f"Error processing file: {result}")
            elif result:
                all_students_results.append(result)
        except Exception as e:
            logger.error(f"Error handling file result: {e}")

    stu_dict = {stu['stu_id']: stu for stu in all_students_results if stu.get('stu_id')}
    student_store.clear()
    student_store.update(stu_dict)

    return stu_dict

@router.post("/")
async def handle_answer_upload(
    file: UploadFile = File(...),
    problem_store: Dict = Depends(get_problem_store),
    student_store: Dict = Depends(get_student_store),
    # 修改点：注入工厂依赖
    llm_factory: Callable = Depends(get_llm_factory)
    ):
    """
    接收上传的作业文件（压缩包或单个txt），提取内容，并交由AI分析。
    """
    logger.info(f"接收到文件: {file.filename}, 类型: {file.content_type}")
    
    try:
        file_bytes = await file.read()
        
        files_data = await extract_files_from_archive(file_bytes, file.filename)
        
        if not files_data:
            raise HTTPException(status_code=400, detail="未在上传文件中找到有效的文本文件。")

        logger.info(f"成功从 '{file.filename}' 中提取了 {len(files_data)} 个文件。")

        # 调用修改后的分析函数，传入工厂
        recognized_ans = await analyze_submissions(
            files_data=files_data,
            problems_data=problem_store,
            student_store=student_store,
            llm_factory=llm_factory, # 传入工厂
        )
        logger.info(f"成功分割作答内容，共处理 {len(recognized_ans)} 份。")

        return recognized_ans

    except ValueError as e:
        logger.error(f"处理失败: {e}")
        raise HTTPException(status_code=501, detail=str(e))
    except RuntimeError as e:
        logger.error(f"处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"处理文件 '{file.filename}' 时发生未知错误。")
        raise HTTPException(status_code=500, detail=f"处理文件时发生内部错误: {e}")