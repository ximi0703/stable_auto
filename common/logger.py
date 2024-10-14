#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
# @Author   : chuanwen.peng
# @Time     : 2023/3/6 10:23
# @File     : logger.py
# @Project  : StabilityTest
"""

import logging.config
import os


def main(project_dir, func_stack):
    log_dir = os.path.join(project_dir, "report", func_stack, "log")
    # 日志配置
    LOGGING_DIC = {
        'version': 1,
        # 禁用已经存在的logger实例
        'disable_existing_loggers': False,
        # 日志格式化(负责配置log message 的最终顺序，结构，及内容)
        'formatters': {
            'simple': {
                'format': "[%(levelname)s %(asctime)s %(filename)s:%(lineno)d %(funcName)s] %(message)s",
                'datefmt': "%m-%d %H:%M:%S"
            }
        },
        # 过滤器，决定哪个log记录被输出
        'filters': {},
        # 负责将Log message 分派到指定的destination
        'handlers': {
            # 打印到终端的日志
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',  # 打印到屏幕
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
            },
            # 打印到common文件的日志,收集info及以上的日志
            'common': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件
                'formatter': 'simple',
                'filename': '%s/info.log' % log_dir,  # 日志文件路径
                'maxBytes': 1024 * 1024 * 5,  # 日志大小 5M
                'backupCount': 5,  # 备份5个日志文件
                'encoding': 'utf-8',  # 日志文件的编码，再也不用担心中文log乱码了
            },
            # 打印到importance文件的日志,收集error及以上的日志
            'importance': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',  # 保存到文件
                'formatter': 'simple',
                'filename': '%s/error.log' % log_dir,  # 日志文件
                'maxBytes': 1024 * 1024 * 5,  # 日志大小 5M
                'backupCount': 5,  # 备份5个日志文件
                'encoding': 'utf-8',  # 日志文件的编码，再也不用担心中文log乱码了
            }
        },
        # logger实例
        'loggers': {
            'app': {
                'handlers': ['console', 'common', 'importance'],
                'level': 'INFO',
                'propagate': True,  # 向上（更高level的logger）传递
            }
        },
        'root': {
            'handlers': ['console', 'common', 'importance'],
            'level': 'INFO'
        }
    }
    return LOGGING_DIC


def setup_logger(project_dir, func_stack):
    """初始化日志配置"""
    LOGGING_DIC = main(project_dir,func_stack)
    log_path = os.path.join(project_dir, "report",func_stack, "log")
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    logging.config.dictConfig(LOGGING_DIC)
