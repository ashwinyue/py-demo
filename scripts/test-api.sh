#!/bin/bash
# -*- coding: utf-8 -*-
# API接口完整测试脚本（使用curl替代Python）
# 测试所有API接口，包括用户注册、登录、激活、CRUD操作等

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
USER_SERVICE_URL="${USER_SERVICE_URL:-http://localhost:5001}"
BLOG_SERVICE_URL="${BLOG_SERVICE_URL:-http://localhost:5002}"
BASE_URL="${BASE_URL:-http://localhost:8080}"

# 全局变量
ACCESS_TOKEN=""
REFRESH_TOKEN=""
USER_ID=""
USERNAME=""
POST_ID=""
TEST_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0

# 生成随机字符串
generate_random_string() {
    local length=${1:-8}
    cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w $length | head -n 1
}

# 记录测试结果
log_test() {
    local test_name="$1"
    local success="$2"
    local message="$3"
    
    TEST_COUNT=$((TEST_COUNT + 1))
    
    if [ "$success" = "true" ]; then
        echo -e "${GREEN}✅ PASS${NC} $test_name: $message"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${RED}❌ FAIL${NC} $test_name: $message"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

# 发送HTTP请求
make_request() {
    local method="$1"
    local url="$2"
    local data="$3"
    local auth_required="${4:-false}"
    
    local headers="-H 'Content-Type: application/json' -H 'Accept: application/json'"
    
    if [ "$auth_required" = "true" ] && [ -n "$ACCESS_TOKEN" ]; then
        headers="$headers -H 'Authorization: Bearer $ACCESS_TOKEN'"
    fi
    
    if [ -n "$data" ]; then
        eval "curl -s -X $method $headers -d '$data' '$url'"
    else
        eval "curl -s -X $method $headers '$url'"
    fi
}

# 测试健康检查
test_health_check() {
    echo -e "\n${BLUE}=== 测试健康检查 ===${NC}"
    
    # 测试用户服务健康检查
    local response=$(make_request "GET" "$USER_SERVICE_URL/health")
    if echo "$response" | grep -q "healthy\|ok\|success" 2>/dev/null; then
        log_test "用户服务健康检查" "true" "服务正常运行"
    else
        log_test "用户服务健康检查" "false" "服务可能未运行或异常"
    fi
    
    # 测试博客服务健康检查
    response=$(make_request "GET" "$BLOG_SERVICE_URL/health")
    if echo "$response" | grep -q "healthy\|ok\|success" 2>/dev/null; then
        log_test "博客服务健康检查" "true" "服务正常运行"
    else
        log_test "博客服务健康检查" "false" "服务可能未运行或异常"
    fi
}

# 测试用户注册
test_user_registration() {
    echo -e "\n${BLUE}=== 测试用户注册 ===${NC}"
    
    local random_suffix=$(generate_random_string 6)
    USERNAME="testuser_${random_suffix}"
    local email="${USERNAME}@example.com"
    local password="TestPass123!"
    
    local data=$(cat <<EOF
{
    "username": "$USERNAME",
    "email": "$email",
    "password": "$password"
}
EOF
)
    
    local response=$(make_request "POST" "$USER_SERVICE_URL/api/v1/users/register" "$data")
    
    if echo "$response" | grep -q "success\|created\|registered" 2>/dev/null; then
        USER_ID=$(echo "$response" | grep -o '"user_id":[0-9]*' | cut -d':' -f2 2>/dev/null || echo "")
        log_test "用户注册" "true" "用户 $USERNAME 注册成功"
    else
        log_test "用户注册" "false" "用户注册失败: $response"
    fi
}

# 测试用户登录
test_user_login() {
    echo -e "\n${BLUE}=== 测试用户登录 ===${NC}"
    
    local data=$(cat <<EOF
{
    "username": "$USERNAME",
    "password": "TestPass123!"
}
EOF
)
    
    local response=$(make_request "POST" "$USER_SERVICE_URL/api/v1/users/login" "$data")
    
    if echo "$response" | grep -q "access_token" 2>/dev/null; then
        ACCESS_TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "")
        REFRESH_TOKEN=$(echo "$response" | grep -o '"refresh_token":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "")
        log_test "用户登录" "true" "用户 $USERNAME 登录成功"
    else
        log_test "用户登录" "false" "用户登录失败: $response"
    fi
}

# 测试获取当前用户信息
test_get_current_user() {
    echo -e "\n${BLUE}=== 测试获取当前用户信息 ===${NC}"
    
    local response=$(make_request "GET" "$USER_SERVICE_URL/api/v1/users/profile" "" "true")
    
    if echo "$response" | grep -q "$USERNAME" 2>/dev/null; then
        log_test "获取当前用户信息" "true" "成功获取用户信息"
    else
        log_test "获取当前用户信息" "false" "获取用户信息失败: $response"
    fi
}

# 测试创建博客文章
test_create_post() {
    echo -e "\n${BLUE}=== 测试创建博客文章 ===${NC}"
    
    local title="测试文章_$(generate_random_string 4)"
    local content="这是一篇测试文章的内容，用于验证API功能。"
    
    local data=$(cat <<EOF
{
    "title": "$title",
    "content": "$content",
    "status": "published"
}
EOF
)
    
    local response=$(make_request "POST" "$BLOG_SERVICE_URL/api/v1/posts" "$data" "true")
    
    if echo "$response" | grep -q "success\|created" 2>/dev/null; then
        POST_ID=$(echo "$response" | grep -o '"post_id":[0-9]*' | cut -d':' -f2 2>/dev/null || echo "")
        log_test "创建博客文章" "true" "文章创建成功: $title"
    else
        log_test "创建博客文章" "false" "文章创建失败: $response"
    fi
}

# 测试获取博客文章列表
test_get_posts() {
    echo -e "\n${BLUE}=== 测试获取博客文章列表 ===${NC}"
    
    local response=$(make_request "GET" "$BLOG_SERVICE_URL/api/v1/posts")
    
    if echo "$response" | grep -q "posts\|data" 2>/dev/null; then
        log_test "获取博客文章列表" "true" "成功获取文章列表"
    else
        log_test "获取博客文章列表" "false" "获取文章列表失败: $response"
    fi
}

# 测试获取博客文章详情
test_get_post_detail() {
    echo -e "\n${BLUE}=== 测试获取博客文章详情 ===${NC}"
    
    if [ -z "$POST_ID" ]; then
        log_test "获取博客文章详情" "false" "没有可用的文章ID"
        return
    fi
    
    local response=$(make_request "GET" "$BLOG_SERVICE_URL/api/v1/posts/$POST_ID")
    
    if echo "$response" | grep -q "title\|content" 2>/dev/null; then
        log_test "获取博客文章详情" "true" "成功获取文章详情"
    else
        log_test "获取博客文章详情" "false" "获取文章详情失败: $response"
    fi
}

# 测试更新博客文章
test_update_post() {
    echo -e "\n${BLUE}=== 测试更新博客文章 ===${NC}"
    
    if [ -z "$POST_ID" ]; then
        log_test "更新博客文章" "false" "没有可用的文章ID"
        return
    fi
    
    local new_title="更新后的测试文章_$(generate_random_string 4)"
    local new_content="这是更新后的文章内容。"
    
    local data=$(cat <<EOF
{
    "title": "$new_title",
    "content": "$new_content"
}
EOF
)
    
    local response=$(make_request "PUT" "$BLOG_SERVICE_URL/api/v1/posts/$POST_ID" "$data" "true")
    
    if echo "$response" | grep -q "success\|updated" 2>/dev/null; then
        log_test "更新博客文章" "true" "文章更新成功"
    else
        log_test "更新博客文章" "false" "文章更新失败: $response"
    fi
}

# 测试点赞文章
test_like_post() {
    echo -e "\n${BLUE}=== 测试点赞文章 ===${NC}"
    
    if [ -z "$POST_ID" ]; then
        log_test "点赞文章" "false" "没有可用的文章ID"
        return
    fi
    
    local response=$(make_request "POST" "$BLOG_SERVICE_URL/api/v1/posts/$POST_ID/like" "" "true")
    
    if echo "$response" | grep -q "success\|liked" 2>/dev/null; then
        log_test "点赞文章" "true" "文章点赞成功"
    else
        log_test "点赞文章" "false" "文章点赞失败: $response"
    fi
}

# 测试删除博客文章
test_delete_post() {
    echo -e "\n${BLUE}=== 测试删除博客文章 ===${NC}"
    
    if [ -z "$POST_ID" ]; then
        log_test "删除博客文章" "false" "没有可用的文章ID"
        return
    fi
    
    local response=$(make_request "DELETE" "$BLOG_SERVICE_URL/api/v1/posts/$POST_ID" "" "true")
    
    if echo "$response" | grep -q "success\|deleted" 2>/dev/null; then
        log_test "删除博客文章" "true" "文章删除成功"
    else
        log_test "删除博客文章" "false" "文章删除失败: $response"
    fi
}

# 测试用户登出
test_user_logout() {
    echo -e "\n${BLUE}=== 测试用户登出 ===${NC}"
    
    local response=$(make_request "POST" "$USER_SERVICE_URL/api/v1/users/logout" "" "true")
    
    if echo "$response" | grep -q "success\|logout" 2>/dev/null; then
        log_test "用户登出" "true" "用户登出成功"
        ACCESS_TOKEN=""
        REFRESH_TOKEN=""
    else
        log_test "用户登出" "false" "用户登出失败: $response"
    fi
}

# 运行所有测试
run_all_tests() {
    echo -e "${YELLOW}开始运行API接口测试...${NC}"
    echo -e "用户服务URL: $USER_SERVICE_URL"
    echo -e "博客服务URL: $BLOG_SERVICE_URL"
    echo -e "基础URL: $BASE_URL"
    
    # 运行测试
    test_health_check
    test_user_registration
    test_user_login
    test_get_current_user
    test_create_post
    test_get_posts
    test_get_post_detail
    test_update_post
    test_like_post
    test_delete_post
    test_user_logout
    
    # 打印测试总结
    print_test_summary
}

# 打印测试总结
print_test_summary() {
    echo -e "\n${YELLOW}=== 测试总结 ===${NC}"
    echo -e "总测试数: $TEST_COUNT"
    echo -e "${GREEN}通过: $PASS_COUNT${NC}"
    echo -e "${RED}失败: $FAIL_COUNT${NC}"
    
    local success_rate=0
    if [ $TEST_COUNT -gt 0 ]; then
        success_rate=$((PASS_COUNT * 100 / TEST_COUNT))
    fi
    echo -e "成功率: ${success_rate}%"
    
    if [ $FAIL_COUNT -eq 0 ]; then
        echo -e "\n${GREEN}🎉 所有测试通过！${NC}"
        exit 0
    else
        echo -e "\n${RED}❌ 有测试失败，请检查服务状态${NC}"
        exit 1
    fi
}

# 主函数
main() {
    # 检查curl是否可用
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}错误: curl 命令未找到，请先安装 curl${NC}"
        exit 1
    fi
    
    # 运行所有测试
    run_all_tests
}

# 如果直接运行此脚本
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi