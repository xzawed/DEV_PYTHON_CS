import sys
# SSH 클라이언트 라이브러리 임포트
import paramiko
# PyQt 라이브러리 임포트
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtCore import QTimer
from PyQt6.uic import loadUiType
from PyQt6.QtGui import QIcon
# 암호화 라이브러리 임포트
from cryptography.fernet import Fernet
# base64 라이브러리 임포트
import base64
# ini 파일 라이브러리 임포트
import configparser
# 로깅 라이브러리 임포트
import logging
# 관리자 권한 라이브러리 임포트
import ctypes
# 인코딩 라이브러리 임포트
import chardet

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

config = configparser.ConfigParser()
# UI 파일 로드
Ui_MainWindow, QMainWindowBase = loadUiType("frmMain_Test.ui")

# KeyValue = Fernet.generate_key()
KeyValue = b'0123456789ABCDEF0!@#$%^&*(abcdef'
KeyValue = KeyValue.ljust(32)[:32]  # 문자열 길이가 32가 되도록 조절 (오른쪽으로 공백 채우고 다시 32로 자름)
encoded_key = base64.urlsafe_b64encode(KeyValue)

class TextEditorApp(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()

        # 로깅 설정
        logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.run_task)
        icon_path = "OrangeKill.png"  # 아이콘 파일 경로를 지정하세요
        self.setWindowIcon(QIcon(icon_path))
        try:
            # Fernet 객체 생성
            self.cipher_suite = Fernet(encoded_key)
            # 프로그램 종료 시 ini 파일에 내용을 저장하기
            self.closeEvent = self.on_closing
            # 버튼 클릭시 실행
            self.initUI()
            # 버튼 클릭시 실행
            self.setup_connection()
            # 반복실행문 실행
            self.run_task()

        except Exception as e:
            logging.error(f"Error initializing app: {e}")
            self.show_error_message(f"Error initializing app:\n{e}")

    def setup_connection(self):
        # 버튼 클릭시 이벤트 연결
        self.BtnAction.clicked.connect(self.modify_remote_files)
        # 로컬영역에서 실행 이벤트 연결
        self.chkLocal.clicked.connect(self.on_change_ui)
        # 체크박스 상태에 따라 타이머 동작 설정
        self.chkRepeat.clicked.connect(self.toggle_timer)

    def initUI(self):
        # UI 초기화
        self.setupUi(self)
        # 프로그램 시작 시 ini 파일에서 내용을 읽어와 텍스트 에디터에 불러오기
        self.load_from_ini()
        # UI 변경시 실행
        self.on_change_ui()

    def toggle_timer(self):
        if self.chkRepeat.isChecked():
            # 체크박스가 체크되면 타이머 시작
            self.timer.start(5 * 60 * 1000)  # 5분(밀리초 단위)
            self.BtnAction.setEnabled(False)
        else:
            # 체크박스가 해제되면 타이머 중지
            self.timer.stop()
            self.BtnAction.setEnabled(True)

    def on_closing(self, event):
        # 프로그램이 종료될 때 호출되는 함수
        # 여기서 ini 파일에 내용을 저장할 수 있습니다.
        self.save_to_ini()
        super().closeEvent(event)

    def on_remote(self): # 원격영역 실행
        # SSH 클라이언트 생성
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # SSH 연결
            host = self.txtIPADDR.toPlainText()
            port = 22
            username = self.txtHOSTID.toPlainText()
            password = self.lttHOSTPW.text()

            client.connect(host, port, username, password)
        except Exception as e:
            client = None
            logging.error(f"Error connecting to remote server: {e}")

        return client

    def on_change_ui(self): # 로컬영역 실행
        if self.chkLocal.isChecked():
               self.txtIPADDR.setEnabled(False)
               self.txtHOSTID.setEnabled(False)
               self.lttHOSTPW.setEnabled(False)
        else:
               self.txtIPADDR.setEnabled(True)
               self.txtHOSTID.setEnabled(True)
               self.lttHOSTPW.setEnabled(True)
        self.toggle_timer()

    def detect_encoding(self, file_path):
        with open(file_path, 'rb') as file:
            result = chardet.detect(file.read())
            return result['encoding']

    def encrypt_data(self, text):
        return self.cipher_suite.encrypt(text.encode('utf-8')).decode('utf-8')

    def decrypt_data(self, encrypted_text):
        return self.cipher_suite.decrypt(encrypted_text.encode('utf-8')).decode('utf-8')

    def load_text_from_ini(self, key):
        if config.has_option(key, 'content'):
            encrypted_content = config[key]['content']
            content = self.decrypt_data(encrypted_content)
            if key == 'lttHOSTPW':
                getattr(self, key).setText(content)
            else:
                getattr(self, key).setPlainText(content)

    def save_to_ini(self):
        # ini 파일에 내용 저장
        config['txtIPADDR'] = {'content': self.encrypt_data(self.txtIPADDR.toPlainText())}
        config['txtHOSTID'] = {'content': self.encrypt_data(self.txtHOSTID.toPlainText())}
        config['lttHOSTPW'] = {'content': self.encrypt_data(self.lttHOSTPW.text())}
        config['txtPATH1ST'] = {'content': self.encrypt_data(self.txtPATH1ST.toPlainText())}
        config['txtPATH2ND'] = {'content': self.encrypt_data(self.txtPATH2ND.toPlainText())}

        config['RePeat'] = {'value': "Checked" if self.chkRepeat.isChecked() else "UnChecked"}
        config['Local'] = {'value': "Checked" if self.chkLocal.isChecked() else "UnChecked"}

        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    def load_from_ini(self):
        # 프로그램 시작 시 ini 파일에서 내용 읽어오기
        try:
            config.read('config.ini')

            self.load_text_from_ini('txtIPADDR')
            self.load_text_from_ini('txtHOSTID')
            self.load_text_from_ini('lttHOSTPW')
            self.load_text_from_ini('txtPATH1ST')
            self.load_text_from_ini('txtPATH2ND')

            # 반복호출처리
            repeat_value = config.get('RePeat', 'value', fallback=None)
            if repeat_value is not None:
                self.chkRepeat.setChecked(repeat_value.lower() == 'checked')

            # 로컬영역실행
            local_value = config.get('Local', 'value', fallback=None)
            if local_value is not None:
                self.chkLocal.setChecked(local_value.lower() == 'checked')

        except Exception as e:
            logging.error(f"Error loading content from INI: {e}")
            self.show_error_message(f"Error loading content from INI:\n{e}")

    def read_remote_files(self, remote_file_paths):
        try:
            if not self.chkLocal.isChecked():
                try:
                    client = self.on_remote()
                    if client is None:
                        return None

                    # return content
                    file_contents = {}
                    for remote_file_path in remote_file_paths:
                        encoding = self.detect_encoding(remote_file_path)
                        with client.open_sftp().file(remote_file_path, 'r', encoding=encoding) as remote_file:
                            content = remote_file.read()
                            file_contents[remote_file_path] = content
                finally:
                    if client is not None:
                        client.close()
            else:
                # return content
                file_contents = {}
                for remote_file_path in remote_file_paths:
                    with open(remote_file_path, 'r') as local_file:
                        content = local_file.read()
                        file_contents[remote_file_path] = content

            return file_contents

        except Exception as e:
            logging.error(f"Error reading file: {e}")
            self.show_error_message(f"Error reading file:\n{e}")
            return None

    def write_remote_files(self, file_contents):
        try:
            if not self.chkLocal.isChecked():
                try:
                    client = self.on_remote()
                    if client is None: return None

                    # 여러 원격 파일 쓰기
                    for remote_file_path, content in file_contents.items():
                        encoding = self.detect_encoding(remote_file_path)
                        with client.open_sftp().file(remote_file_path, 'w', encoding=encoding) as remote_file:
                            remote_file.write(content)
                    #logging.info(f"Remote file {remote_file_path} has been updated.")
                finally:
                    if client is not None: client.close()
            else:
                # 여러 로컬 파일 쓰기
                for remote_file_path, content in file_contents.items():
                    with open(remote_file_path, 'w') as local_file:
                        local_file.write(content)
                #logging.info(f"Local file {remote_file_path} has been updated.")

        except Exception as e:
            logging.error(f"Error writing to files: {e}")
            self.show_error_message(f"Error writing to files:\n{e}")

    def modify_remote_files(self):

        remote_file_path1st = self.txtPATH1ST.toPlainText()
        remote_file_path2nd = self.txtPATH2ND.toPlainText()

        # 원격 파일 읽기
        try:

            # 원격 파일 쓰기
            new_contents = {
                remote_file_path1st: "",
                remote_file_path2nd: ""
            }

            self.write_remote_files(new_contents)

        except Exception as e:
            logging.error(f"Error modifying files: {e}")
            self.show_error_message(f"Error modifying files:\n{e}")

    def run_task(self):
        try:
            self.modify_remote_files()
        except Exception as e:
            logging.error(f"Error running task: {e}")
            self.show_error_message(f"Error running task:\n{e}")

    # 새로운 메서드 추가: 에러 메시지 팝업 표시
    def show_error_message(self, message):
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setText("Error")
        error_dialog.setInformativeText(message)
        error_dialog.setWindowTitle("Error")
        error_dialog.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TextEditorApp()
    window.show()
    app.exec()
