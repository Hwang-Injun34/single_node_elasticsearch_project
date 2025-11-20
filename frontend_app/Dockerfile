# 1. Node.js 20-slim 사용 (빌더)
# (--platform=linux/amd64 제거됨 -> 자동으로 호스트 아키텍처에 맞게 설정)
FROM node:20-slim AS builder

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 의존성 파일 복사
COPY package*.json ./

# 4. 의존성 설치
RUN npm install

# 5. lightningcss 플랫폼 재빌드
# (네이티브 아키텍처로 빌드되므로 호환성 문제가 사라집니다)
RUN npm rebuild lightningcss

# 6. 소스 코드 복사
COPY . .

# 7. Next.js 앱 빌드
RUN npm run build

# ---------------------------------
# 2단계: 런타임 이미지
# ---------------------------------
# (여기도 --platform 제거)
FROM node:20-slim

WORKDIR /app

# 8. builder에서 필요한 파일만 복사
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# 9. 환경 변수 기본값
ENV NODE_ENV=production
ENV PORT=3000

# 10. 포트 노출
EXPOSE 3000

# 11. 서버 실행
CMD ["npm", "start"]