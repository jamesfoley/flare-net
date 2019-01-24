from cresset import flare
from lomond import WebSocket
from lomond.persist import persist

from PySide2 import QtCore, QtWidgets
from PySide2.QtWidgets import (QLineEdit, QPushButton, QApplication,
    QVBoxLayout, QDialog)

import threading
import time


@flare.extension
class FlareNet:

    def __init__(self):
        # Store for connection thread
        self.address = '127.0.0.1:8080'
        self.key = 'TestKey'
        self.thread = None
        self.thread_exit = False
        self.websocket = None

        self.checker_thread = None
        self.checker_thread_exit = False

        self.last_view = None

        self.websocket_id = None

        super().__init__()

    def load(self):
        # Add button to ribbon for settings
        flare.main_window().ribbon["FlareNet"]["Settings"].add_button('Settings', self.settings)

        self.checker_thread = threading.Thread(target=self.viewer_changed_checker)
        self.checker_thread.start()

    def set_address(self, address):
        self.address = address
        if self.thread:
            self.disconnect()
            self.connect()

    def set_key(self, key):
        self.key = key
        if self.thread:
            self.disconnect()
            self.connect()

    # Starts a thread which connects to the websocket
    def connect(self):
        self.thread = threading.Thread(target=self.start_websocket)
        self.thread.start()

    # Kill the thread and websocket
    def disconnect(self):
        self.thread_exit = True
        self.thread.join()

        self.checker_thread_exit = True
        self.checker_thread.join()

    def settings(self):
        # Get flare main window
        window = flare.main_window().widget()

        # Open settings dialog
        form = Form(flare=self, parent=window)
        form.show()

    def start_websocket(self):
        self.websocket = WebSocket(f'ws://{self.address}/')

        for event in persist(self.websocket):

            if event.name == 'ready':
                self.websocket.send_json(
                    command='join_group',
                    data=dict(
                        key=self.key
                    )
                )

            if event.name == 'text':
                if event.json['command'] == 'new_id':
                    self.websocket_id = event.json['id']

                if event.json['command'] == 'new_view':
                    print('New view')
                    print(event.json['source'])
                    print(self.websocket_id)
                    if event.json['source'] != self.websocket_id:
                        flare.invoke_later(target=self.set_camera, args=(event.json['view'],))

            if self.thread_exit:
                self.thread_exit = False
                break

    def save_settings(self, settings):
        self.disconnect()

    def viewer_changed_checker(self):
        while True:

            flare.invoke_later(target=self.check_camera)

            time.sleep(0.05)

            if self.checker_thread_exit:
                break

    def check_camera(self):
        view = flare.main_window().camera.save_view()

        if self.last_view != view:
            self.last_view = view

            if self.websocket:
                self.websocket.send_json(
                    command='view_change',
                    data=dict(
                        key=self.key,
                        view=view
                    )
                )

            print('View changed')

    def set_camera(self, matrix):
        self.last_view = matrix
        flare.main_window().camera.restore_view(view=matrix)


class Form(QDialog):

    def __init__(self, flare=None, parent=None):
        super(Form, self).__init__(parent)

        self.flare = flare

        # Set window title
        self.setWindowTitle("FlareNet Settings")

        # Create widgets
        self.address = QLineEdit(self.flare.address)
        self.save_address = QPushButton("Save Address")
        self.key = QLineEdit(self.flare.key)
        self.save_key = QPushButton("Save Key")
        self.connect = QPushButton("Connect")
        self.disconnect = QPushButton("Disconnect")

        # Create layout and add widgets
        layout = QVBoxLayout()
        layout.addWidget(self.address)
        layout.addWidget(self.save_address)
        layout.addWidget(self.key)
        layout.addWidget(self.save_key)
        layout.addWidget(self.connect)
        layout.addWidget(self.disconnect)

        # Set dialog layout
        self.setLayout(layout)

        # Add button signal to greetings slot
        self.save_address.clicked.connect(self.save_address_func)
        self.save_key.clicked.connect(self.save_key_func)
        self.connect.clicked.connect(self.connect_func)
        self.disconnect.clicked.connect(self.disconnect_func)

    def save_address_func(self):
        self.flare.set_address(self.address.text())

    def save_key_func(self):
        self.flare.set_key(self.key.text())

    def connect_func(self):
        self.flare.connect()

    def disconnect_func(self):
        self.flare.disconnect()
