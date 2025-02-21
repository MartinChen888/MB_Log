import sys
import os
import re
import traceback
import csv
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QFileDialog, QMessageBox
from PyQt5.QtGui import QFont
from datetime import datetime

class TextFileSearcher(QWidget):
    def __init__(self):
        super().__init__()
        self.timestamps = {}  # 用來儲存關鍵字比對的時間戳
        self.filtered_lines = []  # 存儲處理後的日誌數據
        self.filtered_lines2 = []  # 存儲處理後的日誌數據
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        self.textView = QTextEdit(self)
        self.textView.setReadOnly(True)
        self.textView.setFont(QFont("Arial", 15))
        layout.addWidget(self.textView)

        # 按鈕區域 (Export & Clear) 並靠左對齊
        button_layout = QHBoxLayout()
        
        # "Export" 按鈕
        self.exportButton = QPushButton("Export", self)
        self.exportButton.setFixedSize(100, 40)
        self.exportButton.clicked.connect(self.exportToCSV)
        button_layout.addWidget(self.exportButton)
        
        # "Clear" 按鈕
        self.clearButton = QPushButton("Clear", self)
        self.clearButton.setFixedSize(100, 40)
        self.clearButton.clicked.connect(self.clearTextView)
        button_layout.addWidget(self.clearButton)
        
        # 讓按鈕靠左對齊
        button_layout.addStretch()  # ✅ 在按鈕後面增加彈性空間，使它們靠左
        
        layout.addLayout(button_layout)
        
        self.button = QPushButton("選擇檔案", self)
        self.button.clicked.connect(self.openFileDialog)
        layout.addWidget(self.button)
        
        self.setLayout(layout)
        self.setWindowTitle("Log 動作分析器 V1.2")
        self.resize(900, 750)

    def openFileDialog(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getOpenFileName(self, "選擇TXT文件", "", "Text Files (*.txt);;All Files (*)", options=options)
        
        if filePath:
            if not filePath.lower().endswith(".txt"):
                QMessageBox.warning(self, "錯誤", "請選擇 .txt 文件！")
                return
            
            self.searchTextInFile(filePath)
            
    # **計算時間差**
    def calculate_duration(self, start, end):
        """計算兩個關鍵時間點的時間差"""
        if start in self.timestamps and end in self.timestamps:
            try:
                start_dt = datetime.strptime(self.timestamps[start], "%m-%d %H:%M:%S.%f")
                end_dt = datetime.strptime(self.timestamps[end], "%m-%d %H:%M:%S.%f")
                duration = end_dt - start_dt
                return f"{duration.seconds // 60} 分 {duration.seconds % 60} 秒"
            except ValueError:
                return "無法計算"
        return "無法計算"          

    def searchTextInFile(self, filePath):
        try:
            self.timestamps = {}  # 清空時間戳記
            self.filtered_lines = []  # 清空已處理的日誌數據
            self.filtered_lines2 = []  # 清空已處理的日誌數據

            with open(filePath, "r", encoding="utf-8") as file:
                lines = file.readlines()
                previous_time = None
                
                keywords = [
                    ("時間起點", "42 32 C8", "full"),
                    ("QR終點", "55 04 00", "full"),
                    ("Urine終點", "55 01 01", "full"),
                    ("Sample終點", "48 00", "full"),
                    ("Tip終點", "21 04 00 00 00", "full"),
                    ("停轉終點", "49", "first"),
                    ("夾放終點", "4A", "first"),
                    ("吸打終點", "40 FF", "full"),
                    ("Pre-起轉終點", "32 F1 14 03 03", "full"),
                    ("起轉終點", "25", "first"),
                    ("Profile終點", "32 F1 00 03 03", "full"),
                    ("賦歸終點", "21 04 00 00 00", "full")
                ]
                
                keywords2 = [
                    ("時間起點", "ProfileAnalyzingTool Pre-start", "full"),
                    ("QR終點", "ProfileAnalyzingTool QR finish", "full"),
                    ("Urine終點", "ProfileAnalyzingTool Urine finish", "full"),
                    ("Sample終點", "ProfileAnalyzingTool Sample finish", "full"),
                    ("Tip終點", "ProfileAnalyzingTool Tip finish", "full"),
                    ("停轉終點", "ProfileAnalyzingTool stop motor finish", "full"),
                    ("夾放終點", "ProfileAnalyzingTool grip disc finish", "full"),
                    ("吸打終點", "ProfileAnalyzingTool tip finish", "full"),
                    ("Pre-起轉終點", "ProfileAnalyzingTool pre 1000 rpm finish", "full"),
                    ("起轉終點", "ProfileAnalyzingTool pre carrier profile start", "full"),
                    ("Profile終點", "ProfileAnalyzingTool Profile finish", "full"),
                    ("賦歸終點", "ProfileAnalyzingTool disc recovery finish", "full")
                ]
                
                # **第一步：處理並儲存符合條件的日誌行**
                for line in lines:
                    if "Qbi cmd TX:" in line:
                        match = re.search(r'^(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) D/loaderprotocol.*?Qbi cmd TX:(.*?)  2025', line)

                        if match:
                            timestamp_str = match.group(1).strip()
                            extracted_text = match.group(2).strip()
                            if not extracted_text.startswith(("3F", "1E", "2F", "4F","1D","10")):
                                if previous_time:
                                    try:
                                        current_time = datetime.strptime(timestamp_str, "%m-%d %H:%M:%S.%f")
                                        time_diff = str(int((current_time - previous_time).total_seconds() * 1000)) + " ms"
                                    except ValueError:
                                        time_diff = "解析錯誤"
                                else:
                                    time_diff = "0 ms"
                                
                                previous_time = datetime.strptime(timestamp_str, "%m-%d %H:%M:%S.%f")
                                self.filtered_lines.append((timestamp_str, time_diff, extracted_text))  # ✅ 存成 tuple
                                
                    elif "ProfileAnalyzingTool" in line:
                        match = re.search(r'^(\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+.*\s+ProfileAnalyzingTool\s+(.*)', line)
                        if match:
                            timestamp_str2 = match.group(1).strip()
                            extracted_text2 = match.group(2).strip()
                            
                            if previous_time:
                                try:
                                    current_time = datetime.strptime(timestamp_str, "%m-%d %H:%M:%S.%f")
                                    time_diff2 = str(int((current_time - previous_time).total_seconds() * 1000)) + " ms"
                                except ValueError:
                                    time_diff2 = "解析錯誤"
                            else:
                                time_diff2 = "0 ms"
                                
                            previous_time = datetime.strptime(timestamp_str, "%m-%d %H:%M:%S.%f")
                            self.filtered_lines2.append((timestamp_str2, time_diff2, extracted_text2))  # ✅ 存成 tuple
                              
                # **第二步：依序比對 `keywords`**
                keyword_index = 0
                total_keywords = len(keywords)

                for timestamp_str, time_diff, extracted_text in self.filtered_lines:
                    if keyword_index >= total_keywords:
                        break

                    key, value, match_type = keywords[keyword_index]

                    if match_type == "full" and extracted_text == value:
                        #self.timestamps[key] = timestamp_str
                        keyword_index += 1  
                    
                    elif match_type == "first" and extracted_text.startswith(value):
                        #self.timestamps[key] = timestamp_str
                        keyword_index += 1
                        
                # **比對 `keywords2`，存入 self.timestamps**
                keyword2_index = 0
                total_keywords2 = len(keywords2)

                # **比對 `keywords2`，存入 self.timestamps**
                for timestamp_str2, time_diff2, extracted_text2 in self.filtered_lines2:
                    if keyword2_index >= total_keywords2:
                        break  # ✅ 所有 keywords2 都匹配後就停止

                    key, value, match_type = keywords2[keyword2_index]
                    extracted_text2_clean = extracted_text2.strip()  # 移除前後空格
                    value_clean = value.replace("ProfileAnalyzingTool ", "").strip()  # 移除開頭的 "ProfileAnalyzingTool "

                    print(f"比對: '{extracted_text2_clean}' vs '{value_clean}'")  # 🛠️ Debug: 看比對過程

                    if match_type == "full" and extracted_text2_clean == value_clean:
                        self.timestamps[key] = timestamp_str2  # ✅ 成功匹配後存入
                        print(f"✅ 匹配成功: {key} -> {timestamp_str2}")
                        keyword2_index += 1  # ✅ 只移動到下一個關鍵字
                        continue  # ✅ 繼續比對下一條日誌

                    elif match_type == "first" and extracted_text2_clean.startswith(value_clean):
                        self.timestamps[key] = timestamp_str2  # ✅ 成功匹配後存入
                        print(f"✅ 匹配成功: {key} -> {timestamp_str2}")
                        keyword2_index += 1  # ✅ 只移動到下一個關鍵字
                        continue  # ✅ 繼續比對下一條日誌

                # **檢查 self.timestamps 是否存入值**
                print("存入的 timestamps:", self.timestamps)  # ✅ 確保 timestamps 不是空的

                # **輸出結果**
                analysis_result = "\n分析結果:\n"
                for key, _, _ in keywords2:  # ✅ 確保正確讀取 keywords2
                    analysis_result += f"{key}： {self.timestamps.get(key, '未找到')}\n"
                
                analysis_result += f"測試時間 : {self.calculate_duration('時間起點', 'Profile終點')}\n"
                analysis_result += f"QR Read : {self.calculate_duration('時間起點', 'QR終點')}\n"
                analysis_result += f"Urine   : {self.calculate_duration('QR終點', 'Urine終點')}\n"
                analysis_result += f"Sample  : {self.calculate_duration('Urine終點', 'Sample終點')}\n"
                analysis_result += f"Tip     : {self.calculate_duration('Sample終點', 'Tip終點')}\n"
                analysis_result += f"停轉    : {self.calculate_duration('Tip終點', '停轉終點')}\n"
                analysis_result += f"夾放    : {self.calculate_duration('停轉終點', '夾放終點')}\n"
                analysis_result += f"吸打    : {self.calculate_duration('夾放終點', '吸打終點')}\n"
                analysis_result += f"Profile : {self.calculate_duration('起轉終點', 'Profile終點')}\n"
                analysis_result += f"賦歸    : {self.calculate_duration('Profile終點', '賦歸終點')}\n"


                # 修正輸出文本
                self.textView.setPlainText("\n".join(["\t".join(map(str, item)) for item in self.filtered_lines])  + "\n\n\n" +
                                           "\n".join(["\t".join(map(str, item)) for item in self.filtered_lines2]) + "\n" + analysis_result)
                self.textView.moveCursor(self.textView.textCursor().End)

        except Exception as e:
            QMessageBox.critical(self, "讀取錯誤", f"無法讀取文件: {str(e)}")

    def exportToCSV(self):
        try:
            # 取得當前執行檔案所在資料夾
            save_path = os.path.dirname(sys.argv[0])
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            filePath = os.path.join(save_path, f"data_{current_time}.csv")

            # 寫入 CSV，確保 utf-8-sig 避免 Excel 亂碼
            with open(filePath, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(["時間戳", "時間差", "指令碼"])
                writer.writerows(self.filtered_lines)
                writer.writerows(self.filtered_lines2)

                writer.writerow([])
                writer.writerow(["項目", "時間"])
                for key, value in self.timestamps.items():
                    writer.writerow([key, value])
                    
                writer.writerow([])  # 加空行做區隔
                
                # **3️⃣ 寫入 "時間計算結果"**
                writer.writerow(["計算結果", "時間長度"])
                writer.writerow(["測試時間", self.calculate_duration("時間起點", "Profile終點")])
                writer.writerow(["QR Read", self.calculate_duration("時間起點", "QR終點")])
                writer.writerow(["Urine", self.calculate_duration("QR終點", "Urine終點")])
                writer.writerow(["Sample", self.calculate_duration("Urine終點", "Sample終點")])
                writer.writerow(["Tip", self.calculate_duration("Sample終點", "Tip終點")])
                writer.writerow(["停轉", self.calculate_duration("Tip終點", "停轉終點")])
                writer.writerow(["夾放", self.calculate_duration("停轉終點", "夾放終點")])
                writer.writerow(["吸打", self.calculate_duration("夾放終點", "吸打終點")])
                writer.writerow(["Profile", self.calculate_duration("起轉終點", "Profile終點")])
                writer.writerow(["賦歸", self.calculate_duration("Profile終點", "賦歸終點")])                    

            QMessageBox.information(self, "成功", f"CSV 檔案儲存成功！\n存放位置: {filePath}")

        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"無法儲存CSV:\n{str(e)}")
            
    def clearTextView(self):
        """清空上方視窗內容"""
        self.textView.clear()
        self.timestamps = {}  # 清除時間戳記
        self.filtered_lines = []  # 清除過濾的日誌數據
        self.filtered_lines2 = []  # 清除過濾的日誌數據

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = TextFileSearcher()
    ex.show()
    sys.exit(app.exec_())
