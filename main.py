import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                             QLabel, QPushButton, QProgressBar, QFrame, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import qdarkstyle
from core import scrape, analyze

class ScrapingThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.data = None

    def run(self):
        try:
            self.progress.emit(20)
            # Simulate scraping process
            matrix = scrape()
            self.progress.emit(60)
            
            self.progress.emit(80)
            ranked_data = analyze(matrix)
            self.progress.emit(100)
            
            self.finished.emit(ranked_data)
        except Exception as e:
            self.error.emit(str(e))

class StockTableWidget(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        # Set column headers
        headers = [
            "ID", "Company", "Opening", "Closing", "Change %", 
            "Monthly %", "Annual %", "P/E", "Dividend Yield", 
            "Volume", "Value", "Score"
        ]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Style the table
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSortingEnabled(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        
        # Set minimum sizes
        self.setMinimumSize(1200, 600)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.scraping_thread = None
        
    def setup_ui(self):
        self.setWindowTitle("Stock Market Analyzer - SGBV Algeria")
        self.setGeometry(100, 100, 1400, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = self.create_header()
        layout.addWidget(header)
        
        # Controls
        controls = self.create_controls()
        layout.addWidget(controls)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Table
        self.table_widget = StockTableWidget()
        layout.addWidget(self.table_widget)
        
        # Status bar
        self.status_label = QLabel("Ready to load data")
        layout.addWidget(self.status_label)
        
        # Apply dark theme
        self.apply_styles()
        
    def create_header(self):
        header_frame = QFrame()
        header_layout = QVBoxLayout(header_frame)
        
        title = QLabel("Stock Market Analysis - Algerian Stock Exchange")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        
        subtitle = QLabel("SGBV Debt Securities Market Data")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle.setFont(subtitle_font)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        
        return header_frame
        
    def create_controls(self):
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        
        self.load_button = QPushButton("Load Stock Data")
        self.load_button.clicked.connect(self.load_data)
        self.load_button.setMinimumHeight(40)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_data)
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.setEnabled(False)
        
        controls_layout.addWidget(self.load_button)
        controls_layout.addWidget(self.refresh_button)
        controls_layout.addStretch()
        
        return controls_frame
        
    def apply_styles(self):
        # Apply dark theme
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        
        # Custom styles
        custom_style = """
        QPushButton {
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #2a82da;
        }
        
        QTableWidget {
            gridline-color: #555555;
            border: 1px solid #555555;
        }
        
        QHeaderView::section {
            background-color: #2b2b2b;
            padding: 8px;
            border: 1px solid #555555;
            font-weight: bold;
        }
        """
        self.setStyleSheet(self.styleSheet() + custom_style)
        
    def load_data(self):
        """Start the scraping and analysis process"""
        self.set_loading_state(True)
        self.status_label.setText("Loading stock data...")
        
        self.scraping_thread = ScrapingThread()
        self.scraping_thread.finished.connect(self.on_data_loaded)
        self.scraping_thread.error.connect(self.on_error)
        self.scraping_thread.progress.connect(self.progress_bar.setValue)
        self.scraping_thread.start()
        
    def on_data_loaded(self, data):
        """Populate table with loaded data"""
        self.set_loading_state(False)
        self.populate_table(data)
        self.status_label.setText(f"Data loaded successfully - {len(data)} records found")
        self.refresh_button.setEnabled(True)
        
    def on_error(self, error_message):
        """Handle errors during scraping"""
        self.set_loading_state(False)
        self.status_label.setText("Error loading data")
        QMessageBox.critical(self, "Error", f"Failed to load data:\n{error_message}")
        
    def set_loading_state(self, loading):
        """Update UI for loading state"""
        self.load_button.setEnabled(not loading)
        self.refresh_button.setEnabled(not loading and self.table_widget.rowCount() > 0)
        self.progress_bar.setVisible(loading)
        
    def populate_table(self, data):
        """Populate the table with stock data"""
        self.table_widget.setRowCount(0)  # Clear existing data
        
        if not data:
            self.status_label.setText("No data available")
            return
            
        self.table_widget.setRowCount(len(data))
        
        # Color coding for positive/negative values
        positive_color = QColor(76, 175, 80)  # Green
        negative_color = QColor(244, 67, 54)  # Red
        
        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                
                # Apply color coding for numeric columns
                if col_idx in [4, 5, 6, 8, 11]:  # Change%, Monthly%, Annual%, Dividend, Score
                    try:
                        num_value = float(str(value).replace('%', ''))
                        if num_value > 0:
                            item.setForeground(positive_color)
                        elif num_value < 0:
                            item.setForeground(negative_color)
                    except ValueError:
                        pass
                
                # Center align numeric columns
                if col_idx >= 2:  # All columns after Company name
                    item.setTextAlignment(Qt.AlignCenter)
                
                self.table_widget.setItem(row_idx, col_idx, item)
        
        # Sort by score (highest first)
        self.table_widget.sortByColumn(11, Qt.DescendingOrder)
        
        # Resize columns to fit content
        self.table_widget.resizeColumnsToContents()
        
    def closeEvent(self, event):
        """Handle application close"""
        if self.scraping_thread and self.scraping_thread.isRunning():
            self.scraping_thread.terminate()
            self.scraping_thread.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Stock Market Analyzer")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("SGBV Analyzer")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
