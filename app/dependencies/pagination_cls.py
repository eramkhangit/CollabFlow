from pydantic import BaseModel
from typing import TypeVar, Generic, List, Optional
from math import ceil

T = TypeVar('T')

class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 10
    
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        return self.page_size

class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    pagination: dict
    
    @classmethod
    def create(cls, items: List[T], total_count: int, params: PaginationParams):
        total_pages = ceil(total_count / params.page_size) if params.page_size > 0 else 0
        
        return cls(
            data=items,
            pagination={
                "total_count": total_count,
                "total_pages": total_pages,
                "current_page": params.page,
                "page_size": params.page_size,
                "has_next": params.page < total_pages,
                "has_previous": params.page > 1
            }
        )