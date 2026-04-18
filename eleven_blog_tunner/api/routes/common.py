"""
通用响应类型模块

提供统一的 API 响应格式
"""
from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel
from enum import Enum

T = TypeVar("T")


class ResponseCode(str, Enum):
    """响应码枚举"""
    SUCCESS = "200"           # 成功
    BAD_REQUEST = "400"      # 请求参数错误
    UNAUTHORIZED = "401"     # 未授权
    FORBIDDEN = "403"        # 禁止访问
    NOT_FOUND = "404"        # 资源不存在
    INTERNAL_ERROR = "500"   # 服务器内部错误
    VALIDATION_ERROR = "422"  # 数据验证错误


class CommonResponse(BaseModel, Generic[T]):
    """通用响应类型

    所有 API 响应统一使用此格式

    Attributes:
        code: 状态码 (默认 "200" 表示成功)
        data: 响应数据
        message: 提示信息（成功信息或错误信息）
    """
    code: str = ResponseCode.SUCCESS.value
    data: Optional[T] = None
    message: str = "操作成功"

    class Config:
        json_schema_extra = {
            "example": {
                "code": "200",
                "data": {},
                "message": "操作成功"
            }
        }


class SuccessResponse(Generic[T]):
    """成功响应工厂"""

    @staticmethod
    def build(
        data: Optional[T] = None,
        message: str = "操作成功"
    ) -> CommonResponse[T]:
        """
        构建成功响应

        Args:
            data: 响应数据
            message: 提示信息

        Returns:
            CommonResponse 实例
        """
        return CommonResponse(
            code=ResponseCode.SUCCESS.value,
            data=data,
            message=message
        )


class ErrorResponse:
    """错误响应工厂"""

    @staticmethod
    def build(
        code: str = ResponseCode.INTERNAL_ERROR.value,
        message: str = "操作失败",
        data: Optional[Any] = None
    ) -> CommonResponse[Any]:
        """
        构建错误响应

        Args:
            code: 错误码
            message: 错误信息
            data: 附加数据

        Returns:
            CommonResponse 实例
        """
        return CommonResponse(
            code=code,
            data=data,
            message=message
        )

    @staticmethod
    def bad_request(message: str = "请求参数错误") -> CommonResponse[Any]:
        """400 错误响应"""
        return ErrorResponse.build(
            code=ResponseCode.BAD_REQUEST.value,
            message=message
        )

    @staticmethod
    def not_found(message: str = "资源不存在") -> CommonResponse[Any]:
        """404 错误响应"""
        return ErrorResponse.build(
            code=ResponseCode.NOT_FOUND.value,
            message=message
        )

    @staticmethod
    def internal_error(message: str = "服务器内部错误") -> CommonResponse[Any]:
        """500 错误响应"""
        return ErrorResponse.build(
            code=ResponseCode.INTERNAL_ERROR.value,
            message=message
        )

    @staticmethod
    def validation_error(message: str = "数据验证错误") -> CommonResponse[Any]:
        """422 错误响应"""
        return ErrorResponse.build(
            code=ResponseCode.VALIDATION_ERROR.value,
            message=message
        )