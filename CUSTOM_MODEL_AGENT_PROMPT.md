# 給 Agent：訓練並整合自訂物件偵測模型

請協助我訓練一個「自訂物件偵測器」，並與 TouchDesigner 的 RelateAnything TOX 整合。我的目標是保留現有 YOLOE 的 4,585 類，同時增加我提供的特定物件。請先詢問或檢查我的資料集位置、圖片／影片、物件類別、目標硬體與可用標註；不要假設資料已存在或宣稱模型已達到指定準確率。

## 專案與既有功能

- 專案根目錄：此檔案所在資料夾；`RelateAnything.tox` 是 TouchDesigner 免安裝原型。
- 瀏覽器推論程式：`browser/index.html`、`browser/js/worker.js`、`browser/js/pipeline.js`；TD 程式在 `td/browser_logic.py` 和 `td/browser_server_callbacks.py`。
- 現在 TOX 已有實驗性的單一檔案自訂 YOLO26 ONNX 並行入口。請產出與其契約相符的模型與類別檔，並在實際 TOX 驗證；若模型不符合既有介面，請提供並測試必要適配，不要只交付檔案後聲稱可用。
- 若你無法讀取上述 TOX 或來源檔，請先請我提供它們；這段文字只是規格，並不包含模型權重或專案檔。
- 保留現有內建 YOLOE、YOLO、使用者的關係詞、三個輸出（Raw JSON DAT、Relationship CHOP、YOLO CHOP）、Base 預覽與 overlay；不破壞現有參數與連線。

## 訓練與模型交付

1. 整理資料集與類別，以實例框標註，依影像來源／影片切分訓練、驗證與測試；避免相近連續影格跨集合造成資料洩漏。提供標註檢查和資料統計。
2. 在我的硬體上選用合適的 YOLO 偵測架構並進行微調。先用預訓練權重作為起點；如訓練條件不足，明確報告，不虛構權重或成效。
3. 交付訓練設定、可重現步驟、權重、類別清單、ONNX，以及在獨立測試集上的指標、閾值和錯誤案例。原模型和新模型分開運行，以保留內建類別；若改為微調取代內建模型，須量測原有類別是否退化。
4. 說明訓練資料、權重、依賴、匯出與散佈適用的授權限制。

## 必須匹配的執行介面

TOX 使用 TD Web Render 的 Chromium、ONNX Runtime Web（WebGPU 優先／WASM 回退），模型需在此環境可用。請檢查實際版本、算子、ONNX 外部權重與記憶體需求，不要只以 Python ONNX Runtime 成功為結論。

目前 worker 使用 RGB、NCHW float32、0–1、640×640 letterbox 輸入（`images`）。自訂模型入口目前只接受下列 `e2e_xyxy` 格式；內建模型另有 `boxes_conf_cls` 解碼，但自訂入口尚不接受它：
- `e2e_xyxy`：名為 `output0` 的 `[1,N,6]`，每列為 `[x1,y1,x2,y2,confidence,class_id]`，座標為 letterbox 後影像像素；此路徑假設輸出已排好分數且不需額外 NMS。
- `boxes_conf_cls`：`boxes` 為 `[1,4,A]` 的 cx、cy、w、h，`conf` 和 `cls` 各為 `[1,A]`；後處理會做類別感知 NMS。

請以實際匯出的 ONNX 檢查上述名稱、維度、型別、座標系與 NMS，不要假設任何 YOLO 版本的預設輸出符合。若不符合，提供適配器或調整後處理，並測試 letterbox 反轉及邊界情況。類別檔為 JSON 字串陣列，索引對應 class_id；置信分數須是 0–1。

TD raw JSON 至少保留 `result_valid`、影像 `width`／`height`、`inference_ms`、`objects` 和 `relations`。每個 object 至少含穩定於該影格的 `index`、`label`、`confidence`、`box_pixels=[x1,y1,x2,y2]`、0–1 左上原點的 `center_x`、`center_y`、`width`、`height`；2D 偵測不能假造深度，`z` 為 null。關係使用 subject／object 索引、tag 和 score。請清楚說明 index 不跨影格追蹤。

## 合併與使用者介面

在外層 Base 的 Custom Model 頁使用已提供的自訂偵測器開關、模型／類別清單與狀態；預設保留內建偵測器。明確區分內建與自訂來源，處理類別命名衝突、重複物件及模型錯誤。自訂與內建結果合併後再交給關係模型，確保總框數限制及跨來源去重規則可設定或有清楚預設。輸出需維持現有有效狀態、逾時清除與可調偵測門檻。

目前外部模型載入不依賴系統 Python，但自訂檔案需保持在磁碟原路徑；若要求包成單一 TOX，須另行將授權允許的模型與資源嵌入 VFS 並測試。不要假設 Web Render 可以直接讀任意本機路徑；由本機 server 安全提供已選資源，限制非預期網路存取。

## 驗收

用有與沒有自訂物件、遮擋、負樣本及動態影片實測。確認內建類別仍可偵測、自訂類別可產生框與 YOLO CHOP、自訂物件能參與關係推論、raw data 正確且結果失效時清空。測 CPU／GPU、測端到端延遲與記憶體，分別在 Mac 和 Windows 的目標 TD 版本測試；沒測到的平台需明說。完成後給出模型與檔案清單、操作說明及測試結果。
