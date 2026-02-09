"""
知识库管理界面 (pages/knowledge_base.py)

提供完整的知识库管理功能，包括：
1. 知识库增删改查
2. 文件管理：上传、删除、预览文件
3. 知识库搜索和分类
4. 知识库使用统计
"""

import streamlit as st
import os
import json
import shutil
import time
from datetime import datetime
# from typing import Dict, List, Any, Optional
import pandas as pd
# from pathlib import Path
import hashlib
from utils import *

# 页面配置
st.set_page_config(
    page_title="SmarTAI - Knowledge Base Management",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 初始化会话状态
initialize_session_state()
load_custom_css()

# 知识库存储路径
KNOWLEDGE_BASE_DIR = "knowledge_bases"
KNOWLEDGE_BASE_CONFIG = "knowledge_base_config.json"

def init_knowledge_base():
    """初始化知识库系统"""
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        os.makedirs(KNOWLEDGE_BASE_DIR)
    
    if 'knowledge_bases' not in st.session_state:
        st.session_state.knowledge_bases = load_knowledge_base_config()
    
    if 'selected_kb' not in st.session_state:
        st.session_state.selected_kb = None

def load_knowledge_base_config():
    """加载知识库配置"""
    # 1. 尝试读取文件
    if os.path.exists(KNOWLEDGE_BASE_CONFIG):
        try:
            with open(KNOWLEDGE_BASE_CONFIG, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # ✅ 关键修改：如果读取到的数据不为空，才返回；如果是空的({})，则视为无效，去加载默认值
                if data: 
                    return data
        except Exception as e:
            st.error(f"Failed to load knowledge base configuration: {e}")
            # 如果出错，也加载默认值
            return get_default_knowledge_bases()
    # 2. 文件不存在，或文件内容为空 -> 加载默认演示数据
    return get_default_knowledge_bases()

def get_default_knowledge_bases():
    """获取默认的计算机类知识库数据"""
    current_time = datetime.now().isoformat()
    return {
        "kb_cs_algorithms": {
            "id": "kb_cs_algorithms",
            "name": "Advanced Algorithms and Data Structures",
            "description": "Covers advanced algorithm design, complexity analysis, dynamic programming, graph algorithms, etc.",
            "category": "Computer Science",
            "created_at": current_time,
            "updated_at": current_time,
            "file_count": 25,
            "total_size": 15728640,  # 约15MB
            "files": {}
        },
        "kb_cs_systems": {
            "id": "kb_cs_systems",
            "name": "Computer Systems Principles and Architecture",
            "description": "Computer organization, OS kernels, distributed system design, etc.",
            "category": "Computer Science",
            "created_at": current_time,
            "updated_at": current_time,
            "file_count": 32,
            "total_size": 22020096,
            "files": {}
        },
        "kb_cs_ai": {
            "id": "kb_cs_ai",
            "name": "Frontier AI Technologies",
            "description": "Machine learning, deep learning, NLP, computer vision, etc.",
            "category": "Computer Science",
            "created_at": current_time,
            "updated_at": current_time,
            "file_count": 41,
            "total_size": 31457280,  # 约30MB
            "files": {}
        },
        "kb_cs_security": {
            "id": "kb_cs_security",
            "name": "Network Security and Cryptography",
            "description": "Information security theory, cryptography algorithms, network defense, blockchain, etc.",
            "category": "Computer Science",
            "created_at": current_time,
            "updated_at": current_time,
            "file_count": 28,
            "total_size": 18874368,  # 约18MB
            "files": {}
        },
        "kb_cs_database": {
            "id": "kb_cs_database",
            "name": "Advanced Database Systems",
            "description": "Database kernel principles, distributed databases, NoSQL",
            "category": "Computer Science",
            "created_at": current_time,
            "updated_at": current_time,
            "file_count": 19,
            "total_size": 12582912,  # 约12MB
            "files": {}
        },
    }

def save_knowledge_base_config():
    """保存知识库配置"""
    try:
        with open(KNOWLEDGE_BASE_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.knowledge_bases, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        st.error(f"Failed to save knowledge base configuration: {e}")

def create_knowledge_base(name: str, description: str, category: str = "General"):
    """创建新的知识库"""
    kb_id = f"kb_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(name.encode()).hexdigest()[:8]}"
    kb_path = os.path.join(KNOWLEDGE_BASE_DIR, kb_id)
    
    if not os.path.exists(kb_path):
        os.makedirs(kb_path)
    
    kb_info = {
        "id": kb_id,
        "name": name,
        "description": description,
        "category": category,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "file_count": 0,
        "total_size": 0,
        "files": {}
    }
    
    st.session_state.knowledge_bases[kb_id] = kb_info
    save_knowledge_base_config()
    return kb_id

def delete_knowledge_base(kb_id: str):
    """删除知识库"""
    if kb_id in st.session_state.knowledge_bases:
        # 删除文件夹
        kb_path = os.path.join(KNOWLEDGE_BASE_DIR, kb_id)
        if os.path.exists(kb_path):
            try:
                shutil.rmtree(kb_path)
            except:
                print("Failed to delete path!")
        
        # 从配置中删除
        del st.session_state.knowledge_bases[kb_id]
        save_knowledge_base_config()
        
        # 如果删除的是当前选中的知识库，清除选择
        if st.session_state.selected_kb == kb_id:
            st.session_state.selected_kb = None

def add_file_to_kb(kb_id: str, file_name: str, file_content: bytes, file_type: str = "unknown"):
    """向知识库添加文件"""
    if kb_id not in st.session_state.knowledge_bases:
        return False
    
    kb_path = os.path.join(KNOWLEDGE_BASE_DIR, kb_id)
    file_path = os.path.join(kb_path, file_name)
    
    try:
        # 保存文件
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        # 更新配置
        file_id = hashlib.md5((file_name + datetime.now().isoformat()).encode()).hexdigest()[:12]
        file_info = {
            "id": file_id,
            "name": file_name,
            "type": file_type,
            "size": len(file_content),
            "uploaded_at": datetime.now().isoformat(),
            "path": file_path
        }
        
        st.session_state.knowledge_bases[kb_id]["files"][file_id] = file_info
        st.session_state.knowledge_bases[kb_id]["file_count"] += 1
        st.session_state.knowledge_bases[kb_id]["total_size"] += len(file_content)
        st.session_state.knowledge_bases[kb_id]["updated_at"] = datetime.now().isoformat()
        
        save_knowledge_base_config()
        return True
    except Exception as e:
        st.error(f"Failed to add file: {e}")
        return False

def remove_file_from_kb(kb_id: str, file_id: str):
    """从知识库中删除文件"""
    if kb_id not in st.session_state.knowledge_bases:
        return False
    
    kb_info = st.session_state.knowledge_bases[kb_id]
    if file_id not in kb_info["files"]:
        return False
    
    try:
        # 删除物理文件
        file_info = kb_info["files"][file_id]
        if os.path.exists(file_info["path"]):
            os.remove(file_info["path"])
        
        # 更新配置
        kb_info["file_count"] -= 1
        kb_info["total_size"] -= file_info["size"]
        kb_info["updated_at"] = datetime.now().isoformat()
        del kb_info["files"][file_id]
        
        save_knowledge_base_config()
        return True
    except Exception as e:
        st.error(f"Failed to delete file: {e}")
        return False

def render_header():
    """渲染页面头部"""
    col1, col2, col3 = st.columns([2, 16, 2])
    
    with col1:
        if st.button("🏠 Return Home", type="secondary"):
            st.switch_page("pages/main.py")
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>📚 Knowledge Base Management</h1>", 
                   unsafe_allow_html=True)
    
    with col3:
        if st.button("🔄 Refresh Data", type="secondary"):
            st.session_state.knowledge_bases = load_knowledge_base_config()
            st.success("Data refreshed!")
            st.rerun()

def render_knowledge_base_overview():
    """渲染知识库概览"""
    st.markdown("## 📊 Knowledge Base Overview")
    
    kbs = st.session_state.knowledge_bases
    total_kbs = len(kbs)
    total_files = sum(kb.get("file_count", 0) for kb in kbs.values())
    total_size = sum(kb.get("total_size", 0) for kb in kbs.values())
    
    # 格式化文件大小
    def format_size(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    # 统计卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 8px solid #1E3A8A;">
            <h1 style="color: #1E3A8A; margin: 0; font-size: 3rem;">{total_kbs}</h1>
            <p style="margin: 0.5rem 0 0 0; color: #64748B; font-weight: 600;">Total KBs</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 8px solid #10B981;">
            <h1 style="color: #10B981; margin: 0; font-size: 3rem;">{total_files}</h1>
            <p style="margin: 0.5rem 0 0 0; color: #64748B; font-weight: 600;">Total Files</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 8px solid #F59E0B;">
            <h1 style="color: #F59E0B; margin: 0; font-size: 3rem;">{format_size(total_size)}</h1>
            <p style="margin: 0.5rem 0 0 0; color: #64748B; font-weight: 600;">Storage Used</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        categories = set(kb.get("category", "General") for kb in kbs.values())
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem; background: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border-top: 8px solid #8B5CF6;">
            <h1 style="color: #8B5CF6; margin: 0; font-size: 3rem;">{len(categories)}</h1>
            <p style="margin: 0.5rem 0 0 0; color: #64748B; font-weight: 600;">Categories</p>
        </div>
        """, unsafe_allow_html=True)

def render_knowledge_base_list():
    """渲染知识库列表"""
    st.markdown("## 📖 Knowledge Base List")

    # 使用 st.expander 来包裹创建表单，代码更简洁
    with st.expander("➕ Click here to create a new Knowledge Base"):
        st.markdown("##### 1. Select Category")
        categories = ["General", "Computer Science", "Mathematics", "Physics", "Chemistry", "Biology", "Other"]
        # 使用 session_state 来保存用户的选择，以便在页面刷新后保留
        if 'category_selection' not in st.session_state:
            st.session_state.category_selection = "General"
        
        st.selectbox(
            "Category", 
            categories, 
            key="category_selection" # 绑定到 session_state
        )

        with st.form("new_kb_form", clear_on_submit=True):
            st.markdown("#### 2. Fill in details")
            new_kb_name = st.text_input("New Knowledge Base Name*", placeholder="e.g., Advanced Calculus - Chapter 5 - Key Points")
            new_kb_desc = st.text_area("Description (optional)", placeholder="Briefly describe content, course, or chapters.")
            
            # 使用 selectbox 提供更好的分类选择
            if st.session_state.category_selection == "Other":
                new_kb_category = st.text_input("Custom Category", placeholder="Enter custom category...")
            else:
                new_kb_category = st.session_state.category_selection

            knowledge_files = st.file_uploader(
                "Upload Knowledge Base Files (multi-select)",
                accept_multiple_files=True,
                type=['pdf', 'docx', 'txt', 'md']
            )
            
            submitted = st.form_submit_button("✅ Create Knowledge Base", type="primary", use_container_width=True)

            if submitted:
                if not new_kb_name:
                    st.error("Knowledge base name cannot be empty.")
                elif not knowledge_files:
                    st.error("Please upload at least one file.")
                else:
                    final_category = new_kb_category or "General"
                    with st.spinner(f"Creating knowledge base '{new_kb_name}'..."):
                        # 调用您已有的函数来创建知识库
                        kb_id = create_knowledge_base(new_kb_name, new_kb_desc, final_category)
                        
                        # 如果有上传文件，则添加到知识库中
                        if knowledge_files:
                            success_count = 0
                            for uploaded_file in knowledge_files:
                                file_content = uploaded_file.read()
                                file_type = uploaded_file.type or "unknown"
                                if add_file_to_kb(kb_id, uploaded_file.name, file_content, file_type):
                                    success_count += 1
                            st.success(f"✅ Knowledge base '{new_kb_name}' created successfully with {success_count} files uploaded!")
                            time.sleep(1)
                        else:
                            st.success(f"Knowledge base '{new_kb_name}' created successfully!")
                            time.sleep(1)
                    
                    # 成功后刷新页面，expander 会自动折叠，列表会更新
                    st.rerun()

    st.markdown("---") # 添加一条分割线，让界面更清晰

    # 搜索和筛选
    col1, col2 = st.columns(2)
    with col1:
        search_term = st.text_input("🔍 Search Knowledge Base", placeholder="Enter name or description...")
    with col2:
        categories = list(set(kb.get("category", "General") for kb in st.session_state.knowledge_bases.values()))
        if not categories:
            categories = ["General"]
        selected_category = st.selectbox("📂 Filter by Category", ["All"] + categories)
    
    # 过滤知识库
    filtered_kbs = {}
    for kb_id, kb_info in st.session_state.knowledge_bases.items():
        # 搜索过滤
        if search_term and search_term.lower() not in kb_info.get("name", "").lower() and search_term.lower() not in kb_info.get("description", "").lower():
            continue
        
        # 分类过滤
        if selected_category != "All" and kb_info.get("category", "General") != selected_category:
            continue
        
        filtered_kbs[kb_id] = kb_info
    
    if not filtered_kbs:
        st.info("No matching knowledge bases found.")
        return
    
    # 显示知识库卡片
    for kb_id, kb_info in filtered_kbs.items():
        with st.container():
            # 计算文件大小
            def format_size(size_bytes):
                if size_bytes < 1024:
                    return f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    return f"{size_bytes / 1024:.1f} KB"
                else:
                    return f"{size_bytes / (1024 * 1024):.1f} MB"
            
            file_count = kb_info.get("file_count", 0)
            total_size = kb_info.get("total_size", 0)
            category = kb_info.get("category", "General")
            
            # 根据分类设置颜色
            category_colors = {
                "General": "#6B7280",
                "Computer Science": "#3B82F6",
                "Mathematics": "#10B981",
                "Physics": "#F59E0B",
                "Chemistry": "#8B5CF6",
                "Biology": "#EF4444"
            }
            category_color = category_colors.get(category, "#6B7280")
            
            st.markdown(f"""
            <div style="background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: 1rem 0; border-left: 8px solid {category_color};">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                    <div style="flex: 1;">
                        <h3 style="color: #1E3A8A; margin: 0 0 0.5rem 0; font-size: 1.25rem;">📚 {kb_info['name']}</h3>
                        <p style="color: #64748B; margin: 0 0 0.75rem 0; line-height: 1.5;">{kb_info.get('description', 'No description')}</p>
                        <div style="display: flex; gap: 1rem; font-size: 0.85rem; color: #64748B;">
                            <span><strong>Category:</strong> {category}</span>
                            <span><strong>Files:</strong> {file_count}</span>
                            <span><strong>Size:</strong> {format_size(total_size)}</span>
                            <span><strong>Created:</strong> {kb_info.get('created_at', 'Unknown')[:10]}</span>
                        </div>
                    </div>
                    <div style="display: flex; gap: 0.5rem;">
                        <span style="background: {category_color}20; color: {category_color}; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.75rem; font-weight: 600;">
                            {category}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 操作按钮
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                if st.button("📂 Manage Files", key=f"manage_{kb_id}", use_container_width=True, type="secondary"):
                    st.session_state.selected_kb = kb_id
                    st.session_state.show_file_management = True
                    st.rerun()
            
            with col2:
                if st.button("✏️ Edit", key=f"edit_{kb_id}", use_container_width=True):
                    st.session_state.edit_kb_id = kb_id
                    st.session_state.show_edit_kb = True
                    st.rerun()
            
            with col3:
                if st.button("📋 Copy", key=f"copy_{kb_id}", use_container_width=True):
                    # 复制知识库
                    new_name = f"{kb_info['name']}_Copy"
                    new_kb_id = create_knowledge_base(new_name, kb_info.get('description', ''), kb_info.get('category', 'General'))
                    st.success(f"Knowledge base copied as: {new_name}")
                    st.rerun()
            
            with col4:
                if st.button("📊 Stats", key=f"stats_{kb_id}", use_container_width=True):
                    st.session_state.stats_kb_id = kb_id
                    st.session_state.show_kb_stats = True
                    st.rerun()
            
            with col5:
                if st.button("🗑️ Delete", key=f"delete_{kb_id}", use_container_width=True, type="secondary"):
                    st.session_state.delete_kb_id = kb_id
                    st.session_state.show_delete_confirm = True
                    st.rerun()
    
    # 处理各种弹窗
    handle_modals()

def handle_modals():
    """处理各种模态框"""
    # 创建知识库模态框
    # if st.session_state.get('show_create_kb', False):
    #     render_create_kb_modal()
    
    # 编辑知识库模态框
    if st.session_state.get('show_edit_kb', False):
        render_edit_kb_modal()
    
    # 文件管理模态框
    if st.session_state.get('show_file_management', False):
        render_file_management_modal()
    
    # 删除确认模态框
    if st.session_state.get('show_delete_confirm', False):
        render_delete_confirm_modal()
    
    # 知识库统计模态框
    if st.session_state.get('show_kb_stats', False):
        render_kb_stats_modal()

def render_create_kb_modal():
    """渲染创建知识库模态框（完整功能版）"""
    with st.expander("➕ Create New Knowledge Base", expanded=True):
        st.markdown("### Create a New Knowledge Base")
        
        with st.form("create_kb_form", clear_on_submit=True):
            name = st.text_input("Knowledge Base Name*", placeholder="Enter name...")
            description = st.text_area("Description", placeholder="Enter description...", height=100)
            
            # 预设分类 + 其他选项
            categories = ["General", "Computer Science", "Mathematics", "Physics", "Chemistry", "Biology", "Other"]
            category_selection = st.selectbox("Category", categories)
            
            # 如果选择"其他"，则显示自定义输入框
            if category_selection == "Other":
                category = st.text_input("Custom Category", placeholder="Enter custom category...")
            else:
                category = category_selection

            # 文件上传
            uploaded_files = st.file_uploader(
                "Upload Initial Files (Optional)",
                accept_multiple_files=True,
                type=['txt', 'pdf', 'doc', 'docx', 'json', 'csv', 'xlsx']
            )

            # 提交按钮
            submitted = st.form_submit_button("✅ Create Knowledge Base", type="primary")

            if submitted:
                if not name:
                    st.error("Knowledge base name cannot be empty!")
                else:
                    final_category = category if category else "General"
                    with st.spinner(f"Creating knowledge base '{name}'..."):
                        # 1. 创建知识库基础信息
                        kb_id = create_knowledge_base(name, description, final_category)
                        
                        # 2. 如果有上传文件，则添加到知识库中
                        if uploaded_files:
                            success_count = 0
                            for uploaded_file in uploaded_files:
                                file_content = uploaded_file.read()
                                file_type = uploaded_file.type or "unknown"
                                if add_file_to_kb(kb_id, uploaded_file.name, file_content, file_type):
                                    success_count += 1
                            st.success(f"Knowledge base '{name}' created successfully with {success_count} files uploaded!")
                        else:
                            st.success(f"Knowledge base '{name}' created successfully!")
                    
                    # 3. 关闭模态框并刷新
                    st.session_state.show_create_kb = False
                    st.rerun()

        # 在表单外部添加取消按钮
        if st.button("❌ Cancel", key="cancel_create_kb"):
            st.session_state.show_create_kb = False
            st.rerun()

def render_edit_kb_modal():
    """渲染编辑知识库模态框"""
    kb_id = st.session_state.get('edit_kb_id')
    if not kb_id or kb_id not in st.session_state.knowledge_bases:
        return
    
    kb_info = st.session_state.knowledge_bases[kb_id]
    
    with st.expander("✏️ Edit Knowledge Base", expanded=True):
        st.markdown(f"### Edit Knowledge Base: {kb_info['name']}")
        
        new_name = st.text_input("Knowledge Base Name*", value=kb_info['name'], key="edit_kb_name")
        new_description = st.text_area("Description", value=kb_info.get('description', ''), height=100, key="edit_kb_desc")
        
        categories = ["General", "Computer Science", "Mathematics", "Physics", "Chemistry", "Biology", "Other"]
        current_category = kb_info.get('category', 'General')
        if current_category not in categories:
            categories.append(current_category)
        
        new_category = st.selectbox("Category", categories, index=categories.index(current_category), key="edit_kb_category")
        
        if new_category == "Other":
            new_category = st.text_input("Custom Category", placeholder="Enter custom category...", key="edit_kb_custom_category")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Save", key="save_edit_kb", type="primary"):
                st.session_state.knowledge_bases[kb_id]['name'] = new_name
                st.session_state.knowledge_bases[kb_id]['description'] = new_description
                st.session_state.knowledge_bases[kb_id]['category'] = new_category
                st.session_state.knowledge_bases[kb_id]['updated_at'] = datetime.now().isoformat()
                save_knowledge_base_config()
                st.success("Knowledge base updated!")
                st.session_state.show_edit_kb = False
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel", key="cancel_edit_kb"):
                st.session_state.show_edit_kb = False
                st.rerun()

def render_file_management_modal():
    """渲染文件管理模态框"""
    kb_id = st.session_state.get('selected_kb')
    if not kb_id or kb_id not in st.session_state.knowledge_bases:
        return
    
    kb_info = st.session_state.knowledge_bases[kb_id]
    
    with st.expander(f"📂 Manage Files - {kb_info['name']}", expanded=True):
        st.markdown(f"### 📂 {kb_info['name']} - File Management")
        
        # 文件上传
        st.markdown("#### 📤 Upload Files")
        uploaded_files = st.file_uploader(
            "Select files to upload",
            accept_multiple_files=True,
            type=['txt', 'pdf', 'doc', 'docx', 'json', 'csv', 'xlsx'],
            key="file_upload"
        )
        
        if uploaded_files:
            if st.button("📤 Upload Selected Files", type="primary"):
                success_count = 0
                for uploaded_file in uploaded_files:
                    file_content = uploaded_file.read()
                    file_type = uploaded_file.type or "unknown"
                    
                    if add_file_to_kb(kb_id, uploaded_file.name, file_content, file_type):
                        success_count += 1
                
                if success_count > 0:
                    st.success(f"Successfully uploaded {success_count} files!")
                    st.rerun()
                else:
                    st.error("File upload failed!")
        
        st.markdown("---")
        
        # 文件列表
        st.markdown("#### 📁 Existing Files")
        files = kb_info.get("files", {})
        
        if not files:
            st.info("No files in this knowledge base.")
        else:
            # 文件搜索
            file_search = st.text_input("🔍 Search Files", placeholder="Enter filename...")
            
            # 过滤文件
            filtered_files = {}
            for file_id, file_info in files.items():
                if not file_search or file_search.lower() in file_info.get("name", "").lower():
                    filtered_files[file_id] = file_info
            
            if not filtered_files:
                st.info("No matching files found.")
            else:
                # 显示文件列表
                for file_id, file_info in filtered_files.items():
                    def format_size(size_bytes):
                        if size_bytes < 1024:
                            return f"{size_bytes} B"
                        elif size_bytes < 1024 * 1024:
                            return f"{size_bytes / 1024:.1f} KB"
                        else:
                            return f"{size_bytes / (1024 * 1024):.1f} MB"
                    
                    # 文件类型图标
                    type_icons = {
                        "text/plain": "📄",
                        "application/pdf": "📕",
                        "application/msword": "📘",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "📘",
                        "application/json": "📋",
                        "text/csv": "📊",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "📊"
                    }
                    file_icon = type_icons.get(file_info.get("type", ""), "📄")
                    
                    st.markdown(f"""
                    <div style="background: #F8FAFC; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 8px solid #3B82F6;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 1.2rem; margin-right: 0.5rem;">{file_icon}</span>
                                <strong style="color: #1E3A8A;">{file_info['name']}</strong>
                                <span style="color: #64748B; margin-left: 1rem; font-size: 0.85rem;">
                                    {format_size(file_info.get('size', 0))} | {file_info.get('uploaded_at', 'Unknown')[:10]}
                                </span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 文件操作按钮
                    col1, col2, col3 = st.columns([1, 1, 1])
                    
                    with col1:
                        if st.button("👀 Preview", key=f"preview_file_{file_id}", use_container_width=True):
                            st.info(f"Previewing file: {file_info['name']}")
                    
                    with col2:
                        if st.button("📥 Download", key=f"download_file_{file_id}", use_container_width=True):
                            st.info(f"Downloading file: {file_info['name']}")
                    
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_file_{file_id}", use_container_width=True, type="secondary"):
                            if remove_file_from_kb(kb_id, file_id):
                                st.success(f"File '{file_info['name']}' deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete file!")
        
        # 关闭按钮
        if st.button("❌ Close File Management", key="close_file_management"):
            st.session_state.show_file_management = False
            st.rerun()

def render_delete_confirm_modal():
    """渲染删除确认模态框"""
    kb_id = st.session_state.get('delete_kb_id')
    if not kb_id or kb_id not in st.session_state.knowledge_bases:
        return
    
    kb_info = st.session_state.knowledge_bases[kb_id]
    
    st.error(f"⚠️ Confirm delete knowledge base: **{kb_info['name']}**?")
    st.markdown(f"This knowledge base contains **{kb_info.get('file_count', 0)}** files. Deletion cannot be undone!")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🗑️ Confirm Delete", key="confirm_delete_kb", type="primary"):
            delete_knowledge_base(kb_id)
            st.success(f"Knowledge base '{kb_info['name']}' deleted!")
            st.session_state.show_delete_confirm = False
            st.rerun()
    
    with col2:
        if st.button("❌ Cancel", key="cancel_delete_kb"):
            st.session_state.show_delete_confirm = False
            st.rerun()

def render_kb_stats_modal():
    """渲染知识库统计模态框"""
    kb_id = st.session_state.get('stats_kb_id')
    if not kb_id or kb_id not in st.session_state.knowledge_bases:
        return
    
    kb_info = st.session_state.knowledge_bases[kb_id]
    
    with st.expander(f"📊 KB Statistics - {kb_info['name']}", expanded=True):
        st.markdown(f"### 📊 {kb_info['name']} - Detailed Statistics")
        
        # 基本统计
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Files", kb_info.get('file_count', 0))
        
        with col2:
            def format_size(size_bytes):
                if size_bytes < 1024:
                    return f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    return f"{size_bytes / 1024:.1f} KB"
                else:
                    return f"{size_bytes / (1024 * 1024):.1f} MB"
            
            st.metric("Total Size", format_size(kb_info.get('total_size', 0)))
        
        with col3:
            created_date = kb_info.get('created_at', '')
            if created_date:
                days_ago = (datetime.now() - datetime.fromisoformat(created_date)).days
                st.metric("Days Created", f"{days_ago} days")
        
        # 文件类型统计
        st.markdown("#### 📁 File Type Distribution")
        files = kb_info.get("files", {})
        
        if files:
            type_counts = {}
            for file_info in files.values():
                file_type = file_info.get("type", "unknown").split("/")[-1]
                type_counts[file_type] = type_counts.get(file_type, 0) + 1
            
            # 创建简单的条形图数据
            df = pd.DataFrame(list(type_counts.items()), columns=['File Type', 'Count'])
            st.bar_chart(df.set_index('File Type'))
        else:
            st.info("No file data available.")
        
        # 时间线
        st.markdown("#### 📅 File Upload Timeline")
        if files:
            upload_dates = []
            for file_info in files.values():
                upload_date = file_info.get('uploaded_at', '')
                if upload_date:
                    upload_dates.append(upload_date[:10])  # 只取日期部分
            
            if upload_dates:
                date_counts = {}
                for date in upload_dates:
                    date_counts[date] = date_counts.get(date, 0) + 1
                
                df_timeline = pd.DataFrame(list(date_counts.items()), columns=['Date', 'Upload Count'])
                df_timeline['Date'] = pd.to_datetime(df_timeline['Date'])
                df_timeline = df_timeline.sort_values('Date')
                st.line_chart(df_timeline.set_index('Date'))
        
        if st.button("❌ Close Stats", key="close_kb_stats"):
            st.session_state.show_kb_stats = False
            st.rerun()

def main():
    """主函数"""
    init_knowledge_base()
    
    render_header()
    st.markdown("---")
    
    render_knowledge_base_overview()
    st.markdown("---")
    
    render_knowledge_base_list()

    inject_pollers_for_active_jobs()

if __name__ == "__main__":
    main()