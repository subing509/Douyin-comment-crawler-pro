# -*- coding: utf-8 -*-
"""
配置管理器 - 配置文件读写和验证
"""

import os
import json
import shutil
from typing import Dict, List, Optional
from ..models.config import CrawlerConfig


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.json", default_template_path: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
            default_template_path: 默认模板路径（可选）
        """
        self.config_path = os.path.abspath(config_path)
        self.default_template_path = default_template_path
        self.template_candidates: List[str] = []
        if default_template_path:
            self.template_candidates.append(os.path.abspath(default_template_path))
        self.template_candidates.append(f"{self.config_path}.example")
        example_in_dir = os.path.join(os.path.dirname(self.config_path), "config.json.example")
        self.template_candidates.append(example_in_dir)
    
    def load_config(self) -> CrawlerConfig:
        """加载配置
        
        Returns:
            配置对象
        """
        self._ensure_config_file()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            config = CrawlerConfig.from_dict(data)
            
            if not config.validate():
                print("⚠️ 配置验证失败，使用默认配置")
                return self.get_default_config()

            self._normalize_extra_config(config)
            
            print(f"✅ 已加载配置: {self.config_path}")
            return config
            
        except Exception as e:
            print(f"⚠️ 加载配置失败: {e}，使用默认配置")
            return self.get_default_config()
    
    def save_config(self, config: CrawlerConfig):
        """保存配置
        
        Args:
            config: 配置对象
        """
        try:
            if not config.validate():
                print("❌ 配置验证失败，无法保存")
                return
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
            
            print(f"✅ 配置已保存: {self.config_path}")
            
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")
    
    def get_default_config(self) -> CrawlerConfig:
        """获取默认配置
        
        Returns:
            默认配置对象
        """
        return CrawlerConfig()

    def _normalize_extra_config(self, config: CrawlerConfig) -> None:
        """对代理与断点设置做类型检查"""
        config.enable_proxy = bool(config.enable_proxy)

        if config.proxy_list:
            if not isinstance(config.proxy_list, list):
                print("⚠️ proxy_list 格式错误，已忽略")
                config.proxy_list = None
            else:
                cleaned = [p for p in config.proxy_list if isinstance(p, str) and p.strip()]
                config.proxy_list = cleaned if cleaned else None

        if config.proxy and (not isinstance(config.proxy, str) or not config.proxy.strip()):
            print("⚠️ proxy 配置无效，已忽略")
            config.proxy = None

        if config.resume_state_file and (not isinstance(config.resume_state_file, str) or not config.resume_state_file.strip()):
            print("⚠️ resume_state_file 配置无效，已忽略")
            config.resume_state_file = None
    
    def validate_config(self, config: CrawlerConfig) -> bool:
        """验证配置有效性
        
        Args:
            config: 配置对象
            
        Returns:
            True表示配置有效
        """
        return config.validate()

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------

    def _ensure_config_file(self) -> None:
        """若配置不存在则尝试自动创建"""
        if os.path.exists(self.config_path):
            return

        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        for template in self.template_candidates:
            if template and os.path.exists(template):
                shutil.copyfile(template, self.config_path)
                print(f"🆕 已基于 {os.path.basename(template)} 创建配置: {self.config_path}")
                return

        # 无模板时写入默认配置
        default_config = self.get_default_config()
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"🆕 已生成默认配置: {self.config_path}")
