from typing import Dict, Any

"""
제목: 애플리케이션 전역 상태 저장소 
목적: DB 커넥션, 모델 인스턴스 등 공용 객체 관리
핵심동작: 키-값 형태로 런타임 상태 저장
"""
state: Dict[str, Any] = {}