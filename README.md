# Bot nhạc Discord / YouTube

## Cài đặt (Windows PowerShell)

1. Cài Python 3.11 trở lên và FFmpeg; kiểm tra `ffmpeg -version` chạy được trong terminal. Cài Node.js nếu phiên bản yt-dlp cần runtime JavaScript để hỗ trợ YouTube.
2. Vào https://discord.com/developers/applications tạo Application và Bot, lấy token ở trang Bot. Đừng chia sẻ token hoặc đưa file `.env` lên Git.
3. Trong Installation / OAuth2 tạo link cài vào server với scopes `bot` và `applications.commands`; cấp quyền `View Channels`, `Send Messages`, `Connect`, `Speak`. Mời bot vào server bạn quản lý.
4. Mở terminal tại thư mục này và chạy:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python bot.py
```

Trong `.env`, thay `dien_token_bot_vao_day` bằng token thật. Vào kênh thoại rồi dùng `/play <link YouTube hoặc tên bài>`. Các lệnh còn lại: `/skip`, `/stop`, `/leave`.

Bot phải luôn chạy trên máy chủ hoặc máy tính để phát nhạc. Trích xuất YouTube có thể gián đoạn khi YouTube thay đổi; cập nhật bằng `pip install -U yt-dlp discord.py[voice]`. Chỉ phát nội dung bạn có quyền sử dụng và tuân thủ điều khoản nền tảng.
"# discordbotyoutube" 
