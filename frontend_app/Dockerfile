# 1. Node.js 20-slim 사용
FROM node:20-slim AS builder

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 의존성 캐싱 최적화
COPY package*.json ./

# 4. 의존성 설치
RUN npm install --production

# 5. 소스 코드 복사
COPY . .

# 6. Next.js 앱 빌드
RUN npm run build

# ---------------------------------
# 2단계: 실제 배포 이미지 (가벼운 런타임)
# ---------------------------------
FROM node:20-slim

WORKDIR /app

# 7. builder에서 필요한 파일만 복사
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# 8. 환경 변수 기본값 (선택)
ENV NODE_ENV=production
ENV PORT=3000

# 9. 포트 노출
EXPOSE 3000

# 10. 서버 실행
CMD ["npm", "start"]
