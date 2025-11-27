from pydantic import BaseModel, Field
from typing import List, Any, Optional


# ===============================
#           [1단계]
# ===============================
# -- 1. 개별 페이지 텍스트 -- 
class PageTextSchema(BaseModel):
    page_num: int
    text: str

# -- 2. 전체 페이지 리스트 --
class TotalPageTextSchema(BaseModel):
    page_list: List[PageTextSchema]

# -- 3. DB 저자용 스키마 --
class DocumentContentSaveSchema(BaseModel):
    compressed_page_texts: bytes


# ===============================
#           [2단계]
# ===============================
# -- 추출한 json_data를 세그먼트로 파싱하기 위한 [2단계] 전용 -- 
class SegmentSchema(BaseModel):
    segment_id: str 
    page: int 
    speaker_name: Optional[str]
    speaker_role: Optional[str]
    text: str 

class PageSegmentsSchema(BaseModel):
    page: int
    segments: List[SegmentSchema]

class DocumentPageSegmentsSchema(BaseModel):
    pages: List[PageSegmentsSchema]



"""
{
    "pages": [
        {
            "page": 1,
            "segments": [
                {
                "segment_id": "1_1",
                "page": 1,
                "speaker_name": "박주민",
                "speaker_role": "위원장",
                "text": "10시가 됐습니다.\n좌석을 정돈해 주시기 바랍니다.\n성원이 되었으므로..."
                }
            ]
        },
        {
            "page": 2,
            "segments": [
                {
                "segment_id": "2_1",
                "page": 2,
                "speaker_name": "강선우",
                "speaker_role": "위원",
                "text": "서울 강서갑 국회의원 강선우입니다..."
                },
        {
            "segment_id": "2_2",
            "page": 2,
            "speaker_name": "박주민",
            "speaker_role": "위원장",
            "text": "다음은 김남희 위원님 인사말씀 부탁드리겠습니다."
            },
        {
            "segment_id": "2_3",
            "page": 2,
            "speaker_name": "김남희",
            "speaker_role": "위원",
            "text": "안녕하십니까? 광명을 국회의원 김남희입니다..."
            }
        ]
        }
    ]
}

"""