from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QTextEdit, QFileDialog,
                             QPushButton, QCheckBox, QComboBox, QListWidget, QTabWidget,
                             QHBoxLayout, QAbstractItemView, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QTimer
from db import save_complete_tpd, select_from_db_stats, select_from_db_view_data, delete_record_from_db

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TID")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        self.create_add_tab()
        self.create_view_tab()
        self.create_stats_tab()

        # Initialize tweet_times
        self.tweet_times = []

        # Status label for success/error messages
        self.status_label = QLabel("")
        self.layout.addWidget(self.status_label)

        # Timer for hiding status message
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.clear_status)
        
        # Timer for refreshing stats
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_stats)
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(600000)  # Refresh every 10 min

    def create_add_tab(self):
        self.add_tab = QWidget()
        self.tab_widget.addTab(self.add_tab, "Add Data")

        self.add_tab_layout = QVBoxLayout(self.add_tab)
        self.form_layout = QFormLayout()
        self.add_tab_layout.addLayout(self.form_layout)

        self.name_input = QLineEdit()
        self.form_layout.addRow("Name:", self.name_input)

        self.text_input = QTextEdit()
        self.form_layout.addRow("Text:", self.text_input)

        self.media_input = QPushButton("Select Media")
        self.media_input.clicked.connect(self.select_files)
        self.form_layout.addRow("Media:", self.media_input)

        self.media_list_widget = QListWidget()
        self.form_layout.addRow("Selected Files:", self.media_list_widget)

        self.is_link_check = QCheckBox("Is Link")
        self.form_layout.addRow("Is Link:", self.is_link_check)

        self.week_days_layout = QHBoxLayout()
        self.form_layout.addRow("Week Days:", self.week_days_layout)

        self.week_days = [
            ("Monday", "Monday"),
            ("Tuesday", "Tuesday"),
            ("Wednesday", "Wednesday"),
            ("Thursday", "Thursday"),
            ("Friday", "Friday"),
            ("Saturday", "Saturday"),
            ("Sunday", "Sunday")
        ]

        self.week_day_checkboxes = {}
        for label, value in self.week_days:
            checkbox = QCheckBox(label)
            self.week_days_layout.addWidget(checkbox)
            self.week_day_checkboxes[value] = checkbox

        self.tweet_times_label = QLabel("Tweet Times:")
        self.form_layout.addRow(self.tweet_times_label)

        self.time_input_layout = QHBoxLayout()
        self.form_layout.addRow(self.time_input_layout)

        self.hour_combo = QComboBox()
        self.hour_combo.addItems([f"{h:02}" for h in range(24)])
        self.time_input_layout.addWidget(self.hour_combo)

        self.minute_combo = QComboBox()
        self.minute_combo.addItems([f"{m:02}" for m in range(0, 60, 5)])
        self.time_input_layout.addWidget(self.minute_combo)

        self.add_time_button = QPushButton("Add Time")
        self.add_time_button.clicked.connect(self.add_time)
        self.time_input_layout.addWidget(self.add_time_button)

        self.time_list_layout = QHBoxLayout()
        self.form_layout.addRow(self.time_list_layout)

        self.tweet_times_list_widget = QListWidget()
        self.tweet_times_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.time_list_layout.addWidget(self.tweet_times_list_widget)

        self.remove_time_button = QPushButton("Remove Selected Time")
        self.remove_time_button.clicked.connect(self.remove_time)
        self.time_list_layout.addWidget(self.remove_time_button)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit)
        self.add_tab_layout.addWidget(self.submit_button)

    def create_view_tab(self):
        self.view_tab = QWidget()
        self.tab_widget.addTab(self.view_tab, "View Data")

        self.view_tab_layout = QVBoxLayout(self.view_tab)
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(7)
        self.data_table.setHorizontalHeaderLabels(["ID", "Name", "Text", "Media", "Is Link", "Week Days", "Tweet Times"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Set column widths
        self.data_table.setColumnWidth(0, 50)
        self.data_table.setColumnWidth(1, 150)
        self.data_table.setColumnWidth(2, 200)
        self.data_table.setColumnWidth(3, 150)
        self.data_table.setColumnWidth(4, 80)
        self.data_table.setColumnWidth(5, 150)
        self.data_table.setColumnWidth(6, 150)

        # Set header styles
        header = self.data_table.horizontalHeader()
        header.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Set cell styles
        self.data_table.setStyleSheet("""
            QTableWidget {
                background-color: #f5f5f5;
                gridline-color: #ddd;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #c8e6c9;
            }
        """)

        # Add alternating row colors
        self.data_table.setAlternatingRowColors(True)

        self.view_tab_layout.addWidget(self.data_table)

        self.refresh_button = QPushButton("Refresh Data")
        self.refresh_button.clicked.connect(self.refresh_data)
        self.view_tab_layout.addWidget(self.refresh_button)

        self.delete_button = QPushButton("Delete Selected Record")
        self.delete_button.clicked.connect(self.delete_record)
        self.view_tab_layout.addWidget(self.delete_button)

        self.refresh_data()  # Initial load of data

    def create_stats_tab(self):
        self.stats_tab = QWidget()
        self.tab_widget.addTab(self.stats_tab, "Statistics")

        self.stats_tab_layout = QVBoxLayout(self.stats_tab)
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(3)
        self.stats_table.setHorizontalHeaderLabels(["ID", "Name", "Tweet Time"])

        # Set header styles
        header = self.stats_table.horizontalHeader()
        header.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Set column widths
        self.stats_table.setColumnWidth(0, 50)
        self.stats_table.setColumnWidth(1, 200)
        self.stats_table.setColumnWidth(2, 150)

        # Set cell styles
        self.stats_table.setStyleSheet("""
            QTableWidget {
                background-color: #f5f5f5;
                gridline-color: #ddd;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #c8e6c9;
            }
        """)

        # Add alternating row colors
        self.stats_table.setAlternatingRowColors(True)

        self.stats_tab_layout.addWidget(self.stats_table)

        # Add Refresh Button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.update_stats)
        self.stats_tab_layout.addWidget(self.refresh_button)

        self.update_stats()


    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Media Files", "", "All Files (*);;Text Files (*.txt)")
        self.media_files = files
        
        self.media_list_widget.clear()
        for file in self.media_files:
            self.media_list_widget.addItem(file)

    def add_time(self):
        hour = self.hour_combo.currentText()
        minute = self.minute_combo.currentText()
        time = f"{hour}:{minute}"
        if time not in self.tweet_times:
            self.tweet_times.append(time)
            self.tweet_times.sort()
            self.update_time_list_widget()

    def remove_time(self):
        selected_items = self.tweet_times_list_widget.selectedItems()
        if selected_items:
            selected_item = selected_items[0].text()
            self.tweet_times.remove(selected_item)
            self.update_time_list_widget()

    def update_time_list_widget(self):
        self.tweet_times_list_widget.clear()
        for time in self.tweet_times:
            self.tweet_times_list_widget.addItem(time)

    def submit(self):
        name = self.name_input.text()
        text = self.text_input.toPlainText()
        media_files = getattr(self, 'media_files', [])
        is_link = self.is_link_check.isChecked()

        week_days = [day for day, checkbox in self.week_day_checkboxes.items() if checkbox.isChecked()]
        tweet_times = self.tweet_times

        # Here, you would normally save to the database, but for now, we'll just print.
        print(f"Submitting:\nName: {name}\nText: {text}\nMedia: {media_files}\nIs Link: {is_link}\nWeek Days: {week_days}\nTweet Times: {tweet_times}")

        # Save to database
        err_code = save_complete_tpd(name, text, is_link, media_files, week_days, tweet_times)

        # Update status label based on result
        if err_code == 0:
            self.status_label.setText("Done")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("Error")
            self.status_label.setStyleSheet("color: red;")
        
        # Start timer to clear status label after 3 seconds
        self.timer.start(5000)

        # Clear all fields
        self.name_input.clear()
        self.text_input.clear()
        self.is_link_check.setChecked(False)

        self.media_files = []
        self.media_list_widget.clear()

        self.tweet_times = []
        self.update_time_list_widget()

        # Reset all checkboxes
        for checkbox in self.week_day_checkboxes.values():
            checkbox.setChecked(False)

    def clear_status(self):
        self.status_label.setText("")

    def refresh_data(self):
        # Clear existing rows
        self.data_table.setRowCount(0)
        
        # Fetch the data from the database
        data = select_from_db_view_data()
        
        if data is None:
            data = []  # Default to an empty list if None is returned

        # Populate the table
        for row_data in data:
            row_position = self.data_table.rowCount()
            self.data_table.insertRow(row_position)
            for column, value in enumerate(row_data):
                self.data_table.setItem(row_position, column, QTableWidgetItem(str(value)))

    def delete_record(self):
        selected_row = self.data_table.currentRow()
        if selected_row >= 0:
            item_id = self.data_table.item(selected_row, 0).text()
            
            # Delete the record from the database
            err_code = delete_record_from_db(item_id)
            
            if err_code == 0:
                # Remove the row from the table
                self.data_table.removeRow(selected_row)
                # Optionally show a success message
                self.status_label.setText("Record deleted successfully")
                self.status_label.setStyleSheet("color: green;")
                self.timer.start(5000)  # Clear status after 5 seconds
            else:
                # Optionally show an error message
                self.status_label.setText("Error deleting record")
                self.status_label.setStyleSheet("color: red;")
                self.timer.start(5000)  # Clear status after 5 seconds

    def update_stats(self):
        # Fetch the data from the database
        data = select_from_db_stats()

        if data is None:
            data = []  # Default to an empty list if None is returned
    
        self.stats_table.setRowCount(0)  # Clear existing rows

        # Assuming data is a list of tuples: (id, name, tweet_time)
        for row_data in data:
            row_position = self.stats_table.rowCount()
            self.stats_table.insertRow(row_position)
            for column, value in enumerate(row_data):
                self.stats_table.setItem(row_position, column, QTableWidgetItem(str(value)))

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())

