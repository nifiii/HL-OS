"""
API重试工具函数
"""

import asyncio
import functools
import random
from typing import TypeVar, Callable
import logging

from app.core.exceptions import ExternalAPIError

logger = logging.getLogger(__name__)
T = TypeVar('T')


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    异步函数重试装饰器（指数退避）
    
    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        exponential_base: 指数基数
        jitter: 是否添加随机抖动
        exceptions: 需要重试的异常类型
    
    Returns:
        装饰器函数
    """
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    # 某些错误不应重试
                    if isinstance(e, (ValueError, KeyError, TypeError)):
                        raise
                    
                    if attempt < max_retries - 1:
                        # 计算延迟时间
                        sleep_time = delay
                        if jitter:
                            # 添加±50%的随机抖动
                            sleep_time *= (0.5 + random.random())
                        
                        logger.warning(
                            f"API调用失败，{sleep_time:.2f}秒后重试 "
                            f"(尝试 {attempt + 1}/{max_retries}): {str(e)}"
                        )
                        
                        await asyncio.sleep(sleep_time)
                        delay *= exponential_base
                    else:
                        logger.error(
                            f"API调用失败，已达最大重试次数 ({max_retries}): {str(e)}"
                        )
            
            # 所有重试都失败
            raise ExternalAPIError(
                message=f"API调用失败（已重试{max_retries}次）: {str(last_exception)}",
                service=func.__module__
            )
        
        return wrapper
    return decorator


class RateLimiter:
    """简单的速率限制器"""
    
    def __init__(self, max_calls: int, time_window: float):
        """
        初始化速率限制器
        
        Args:
            max_calls: 时间窗口内最大调用次数
            time_window: 时间窗口（秒）
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def acquire(self):
        """获取调用许可"""
        now = asyncio.get_event_loop().time()
        
        # 清理过期的调用记录
        self.calls = [t for t in self.calls if now - t < self.time_window]
        
        # 检查是否超过限制
        if len(self.calls) >= self.max_calls:
            # 等待直到最早的调用过期
            wait_time = self.time_window - (now - self.calls[0])
            logger.info(f"速率限制：等待 {wait_time:.2f}秒")
            await asyncio.sleep(wait_time)
            
            # 重新清理
            now = asyncio.get_event_loop().time()
            self.calls = [t for t in self.calls if now - t < self.time_window]
        
        # 记录本次调用
        self.calls.append(now)


# 全局速率限制器实例
gemini_rate_limiter = RateLimiter(max_calls=50, time_window=60)  # 50次/分钟
claude_rate_limiter = RateLimiter(max_calls=40, time_window=60)  # 40次/分钟
