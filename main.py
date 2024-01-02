import sys
import paramiko
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.uic import loadUiType
import configparser
from apscheduler.schedulers.qt import QtScheduler
import logging

config = configparser.ConfigParser()
# UI 파일 로드
Ui_MainWindow, QMainWindowBase = loadUiType("frmMain_Test.ui")

class TextEditorApp(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()

        # 로깅 설정
        logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        # UI 초기화
        self.setupUi(self)
        # 프로그램 시작 시 ini 파일에서 내용을 읽어와 텍스트 에디터에 불러오기
        self.load_from_ini()
        # 프로그램 종료 시 ini 파일에 내용을 저장하기
        self.closeEvent = self.on_closing
        # 버튼 클릭시 실행
        self.initUI()


    def initUI(self):
        # 버튼 클릭시 이벤트 연결
        self.BtnAction.clicked.connect(self.run_task)


    def on_closing(self, event):
        # 프로그램이 종료될 때 호출되는 함수
        # 여기서 ini 파일에 내용을 저장할 수 있습니다.
        self.save_to_ini()
        super().closeEvent(event)

    def save_to_ini(self):
        # ini 파일에 내용 저장
        config['txtIPADDR'] = {'content': self.txtIPADDR.toPlainText()}
        config['txtHOSTID'] = {'content': self.txtHOSTID.toPlainText()}
        config['lttHOSTPW'] = {'content': self.lttHOSTPW.text()}
        config['txtPATH1ST'] = {'content': self.txtPATH1ST.toPlainText()}
        config['txtPATH2ND'] = {'content': self.txtPATH2ND.toPlainText()}

        if self.rdbRepeat.isChecked():
            config['RePeat'] = {'value': "Checked"}
        else:
            config['RePeat'] = {'value': "UnChecked"}

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
                    self.rdbRepeat.setChecked(True)
                else:
                    self.rdbRepeat.setChecked(False)

        except Exception as e:
            logging.error(f"Error loading content from INI: {e}")
            self.show_error_message(f"Error loading content from INI:\n{e}")

    def on_save_and_exit(self):
        # 저장 후 종료 버튼 클릭 시 호출되는 함수
        self.save_to_ini()
        self.close()

    def read_remote_files(self, remote_file_paths):
        try:
            # SSH 클라이언트 생성
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # SSH 연결
            host = self.txtIPADDR.toPlainText()
            port = 22
            username = self.txtHOSTID.toPlainText()
            password = self.lttHOSTPW.text()

            client.connect(host, port, username, password)

            # return content
            file_contents = {}
            for remote_file_path in remote_file_paths:
                with client.open_sftp().file(remote_file_path, 'r') as remote_file:
                    content = remote_file.read()
                    file_contents[remote_file_path] = content

            return file_contents

        except Exception as e:
            logging.error(f"Error reading remote file: {e}")
            self.show_error_message(f"Error reading remote file:\n{e}")
            return None

    def write_remote_files(self, file_contents):
        try:
            # SSH 클라이언트 생성
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # SSH 연결
            host = self.txtIPADDR.toPlainText()
            port = 22
            username = self.txtHOSTID.toPlainText()
            password = self.lttHOSTPW.text()

            client.connect(host, port, username, password)

            # 여러 원격 파일 쓰기
            for remote_file_path, content in file_contents.items():
                with client.open_sftp().file(remote_file_path, 'w') as remote_file:
                    remote_file.write(content)

                logging.info(f"Remote file {remote_file_path} has been updated.")

        except Exception as e:
            logging.error(f"Error writing to remote files: {e}")
            self.show_error_message(f"Error writing to remote files:\n{e}")

        finally:
            client.close()

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
                    logging.info(f"Remote file content ({remote_file_path}):\n{content}")

            # 원격 파일 쓰기
            new_contents = {
                remote_file_path1st: "",
                remote_file_path2nd: ""
            }

            self.write_remote_files(new_contents)

        except Exception as e:
            logging.error(f"Error modifying remote files: {e}")
            self.show_error_message(f"Error modifying remote files:\n{e}")

    def run_task(self):
        if self.rdbRepeat.isChecked():
            # 여기에 5분마다 실행되어야 할 작업을 추가하세요.
            self.modify_remote_files()
        else:
            # 여기에 1번 실행되어야 할 작업을 추가하세요.
            self.modify_remote_files()

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
    scheduler = QtScheduler()
    scheduler.start()
    # 5분 간격으로 run_task 함수 실행
    scheduler.add_job(window.run_task, 'interval', minutes=5)
    app.exec()
