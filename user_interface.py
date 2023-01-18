from PySide6.QtWidgets import QMessageBox, QMenu, QSystemTrayIcon, QCheckBox, QMenuBar, QFrame, QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QComboBox, QDialog, QSizePolicy
from PySide6.QtCore import Qt, QThread, Signal, QObject, QUrl

from PySide6.QtGui import   QPixmap, QIcon, QDesktopServices, QAction
from qt_material import apply_stylesheet
import sys
import requests
import json
from pyvaloapi import ValorantClient
from time import sleep
import random
import os

#Themes
themes_list = ['dark_amber.xml',
 'dark_blue.xml',
 'dark_cyan.xml',
 'dark_lightgreen.xml',
 'dark_pink.xml',
 'dark_purple.xml',
 'dark_red.xml',
 'dark_teal.xml',
 'dark_yellow.xml',
 'light_amber.xml',
 'light_blue.xml',
 'light_cyan.xml',
 'light_cyan_500.xml',
 'light_lightgreen.xml',
 'light_pink.xml',
 'light_purple.xml',
 'light_red.xml',
 'light_teal.xml',
 'light_yellow.xml']
agents_dict = {} # Initialize an empty agents dict to populate afterwards

#TODO: Implement agents in PyValo
agents = requests.get("https://valorant-api.com/v1/agents")
agents = json.loads(agents.content)["data"]


for agent in agents:
	agents_dict[agent["displayName"]] = agent["uuid"]
instalock_signal = Signal()
try:
    client = ValorantClient()
    unofficial_api = client.unofficial_api()
    
except:
    print("Oops!", "Make sure you have valorant open with Companion")

queue_options = {"keep_loop": False}
party_force_open_options = {"keep_loop": False}
party_force_close_options = {"keep_loop": False}
party_force_decline_req_options ={"keep_loop": False}

def api_player_ready(state):
        unofficial_api.set_player_ready(state)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)        
class Worker(QObject):
    finished = Signal()
    def __init__(self, args, components):
        super().__init__()	
        self.args = args
        self.components = components

    def api_instalock(self):
        while("MatchID" not in unofficial_api.get_current_pregame(unofficial_api.get_current_player_puuid())): pass
        sleep(random.randint(1, 5)) # wait a random amount of time before locking agent to throw off vanguard
        response_code = unofficial_api.lock_pregame_agent(self.args[0])	
        if response_code == 200:
            self.components[0].setDisabled(False)
            self.finished.emit()
    

    def api_queue_settings(self):
        if self.args[0] == "Force-Leave":
            while(True):
                 unofficial_api.leave_queue()
                 sleep(random.randint(0, 2)/10)
                 if self.args[1]["keep_loop"] == False:
                    self.finished.emit()
                    break;

        elif self.args[0] == "Force-Join":
             while(True):
                  unofficial_api.join_queue()
                  sleep(random.randint(0, 2)/10)
                  if self.args[1]["keep_loop"] == False:
                    self.finished.emit()
                    break;
    
    def api_party_force_settings(self):
        if self.args[0] == "Force-Open":
            while(True):
                 unofficial_api.set_party_accessibility(accessibility=True)
                 sleep(random.randint(0, 6)/10)
                 if self.args[1]["keep_loop"] == False:
                    self.finished.emit()
                    break;

        elif self.args[0] == "Force-Close":
             while(True):
                  unofficial_api.set_party_accessibility(False)
                  sleep(random.randint(0, 6)/10)
                  if self.args[1]["keep_loop"] == False:
                    self.finished.emit()
                    break;
        else:
            while(True):
                current_requests = unofficial_api.get_current_party()["Requests"]
                if current_requests:
                    for request in current_requests:
                        unofficial_api.decline_party_request(unofficial_api.get_current_party_id(), request["RequestID"])
                sleep(random.randint(8, 10)/10) #Check every 10 seconds or so is fair enough
                if self.args[1]["keep_loop"] == False:
                    self.finished.emit()
                    break;

            
      
        

def gen_seperator():
        separatorLine = QFrame()
        separatorLine.setFrameShape(QFrame.HLine)
        separatorLine.setFrameShadow(QFrame.Raised)
        separatorLine.setStyleSheet("font: 9pt; background: #F44336")
        separatorLine.setLineWidth(0)
        separatorLine.setMidLineWidth(10) 
        return separatorLine

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        tray_icon = QIcon("icon.ico")
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(tray_icon)
        self.tray.setVisible(True)
        self.tray_context_menu = QMenu()
        self.open_action = QAction("Open")
        self.close_action = QAction("Close")
        self.tray_context_menu.addAction(self.open_action)
        self.tray_context_menu.addAction(self.close_action)
        self.open_action.triggered.connect(lambda: self.show())
        self.close_action.triggered.connect(lambda: exit(0))
        self.tray.setContextMenu(self.tray_context_menu)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.MaximizeUsingFullscreenGeometryHint)
        self.menuBar = QMenuBar()
        self.help_menu = self.menuBar.addMenu("Help")
        self.poweredby_action = self.help_menu.addAction("Powered By PyValo 1.1.3")
        self.github_action = self.help_menu.addAction("Visit Github")
        github_url = QUrl("https://github.com/YASSINE-AA")
        pyvalo_url = QUrl("https://github.com/YASSINE-AA/PyValo")
        self.poweredby_action.triggered.connect(lambda: QDesktopServices.openUrl(pyvalo_url))
        self.github_action.triggered.connect(lambda: QDesktopServices.openUrl(github_url))
        self.setWindowTitle("Valorant Companion")
        self.instalock_thread = QThread()
        self.queue_worker = None
        self.queue_thread = None
        self.instalock_worker = None
        pixmap = QPixmap(resource_path("res/icon.png"))
        icon = QIcon(pixmap)

        self.setWindowIcon(icon)
        self.setFixedSize(400, 400)
        self.vbox = QVBoxLayout()
        widget = QWidget()
		#===================== INSTALOCK SECTION ===========================
        self.instalock_title = QLabel("Instalock Agent:")
        self.instalock_button = QPushButton("Initiate")
        instalock_widget = QWidget()
        self.agents_comboBox = QComboBox()
        agent_comboBox_contents = []
        for agent in agents_dict.keys():
            agent_comboBox_contents.append(agent)
        self.agents_comboBox.addItems(agent_comboBox_contents)
        self.instalock_button.clicked.connect(lambda: self.instalock_agent(agents_dict[self.agents_comboBox.currentText()]))
        self.instalock_layout = QHBoxLayout()
        self.instalock_layout.addWidget(self.instalock_title)
        self.instalock_layout.addWidget(self.agents_comboBox)	
        self.instalock_layout.addWidget(self.instalock_button)
        instalock_widget.setLayout(self.instalock_layout)
       
       

        #======================== player_ready SECTION =======================
        self.player_ready_title = QLabel("Player Status:")
        self.player_ready_comboBox = QComboBox()
        self.player_ready_comboBox.addItems(["Ready", "Not Ready"])
        self.player_ready_comboBox.currentTextChanged.connect(self.player_ready)
        self.player_ready_layout = QHBoxLayout()
        self.player_ready_layout.addWidget(self.player_ready_title)
        self.player_ready_layout.addWidget(self.player_ready_comboBox)
        player_ready_widget = QWidget()
        player_ready_widget.setLayout(self.player_ready_layout)
       

        #======================= QUEUE SECTION ======================
        self.queue_title = QLabel("Queue Options: ")
        self.queue_comboBox = QComboBox()
        self.queue_comboBox.addItems(["Disabled", "Force-Leave", "Force-Join"])
        self.queue_comboBox.currentTextChanged.connect(self.queue_settings)
        self.queue_layout = QHBoxLayout()
        self.queue_layout.addWidget(self.queue_title)
        self.queue_layout.addWidget(self.queue_comboBox)
        queue_widget = QWidget()
        queue_widget.setLayout(self.queue_layout)
        
        #======================= PARTY SECTION =======================
        self.party_title = QLabel("Party Options: ")
        self.party_comboBox = QComboBox()
        self.party_options_vbox = QVBoxLayout()
        party_options_widget = QWidget()
        party_options_widget.setLayout(self.party_options_vbox)
        self.party_force_open_check = QCheckBox("Force Open")
        self.party_force_open_check.stateChanged.connect(self.party_force_open)
        self.party_force_close_check = QCheckBox("Force Close")
        self.party_force_close_check.stateChanged.connect(self.party_force_close)

        self.party_force_decline_req_check = QCheckBox("Force Decline Party Invite Requests")
        self.party_force_decline_req_check.stateChanged.connect(self.party_force_decline_req)

        self.party_options_vbox.addWidget(self.party_force_open_check)
        self.party_options_vbox.addWidget(self.party_force_close_check)
        self.party_options_vbox.addWidget(self.party_force_decline_req_check)
        self.party_layout = QHBoxLayout()
        self.party_layout.addWidget(self.party_title)
        self.party_layout.addWidget(party_options_widget)
        party_widget = QWidget()
        party_widget.setLayout(self.party_layout)

        #=============================================================
        widget.setLayout(self.vbox)
        self.setCentralWidget(widget)
        self.vbox.addWidget(self.menuBar)
        self.vbox.addWidget(instalock_widget)
        self.vbox.addWidget(gen_seperator())
        self.vbox.addWidget(player_ready_widget)
        self.vbox.addWidget(gen_seperator())
        self.vbox.addWidget(queue_widget)
        self.vbox.addWidget(gen_seperator())
        self.vbox.addWidget(party_widget)



    def instalock_agent(self, agentID):	
        self.instalock_worker = Worker(args=[agentID,], components=[self.instalock_button,])
        self.instalock_button.setDisabled(True)
        self.instalock_worker.moveToThread(self.instalock_thread)
        self.instalock_thread.started.connect(self.instalock_worker.api_instalock)
        self.instalock_worker.finished.connect(self.instalock_thread.quit)
        self.instalock_worker.finished.connect(self.instalock_worker.deleteLater)	
        self.instalock_thread.finished.connect(self.instalock_thread.deleteLater)
        self.instalock_thread.start()

    def player_ready(self, value):
        if value == "Ready":
            api_player_ready(True)
        else:
            api_player_ready(False)

    def queue_settings(self, value):
        #I'm implementing a request code listener method, I'm pretty sure there are better options but I can't think of one rn..
        if value != "Disabled":
            self.queue_thread = QThread()
            queue_options["keep_loop"] = True
            self.queue_worker = Worker(args=[value, queue_options], components=None)            
            self.queue_worker.moveToThread(self.queue_thread)
            self.queue_thread.started.connect(self.queue_worker.api_queue_settings)
            self.queue_worker.finished.connect(self.queue_thread.quit)
            self.queue_worker.finished.connect(self.queue_worker.deleteLater)	
            self.queue_thread.finished.connect(self.queue_thread.deleteLater)
            self.queue_thread.start()
        else:
             queue_options["keep_loop"] = False
            
    def party_force_open(self, value):
        if self.party_force_open_check.isChecked():
            self.party_force_open_thread = QThread()
            party_force_open_options["keep_loop"] = True
            self.party_force_open_worker = Worker(args=["Force-Open", party_force_open_options], components=None)            
            self.party_force_open_worker.moveToThread(self.party_force_open_thread)
            self.party_force_open_thread.started.connect(self.party_force_open_worker.api_party_force_settings)
            self.party_force_open_worker.finished.connect(self.party_force_open_thread.quit)
            self.party_force_open_worker.finished.connect(self.party_force_open_worker.deleteLater)	
            self.party_force_open_thread.finished.connect(self.party_force_open_thread.deleteLater)
            self.party_force_open_thread.start()
        else:
            party_force_open_options["keep_loop"] = False

    def party_force_close(self, value):
        if self.party_force_close_check.isChecked():
            self.party_force_close_thread = QThread()
            party_force_close_options["keep_loop"] = True
            self.party_force_close_worker = Worker(args=["Force-Close", party_force_close_options], components=None)            
            self.party_force_close_worker.moveToThread(self.party_force_close_thread)
            self.party_force_close_thread.started.connect(self.party_force_close_worker.api_party_force_settings)
            self.party_force_close_worker.finished.connect(self.party_force_close_thread.quit)
            self.party_force_close_worker.finished.connect(self.party_force_close_worker.deleteLater)	
            self.party_force_close_thread.finished.connect(self.party_force_close_thread.deleteLater)
            self.party_force_close_thread.start()
        else:
            party_force_close_options["keep_loop"] = False
    def party_force_decline_req(self, value):
        if self.party_force_decline_req_check.isChecked():
            party_force_decline_req_options["keep_loop"] = True
            self.party_force_decline_req_thread = QThread()
            self.party_force_decline_req_worker = Worker(args=["Force-Decline", party_force_decline_req_options], components=None)            
            self.party_force_decline_req_worker.moveToThread(self.party_force_decline_req_thread)
            self.party_force_decline_req_thread.started.connect(self.party_force_decline_req_worker.api_party_force_settings)
            self.party_force_decline_req_worker.finished.connect(self.party_force_decline_req_thread.quit)
            self.party_force_decline_req_worker.finished.connect(self.party_force_decline_req_worker.deleteLater)	
            self.party_force_decline_req_thread.finished.connect(self.party_force_decline_req_thread.deleteLater)
            self.party_force_decline_req_thread.start()
        else:
            party_force_decline_req_options["keep_loop"] = False



app = QApplication(sys.argv)
apply_stylesheet(app, theme="light_red.xml")
window = MainWindow()
window.show()
app.exec()
