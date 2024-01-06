import sys
import paramiko
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtCore import QTimer
from PyQt6.uic import loadUiType
import configparser
import logging
import ctypes
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

class TextEditorApp(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()

        # 로깅 설정
        logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.run_task)

        # UI 초기화
        self.setupUi(self)
        # 프로그램 시작 시 ini 파일에서 내용을 읽어와 텍스트 에디터에 불러오기
        self.load_from_ini()
        # 프로그램 종료 시 ini 파일에 내용을 저장하기
        self.closeEvent = self.on_closing
        # 버튼 클릭시 실행
        self.initUI()
        # UI 변경시 실행
        self.on_change_ui()
        # 반복실행문 실행
        self.run_task()

    def initUI(self):
        # 버튼 클릭시 이벤트 연결
        self.BtnAction.clicked.connect(self.modify_remote_files)
        # 로컬영역에서 실행 이벤트 연결
        self.chkLocal.clicked.connect(self.on_change_ui)
        # 체크박스 상태에 따라 타이머 동작 설정
        self.chkRepeat.clicked.connect(self.toggle_timer)

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
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # SSH 연결
        host = self.txtIPADDR.toPlainText()
        port = 22
        username = self.txtHOSTID.toPlainText()
        password = self.lttHOSTPW.text()

        client.connect(host, port, username, password)
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

    def detect_encoding(file_path):
        with open(file_path, 'rb') as file:
            result = chardet.detect(file.read())
            return result['encoding']

    def save_to_ini(self):
        # ini 파일에 내용 저장
        config['txtIPADDR'] = {'content': self.txtIPADDR.toPlainText()}
        config['txtHOSTID'] = {'content': self.txtHOSTID.toPlainText()}
        config['lttHOSTPW'] = {'content': self.lttHOSTPW.text()}
        config['txtPATH1ST'] = {'content': self.txtPATH1ST.toPlainText()}
        config['txtPATH2ND'] = {'content': self.txtPATH2ND.toPlainText()}

        if self.chkRepeat.isChecked():
            config['RePeat'] = {'value': "Checked"}
        else:
            config['RePeat'] = {'value': "UnChecked"}

        if self.chkLocal.isChecked():
            config['Local'] = {'value': "Checked"}
        else:
            config['Local'] = {'value': "UnChecked"}

        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    def load_from_ini(self):
        # 프로그램 시작 시 ini 파일에서 내용 읽어오기
        try:
            config.read('config.ini')
            # 호스트 IP 주소
            if config.has_option('txtIPADDR', 'content'):
                content = config['txtIPADDR']['content']
                self.txtIPADDR.setPlainText(content)
            # 호스트 아이디
            if config.has_option('txtHOSTID', 'content'):
                content = config['txtHOSTID']['content']
                self.txtHOSTID.setPlainText(content)
            # 호스트 비밀번호
            if config.has_option('lttHOSTPW', 'content'):
                content = config['lttHOSTPW']['content']
                self.lttHOSTPW.setText(content)
            # 파일경로 1번째
            if config.has_option('txtPATH1ST', 'content'):
                content = config['txtPATH1ST']['content']
                self.txtPATH1ST.setPlainText(content)
            # 파일경로 2번째
            if config.has_option('txtPATH2ND', 'content'):
                content = config['txtPATH2ND']['content']
                self.txtPATH2ND.setPlainText(content)

            # 반복호출처리
            if config.has_option('RePeat', 'value'):
                content = config['RePeat']['value']
                if content == "Checked":
                    self.chkRepeat.setChecked(True)
                else:
                    self.chkRepeat.setChecked(False)

            # 로컬영역실행
            if config.has_option('Local', 'value'):
                content = config['Local']['value']
                if content == "Checked":
                    self.chkLocal.setChecked(True)
                else:
                    self.chkLocal.setChecked(False)

        except Exception as e:
            logging.error(f"Error loading content from INI: {e}")
            self.show_error_message(f"Error loading content from INI:\n{e}")

    def read_remote_files(self, remote_file_paths):
        try:
            if not self.chkLocal.isChecked():
                try:
                    client = self.on_remote()
                    # return content
                    file_contents = {}
                    for remote_file_path in remote_file_paths:
                        encoding = self.detect_encoding(remote_file_path)
                        with client.open_sftp().file(remote_file_path, 'r', encoding=encoding) as remote_file:
                            content = remote_file.read()
                            file_contents[remote_file_path] = content
                finally:
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

                    # 여러 원격 파일 쓰기
                    for remote_file_path, content in file_contents.items():
                        encoding = self.detect_encoding(remote_file_path)
                        with client.open_sftp().file(remote_file_path, 'w', encoding=encoding) as remote_file:
                            remote_file.write(content)
                    logging.info(f"Remote file {remote_file_path} has been updated.")
                finally:
                    client.close()
            else:
                # 여러 로컬 파일 쓰기
                for remote_file_path, content in file_contents.items():
                    with open(remote_file_path, 'w') as local_file:
                        local_file.write(content)
                logging.info(f"Local file {remote_file_path} has been updated.")

        except Exception as e:
            logging.error(f"Error writing to files: {e}")
            self.show_error_message(f"Error writing to files:\n{e}")

    def modify_remote_files(self):

        remote_file_path1st = self.txtPATH1ST.toPlainText()
        remote_file_path2nd = self.txtPATH2ND.toPlainText()

        # 원격 파일 읽기
        remote_file_paths = [remote_file_path1st, remote_file_path2nd]

        # 원격 파일 읽기
        try:
            contents = self.read_remote_files(remote_file_paths)
            if contents is not None:
                for remote_file_path, content in contents.items():
                    logging.info(f"File content ({remote_file_path}):\n{content}")

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
