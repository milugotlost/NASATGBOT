# 🌌 NASA 天文圖 Telegram 機器人

這個 Telegram 機器人旨在讓使用者輕鬆探索 NASA 豐富的天文數據，包括每日天文圖、隨機照片、近地小行星資訊、火星探測器照片、地球每日影像以及國際太空站的即時位置。

---

## ✨ 功能特色

* 🌌 每日天文圖 (APOD)：每日更新 NASA 精選的宇宙影像，附帶詳細的中文說明。

* 🎲 隨機天文圖：隨機瀏覽過去的 APOD 影像。

* ☄️ 近地小行星資訊：查詢今日可能接近地球的小行星數據，包括其潛在危險性、距離與預估大小。

* 📸 火星探測器照片：即時獲取火星探測器（目前為「毅力號」）傳回的最新火星地表照片。

* 🌍 地球每日影像 (EPIC)：查看 NASA EPIC 衛星拍攝的地球全彩影像。

* 🛰️ 國際太空站 (ISS) 即時位置：顯示 ISS 當前在地球上空的經緯度與更新時間，並提供地圖連結。

* 💡 隨機天文小知識：提供一系列有趣的天文冷知識，增廣見聞。

* 🌙 月相資訊：查詢今日的月亮相位。

* 💥 太陽耀斑報告：從 NASA DONKI 系統獲取最新的太陽耀斑活動報告，包括等級與峰值時間。

* 🌋 地磁風暴報告：提供當前的地磁活動 Kp 指數，並解釋其對應的磁暴等級。

---

## 🚀 如何使用機器人

1.  在 Telegram 中搜尋並找到您的機器人（如果您已部署）。
2.  發送 `/start` 命令。
3.  機器人將會顯示一個帶有所有功能的選單。
4.  點擊選單中的按鈕即可探索不同的天文資訊！

---

## ⚙️ 部屬指南 (使用 Render 和 GitHub Fork)

本機器人專為 Render.com 的免費 Web 服務優化，您可以使用 GitHub Fork 的方式輕鬆部屬。

### 必備條件

在開始部屬之前，請確保您擁有：

1.  **GitHub 帳戶**：用於 Fork 本專案儲存庫。
2.  **Render 帳戶**：[註冊 Render.com](https://render.com/) (支援 GitHub 登入)。
3.  **Telegram Bot Token**：從 BotFather 獲取您的機器人 token。
4.  **NASA API Key**：從 NASA 官方網站獲取您的 API 金鑰。

### 步驟 1：Fork 本專案儲存庫

1.  前往本專案的 GitHub 頁面。
2.  點擊頁面右上角的 `Fork` 按鈕，將此儲存庫複製到您的 GitHub 帳戶下。

### 步驟 2：獲取 API 金鑰

#### 1. Telegram Bot Token

1.  在 Telegram 中，搜尋 `@BotFather`。
2.  發送 `/newbot` 命令。
3.  按照提示為您的機器人命名，並設置一個獨特的用戶名（例如 `MyNASAAPODBot`）。
4.  BotFather 將會給您一個 `HTTP API Token`。請妥善保管這個 token，這是您機器人的身份證明。它看起來像 `1234567890:ABCDEFGHIJ-KLMNOPQRSTUVWYZABCD`。

#### 2. NASA API Key

1.  前往 [NASA API 官網](https://api.nasa.gov/)。
2.  點擊 "Generate API Key" 或 "Sign Up for API Key"。
3.  填寫您的姓名和電子郵件地址。
4.  NASA 會將一個 API 金鑰發送到您的註冊郵箱。它看起來像 `XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`。

### 步驟 3：創建 Render Web Service

1.  登入您的 [Render.com 控制台](https://dashboard.render.com/)。
2.  點擊 `New +` -> `Web Service`。
3.  選擇 `Connect a Git repository`。
4.  選擇您剛才 Fork 到的本專案儲存庫（您的 GitHub 用戶名下）。
5.  在設定頁面中：
    * **`Name` (名稱)**：為您的服務命名 (例如 `nasa-apod-bot`)。
    * **`Region` (區域)**：選擇一個離您或您的用戶最近的地區。
    * **`Branch` (分支)**：通常是 `main`。
    * **`Root Directory` (根目錄)**：保持空白（如果您的 `main.py` 在儲存庫根目錄）。
    * **`Runtime` (執行環境)**：選擇 `Python 3`。
    * **`Build Command` (建置命令)**：`pip install -r requirements.txt`
    * **`Start Command` (啟動命令)**：`python main.py` (請確保您的主程式檔案名為 `main.py`)
    * **`Health Check Path` (健康檢查路徑)**：` / ` (單一斜線，用於 Render 檢查服務是否活著)。
    * **`Plan Type` (方案類型)**：選擇 `Free` (免費)。

### 步驟 4：設定環境變數

在 Render 的服務設定頁面，找到 `Environment Variables` (環境變數) 部分。點擊 `Add Environment Variable` 並新增以下變數：

* **`BOT_TOKEN`**：
    * `Key`: `BOT_TOKEN`
    * `Value`: 貼上您從 BotFather 獲取的 Telegram Bot Token。
* **`NASA_API_KEY`**：
    * `Key`: `NASA_API_KEY`
    * `Value`: 貼上您從 NASA 郵件中獲取的 API 金鑰。
* **`WEBHOOK_URL`**：
    * `Key`: `WEBHOOK_URL`
    * `Value`: **這個值需要等到您的 Render 服務首次部署成功後才能獲取。**
        * 首次部署時，可以先留空或隨便填一個佔位符。
        * 部署成功後，Render 會為您的服務提供一個公開 URL，例如 `https://your-service-name.onrender.com`。
        * 您需要將這個完整的 URL （**不帶尾部斜線**）複製並貼回 `WEBHOOK_URL` 這個環境變數中，然後手動觸發一次重新部署 (點擊 `Manual Deploy` -> `Deploy latest commit`)。

### 步驟 5：部屬

1.  點擊 `Create Web Service`。
2.  Render 將會開始自動部屬您的機器人。這可能需要幾分鐘的時間。
3.  在部署日誌中，您應該會看到類似 `Your service is live 🎉` 的訊息，以及您的服務公開 URL。
4.  **重要**：務必返回到服務設定頁面，將上一步驟中獲取的 `WEBHOOK_URL` 正確填寫，並再次觸發部署以使 Webhook 生效。

完成這些步驟後，您的 NASA 天文圖機器人應該就能在 Telegram 上正常運作了！

---

## 🤝 貢獻與支持

歡迎對本專案提出建議或貢獻！如果您有任何想法、錯誤報告或功能請求，請隨時在 GitHub 上開立 Issue 或提交 Pull Request。

BTC : bc1pk75yxct4katjntwukry2wxd6ew89kahcfev73d7vdzc40qv9k5fqe2r635

---

## 📄 開發

本專案全程使用Gemini 2.5 Pro全程開發，如果有問題不要問我w
https://linkbio.co/5060807CJw6HL?utm_source=instabio&utm_medium=profile_share
