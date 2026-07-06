# ADAS Scripts

## Cách chạy nhanh nhất

```bash
npm run dev
```

Khởi động đồng thời:
- Dashboard: http://localhost:3000/
- Node Backend: http://127.0.0.1:3000/api/health
- Streamlit AI Demo: http://localhost:8501/

---

## Chạy riêng từng phần

### AI Service (Python/FastAPI)
```bash
cd backend/ai-service
pip install -r requirements.txt
python main.py
```

### Node Server
```bash
cd backend/node-server
npm install
npm start
```

### Frontend
```bash
cd frontend
npm install
npm start
```

---

## Chạy Demo Root (Streamlit)

```bash
streamlit run main.py
```

Chọn:
- Chế độ: Ảnh / Video / Webcam
- Module: Pedestrian, Vehicle, Lane Detection, Traffic Sign
- Bật/tắt preprocessing

---

## Auto-start Scripts

### Linux/macOS
```bash
bash scripts/start-all.sh
```

### Windows
```cmd
scripts\start-all.bat
```
