import sys
import sqlite3
from PyQt6 import QtWidgets, QtGui, QtCore
import pandas as pd

def initialize_database():
    conn = sqlite3.connect('cinema.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            birth_date TEXT,
            role TEXT NOT NULL
        )
    ''')

    # Создание таблицы фильмов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT,
            time TEXT
        )
    ''')

    # Создание таблицы билетов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            movie_id INTEGER,
            seat_number TEXT,
            purchase_date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(movie_id) REFERENCES movies(id)
        )
    ''')

    # Вставка примерных данных пользователей
    cursor.execute('''
        INSERT OR IGNORE INTO users (full_name, username, password, phone, email, birth_date, role)
        VALUES
        ('Admin User', 'admin', 'adminpass', '1234567890', 'admin@example.com', '1980-01-01', 'admin'),
        ('John Doe', 'johndoe', 'password123', '0987654321', 'john@example.com', '1990-05-15', 'user')
    ''')

    # Вставка примерных данных фильмов
    cursor.execute('''
        INSERT OR IGNORE INTO movies (title, description, date, time)
        VALUES
        ('Фильм 1', 'Захватывающий приключенческий фильм.', '2024-11-26', '18:00'),
        ('Фильм 2', 'Драматическая история.', '2024-11-27', '20:00')
    ''')

    conn.commit()
    conn.close()

initialize_database()

# Главный класс приложения
class CinemaApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Система бронирования кинотеатра')
        self.setFixedSize(800, 600)

        # Создаем центральный виджет
        self.central_widget = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.central_widget)

        # Текущий пользователь
        self.current_user = None
        self.selected_movie_id = None

        # Инициализация экранов
        self.login_screen = LoginScreen(self)
        self.session_screen = SessionScreen(self)
        self.purchase_screen = PurchaseScreen(self)
        self.thankyou_screen = ThankYouScreen(self)
        self.admin_screen = AdminScreen(self)

        # Добавление экранов в стек центрального виджета
        self.central_widget.addWidget(self.login_screen)
        self.central_widget.addWidget(self.session_screen)
        self.central_widget.addWidget(self.purchase_screen)
        self.central_widget.addWidget(self.thankyou_screen)
        self.central_widget.addWidget(self.admin_screen)

        self.central_widget.setCurrentWidget(self.login_screen)

        self.setStyleSheet('''
            QWidget {
                font-size: 14px;
            }
            QPushButton {
                background-color: #0078D7;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #005A9E;
            }
            QLineEdit, QTextEdit, QDateEdit, QTimeEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QLabel {
                font-weight: bold;
            }
            QTableWidget {
                gridline-color: #ddd;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #ddd;
            }
            QTabBar::tab {
                padding: 10px;
            }
            QMenuBar {
                background-color: #f0f0f0;
            }
            QMenuBar::item {
                background-color: transparent;
            }
            QMenuBar::item:selected {
                background-color: #e0e0e0;
            }
        ''')

    def setup_menu(self):
        # Создаем меню
        self.menu_bar = self.menuBar()
        self.menu_bar.clear()

        # Меню "Файл"
        file_menu = self.menu_bar.addMenu('Файл')

        # Пункт "Выход"
        exit_action = QtGui.QAction('Выход', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню "Пользователь"
        user_menu = self.menu_bar.addMenu('Пользователь')

        # Пункт "Выйти"
        logout_action = QtGui.QAction('Выйти', self)
        logout_action.triggered.connect(self.logout)
        user_menu.addAction(logout_action)

        # Если пользователь - админ, добавить пункт перехода в админку
        if self.current_user and self.current_user[7] == 'admin':
            admin_action = QtGui.QAction('Панель администратора', self)
            admin_action.triggered.connect(lambda: self.central_widget.setCurrentWidget(self.admin_screen))
            user_menu.addAction(admin_action)

    def logout(self):
        self.current_user = None
        self.menuBar().clear()
        self.central_widget.setCurrentWidget(self.login_screen)

# Экран входа и регистрации
class LoginScreen(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # Вкладки для входа и регистрации
        tabs = QtWidgets.QTabWidget()
        login_tab = QtWidgets.QWidget()
        register_tab = QtWidgets.QWidget()
        tabs.addTab(login_tab, 'Вход')
        tabs.addTab(register_tab, 'Регистрация')

        # Вкладка входа
        login_layout = QtWidgets.QFormLayout()
        self.login_username = QtWidgets.QLineEdit()
        self.login_password = QtWidgets.QLineEdit()
        self.login_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        login_button = QtWidgets.QPushButton('Войти')
        login_button.clicked.connect(self.handle_login)
        login_layout.addRow('Логин:', self.login_username)
        login_layout.addRow('Пароль:', self.login_password)
        login_layout.addRow(login_button)
        login_tab.setLayout(login_layout)

        # Вкладка регистрации
        register_layout = QtWidgets.QFormLayout()
        self.reg_full_name = QtWidgets.QLineEdit()
        self.reg_username = QtWidgets.QLineEdit()
        self.reg_password = QtWidgets.QLineEdit()
        self.reg_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.reg_phone = QtWidgets.QLineEdit()
        self.reg_email = QtWidgets.QLineEdit()
        self.reg_birth_date = QtWidgets.QDateEdit()
        self.reg_birth_date.setCalendarPopup(True)
        register_button = QtWidgets.QPushButton('Зарегистрироваться')
        register_button.clicked.connect(self.handle_registration)
        register_layout.addRow('ФИО:', self.reg_full_name)
        register_layout.addRow('Логин:', self.reg_username)
        register_layout.addRow('Пароль:', self.reg_password)
        register_layout.addRow('Номер телефона:', self.reg_phone)
        register_layout.addRow('Электронная почта:', self.reg_email)
        register_layout.addRow('Дата рождения:', self.reg_birth_date)
        register_layout.addRow(register_button)
        register_tab.setLayout(register_layout)

        layout.addWidget(tabs)
        self.setLayout(layout)

    def handle_login(self):
        username = self.login_username.text()
        password = self.login_password.text()

        conn = sqlite3.connect('cinema.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM users WHERE username=? AND password=?
        ''', (username, password))
        result = cursor.fetchone()
        conn.close()

        if result:
            self.parent.current_user = result
            role = result[7]
            QtWidgets.QMessageBox.information(self, 'Успех', 'Вы успешно вошли в систему!')
            self.parent.setup_menu()
            if role == 'admin':
                self.parent.central_widget.setCurrentWidget(self.parent.admin_screen)
            else:
                self.parent.central_widget.setCurrentWidget(self.parent.session_screen)
        else:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Неправильный логин или пароль.')

    def handle_registration(self):
        full_name = self.reg_full_name.text()
        username = self.reg_username.text()
        password = self.reg_password.text()
        phone = self.reg_phone.text()
        email = self.reg_email.text()
        birth_date = self.reg_birth_date.date().toString('yyyy-MM-dd')

        conn = sqlite3.connect('cinema.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (full_name, username, password, phone, email, birth_date, role)
                VALUES (?, ?, ?, ?, ?, ?, 'user')
            ''', (full_name, username, password, phone, email, birth_date))
            conn.commit()
            QtWidgets.QMessageBox.information(self, 'Успех', 'Регистрация прошла успешно!')
        except sqlite3.IntegrityError:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Логин уже существует.')
        conn.close()

# Экран выбора сеансов
class SessionScreen(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['ID', 'Название', 'Дата', 'Время'])
        self.load_sessions()
        self.table.doubleClicked.connect(self.select_session)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)

        layout.addWidget(QtWidgets.QLabel('Выберите сеанс'))
        layout.addWidget(self.table)

        # Кнопка выхода из учетной записи
        logout_button = QtWidgets.QPushButton('Выйти')
        logout_button.clicked.connect(self.parent.logout)
        layout.addWidget(logout_button, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)

    def load_sessions(self):
        conn = sqlite3.connect('cinema.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, title, date, time FROM movies')
        sessions = cursor.fetchall()
        conn.close()

        self.table.setRowCount(0)
        for row_number, row_data in enumerate(sessions):
            self.table.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.table.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(str(data)))

    def select_session(self):
        selected_row = self.table.currentRow()
        self.parent.selected_movie_id = int(self.table.item(selected_row, 0).text())
        self.parent.central_widget.setCurrentWidget(self.parent.purchase_screen)

# Экран покупки билета
class PurchaseScreen(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.selected_seat = None
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        self.label = QtWidgets.QLabel('Покупка билета')
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        # Отображение схемы зала с местами
        self.seat_layout = QtWidgets.QGridLayout()
        layout.addLayout(self.seat_layout)

        buy_button = QtWidgets.QPushButton('Купить')
        buy_button.clicked.connect(self.purchase_ticket)
        layout.addWidget(buy_button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        back_button = QtWidgets.QPushButton('Назад к сеансам')
        back_button.clicked.connect(lambda: self.parent.central_widget.setCurrentWidget(self.parent.session_screen))
        layout.addWidget(back_button, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)

    def showEvent(self, event):
        super().showEvent(event)
        self.load_seats()

    def load_seats(self):
        # Очистка предыдущей схемы
        for i in reversed(range(self.seat_layout.count())):
            self.seat_layout.itemAt(i).widget().setParent(None)

        # Размеры зала
        rows = 5
        cols = 10

        # Получение занятых мест
        conn = sqlite3.connect('cinema.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT seat_number FROM tickets WHERE movie_id=?
        ''', (self.parent.selected_movie_id,))
        occupied_seats = [seat[0] for seat in cursor.fetchall()]
        conn.close()

        for row in range(rows):
            for col in range(cols):
                seat_number = f'{row + 1}-{col + 1}'
                button = QtWidgets.QPushButton(seat_number)
                button.setFixedSize(50, 50)
                button.setCheckable(True)
                if seat_number in occupied_seats:
                    button.setEnabled(False)
                    button.setStyleSheet('background-color: gray; color: white;')
                else:
                    button.clicked.connect(self.select_seat)
                self.seat_layout.addWidget(button, row, col)

    def select_seat(self):
        button = self.sender()
        if button.isChecked():
            self.selected_seat = button.text()
            # Снятие выделения с других кнопок
            for i in range(self.seat_layout.count()):
                btn = self.seat_layout.itemAt(i).widget()
                if btn != button:
                    btn.setChecked(False)
        else:
            self.selected_seat = None

    def purchase_ticket(self):
        try:
            if not self.selected_seat:
                QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Выберите место для покупки.')
                return

            seat = self.selected_seat
            user_id = self.parent.current_user[0]
            movie_id = self.parent.selected_movie_id

            conn = sqlite3.connect('cinema.db')
            cursor = conn.cursor()

            # Проверка, что место свободно
            cursor.execute('''
                SELECT * FROM tickets WHERE movie_id=? AND seat_number=?
            ''', (movie_id, seat))
            if cursor.fetchone():
                QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Это место уже занято.')
                conn.close()
                self.load_seats()
                return

            # Вставка нового билета
            cursor.execute('''
                INSERT INTO tickets (user_id, movie_id, seat_number, purchase_date)
                VALUES (?, ?, ?, DATE('now'))
            ''', (user_id, movie_id, seat))
            conn.commit()
            conn.close()

            QtWidgets.QMessageBox.information(self, 'Успех', 'Билет успешно приобретен!')
            self.load_seats()  # Обновляем схему мест
            self.selected_seat = None
            self.parent.central_widget.setCurrentWidget(self.parent.thankyou_screen)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка: {str(e)}')

# Экран "Спасибо за покупку"
class ThankYouScreen(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()
        thank_you_label = QtWidgets.QLabel('Спасибо за покупку!')
        thank_you_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(thank_you_label)

        back_button = QtWidgets.QPushButton('Вернуться к сеансам')
        back_button.clicked.connect(self.go_back)
        layout.addWidget(back_button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

    def go_back(self):
        self.parent.central_widget.setCurrentWidget(self.parent.session_screen)

# Панель администратора
class AdminScreen(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout()

        # Вкладки для администратора
        tabs = QtWidgets.QTabWidget()
        sessions_tab = QtWidgets.QWidget()
        users_tab = QtWidgets.QWidget()
        stats_tab = QtWidgets.QWidget()
        tabs.addTab(sessions_tab, 'Управление сеансами')
        tabs.addTab(users_tab, 'Данные пользователей')
        tabs.addTab(stats_tab, 'Статистика')

        # Вкладка управления сеансами
        sessions_layout = QtWidgets.QVBoxLayout()
        self.sessions_table = QtWidgets.QTableWidget()
        self.sessions_table.setColumnCount(5)
        self.sessions_table.setHorizontalHeaderLabels(['ID', 'Название', 'Описание', 'Дата', 'Время'])
        self.load_sessions()
        self.sessions_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sessions_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        add_session_button = QtWidgets.QPushButton('Добавить сеанс')
        add_session_button.clicked.connect(self.add_session)
        delete_session_button = QtWidgets.QPushButton('Удалить сеанс')
        delete_session_button.clicked.connect(self.delete_session)
        sessions_layout.addWidget(self.sessions_table)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(add_session_button)
        buttons_layout.addWidget(delete_session_button)
        sessions_layout.addLayout(buttons_layout)
        sessions_tab.setLayout(sessions_layout)

        # Вкладка данных пользователей
        users_layout = QtWidgets.QVBoxLayout()
        self.users_table = QtWidgets.QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels(['ID', 'ФИО', 'Логин', 'Телефон', 'Email', 'Дата рождения', 'Роль'])
        self.load_users()
        self.users_table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.users_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        users_layout.addWidget(self.users_table)
        users_tab.setLayout(users_layout)

        # Вкладка статистики
        stats_layout = QtWidgets.QVBoxLayout()
        export_button = QtWidgets.QPushButton('Выгрузить статистику в Excel')
        export_button.clicked.connect(self.export_stats)
        stats_layout.addWidget(export_button, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)
        stats_tab.setLayout(stats_layout)

        layout.addWidget(tabs)

        # Кнопка выхода из учетной записи
        logout_button = QtWidgets.QPushButton('Выйти')
        logout_button.clicked.connect(self.parent.logout)
        layout.addWidget(logout_button, alignment=QtCore.Qt.AlignmentFlag.AlignRight)

        self.setLayout(layout)

    def load_sessions(self):
        conn = sqlite3.connect('cinema.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM movies')
        sessions = cursor.fetchall()
        conn.close()

        self.sessions_table.setRowCount(0)
        for row_number, row_data in enumerate(sessions):
            self.sessions_table.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.sessions_table.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(str(data)))

    def add_session(self):
        dialog = AddSessionDialog()
        if dialog.exec():
            title = dialog.title.text()
            description = dialog.description.toPlainText()
            date = dialog.date.date().toString('yyyy-MM-dd')
            time = dialog.time.time().toString('HH:mm')

            conn = sqlite3.connect('cinema.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO movies (title, description, date, time)
                VALUES (?, ?, ?, ?)
            ''', (title, description, date, time))
            conn.commit()
            conn.close()
            self.load_sessions()

    def delete_session(self):
        selected_row = self.sessions_table.currentRow()
        if selected_row >= 0:
            session_id = int(self.sessions_table.item(selected_row, 0).text())
            conn = sqlite3.connect('cinema.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM movies WHERE id=?', (session_id,))
            conn.commit()
            conn.close()
            self.load_sessions()
        else:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Выберите сеанс для удаления.')

    def load_users(self):
        conn = sqlite3.connect('cinema.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, full_name, username, phone, email, birth_date, role FROM users')
        users = cursor.fetchall()
        conn.close()

        self.users_table.setRowCount(0)
        for row_number, row_data in enumerate(users):
            self.users_table.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                self.users_table.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(str(data)))

    def export_stats(self):
        conn = sqlite3.connect('cinema.db')
        tickets_df = pd.read_sql_query('''
            SELECT tickets.id, users.full_name, movies.title, tickets.seat_number, tickets.purchase_date
            FROM tickets
            JOIN users ON tickets.user_id = users.id
            JOIN movies ON tickets.movie_id = movies.id
        ''', conn)
        conn.close()
        tickets_df.to_excel('ticket_stats.xlsx', index=False)
        QtWidgets.QMessageBox.information(self, 'Успех', 'Статистика успешно выгружена в ticket_stats.xlsx')

# Диалоговое окно добавления сеанса
class AddSessionDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Добавить сеанс')
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QFormLayout()
        self.title = QtWidgets.QLineEdit()
        self.description = QtWidgets.QTextEdit()
        self.date = QtWidgets.QDateEdit()
        self.date.setCalendarPopup(True)
        self.time = QtWidgets.QTimeEdit()
        add_button = QtWidgets.QPushButton('Добавить')
        add_button.clicked.connect(self.accept)

        layout.addRow('Название:', self.title)
        layout.addRow('Описание:', self.description)
        layout.addRow('Дата:', self.date)
        layout.addRow('Время:', self.time)
        layout.addRow(add_button)
        self.setLayout(layout)

# Запуск приложения
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    cinema_app = CinemaApp()
    cinema_app.show()
    sys.exit(app.exec())
