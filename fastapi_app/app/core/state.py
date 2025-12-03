# app/core/state.py

from typing import Dict, Any

# 모든 애플리케이션 상태 (모델 인스턴스, DB 연결 풀 등)를 저장할 전역 딕셔너리
state: Dict[str, Any] = {}