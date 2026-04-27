#!/bin/bash
# 抖音评论采集助手 - 快速启动脚本

echo "=================================="
echo "  抖音评论采集助手 v2.0"
echo "=================================="
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "⚠️  未检测到虚拟环境，正在创建..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
if ! python -c "import playwright" 2>/dev/null; then
    echo "⚠️  未检测到依赖，正在安装..."
    pip install -r requirements.txt
    playwright install chromium
    echo "✅ 依赖安装完成"
fi

# 显示菜单
echo ""
echo "请选择操作："
echo "1. 登录抖音账号"
echo "2. 开始采集评论"
echo "3. 运行系统测试"
echo "4. 退出"
echo ""
read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🔐 启动登录模式..."
        python main.py --login
        ;;
    2)
        echo ""
        echo "📊 启动采集模式..."
        python main.py
        ;;
    3)
        echo ""
        echo "🧪 运行系统测试..."
        python test_system.py
        ;;
    4)
        echo "👋 再见！"
        exit 0
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
