#!/usr/bin/env python3
"""开发环境启动脚本"""

from miniblog import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)